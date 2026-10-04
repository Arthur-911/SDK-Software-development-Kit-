"""Configuration options for the NASA SDK."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from nasa_sdk._version import __version__

DEFAULT_BASE_URL = "https://api.nasa.gov"
DEFAULT_USER_AGENT = f"nasa-sdk-python/{__version__}"
DEFAULT_DEMO_KEY = "DEMO_KEY"


@dataclass(frozen=True)
class ClientConfig:
    """Immutable client configuration for NASA API requests.

    Attributes:
        api_key: NASA API Key. Defaults to NASA_API_KEY environment variable or 'DEMO_KEY'.
        base_url: Base URL for NASA API endpoints.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retries for transient failures.
        backoff_factor: Multiplier for exponential backoff between retries.
        headers: Additional HTTP headers to send with each request.
    """

    api_key: str = field(default_factory=lambda: os.environ.get("NASA_API_KEY", DEFAULT_DEMO_KEY))
    base_url: str = DEFAULT_BASE_URL
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
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        backoff_factor: float | None = None,
        headers: dict[str, str] | None = None,
    ) -> ClientConfig:
        """Return a new ClientConfig with specified fields overridden."""
        return ClientConfig(
            api_key=self.api_key if api_key is None else api_key,
            base_url=self.base_url if base_url is None else base_url.rstrip("/"),
            timeout=self.timeout if timeout is None else timeout,
            max_retries=self.max_retries if max_retries is None else max_retries,
            backoff_factor=self.backoff_factor if backoff_factor is None else backoff_factor,
            headers=dict(self.headers if headers is None else headers),
        )
