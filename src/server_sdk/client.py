"""Synchronous Server Developer Kit client."""

from __future__ import annotations

from types import TracebackType
from typing import Any

import httpx

from server_sdk._transport import SyncTransport
from server_sdk.auth import AuthStrategy, NoAuth
from server_sdk.config import ClientConfig
from server_sdk.endpoints import HealthEndpoint, SystemEndpoint


class ServerClient:
    """Synchronous client for communicating with backend REST servers and services.

    Provides ergonomic methods for standard CRUD operations and pre-built endpoints
    with automatic retries, connection pooling, and typed error handling.

    Example:
        ```python
        from server_sdk import ServerClient, BearerAuth

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
        http_client: httpx.Client | None = None,
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

        self._transport = SyncTransport(self.config, client=http_client)

        # Pre-built endpoints
        self.health = HealthEndpoint(self._transport)
        self.system = SystemEndpoint(self._transport)

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send an arbitrary HTTP request to the server."""
        return self._transport.request(
            method=method,
            path=path,
            params=params,
            json=json,
            headers=headers,
            timeout=timeout,
        )

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send a GET request."""
        return self.request("GET", path, params=params, headers=headers, timeout=timeout)

    def post(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send a POST request."""
        return self.request(
            "POST", path, params=params, json=json, headers=headers, timeout=timeout
        )

    def put(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send a PUT request."""
        return self.request("PUT", path, params=params, json=json, headers=headers, timeout=timeout)

    def patch(
        self,
        path: str,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Send a PATCH request."""
        return self.request(
            "PATCH", path, params=params, json=json, headers=headers, timeout=timeout
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
