"""Asynchronous NASA API client."""

from __future__ import annotations

from types import TracebackType

import httpx

from nasa_sdk._transport import AsyncTransport
from nasa_sdk.config import ClientConfig
from nasa_sdk.endpoints.apod import AsyncApodEndpoint
from nasa_sdk.endpoints.mars_rover import AsyncMarsRoverEndpoint
from nasa_sdk.endpoints.neows import AsyncNeoWsEndpoint


class AsyncNasaClient:
    """Asynchronous client for interacting with NASA Open APIs.

    Provides high-performance, non-blocking access to:
    - Astronomy Picture of the Day (APOD)
    - Mars Rover Photos
    - Near Earth Object Web Service (NeoWs)

    Example:
        ```python
        import asyncio
        from nasa_sdk import AsyncNasaClient

        async def main():
            async with AsyncNasaClient() as client:
                apod = await client.apod.get()
                print(f"{apod.title}: {apod.url}")

        asyncio.run(main())
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
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize a new AsyncNasaClient instance.

        Args:
            api_key: NASA API Key. Defaults to NASA_API_KEY env var or DEMO_KEY.
            base_url: Alternative API base URL.
            timeout: Request timeout in seconds (default: 30.0).
            max_retries: Maximum attempts for transient network/rate-limit errors.
            backoff_factor: Multiplier for exponential backoff delays.
            headers: Custom headers to include with every request.
            http_client: Optional custom httpx.AsyncClient instance.
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

        self._transport = AsyncTransport(self.config, client=http_client)

        # Endpoints
        self.apod = AsyncApodEndpoint(self._transport)
        self.mars_rover = AsyncMarsRoverEndpoint(self._transport)
        self.neows = AsyncNeoWsEndpoint(self._transport)

    async def aclose(self) -> None:
        """Close the underlying async HTTP transport connection pool."""
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncNasaClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        masked_key = (
            f"{self.config.api_key[:4]}..." if len(self.config.api_key) > 6 else self.config.api_key
        )
        return (
            f"AsyncNasaClient("
            f"base_url={self.config.base_url!r}, "
            f"api_key={masked_key!r}, "
            f"timeout={self.config.timeout})"
        )
