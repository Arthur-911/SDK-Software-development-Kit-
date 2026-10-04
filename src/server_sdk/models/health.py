"""Health check response models."""

from __future__ import annotations

from server_sdk.models.base import ServerBaseModel


class HealthCheckResponse(ServerBaseModel):
    """Health check payload returned by a backend server.

    Attributes:
        status: Service status (e.g. 'ok', 'healthy', 'degraded').
        uptime: Service uptime in seconds if reported.
        version: Running application or API version.
        timestamp: Timestamp of the health check.
    """

    status: str = "healthy"
    uptime: float | None = None
    version: str | None = None
    timestamp: str | None = None
