"""Tests for top-level sync and async ServerClient lifecycles, models, and pagination."""

from __future__ import annotations

import httpx
import pytest
from pydantic import BaseModel

from server_sdk import ApiKeyAuth, AsyncServerClient, BearerAuth, ServerClient
from server_sdk.exceptions import ValidationError


class ItemModel(BaseModel):
    id: int
    name: str


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
        retry_methods=("GET", "POST"),
        jitter=False,
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


def test_sync_client_response_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/item":
            return httpx.Response(200, json={"id": 42, "name": "Gadget"})
        if request.url.path == "/plain":
            return httpx.Response(200, headers={"Content-Type": "text/plain"}, content=b"not-json")
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with ServerClient(http_client=client) as server:
        item = server.get("/item", response_model=ItemModel)
        assert isinstance(item, ItemModel)
        assert item.id == 42
        assert item.name == "Gadget"

        item_post = server.post("/item", json={"test": True}, response_model=ItemModel)
        assert item_post.id == 42

        item_put = server.put("/item", json={"test": True}, response_model=ItemModel)
        assert item_put.id == 42

        item_patch = server.patch("/item", json={"test": True}, response_model=ItemModel)
        assert item_patch.id == 42

        with pytest.raises(ValidationError, match="Expected JSON object or array"):
            server.get("/plain", response_model=ItemModel)


def test_sync_client_paginate() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        if request.url.path == "/list-items":
            if page == 1:
                return httpx.Response(200, json=[{"id": 1}, {"id": 2}])
            if page == 2:
                return httpx.Response(200, json=[{"id": 3}])
            return httpx.Response(200, json=[])

        if request.url.path == "/dict-items":
            if page == 1:
                return httpx.Response(200, json={"items": ["alpha", "beta"]})
            return httpx.Response(200, json={"items": []})

        if request.url.path == "/results-items":
            if page == 1:
                return httpx.Response(200, json={"results": ["r1", "r2"]})
            return httpx.Response(200, json={"results": []})

        if request.url.path == "/empty-items-precedence":
            # "items" is empty list, should NOT fall back to "data"
            return httpx.Response(200, json={"items": [], "data": ["should_not_yield"]})

        if request.url.path == "/no-items-dict":
            return httpx.Response(200, json={"status": "empty", "count": 0})

        if request.url.path == "/bad-page":
            return httpx.Response(204)

        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with ServerClient(http_client=client) as server:
        # Paginate lists with page_size=2
        items = list(server.paginate("/list-items", page_size=2))
        assert items == [{"id": 1}, {"id": 2}, {"id": 3}]

        # Paginate with max_pages=1
        items_single_page = list(server.paginate("/list-items", page_size=2, max_pages=1))
        assert items_single_page == [{"id": 1}, {"id": 2}]

        # Paginate dict items
        dict_items = list(server.paginate("/dict-items", page_size=2))
        assert dict_items == ["alpha", "beta"]

        # Paginate results dict key
        results_items = list(server.paginate("/results-items", page_size=2))
        assert results_items == ["r1", "r2"]

        # Empty items list takes precedence and doesn't fall back
        empty_prec = list(server.paginate("/empty-items-precedence"))
        assert empty_prec == []

        # Dict with no recognised item keys returns empty
        no_key_items = list(server.paginate("/no-items-dict"))
        assert no_key_items == []

        # Bad page terminates pagination immediately
        bad_items = list(server.paginate("/bad-page"))
        assert bad_items == []


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
        retry_methods=("GET", "POST"),
        jitter=False,
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


