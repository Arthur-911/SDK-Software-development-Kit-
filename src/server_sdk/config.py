"""Configuration options for Server Developer Kit."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from server_sdk._version import __version__
from server_sdk.auth import AuthStrategy, NoAuth

DEFAULT_BASE_URL = os.environ.get("SERVER_BASE_URL", "http://localhost:8000")
DEFAULT_USER_AGENT = f"server-sdk-python/{__version__}"


@dataclass(frozen=True)
class ClientConfig:
    """Immutable client configuration for backend server communication.

    Attributes:
        base_url: Base URL of the backend server.
        auth: Authentication strategy (ApiKeyAuth, BearerAuth, BasicAuth, or NoAuth).
        timeout: Request timeout in seconds.
        max_retries: Maximum attempts for transient network or rate-limit failures.
        backoff_factor: Multiplier for exponential backoff delays.
        headers: Additional custom HTTP headers to include with each request.
    """

    base_url: str = DEFAULT_BASE_URL
    auth: AuthStrategy = field(default_factory=NoAuth)
    timeout: float = 30.0
    max_retries: int = 3
    backoff_factor: float = 0.5
    headers: dict[str, str] = field(default_factory=dict)

    def get_headers(self) -> dict[str, str]:
        """Construct headers combining default User-Agent with custom headers."""
        combined = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json",
        }
        combined.update(self.headers)
        return combined

    def with_overrides(
        self,
        base_url: str | None = None,
        auth: AuthStrategy | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        backoff_factor: float | None = None,
        headers: dict[str, str] | None = None,
    ) -> ClientConfig:
        """Return a new ClientConfig with specified fields overridden."""
        return ClientConfig(
            base_url=self.base_url if base_url is None else base_url.rstrip("/"),
            auth=self.auth if auth is None else auth,
            timeout=self.timeout if timeout is None else timeout,
            max_retries=self.max_retries if max_retries is None else max_retries,
            backoff_factor=self.backoff_factor if backoff_factor is None else backoff_factor,
            headers=dict(self.headers if headers is None else headers),
        )
