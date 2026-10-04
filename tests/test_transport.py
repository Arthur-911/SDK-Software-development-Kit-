"""Tests for sync and async transport, error translation, and retry logic."""

from __future__ import annotations

import httpx
import pytest

from nasa_sdk._transport import (
    AsyncTransport,
    SyncTransport,
    _extract_retry_after,
    _handle_response_error,
)
from nasa_sdk.config import ClientConfig
from nasa_sdk.exceptions import (
    AuthenticationError,
    NasaAPIError,
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
    # Should not raise any exception
    _handle_response_error(response)


def test_handle_response_error_variants() -> None:
    # 401 error with {"error": {"message": "Invalid key"}}
    res_401 = httpx.Response(
        401, json={"error": {"message": "API_KEY_INVALID", "code": "FORBIDDEN"}}
    )
    with pytest.raises(AuthenticationError) as exc_info:
        _handle_response_error(res_401)
    assert "API_KEY_INVALID" in str(exc_info.value)
    assert exc_info.value.status_code == 401

    # 403 error with {"error": {"code": "KEY_EXPIRED"}} (message absent)
    res_403 = httpx.Response(403, json={"error": {"code": "KEY_EXPIRED"}})
    with pytest.raises(AuthenticationError) as exc_info:
        _handle_response_error(res_403)
    assert "KEY_EXPIRED" in str(exc_info.value)

    # 403 error with {"error": "simple string"}
    res_403_str = httpx.Response(403, json={"error": "simple string error"})
    with pytest.raises(AuthenticationError):
        _handle_response_error(res_403_str)

    # 404 error with {"error_message": "Asteroid not found"}
    res_404 = httpx.Response(404, json={"error_message": "Asteroid not found"})
    with pytest.raises(NotFoundError) as exc_info:
        _handle_response_error(res_404)
    assert "Asteroid not found" in str(exc_info.value)

    # 429 error with {"msg": "Over rate limit"} and Retry-After header
    res_429 = httpx.Response(429, headers={"Retry-After": "5.0"}, json={"msg": "Over rate limit"})
    with pytest.raises(RateLimitError) as exc_info:
        _handle_response_error(res_429)
    assert exc_info.value.retry_after == 5.0

    # 500 error with {"message": "Internal error"}
    res_500 = httpx.Response(500, json={"message": "Internal failure"})
    with pytest.raises(ServerError):
        _handle_response_error(res_500)

    # 418 generic error with non-dict json (e.g. ["error 1"])
    res_418 = httpx.Response(418, json=["im a teapot error"])
    with pytest.raises(NasaAPIError) as exc_info:
        _handle_response_error(res_418)
    assert exc_info.value.status_code == 418

    # Non-json response (HTML or plaintext)
    res_html = httpx.Response(502, text="<html>502 Bad Gateway</html>")
    with pytest.raises(ServerError) as exc_info:
        _handle_response_error(res_html)
    assert "502 Bad Gateway" in str(exc_info.value)

    # Empty body
    res_empty = httpx.Response(400, text="")
    with pytest.raises(NasaAPIError):
        _handle_response_error(res_empty)


def test_sync_transport_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "api_key=TEST_KEY" in str(request.url)
        return httpx.Response(200, json={"result": "ok"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ClientConfig(api_key="TEST_KEY")
    transport = SyncTransport(config=config, client=client)

    result = transport.request("GET", "/test")
    assert result == {"result": "ok"}

    # Test absolute URL path branch
    result_abs = transport.request("GET", "https://api.nasa.gov/test")
    assert result_abs == {"result": "ok"}
    transport.close()  # does not close external client


def test_sync_transport_owns_client_close() -> None:
    config = ClientConfig(api_key="TEST_KEY")
    transport = SyncTransport(config=config)
    assert transport._owns_client is True
    transport.close()


def test_sync_transport_custom_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "api_key=CUSTOM_KEY" in str(request.url)
        return httpx.Response(200, json={"ok": True})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = SyncTransport(config=ClientConfig(api_key="DEFAULT"), client=client)
    res = transport.request("GET", "/test", params={"api_key": "CUSTOM_KEY"})
    assert res == {"ok": True}


def test_sync_transport_retry_on_500_and_succeed() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(500, json={"error": "temporary glitch"})
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
            return httpx.Response(429, headers={"Retry-After": "0.01"}, json={"msg": "slow down"})
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
            raise httpx.ConnectError("Connection refused")
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
        raise httpx.PoolTimeout("Socket timeout")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=0)
    transport = SyncTransport(config=config, client=client)

    with pytest.raises(TimeoutError):
        transport.request("GET", "/timeout")


@pytest.mark.asyncio
async def test_async_transport_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "api_key=TEST_ASYNC" in str(request.url)
        return httpx.Response(200, json={"async": "ok"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = ClientConfig(api_key="TEST_ASYNC")
    transport = AsyncTransport(config=config, client=client)

    result = await transport.request("GET", "/async-test")
    assert result == {"async": "ok"}

    result_abs = await transport.request("GET", "https://api.nasa.gov/async-test")
    assert result_abs == {"async": "ok"}
    await transport.aclose()


@pytest.mark.asyncio
async def test_async_transport_owns_client_close() -> None:
    config = ClientConfig(api_key="TEST_ASYNC")
    transport = AsyncTransport(config=config)
    assert transport._owns_client is True
    await transport.aclose()


@pytest.mark.asyncio
async def test_async_transport_custom_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "api_key=CUSTOM_ASYNC_KEY" in str(request.url)
        return httpx.Response(200, json={"ok": True})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    transport = AsyncTransport(config=ClientConfig(api_key="DEFAULT"), client=client)
    res = await transport.request("GET", "/test", params={"api_key": "CUSTOM_ASYNC_KEY"})
    assert res == {"ok": True}


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
            return httpx.Response(429, headers={"Retry-After": "0.01"}, json={"msg": "rate limit"})
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
        raise httpx.PoolTimeout("Async timeout")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config = ClientConfig(max_retries=0)
    transport = AsyncTransport(config=config, client=client)

    with pytest.raises(TimeoutError):
        await transport.request("GET", "/timeout")
