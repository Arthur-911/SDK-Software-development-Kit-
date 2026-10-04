"""Tests for pre-built health and system endpoints."""

from __future__ import annotations

import httpx
import pytest

from server_sdk import AsyncServerClient, ServerClient
from server_sdk.exceptions import ValidationError

SAMPLE_HEALTH = {
    "status": "healthy",
    "uptime": 1200.0,
    "version": "1.0.0",
}

SAMPLE_INFO = {
    "name": "core-api",
    "version": "2.4.1",
    "environment": "production",
    "services": {"database": "up"},
}


def test_sync_health_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json=SAMPLE_HEALTH)
        if request.url.path == "/ping":
            return httpx.Response(200, json={"ping": "pong"})
        return httpx.Response(404, json={"detail": "Not found"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with ServerClient(http_client=client) as server:
        health = server.health.check()
        assert health.status == "healthy"
        assert health.uptime == 1200.0

        assert server.health.ping() is True


def test_sync_health_endpoints_validation_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["unexpected_list"])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with ServerClient(http_client=client) as server:
        with pytest.raises(ValidationError, match="Expected health check object"):
            server.health.check()


def test_sync_system_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=SAMPLE_INFO)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with ServerClient(http_client=client) as server:
        info = server.system.get_info()
        assert info.name == "core-api"
        assert info.environment == "production"


def test_sync_system_endpoints_validation_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["bad_type"])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with ServerClient(http_client=client) as server:
        with pytest.raises(ValidationError, match="Expected system info object"):
            server.system.get_info()


@pytest.mark.asyncio
async def test_async_health_and_system_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json=SAMPLE_HEALTH)
        if request.url.path == "/ping":
            return httpx.Response(200, json={"pong": True})
        if request.url.path == "/info":
            return httpx.Response(200, json=SAMPLE_INFO)
        return httpx.Response(404, json={"detail": "Not found"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncServerClient(http_client=client) as server:
        health = await server.health.check()
        assert health.status == "healthy"

        ping_result = await server.health.ping()
        assert ping_result is True

        info = await server.system.get_info()
        assert info.name == "core-api"


@pytest.mark.asyncio
async def test_async_endpoints_validation_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["invalid"])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncServerClient(http_client=client) as server:
        with pytest.raises(ValidationError, match="Expected health check object"):
            await server.health.check()

        with pytest.raises(ValidationError, match="Expected system info object"):
            await server.system.get_info()
