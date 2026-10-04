"""Tests for top-level sync and async ServerClient lifecycles and HTTP methods."""

from __future__ import annotations

import httpx
import pytest

from server_sdk import ApiKeyAuth, AsyncServerClient, BearerAuth, ServerClient


def test_sync_client_methods() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(f"{request.method} {request.url.path}")
        return httpx.Response(200, json={"status": "ok"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with ServerClient(
        base_url="https://api.example.com",
        auth=ApiKeyAuth(api_key="my-key"),
        timeout=15.0,
        max_retries=2,
        backoff_factor=0.1,
        http_client=client,
    ) as server:
        assert server.get("/users") == {"status": "ok"}
        assert server.post("/users", json={"name": "Alice"}) == {"status": "ok"}
        assert server.put("/users/1", json={"name": "Bob"}) == {"status": "ok"}
        assert server.patch("/users/1", json={"name": "Charlie"}) == {"status": "ok"}
        assert server.delete("/users/1") == {"status": "ok"}

        assert "ServerClient(" in repr(server)
        assert "base_url='https://api.example.com'" in repr(server)

    assert calls == [
        "GET /users",
        "POST /users",
        "PUT /users/1",
        "PATCH /users/1",
        "DELETE /users/1",
    ]


@pytest.mark.asyncio
async def test_async_client_methods() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(f"{request.method} {request.url.path}")
        return httpx.Response(200, json={"status": "async_ok"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncServerClient(
        base_url="https://api.async.com",
        auth=BearerAuth(token="jwt-token"),
        http_client=client,
    ) as server:
        assert await server.get("/items") == {"status": "async_ok"}
        assert await server.post("/items", json={"id": 1}) == {"status": "async_ok"}
        assert await server.put("/items/1", json={"id": 1}) == {"status": "async_ok"}
        assert await server.patch("/items/1", json={"id": 1}) == {"status": "async_ok"}
        assert await server.delete("/items/1") == {"status": "async_ok"}

        assert "AsyncServerClient(" in repr(server)

    assert calls == [
        "GET /items",
        "POST /items",
        "PUT /items/1",
        "PATCH /items/1",
        "DELETE /items/1",
    ]
