"""Server Developer Kit (server-sdk).

A typed, resilient Python client library for communicating with
backend REST servers and microservices.
"""

from server_sdk._version import __version__
from server_sdk.async_client import AsyncServerClient
from server_sdk.auth import (
    ApiKeyAuth,
    AuthStrategy,
    BasicAuth,
    BearerAuth,
    NoAuth,
)
from server_sdk.client import ServerClient
from server_sdk.config import ClientConfig
from server_sdk.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ServerSDKError,
    TimeoutError,
    ValidationError,
)
from server_sdk.models import (
    HealthCheckResponse,
    ServerBaseModel,
    ServerInfoResponse,
)

__all__ = [
    "APIError",
    "ApiKeyAuth",
    "AsyncServerClient",
    "AuthStrategy",
    "AuthenticationError",
    "BasicAuth",
    "BearerAuth",
    "ClientConfig",
    "HealthCheckResponse",
    "NoAuth",
    "NotFoundError",
    "RateLimitError",
    "ServerBaseModel",
    "ServerClient",
    "ServerError",
    "ServerInfoResponse",
    "ServerSDKError",
    "TimeoutError",
    "ValidationError",
    "__version__",
]