@pytest.mark.asyncio
async def test_async_client_response_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/item":
            return httpx.Response(200, json={"id": 99, "name": "AsyncWidget"})
        if request.url.path == "/plain":
            return httpx.Response(200, headers={"Content-Type": "text/plain"}, content=b"text")
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncServerClient(http_client=client) as server:
        item = await server.get("/item", response_model=ItemModel)
        assert item.id == 99

        item_post = await server.post("/item", json={"test": True}, response_model=ItemModel)
        assert item_post.id == 99

        item_put = await server.put("/item", json={"test": True}, response_model=ItemModel)
        assert item_put.id == 99

        item_patch = await server.patch("/item", json={"test": True}, response_model=ItemModel)
        assert item_patch.id == 99

        with pytest.raises(ValidationError, match="Expected JSON object or array"):
            await server.get("/plain", response_model=ItemModel)


@pytest.mark.asyncio
async def test_async_client_paginate() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        if request.url.path == "/async-items":
            if page == 1:
                return httpx.Response(200, json=[10, 20])
            if page == 2:
                return httpx.Response(200, json=[30])
            return httpx.Response(200, json=[])

        if request.url.path == "/async-dict":
            if page == 1:
                return httpx.Response(200, json={"data": ["x", "y"]})
            return httpx.Response(200, json={"data": []})

        if request.url.path == "/async-results":
            if page == 1:
                return httpx.Response(200, json={"results": ["ar1", "ar2"]})
            return httpx.Response(200, json={"results": []})

        if request.url.path == "/async-no-items-dict":
            return httpx.Response(200, json={"status": "none"})

        if request.url.path == "/async-bad":
            return httpx.Response(204)

        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncServerClient(http_client=client) as server:
        items = []
        async for item in server.paginate("/async-items", page_size=2):
            items.append(item)
        assert items == [10, 20, 30]

        items_single = []
        async for item in server.paginate("/async-items", page_size=2, max_pages=1):
            items_single.append(item)
        assert items_single == [10, 20]

        dict_items = []
        async for item in server.paginate("/async-dict", page_size=2):
            dict_items.append(item)
        assert dict_items == ["x", "y"]

        results_items = []
        async for item in server.paginate("/async-results", page_size=2):
            results_items.append(item)
        assert results_items == ["ar1", "ar2"]

        no_key_items = []
        async for item in server.paginate("/async-no-items-dict"):
            no_key_items.append(item)
        assert no_key_items == []

        bad_items = []
        async for item in server.paginate("/async-bad"):
            bad_items.append(item)
        assert bad_items == []


def test_client_security_init() -> None:
    client = ServerClient(
        base_url="https://api.example.com",
        max_response_bytes=4096,
        allow_private_ips=True,
        allow_localhost=False,
        connect_timeout=2.0,
        read_timeout=10.0,
        write_timeout=5.0,
        pool_timeout=1.0,
        circuit_breaker_enabled=True,
        circuit_breaker_failure_threshold=3,
        circuit_breaker_recovery_time=15.0,
        verify_ssl=False,
        ssl_ca_bundle="/path/to/ca.pem",
        ssl_min_version="TLSv1_3",
        http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200))),
    )
    assert client.config.max_response_bytes == 4096
    assert client.config.allow_private_ips is True
    assert client.config.allow_localhost is False
    assert client.config.connect_timeout == 2.0
    assert client.config.circuit_breaker_enabled is True
    assert client.config.verify_ssl is False
    client.close()


@pytest.mark.asyncio
async def test_async_client_security_init() -> None:
    client = AsyncServerClient(
        base_url="https://api.example.com",
        max_response_bytes=4096,
        allow_private_ips=True,
        allow_localhost=False,
        connect_timeout=2.0,
        read_timeout=10.0,
        write_timeout=5.0,
        pool_timeout=1.0,
        circuit_breaker_enabled=True,
        circuit_breaker_failure_threshold=3,
        circuit_breaker_recovery_time=15.0,
        verify_ssl=False,
        ssl_ca_bundle="/path/to/ca.pem",
        ssl_min_version="TLSv1_3",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))),
    )
    assert client.config.max_response_bytes == 4096
    assert client.config.allow_private_ips is True
    assert client.config.allow_localhost is False
    assert client.config.circuit_breaker_enabled is True
    assert client.config.verify_ssl is False
    await client.aclose()
