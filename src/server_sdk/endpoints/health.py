"""Health and liveness endpoints."""

from __future__ import annotations

from server_sdk.endpoints.base import AsyncBaseEndpoint, BaseEndpoint
from server_sdk.exceptions import ValidationError
from server_sdk.models.health import HealthCheckResponse


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
