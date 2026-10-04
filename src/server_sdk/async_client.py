"""Asynchronous Server Developer Kit client."""

from __future__ import annotations

from types import TracebackType
from typing import Any

import httpx

from server_sdk._transport import AsyncTransport
from server_sdk.auth import AuthStrategy, NoAuth
from server_sdk.config import ClientConfig
from server_sdk.endpoints.health import AsyncHealthEndpoint
from server_sdk.endpoints.system import AsyncSystemEndpoint


class AsyncServerClient:
    """Asynchronous client for communicating with backend REST servers and services.

    Provides non-blocking async methods for CRUD operations, background polling,
    and concurrent requests using the Python asyncio event loop.

    Example:
        ```python
        import asyncio
        from server_sdk import AsyncServerClient, BearerAuth

        async def main():
            async with AsyncServerClient(
                base_url="https://api.example.com", auth=BearerAuth("token")
            ) as client:
                status = await client.health.check()
                print(f"Status: {status.status}")

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        base_url: str | None = None,
        auth: AuthStrategy | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        backoff_factor: float | None = None,
        headers: dict[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        config = ClientConfig(auth=auth or NoAuth())
        self.config = config.with_overrides(
            base_url=base_url,
            auth=auth,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            headers=headers,
        )

        self._transport = AsyncTransport(self.config, client=http_client)

        # Pre-built endpoints
        self.health = AsyncHealthEndpoint(self._transport)
        self.system = AsyncSystemEndpoint(self._transport)

    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send an arbitrary HTTP request asynchronously."""
        return await self._transport.request(
            method=method,
            path=path,
            params=params,
            json=json,
            headers=headers,
            timeout=timeout,
        )

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send an async GET request."""
        return await self.request("GET", path, params=params, headers=headers, timeout=timeout)

    async def post(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send an async POST request."""
        return await self.request(
            "POST", path, params=params, json=json, headers=headers, timeout=timeout
        )

    async def put(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send an async PUT request."""
        return await self.request(
            "PUT", path, params=params, json=json, headers=headers, timeout=timeout
        )

    async def patch(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send an async PATCH request."""
        return await self.request(
            "PATCH", path, params=params, json=json, headers=headers, timeout=timeout
        )

    async def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send an async DELETE request."""
        return await self.request("DELETE", path, params=params, headers=headers, timeout=timeout)

    async def aclose(self) -> None:
        """Close the underlying async HTTP transport connection pool."""
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncServerClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return (
            f"AsyncServerClient("
            f"base_url={self.config.base_url!r}, "
            f"auth={self.config.auth.__class__.__name__}, "
            f"timeout={self.config.timeout})"
        )
