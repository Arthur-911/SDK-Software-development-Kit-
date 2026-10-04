"""Data models for Server Developer Kit."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ServerBaseModel(BaseModel):
    """Base model with common serialization utilities."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance into a Python dictionary."""
        return self.model_dump(by_alias=True)

    def to_json(self, indent: int = 2) -> str:
        """Convert model instance into a JSON formatted string."""
        return self.model_dump_json(indent=indent, by_alias=True)


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


class ServerInfoResponse(ServerBaseModel):
    """System information returned by a backend server.

    Attributes:
        name: Name of the server or service.
        version: Service version.
        environment: Deployment environment (e.g. 'production', 'staging', 'development').
        services: Status map of dependent microservices or databases.
    """

    name: str = "server"
    version: str = "1.0.0"
    environment: str = "production"
    services: dict[str, str] = Field(default_factory=dict)


__all__ = [
    "HealthCheckResponse",
    "ServerBaseModel",
    "ServerInfoResponse",
]
