"""Tests for sync and async transport, error translation, and retry logic."""

from __future__ import annotations

import socket
import ssl
import time

import httpx
import pytest

from server_sdk._transport import (
    AsyncTransport,
    CircuitBreaker,
    CircuitState,
    SyncTransport,
    _calculate_sleep,
    _check_payload_size,
    _create_ssl_context,
    _extract_retry_after,
    _handle_response_error,
    _is_same_origin,
    _parse_response_data,
    _sanitize_params,
    _validate_header_injection,
    _validate_target_url,
)
from server_sdk.auth import BearerAuth
from server_sdk.config import ClientConfig
from server_sdk.exceptions import (
    APIError,
    AuthenticationError,
    CircuitBreakerOpenError,
    NotFoundError,
    PayloadTooLargeError,
    RateLimitError,
    SecurityError,
    ServerError,
    SSRFError,
    TimeoutError,
)


def test_extract_retry_after() -> None:
    headers_valid = httpx.Headers({"Retry-After": "10"})
    assert _extract_retry_after(headers_valid) == 10.0

    headers_invalid = httpx.Headers({"Retry-After": "invalid-int"})
    assert _extract_retry_after(headers_invalid) is None

    headers_empty = httpx.Headers({})
    assert _extract_retry_after(headers_empty) is None

    # Clamping large values
    headers_large = httpx.Headers({"Retry-After": "999999"})
    assert _extract_retry_after(headers_large) == 300.0

    # Negative values clamped to 0
    headers_neg = httpx.Headers({"Retry-After": "-10"})
    assert _extract_retry_after(headers_neg) == 0.0

    # HTTP-date format
    headers_date = httpx.Headers({"Retry-After": "Wed, 21 Oct 2040 07:28:00 GMT"})
    extracted_date = _extract_retry_after(headers_date)
    assert extracted_date is not None and extracted_date > 0.0

    # Non-date string exception handled
    headers_bad_date = httpx.Headers({"Retry-After": "NotADate 9999"})
    assert _extract_retry_after(headers_bad_date) is None


def test_sanitize_params() -> None:
    raw = {
        "api_key": "secret",
        "user": "alice",
        "auth_token": "xyz",
        "limit": 10,
        "custom_id": "abc",
    }
    sanitized = _sanitize_params(raw, extra_sensitive={"custom_id"})
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["auth_token"] == "[REDACTED]"
    assert sanitized["custom_id"] == "[REDACTED]"
    assert sanitized["user"] == "alice"
    assert sanitized["limit"] == 10


def test_is_same_origin() -> None:
    assert _is_same_origin("https://api.example.com/v1", "https://api.example.com/v2") is True
    assert _is_same_origin("https://api.example.com:8080/v1", "https://api.example.com/v1") is False
    assert _is_same_origin("http://api.example.com/v1", "https://api.example.com/v1") is False
    assert _is_same_origin("https://api.example.com", "https://evil.com") is False


def test_handle_response_error_status_less_than_400() -> None:
    response = httpx.Response(200, json={"status": "ok"})
    _handle_response_error(response)


