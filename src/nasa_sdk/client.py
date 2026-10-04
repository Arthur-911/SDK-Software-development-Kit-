"""Synchronous NASA API client."""

from __future__ import annotations

from types import TracebackType

import httpx

from nasa_sdk._transport import SyncTransport
from nasa_sdk.config import ClientConfig
from nasa_sdk.endpoints.apod import ApodEndpoint
from nasa_sdk.endpoints.mars_rover import MarsRoverEndpoint
from nasa_sdk.endpoints.neows import NeoWsEndpoint


class NasaClient:
    """Synchronous client for interacting with NASA Open APIs.

    Provides ergonomic, strongly-typed access to:
    - Astronomy Picture of the Day (APOD)
    - Mars Rover Photos
    - Near Earth Object Web Service (NeoWs)

    Example:
        ```python
        from nasa_sdk import NasaClient

        # Automatically loads NASA_API_KEY from environment or defaults to DEMO_KEY
        with NasaClient() as client:
            apod = client.apod.get()
            print(f"{apod.title} ({apod.date}): {apod.url}")
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        backoff_factor: float | None = None,
        headers: dict[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize a new NasaClient instance.

        Args:
            api_key: NASA API Key. Defaults to NASA_API_KEY env var or DEMO_KEY.
            base_url: Alternative API base URL.
            timeout: Request timeout in seconds (default: 30.0).
            max_retries: Maximum attempts for transient network/rate-limit errors.
            backoff_factor: Multiplier for exponential backoff delays.
            headers: Custom headers to include with every request.
            http_client: Optional custom httpx.Client instance.
        """
        config = ClientConfig()
        self.config = config.with_overrides(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            headers=headers,
        )

        self._transport = SyncTransport(self.config, client=http_client)

        # Endpoints
        self.apod = ApodEndpoint(self._transport)
        self.mars_rover = MarsRoverEndpoint(self._transport)
        self.neows = NeoWsEndpoint(self._transport)

    def close(self) -> None:
        """Close the underlying HTTP transport connection pool."""
        self._transport.close()

    def __enter__(self) -> NasaClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        masked_key = (
            f"{self.config.api_key[:4]}..." if len(self.config.api_key) > 6 else self.config.api_key
        )
        return (
            f"NasaClient("
            f"base_url={self.config.base_url!r}, "
            f"api_key={masked_key!r}, "
            f"timeout={self.config.timeout})"
        )
