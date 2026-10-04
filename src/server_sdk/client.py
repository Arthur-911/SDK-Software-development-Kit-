"""Synchronous Server Developer Kit client."""

from __future__ import annotations

from collections.abc import Iterator
from types import TracebackType
from typing import Any, TypeVar, overload

import httpx
from pydantic import BaseModel

from server_sdk._transport import SyncTransport
from server_sdk.auth import AuthStrategy
from server_sdk.config import ClientConfig
from server_sdk.endpoints import HealthEndpoint, SystemEndpoint
from server_sdk.exceptions import ValidationError

ModelT = TypeVar("ModelT", bound=BaseModel)


class ServerClient:
    """Synchronous client for communicating with backend REST servers and services.

    Provides ergonomic methods for standard CRUD operations, model parsing,
    pagination, and pre-built endpoints with automatic retries and connection pooling.

    Example:
        ```python
        from server_sdk import BearerAuth, ServerClient

        with ServerClient(base_url="https://api.example.com", auth=BearerAuth("token")) as client:
            status = client.health.check()
            print(f"Status: {status.status}")
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
        http_client: httpx.Client | None = None,
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

        self._transport = SyncTransport(self.config, client=http_client)

        # Pre-built endpoints
        self.health = HealthEndpoint(self._transport)
        self.system = SystemEndpoint(self._transport)

    @overload
    def request(
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
    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: None = None,
    ) -> Any: ...

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: type[ModelT] | None = None,
    ) -> Any:
        """Send an arbitrary HTTP request to the server."""
        data = self._transport.request(
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
    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        *,
        response_model: type[ModelT],
    ) -> ModelT: ...

    @overload
    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: None = None,
    ) -> Any: ...

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: type[ModelT] | None = None,
    ) -> Any:
        """Send a GET request."""
        return self.request(
            "GET",
            path,
            params=params,
            headers=headers,
            timeout=timeout,
            response_model=response_model,
        )

    @overload
    def post(
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
    def post(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: None = None,
    ) -> Any: ...

    def post(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: type[ModelT] | None = None,
    ) -> Any:
        """Send a POST request."""
        return self.request(
            "POST",
            path,
            params=params,
            json=json,
            headers=headers,
            timeout=timeout,
            response_model=response_model,
        )

    @overload
    def put(
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
    def put(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: None = None,
    ) -> Any: ...

    def put(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: type[ModelT] | None = None,
    ) -> Any:
        """Send a PUT request."""
        return self.request(
            "PUT",
            path,
            params=params,
            json=json,
            headers=headers,
            timeout=timeout,
            response_model=response_model,
        )

    @overload
    def patch(
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
    def patch(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: None = None,
    ) -> Any: ...

    def patch(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        response_model: type[ModelT] | None = None,
    ) -> Any:
        """Send a PATCH request."""
        return self.request(
            "PATCH",
            path,
            params=params,
            json=json,
            headers=headers,
            timeout=timeout,
            response_model=response_model,
        )

    def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send a DELETE request."""
        return self.request("DELETE", path, params=params, headers=headers, timeout=timeout)

    def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        page_param: str = "page",
        size_param: str = "limit",
        page_size: int = 50,
        max_pages: int | None = None,
    ) -> Iterator[Any]:
        """Iterate through paginated items across multiple pages.

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
            data = self.get(path, params=query_params, headers=headers)

            items: list[Any]
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                extracted = data.get("items") or data.get("data") or data.get("results")
                items = extracted if isinstance(extracted, list) else []
            else:
                break

            if not items:
                break

            yield from items

            if len(items) < page_size:
                break

            page += 1

    def close(self) -> None:
        """Close the underlying HTTP transport connection pool."""
        self._transport.close()

    def __enter__(self) -> ServerClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        return (
            f"ServerClient("
            f"base_url={self.config.base_url!r}, "
            f"auth={self.config.auth.__class__.__name__}, "
            f"timeout={self.config.timeout})"
        )
