"""HTTP transport layer for Server Developer Kit."""

from __future__ import annotations

import asyncio
import email.utils
import logging
import random
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Any

import httpx

from server_sdk.config import ClientConfig
from server_sdk.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
)

logger = logging.getLogger("server_sdk")

MAX_RETRY_AFTER_SECONDS = 300.0
MAX_ERROR_MESSAGE_LEN = 500
SENSITIVE_PARAM_NAMES = ("api_key", "token", "secret", "password", "key", "auth", "authorization")
RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
)


def _is_same_origin(url_a: str, url_b: str) -> bool:
    """Check if two URLs share the same scheme, host, and port."""
    parsed_a = urllib.parse.urlparse(url_a)
    parsed_b = urllib.parse.urlparse(url_b)
    return (parsed_a.scheme, parsed_a.netloc) == (parsed_b.scheme, parsed_b.netloc)


def _sanitize_params(
    params: dict[str, Any], extra_sensitive: set[str] | None = None
) -> dict[str, Any]:
    """Sanitize sensitive keys in query parameters for safe logging."""
    sanitized: dict[str, Any] = {}
    extra = extra_sensitive or set()
    for k, v in params.items():
        if k in extra or any(sensitive in k.lower() for sensitive in SENSITIVE_PARAM_NAMES):
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = v
    return sanitized


def _extract_retry_after(headers: httpx.Headers) -> float | None:
    """Extract Retry-After header value in seconds if present."""
    retry_after = headers.get("Retry-After")
    if not retry_after:
        return None
    try:
        seconds = float(retry_after)
        return max(0.0, min(seconds, MAX_RETRY_AFTER_SECONDS))
    except ValueError:
        pass

    try:
        parsed_date = email.utils.parsedate_to_datetime(retry_after)
        now = datetime.now(timezone.utc)
        seconds = (parsed_date - now).total_seconds()
        return max(0.0, min(seconds, MAX_RETRY_AFTER_SECONDS))
    except Exception:
        pass

    return None


def _calculate_sleep(
    backoff_factor: float,
    attempt: int,
    retry_after: float | None = None,
    jitter: bool = True,
) -> float:
    """Calculate exponential backoff sleep with optional randomized jitter."""
    if retry_after is not None:
        return max(0.0, min(float(retry_after), MAX_RETRY_AFTER_SECONDS))
    delay = backoff_factor * (2**attempt)
    if jitter:
        return float(random.uniform(0.5 * delay, 1.0 * delay))
    return float(delay)


def _parse_response_data(response: httpx.Response) -> Any:
    """Parse HTTP response payload safely handling 204 No Content, empty bodies, and JSON."""
    if response.status_code == 204 or not response.content:
        return None

    content_type = response.headers.get("Content-Type", "")
    if "application/json" in content_type or "+json" in content_type:
        return response.json()

    try:
        return response.json()
    except Exception:
        return response.text


def _truncate_msg(msg: str) -> str:
    """Truncate long raw error messages to prevent log flooding (CWE-400)."""
    return (msg[:MAX_ERROR_MESSAGE_LEN] + "...") if len(msg) > MAX_ERROR_MESSAGE_LEN else msg


def _handle_response_error(response: httpx.Response) -> None:
    """Parse error response and raise corresponding typed APIError."""
    status_code = response.status_code
    if status_code < 400:
        return

    try:
        body: Any = response.json()
        if isinstance(body, dict):
            if "error" in body and isinstance(body["error"], dict):
                raw_m = body["error"].get("message") or body["error"].get("code") or str(body)
                message = _truncate_msg(str(raw_m))
            elif "error_message" in body:
                message = _truncate_msg(str(body["error_message"]))
            elif "detail" in body:
                message = _truncate_msg(str(body["detail"]))
            elif "message" in body:
                message = _truncate_msg(str(body["message"]))
            else:
                raw_text = response.text or f"HTTP {status_code} server error"
                message = _truncate_msg(raw_text)
        else:
            message = _truncate_msg(str(body))
    except Exception:
        body = response.text
        raw_text = response.text or f"HTTP {status_code} server error"
        message = _truncate_msg(raw_text)

    if status_code in (401, 403):
        raise AuthenticationError(
            message=f"Authentication failed: {message}",
            status_code=status_code,
            response_body=body,
        )
    elif status_code == 404:
        raise NotFoundError(
            message=f"Resource not found: {message}",
            status_code=status_code,
            response_body=body,
        )
    elif status_code == 429:
        retry_after = _extract_retry_after(response.headers)
        raise RateLimitError(
            message=f"Rate limit exceeded: {message}",
            status_code=status_code,
            retry_after=retry_after,
            response_body=body,
        )
    elif 500 <= status_code <= 599:
        raise ServerError(
            message=f"Server error ({status_code}): {message}",
            status_code=status_code,
            response_body=body,
        )
    else:
        raise APIError(
            message=f"API error ({status_code}): {message}",
            status_code=status_code,
            response_body=body,
        )


