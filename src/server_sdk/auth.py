"""Authentication strategies for Server Developer Kit."""

from __future__ import annotations

import base64
from typing import Any


class AuthStrategy:
    """Base class for authentication strategies."""

    def apply(
        self, headers: dict[str, str], params: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """Apply authentication to outgoing headers and query params."""
        return headers, params


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
        credentials = f"{username}:{password}".encode()
        self.encoded = base64.b64encode(credentials).decode()

    def apply(
        self, headers: dict[str, str], params: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, Any]]:
        headers["Authorization"] = f"Basic {self.encoded}"
        return headers, params
