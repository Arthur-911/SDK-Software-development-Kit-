"""Asynchronous Server Developer Kit client."""

from __future__ import annotations

from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any, TypeVar, overload

import httpx
from pydantic import BaseModel

from server_sdk._transport import AsyncTransport
from server_sdk.auth import AuthStrategy
from server_sdk.config import ClientConfig
from server_sdk.endpoints import AsyncHealthEndpoint, AsyncSystemEndpoint
from server_sdk.exceptions import ValidationError

ModelT = TypeVar("ModelT", bound=BaseModel)


class AsyncServerClient:
    """Asynchronous client for communicating with backend REST servers and services.

    Provides non-blocking async methods for CRUD operations, model parsing,
    pagination, and concurrent requests using the Python asyncio event loop.

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
        retry_methods: tuple[str, ...] | None = None,
        jitter: bool | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        config = ClientConfig() if auth is None else ClientConfig(auth=auth)
        self.config = config.with_overrides(
            base_url=base_url,
            auth=auth,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            headers=headers,
            retry_methods=retry_methods,
            jitter=jitter,
        )

        self._transport = AsyncTransport(self.config, client=http_client)

        # Pre-built endpoints
        self.health = AsyncHealthEndpoint(self._transport)
        self.system = AsyncSystemEndpoint(self._transport)

    @overload
    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        *,
        response_model: type[ModelT],
    ) -> ModelT: ...

    @overload
    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: None = None,
    ) -> Any: ...

    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: type[ModelT] | None = None,
    ) -> Any:
        """Send an arbitrary HTTP request asynchronously."""
        data = await self._transport.request(
            method=method,
            path=path,
            params=params,
            json=json,
            headers=headers,
            timeout=timeout,
        )
        if response_model is not None:
            if isinstance(data, (dict, list)):
                return response_model.model_validate(data)
            raise ValidationError(
                f"Expected JSON object or array for model validation, got {type(data).__name__}"
            )
        return data

    @overload
    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        *,
        response_model: type[ModelT],
    ) -> ModelT: ...

    @overload
    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: None = None,
    ) -> Any: ...

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: type[ModelT] | None = None,
    ) -> Any:
        """Send an async GET request."""
        return await self.request(
            "GET",
            path,
            params=params,
            headers=headers,
            timeout=timeout,
            response_model=response_model,
        )

    @overload
    async def post(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        *,
        response_model: type[ModelT],
    ) -> ModelT: ...

    @overload
    async def post(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: None = None,
    ) -> Any: ...

    async def post(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: type[ModelT] | None = None,
    ) -> Any:
        """Send an async POST request."""
        return await self.request(
            "POST",
            path,
            params=params,
            json=json,
            headers=headers,
            timeout=timeout,
            response_model=response_model,
        )

    @overload
    async def put(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        *,
        response_model: type[ModelT],
    ) -> ModelT: ...

    @overload
    async def put(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: None = None,
    ) -> Any: ...

    async def put(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: type[ModelT] | None = None,
    ) -> Any:
        """Send an async PUT request."""
        return await self.request(
            "PUT",
            path,
            params=params,
            json=json,
            headers=headers,
            timeout=timeout,
            response_model=response_model,
        )

    @overload
    async def patch(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        *,
        response_model: type[ModelT],
    ) -> ModelT: ...

    @overload
    async def patch(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: None = None,
    ) -> Any: ...

    async def patch(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: type[ModelT] | None = None,
    ) -> Any:
        """Send an async PATCH request."""
        return await self.request(
            "PATCH",
            path,
            params=params,
            json=json,
            headers=headers,
            timeout=timeout,
            response_model=response_model,
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

    async def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        page_param: str = "page",
        size_param: str = "limit",
        page_size: int = 50,
        max_pages: int | None = None,
    ) -> AsyncIterator[Any]:
        """Iterate through paginated items asynchronously across multiple pages.

        Args:
            path: Relative API path.
            params: Base query parameters.
            headers: Optional request headers.
            page_param: Query parameter name for page number (default: 'page').
            size_param: Query parameter name for page size (default: 'limit').
            page_size: Items per page requested.
            max_pages: Maximum number of pages to fetch.

        Yields:
            Individual items extracted from each page response.
        """
        page = 1
        query_params = dict(params or {})
        query_params[size_param] = page_size

        while max_pages is None or page <= max_pages:
            query_params[page_param] = page
            data = await self.get(path, params=query_params, headers=headers)

            items: list[Any] = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for key in ("items", "data", "results"):
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        break

            if not items:
                break

            for item in items:
                yield item

            if len(items) < page_size:
                break

            page += 1

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
