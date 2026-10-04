"""System and metadata endpoints."""

from __future__ import annotations

from server_sdk.endpoints.base import AsyncBaseEndpoint, BaseEndpoint
from server_sdk.exceptions import ValidationError
from server_sdk.models.system import ServerInfoResponse


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