def test_handle_response_error_variants() -> None:
    # 401 error with {"error": {"message": "Invalid token", "code": "UNAUTHORIZED"}}
    res_401 = httpx.Response(
        401, json={"error": {"message": "Invalid token", "code": "UNAUTHORIZED"}}
    )
    with pytest.raises(AuthenticationError) as exc_auth:
        _handle_response_error(res_401)
    assert "Invalid token" in str(exc_auth.value)
    assert exc_auth.value.status_code == 401

    # 403 error with {"error": {"code": "KEY_EXPIRED"}} (message absent)
    res_403 = httpx.Response(403, json={"error": {"code": "KEY_EXPIRED"}})
    with pytest.raises(AuthenticationError) as exc_403_info:
        _handle_response_error(res_403)
    assert "KEY_EXPIRED" in str(exc_403_info.value)

    # 403 error with {"error": "simple string"}
    res_403_str = httpx.Response(403, json={"error": "simple string error"})
    with pytest.raises(AuthenticationError):
        _handle_response_error(res_403_str)

    # 404 error with {"detail": "Resource not found"}
    res_404_detail = httpx.Response(404, json={"detail": "Resource not found"})
    with pytest.raises(NotFoundError) as exc_404_detail:
        _handle_response_error(res_404_detail)
    assert "Resource not found" in str(exc_404_detail.value)

    # 404 error with {"error_message": "User not found"}
    res_404 = httpx.Response(404, json={"error_message": "User not found"})
    with pytest.raises(NotFoundError) as exc_404:
        _handle_response_error(res_404)
    assert "User not found" in str(exc_404.value)

    # 429 error with {"message": "Rate limit exceeded"} and Retry-After header
    res_429 = httpx.Response(
        429, headers={"Retry-After": "5.0"}, json={"message": "Rate limit exceeded"}
    )
    with pytest.raises(RateLimitError) as exc_rate:
        _handle_response_error(res_429)
    assert exc_rate.value.retry_after == 5.0

    # 500 error with {"message": "Internal error"}
    res_500 = httpx.Response(500, json={"message": "Internal failure"})
    with pytest.raises(ServerError):
        _handle_response_error(res_500)

    # Generic error with other status and arbitrary JSON dict
    res_418_dict = httpx.Response(418, json={"custom": "teapot"})
    with pytest.raises(APIError) as exc_api_dict:
        _handle_response_error(res_418_dict)
    assert exc_api_dict.value.status_code == 418

    # Generic error with non-dict json (e.g. list)
    res_418 = httpx.Response(418, json=["teapot error"])
    with pytest.raises(APIError) as exc_api:
        _handle_response_error(res_418)
    assert exc_api.value.status_code == 418

    # Non-json response (HTML or plaintext)
    res_html = httpx.Response(502, text="<html>502 Bad Gateway</html>")
    with pytest.raises(ServerError) as exc_server:
        _handle_response_error(res_html)
    assert "502 Bad Gateway" in str(exc_server.value)

    # Empty body
    res_empty = httpx.Response(400, text="")
    with pytest.raises(APIError):
        _handle_response_error(res_empty)

    # Long body is truncated
    res_long = httpx.Response(500, text="LONG_ERROR " * 100)
    with pytest.raises(ServerError) as exc_long:
        _handle_response_error(res_long)
    assert str(exc_long.value).endswith("...")


