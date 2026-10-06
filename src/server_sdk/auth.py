"""Authentication strategies for Server Developer Kit."""

from __future__ import annotations

import base64
import warnings
from typing import Any


class AuthStrategy:
    """Base class for authentication strategies."""

    def apply(
        self, headers: dict[str, str], params: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """Apply authentication to outgoing headers and query params."""
        return headers, params

    @property
    def sensitive_params(self) -> set[str]:
        """Return set of sensitive query parameter names configured for this strategy."""
        return set()


class NoAuth(AuthStrategy):
    """No authentication applied."""


class ApiKeyAuth(AuthStrategy):
    """API Key authentication strategy via headers or query parameters."""

    def __init__(
        self,
        api_key: str,
        header_name: str = "X-API-Key",
        query_param: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.header_name = header_name
        self.query_param = query_param
        if self.query_param:
            warnings.warn(
                "Passing API keys in query parameters is insecure (CWE-598). "
                "Query parameters may be leaked in server access logs and browser history. "
                "Consider using request headers instead.",
                UserWarning,
                stacklevel=2,
            )

    @property
    def sensitive_params(self) -> set[str]:
        return {self.query_param} if self.query_param else set()

    def apply(
        self, headers: dict[str, str], params: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, Any]]:
        if self.query_param:
            params[self.query_param] = self.api_key
        else:
            headers[self.header_name] = self.api_key
        return headers, params


class BearerAuth(AuthStrategy):
    """Bearer token authentication strategy (JWT / OAuth2)."""

    def __init__(self, token: str) -> None:
        self.token = token

    def apply(
        self, headers: dict[str, str], params: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, Any]]:
        headers["Authorization"] = f"Bearer {self.token}"
        return headers, params


class BasicAuth(AuthStrategy):
    """HTTP Basic authentication strategy."""

    def __init__(self, username: str, password: str) -> None:
        if ":" in username:
            raise ValueError("Username cannot contain a colon ':' per RFC 7617")
        credentials = f"{username}:{password}".encode()
        self.encoded = base64.b64encode(credentials).decode()

    def apply(
        self, headers: dict[str, str], params: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, Any]]:
        headers["Authorization"] = f"Basic {self.encoded}"
        return headers, params
