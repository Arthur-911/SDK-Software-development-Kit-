"""HTTP transport layer handling authentication, retries, and error mapping."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from nasa_sdk.config import ClientConfig
from nasa_sdk.exceptions import (
    AuthenticationError,
    NasaAPIError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
)

RETRYABLE_STATUS_CODES: tuple[int, ...] = (429, 500, 502, 503, 504)
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
)


def _extract_retry_after(headers: httpx.Headers) -> float | None:
    """Extract Retry-After header value in seconds if present."""
    retry_after = headers.get("Retry-After")
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            return None
    return None


def _handle_response_error(response: httpx.Response) -> None:
    """Parse error response and raise the corresponding typed NasaAPIError."""
    status_code = response.status_code
    if status_code < 400:
        return

    try:
        body: Any = response.json()
        if isinstance(body, dict):
            # NASA APIs often return errors like {"error": {"message": ...}} or {"msg": ...}
            if "error" in body and isinstance(body["error"], dict):
                message = body["error"].get("message") or body["error"].get("code") or str(body)
            elif "error_message" in body:
                message = body["error_message"]
            elif "msg" in body:
                message = body["msg"]
            elif "message" in body:
                message = body["message"]
            else:
                message = response.text or f"HTTP {status_code} error from NASA API"
        else:
            message = str(body)
    except Exception:
        body = response.text
        message = response.text or f"HTTP {status_code} error from NASA API"

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
            message=f"NASA server error ({status_code}): {message}",
            status_code=status_code,
            response_body=body,
        )
    else:
        raise NasaAPIError(
            message=f"NASA API error ({status_code}): {message}",
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
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Execute a sync HTTP request with exponential backoff retries."""
        req_params: dict[str, Any] = dict(params or {})
        if "api_key" not in req_params:
            req_params["api_key"] = self.config.api_key

        req_timeout = timeout or self.config.timeout
        full_url = (
            path
            if path.startswith(("http://", "https://"))
            else f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        )

        attempt = 0
        while True:
            try:
                response = self._client.request(
                    method=method,
                    url=full_url,
                    params=req_params,
                    headers=headers,
                    timeout=req_timeout,
                )

                should_retry = (
                    response.status_code in RETRYABLE_STATUS_CODES
                    and attempt < self.config.max_retries
                )
                if should_retry:
                    retry_after = _extract_retry_after(response.headers)
                    sleep_time = (
                        retry_after
                        if retry_after is not None
                        else self.config.backoff_factor * (2**attempt)
                    )
                    time.sleep(sleep_time)
                    attempt += 1
                    continue

                _handle_response_error(response)
                json_data: dict[str, Any] | list[Any] = response.json()
                return json_data

            except RETRYABLE_EXCEPTIONS as exc:
                if attempt < self.config.max_retries:
                    sleep_time = self.config.backoff_factor * (2**attempt)
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
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Execute an async HTTP request with exponential backoff retries."""
        req_params: dict[str, Any] = dict(params or {})
        if "api_key" not in req_params:
            req_params["api_key"] = self.config.api_key

        req_timeout = timeout or self.config.timeout
        full_url = (
            path
            if path.startswith(("http://", "https://"))
            else f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        )

        attempt = 0
        while True:
            try:
                response = await self._client.request(
                    method=method,
                    url=full_url,
                    params=req_params,
                    headers=headers,
                    timeout=req_timeout,
                )

                should_retry = (
                    response.status_code in RETRYABLE_STATUS_CODES
                    and attempt < self.config.max_retries
                )
                if should_retry:
                    retry_after = _extract_retry_after(response.headers)
                    sleep_time = (
                        retry_after
                        if retry_after is not None
                        else self.config.backoff_factor * (2**attempt)
                    )
                    await asyncio.sleep(sleep_time)
                    attempt += 1
                    continue

                _handle_response_error(response)
                json_data: dict[str, Any] | list[Any] = response.json()
                return json_data

            except RETRYABLE_EXCEPTIONS as exc:
                if attempt < self.config.max_retries:
                    sleep_time = self.config.backoff_factor * (2**attempt)
                    await asyncio.sleep(sleep_time)
                    attempt += 1
                    continue
                raise TimeoutError(f"Request failed after {attempt + 1} attempts: {exc}") from exc
            except httpx.TimeoutException as exc:
                raise TimeoutError(f"Request timed out: {exc}") from exc