def test_sync_transport_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "other.com" in str(request.url):
            assert "Authorization" not in request.headers
        else:
            assert request.headers.get("Authorization") == "Bearer secret-token"
        return httpx.Response(200, json={"result": "ok"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ClientConfig(base_url="https://api.example.com", auth=BearerAuth("secret-token"))
    transport = SyncTransport(config=config, client=client)

    result = transport.request("GET", "/test")
    assert result == {"result": "ok"}

    # Absolute URL on same origin
    result_abs = transport.request("GET", "https://api.example.com/test")
    assert result_abs == {"result": "ok"}

    # External origin strips credentials
    result_ext = transport.request("GET", "https://other.com/external")
    assert result_ext == {"result": "ok"}
    transport.close()


def test_sync_transport_owns_client_close() -> None:
    config = ClientConfig()
    transport = SyncTransport(config=config)
    assert transport._owns_client is True
    transport.close()


def test_sync_transport_retry_on_500_and_succeed() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(500, json={"error": "temporary error"})
        return httpx.Response(200, json={"status": "recovered"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=2, backoff_factor=0.01)
    transport = SyncTransport(config=config, client=client)

    res = transport.request("GET", "/retry")
    assert res == {"status": "recovered"}
    assert attempts == 2


def test_sync_transport_retry_on_429_with_retry_after() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "0.01"}, json={"detail": "wait"})
        return httpx.Response(200, json={"status": "ok"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=2, backoff_factor=0.01)
    transport = SyncTransport(config=config, client=client)

    res = transport.request("GET", "/rate-limited")
    assert res == {"status": "ok"}
    assert attempts == 2


def test_sync_transport_retryable_exception_and_recover() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectError("Connection dropped")
        return httpx.Response(200, json={"status": "connected"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=2, backoff_factor=0.01)
    transport = SyncTransport(config=config, client=client)

    res = transport.request("GET", "/connect")
    assert res == {"status": "connected"}
    assert attempts == 2


def test_sync_transport_exceeds_retries_on_exception() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Always fails")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=1, backoff_factor=0.01)
    transport = SyncTransport(config=config, client=client)

    with pytest.raises(TimeoutError, match="Request failed after 2 attempts"):
        transport.request("GET", "/fail")


def test_sync_transport_timeout_exception() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.PoolTimeout("Pool exhausted")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=0)
    transport = SyncTransport(config=config, client=client)

    with pytest.raises(TimeoutError):
        transport.request("GET", "/timeout")


@pytest.mark.asyncio
async def test_async_transport_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "other.com" in str(request.url):
            assert "Authorization" not in request.headers
        else:
            assert request.headers.get("Authorization") == "Bearer async-token"
        return httpx.Response(200, json={"async": "ok"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = ClientConfig(base_url="https://api.example.com", auth=BearerAuth("async-token"))
    transport = AsyncTransport(config=config, client=client)

    result = await transport.request("GET", "/async-test")
    assert result == {"async": "ok"}

    # Same origin absolute URL
    result_abs = await transport.request("GET", "https://api.example.com/async-test")
    assert result_abs == {"async": "ok"}

    # External origin strips credentials
    result_ext = await transport.request("GET", "https://other.com/async-external")
    assert result_ext == {"async": "ok"}
    await transport.aclose()


@pytest.mark.asyncio
async def test_async_transport_owns_client_close() -> None:
    config = ClientConfig()
    transport = AsyncTransport(config=config)
    assert transport._owns_client is True
    await transport.aclose()


@pytest.mark.asyncio
async def test_async_transport_retry_on_503_and_succeed() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, json={"error": "Service Unavailable"})
        return httpx.Response(200, json={"status": "online"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=2, backoff_factor=0.01)
    transport = AsyncTransport(config=config, client=client)

    res = await transport.request("GET", "/retry")
    assert res == {"status": "online"}
    assert attempts == 2


@pytest.mark.asyncio
async def test_async_transport_retry_on_429_with_retry_after() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "0.01"}, json={"detail": "wait"})
        return httpx.Response(200, json={"status": "ok"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=2, backoff_factor=0.01)
    transport = AsyncTransport(config=config, client=client)

    res = await transport.request("GET", "/retry")
    assert res == {"status": "ok"}
    assert attempts == 2


@pytest.mark.asyncio
async def test_async_transport_retryable_exception_and_recover() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectError("Async connection dropped")
        return httpx.Response(200, json={"status": "connected"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=2, backoff_factor=0.01)
    transport = AsyncTransport(config=config, client=client)

    res = await transport.request("GET", "/connect")
    assert res == {"status": "connected"}
    assert attempts == 2


@pytest.mark.asyncio
async def test_async_transport_exceeds_retries_on_exception() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Async permanent fail")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=1, backoff_factor=0.01)
    transport = AsyncTransport(config=config, client=client)

    with pytest.raises(TimeoutError, match="Request failed after 2 attempts"):
        await transport.request("GET", "/fail")


@pytest.mark.asyncio
async def test_async_transport_timeout_exception() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.PoolTimeout("Async pool timeout")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=0)
    transport = AsyncTransport(config=config, client=client)

    with pytest.raises(TimeoutError):
        await transport.request("GET", "/timeout")


def test_calculate_sleep() -> None:
    # Deterministic without jitter
    assert _calculate_sleep(0.5, 0, jitter=False) == 0.5
    assert _calculate_sleep(0.5, 2, jitter=False) == 2.0
    # Explicit retry-after takes precedence
    assert _calculate_sleep(0.5, 2, retry_after=7.5, jitter=False) == 7.5
    # With jitter
    sleep_val = _calculate_sleep(1.0, 1, jitter=True)
    assert 1.0 <= sleep_val <= 2.0


def test_parse_response_data() -> None:
    # 204 No Content
    res_204 = httpx.Response(204, content=b"")
    assert _parse_response_data(res_204) is None

    # 200 with empty body
    res_empty = httpx.Response(200, content=b"")
    assert _parse_response_data(res_empty) is None

    # Application JSON
    res_json = httpx.Response(
        200,
        headers={"Content-Type": "application/json"},
        content=b'{"ok": true}',
    )
    assert _parse_response_data(res_json) == {"ok": True}

    # Text / plain fallback
    res_text = httpx.Response(
        200,
        headers={"Content-Type": "text/plain"},
        content=b"pong plaintext",
    )
    assert _parse_response_data(res_text) == "pong plaintext"


def test_non_retryable_method_fails_immediately() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(500, json={"error": "db down"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    # POST is not in retry_methods by default
    config = ClientConfig(max_retries=3, backoff_factor=0.01)
    transport = SyncTransport(config=config, client=client)

    with pytest.raises(ServerError):
        transport.request("POST", "/create")

    assert attempts == 1


@pytest.mark.asyncio
async def test_async_non_retryable_method_fails_immediately() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(500, json={"error": "async db down"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=3, backoff_factor=0.01)
    transport = AsyncTransport(config=config, client=client)

    with pytest.raises(ServerError):
        await transport.request("POST", "/async-create")

    assert attempts == 1


@pytest.mark.asyncio
async def test_async_transport_204_and_empty() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = AsyncTransport(config=ClientConfig(), client=client)
    res = await transport.request("DELETE", "/item/1")
    assert res is None


def test_circuit_breaker_unit() -> None:
    cb = CircuitBreaker(failure_threshold=2, recovery_time=0.05, enabled=True)
    assert cb.state is CircuitState.CLOSED
    cb.check_state()

    cb.record_failure()
    assert cb.state is CircuitState.CLOSED

    cb.record_failure()
    current_state: CircuitState = cb.state
    assert current_state is CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpenError):
        cb.check_state()

    time.sleep(0.06)
    half_open_state: CircuitState = cb.state
    assert half_open_state is CircuitState.HALF_OPEN

    cb.record_success()
    final_state: CircuitState = cb.state
    assert final_state is CircuitState.CLOSED
    assert cb._consecutive_failures == 0

    # Disabled circuit breaker does nothing
    cb_disabled = CircuitBreaker(enabled=False)
    cb_disabled.record_failure()
    cb_disabled.record_success()
    cb_disabled.check_state()


def test_ssl_context_creation() -> None:
    assert _create_ssl_context(verify=False) is False
    ctx_12 = _create_ssl_context(verify=True, min_tls_version="TLSv1_2")
    assert isinstance(ctx_12, ssl.SSLContext)
    ctx_13 = _create_ssl_context(verify=True, min_tls_version="TLSv1_3")
    assert isinstance(ctx_13, ssl.SSLContext)


def test_validate_target_url_ssrf_mitigation() -> None:
    with pytest.raises(SSRFError, match="Disallowed URL scheme"):
        _validate_target_url("ftp://example.com", False, True)

    with pytest.raises(SSRFError, match="does not contain a valid hostname"):
        _validate_target_url("http://", False, True)

    with pytest.raises(SSRFError, match="Requests to localhost 'localhost' are blocked"):
        _validate_target_url("http://localhost:8080", False, False)

    with pytest.raises(SSRFError, match="cloud metadata endpoint"):
        _validate_target_url("http://metadata.google.internal/v1", False, True)

    with pytest.raises(SSRFError, match=r"Requests to loopback IP '127\.0\.0\.1' are blocked"):
        _validate_target_url("http://127.0.0.1:8080", False, False)

    # Allowed loopback
    _validate_target_url("http://127.0.0.1:8080", False, True)

    with pytest.raises(SSRFError, match="Requests to private or reserved IP"):
        _validate_target_url("http://10.0.0.1", False, True)

    with pytest.raises(SSRFError, match="Requests to private or reserved IP"):
        _validate_target_url("http://169.254.169.254", False, True)

    # Allowed when allow_private_ips=True
    _validate_target_url("http://10.0.0.1", True, True)
    _validate_target_url("http://api.example.com", True, True)


def test_validate_target_url_dns_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "gethostbyname", lambda host: "127.0.0.1")
    with pytest.raises(SSRFError, match="resolved to loopback IP"):
        _validate_target_url("http://loopback.test", False, False)

    monkeypatch.setattr(socket, "gethostbyname", lambda host: "192.168.1.1")
    with pytest.raises(SSRFError, match="resolved to private/reserved IP"):
        _validate_target_url("http://internal.company", False, True)

    def raise_gai(host: str) -> str:
        raise socket.gaierror("lookup failed")

    monkeypatch.setattr(socket, "gethostbyname", raise_gai)
    _validate_target_url("http://unknown.test", False, True)


def test_validate_header_injection() -> None:
    _validate_header_injection({"X-Good": "safe"})

    with pytest.raises(SecurityError, match="CRLF control character detected"):
        _validate_header_injection({"X-Bad\r": "val"})

    with pytest.raises(SecurityError, match="CRLF control character detected"):
        _validate_header_injection({"X-Bad": "val\n"})


def test_check_payload_size() -> None:
    res_cl = httpx.Response(200, headers={"Content-Length": "5000"}, content=b"x")
    with pytest.raises(PayloadTooLargeError, match="Response Content-Length"):
        _check_payload_size(res_cl, 1000)

    res_bad_cl = httpx.Response(200, headers={"Content-Length": "not-a-number"}, content=b"small")
    _check_payload_size(res_bad_cl, 1000)

    res_body = httpx.Response(200, content=b"x" * 2000)
    del res_body.headers["content-length"]
    with pytest.raises(PayloadTooLargeError, match="Response body"):
        _check_payload_size(res_body, 1000)


def test_transport_security_guards_sync() -> None:
    config = ClientConfig(base_url="https://api.example.com")
    transport = SyncTransport(
        config=config,
        client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200))),
    )

    with pytest.raises(SSRFError, match="Protocol-relative URLs"):
        transport.request("GET", "//evil.com")

    with pytest.raises(SecurityError, match="CRLF control character"):
        transport.request("GET", "/test", headers={"Evil\r\n": "val"})

    transport.close()


@pytest.mark.asyncio
async def test_transport_security_guards_async() -> None:
    config = ClientConfig(base_url="https://api.example.com")
    transport = AsyncTransport(
        config=config,
        client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))),
    )

    with pytest.raises(SSRFError, match="Protocol-relative URLs"):
        await transport.request("GET", "//evil.com")

    with pytest.raises(SecurityError, match="CRLF control character"):
        await transport.request("GET", "/test", headers={"Evil\r\n": "val"})

    await transport.aclose()


