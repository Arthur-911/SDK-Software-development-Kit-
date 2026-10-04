"""Pre-built resource endpoint handlers for sync and async operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server_sdk.exceptions import ValidationError
from server_sdk.models import HealthCheckResponse, ServerInfoResponse

if TYPE_CHECKING:
    from server_sdk._transport import AsyncTransport, SyncTransport


class BaseEndpoint:
    """Base class for synchronous resource endpoints."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport


class AsyncBaseEndpoint:
    """Base class for asynchronous resource endpoints."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport


class HealthEndpoint(BaseEndpoint):
    """Synchronous interface for server health and heartbeat endpoints."""

    def check(self, path: str = "/health") -> HealthCheckResponse:
        """Query server health status.

        Args:
            path: Relative path for the health check endpoint.

        Returns:
            HealthCheckResponse model.
        """
        data = self._transport.request("GET", path)
        if isinstance(data, dict):
            return HealthCheckResponse.model_validate(data)
        raise ValidationError(f"Expected health check object, got {type(data).__name__}")

    def ping(self, path: str = "/ping") -> bool:
        """Perform a quick ping check against the server.

        Returns:
            True if the server responds successfully.
        """
        self._transport.request("GET", path)
        return True


class AsyncHealthEndpoint(AsyncBaseEndpoint):
    """Asynchronous interface for server health and heartbeat endpoints."""

    async def check(self, path: str = "/health") -> HealthCheckResponse:
        """Query server health status asynchronously."""
        data = await self._transport.request("GET", path)
        if isinstance(data, dict):
            return HealthCheckResponse.model_validate(data)
        raise ValidationError(f"Expected health check object, got {type(data).__name__}")

    async def ping(self, path: str = "/ping") -> bool:
        """Perform a quick ping check against the server asynchronously."""
        await self._transport.request("GET", path)
        return True


class SystemEndpoint(BaseEndpoint):
    """Synchronous interface for server info and metadata endpoints."""

    def get_info(self, path: str = "/info") -> ServerInfoResponse:
        """Fetch server information and status of dependent services.

        Args:
            path: Relative path for system info endpoint.

        Returns:
            ServerInfoResponse model.
        """
        data = self._transport.request("GET", path)
        if isinstance(data, dict):
            return ServerInfoResponse.model_validate(data)
        raise ValidationError(f"Expected system info object, got {type(data).__name__}")


class AsyncSystemEndpoint(AsyncBaseEndpoint):
    """Asynchronous interface for server info and metadata endpoints."""

    async def get_info(self, path: str = "/info") -> ServerInfoResponse:
        """Fetch server information asynchronously."""
        data = await self._transport.request("GET", path)
        if isinstance(data, dict):
            return ServerInfoResponse.model_validate(data)
        raise ValidationError(f"Expected system info object, got {type(data).__name__}")


__all__ = [
    "AsyncBaseEndpoint",
    "AsyncHealthEndpoint",
    "AsyncSystemEndpoint",
    "BaseEndpoint",
    "HealthEndpoint",
    "SystemEndpoint",
]
