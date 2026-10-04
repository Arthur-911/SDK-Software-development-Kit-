"""Server and system information models."""

from __future__ import annotations

from pydantic import Field

from server_sdk.models.base import ServerBaseModel


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