def test_transport_circuit_breaker_sync() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, json={"error": "failed"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ClientConfig(
        base_url="https://api.example.com",
        circuit_breaker_enabled=True,
        circuit_breaker_failure_threshold=2,
        max_retries=0,
    )
    transport = SyncTransport(config=config, client=client)

    with pytest.raises(ServerError):
        transport.request("GET", "/fail-1")
    with pytest.raises(ServerError):
        transport.request("GET", "/fail-2")

    # 3rd request should fail immediately via circuit breaker without hitting handler
    with pytest.raises(CircuitBreakerOpenError):
        transport.request("GET", "/fail-3")

    assert calls == 2
    transport.close()


@pytest.mark.asyncio
async def test_transport_circuit_breaker_async() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, json={"error": "async failed"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = ClientConfig(
        base_url="https://api.example.com",
        circuit_breaker_enabled=True,
        circuit_breaker_failure_threshold=2,
        max_retries=0,
    )
    transport = AsyncTransport(config=config, client=client)

    with pytest.raises(ServerError):
        await transport.request("GET", "/fail-1")
    with pytest.raises(ServerError):
        await transport.request("GET", "/fail-2")

    with pytest.raises(CircuitBreakerOpenError):
        await transport.request("GET", "/fail-3")

    assert calls == 2
    await transport.aclose()


def test_transport_payload_size_limit_sync() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"a" * 5000))
    )
    config = ClientConfig(base_url="https://api.example.com", max_response_bytes=1000)
    transport = SyncTransport(config=config, client=client)

    with pytest.raises(PayloadTooLargeError):
        transport.request("GET", "/large")
    transport.close()


@pytest.mark.asyncio
async def test_transport_payload_size_limit_async() -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"a" * 5000))
    )
    config = ClientConfig(base_url="https://api.example.com", max_response_bytes=1000)
    transport = AsyncTransport(config=config, client=client)

    with pytest.raises(PayloadTooLargeError):
        await transport.request("GET", "/large")
    await transport.aclose()


@pytest.mark.asyncio
async def test_transport_default_client_construction() -> None:
    t_sync = SyncTransport(ClientConfig(base_url="http://localhost:8000"))
    assert t_sync._owns_client is True
    t_sync.close()

    t_async = AsyncTransport(ClientConfig(base_url="http://localhost:8000"))
    assert t_async._owns_client is True
    await t_async.aclose()