class SyncTransport:
    """Synchronous HTTP transport with exponential backoff and connection pooling."""

    def __init__(
        self,
        config: ClientConfig,
        client: httpx.Client | None = None,
    ) -> None:
        self.config = config
        self._client = client or httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            headers=config.get_headers(),
        )
        self._owns_client = client is None

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._owns_client:
            self._client.close()

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Execute a sync HTTP request with exponential backoff retries."""
        req_headers = dict(headers or {})
        req_params = dict(params or {})

        req_timeout = timeout or self.config.timeout
        is_absolute = path.startswith(("http://", "https://"))
        full_url = (
            path
            if is_absolute
            else f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        )

        if not is_absolute or _is_same_origin(full_url, self.config.base_url):
            req_headers, req_params = self.config.auth.apply(req_headers, req_params)
        else:
            logger.warning(
                "Request targeted an external URL '%s' differing from configured base_url '%s'. "
                "Omitting credentials to prevent exfiltration.",
                full_url,
                self.config.base_url,
            )

        is_retryable_method = method.upper() in self.config.retry_methods
        attempt = 0
        while True:
            try:
                logger.debug(
                    "Request: %s %s params=%s",
                    method,
                    full_url,
                    _sanitize_params(req_params, self.config.auth.sensitive_params),
                )
                response = self._client.request(
                    method=method,
                    url=full_url,
                    params=req_params,
                    json=json,
                    headers=req_headers,
                    timeout=req_timeout,
                )
                logger.debug("Response: %s %s status=%d", method, full_url, response.status_code)

                should_retry = (
                    is_retryable_method
                    and response.status_code in RETRYABLE_STATUS_CODES
                    and attempt < self.config.max_retries
                )
                if should_retry:
                    retry_after = _extract_retry_after(response.headers)
                    sleep_time = _calculate_sleep(
                        self.config.backoff_factor,
                        attempt,
                        retry_after=retry_after,
                        jitter=self.config.jitter,
                    )
                    logger.warning(
                        "Status %d on %s %s. Retrying in %.2fs (attempt %d/%d)",
                        response.status_code,
                        method,
                        full_url,
                        sleep_time,
                        attempt + 1,
                        self.config.max_retries,
                    )
                    time.sleep(sleep_time)
                    attempt += 1
                    continue

                _handle_response_error(response)
                return _parse_response_data(response)

            except RETRYABLE_EXCEPTIONS as exc:
                if is_retryable_method and attempt < self.config.max_retries:
                    sleep_time = _calculate_sleep(
                        self.config.backoff_factor,
                        attempt,
                        jitter=self.config.jitter,
                    )
                    logger.warning(
                        "Request failed (%s). Retrying %s %s in %.2fs (attempt %d/%d)",
                        exc,
                        method,
                        full_url,
                        sleep_time,
                        attempt + 1,
                        self.config.max_retries,
                    )
                    time.sleep(sleep_time)
                    attempt += 1
                    continue
                raise TimeoutError(f"Request failed after {attempt + 1} attempts: {exc}") from exc
            except httpx.TimeoutException as exc:
                raise TimeoutError(f"Request timed out: {exc}") from exc


class AsyncTransport:
    """Asynchronous HTTP transport with exponential backoff and connection pooling."""

    def __init__(
        self,
        config: ClientConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self._client = client or httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            headers=config.get_headers(),
        )
        self._owns_client = client is None

    async def aclose(self) -> None:
        """Close the underlying async HTTP client."""
        if self._owns_client:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Execute an async HTTP request with exponential backoff retries."""
        req_headers = dict(headers or {})
        req_params = dict(params or {})

        req_timeout = timeout or self.config.timeout
        is_absolute = path.startswith(("http://", "https://"))
        full_url = (
            path
            if is_absolute
            else f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        )

        if not is_absolute or _is_same_origin(full_url, self.config.base_url):
            req_headers, req_params = self.config.auth.apply(req_headers, req_params)
        else:
            logger.warning(
                "Request targeted an external URL '%s' differing from configured base_url '%s'. "
                "Omitting credentials to prevent exfiltration.",
                full_url,
                self.config.base_url,
            )

        is_retryable_method = method.upper() in self.config.retry_methods
        attempt = 0
        while True:
            try:
                logger.debug(
                    "Async Request: %s %s params=%s",
                    method,
                    full_url,
                    _sanitize_params(req_params, self.config.auth.sensitive_params),
                )
                response = await self._client.request(
                    method=method,
                    url=full_url,
                    params=req_params,
                    json=json,
                    headers=req_headers,
                    timeout=req_timeout,
                )
                logger.debug(
                    "Async Response: %s %s status=%d", method, full_url, response.status_code
                )

                should_retry = (
                    is_retryable_method
                    and response.status_code in RETRYABLE_STATUS_CODES
                    and attempt < self.config.max_retries
                )
                if should_retry:
                    retry_after = _extract_retry_after(response.headers)
                    sleep_time = _calculate_sleep(
                        self.config.backoff_factor,
                        attempt,
                        retry_after=retry_after,
                        jitter=self.config.jitter,
                    )
                    logger.warning(
                        "Status %d on %s %s. Retrying in %.2fs (attempt %d/%d)",
                        response.status_code,
                        method,
                        full_url,
                        sleep_time,
                        attempt + 1,
                        self.config.max_retries,
                    )
                    await asyncio.sleep(sleep_time)
                    attempt += 1
                    continue

                _handle_response_error(response)
                return _parse_response_data(response)

            except RETRYABLE_EXCEPTIONS as exc:
                if is_retryable_method and attempt < self.config.max_retries:
                    sleep_time = _calculate_sleep(
                        self.config.backoff_factor,
                        attempt,
                        jitter=self.config.jitter,
                    )
                    logger.warning(
                        "Async request failed (%s). Retrying %s %s in %.2fs (attempt %d/%d)",
                        exc,
                        method,
                        full_url,
                        sleep_time,
                        attempt + 1,
                        self.config.max_retries,
                    )
                    await asyncio.sleep(sleep_time)
                    attempt += 1
                    continue
                raise TimeoutError(f"Request failed after {attempt + 1} attempts: {exc}") from exc
            except httpx.TimeoutException as exc:
                raise TimeoutError(f"Request timed out: {exc}") from exc
