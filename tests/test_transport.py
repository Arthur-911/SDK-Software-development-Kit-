"""Tests for sync and async transport, error translation, and retry logic."""

from __future__ import annotations

import httpx
import pytest

from server_sdk._transport import (
    AsyncTransport,
    SyncTransport,
    _calculate_sleep,
    _extract_retry_after,
    _handle_response_error,
    _parse_response_data,
)
from server_sdk.auth import BearerAuth
from server_sdk.config import ClientConfig
from server_sdk.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
)


def test_extract_retry_after() -> None:
    headers_valid = httpx.Headers({"Retry-After": "10"})
    assert _extract_retry_after(headers_valid) == 10.0

    headers_invalid = httpx.Headers({"Retry-After": "invalid-int"})
    assert _extract_retry_after(headers_invalid) is None

    headers_empty = httpx.Headers({})
    assert _extract_retry_after(headers_empty) is None


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


def test_sync_transport_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("Authorization") == "Bearer secret-token"
        return httpx.Response(200, json={"result": "ok"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ClientConfig(auth=BearerAuth("secret-token"))
    transport = SyncTransport(config=config, client=client)

    result = transport.request("GET", "/test")
    assert result == {"result": "ok"}

    # Absolute URL
    result_abs = transport.request("GET", "https://api.example.com/test")
    assert result_abs == {"result": "ok"}
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
        assert request.headers.get("Authorization") == "Bearer async-token"
        return httpx.Response(200, json={"async": "ok"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = ClientConfig(auth=BearerAuth("async-token"))
    transport = AsyncTransport(config=config, client=client)

    result = await transport.request("GET", "/async-test")
    assert result == {"async": "ok"}

    result_abs = await transport.request("GET", "https://api.example.com/async-test")
    assert result_abs == {"async": "ok"}
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
