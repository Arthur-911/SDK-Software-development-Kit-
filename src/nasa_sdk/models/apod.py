"""Data models for NASA's Astronomy Picture of the Day (APOD)."""

from __future__ import annotations

from pathlib import Path

import httpx

from nasa_sdk.exceptions import NasaError
from nasa_sdk.models.base import NasaBaseModel


class ApodItem(NasaBaseModel):
    """Represents a single Astronomy Picture of the Day entry.

    Attributes:
        date: The date of the APOD image (YYYY-MM-DD).
        title: The title of the image or video.
        explanation: The description written by a professional astronomer.
        url: URL of the APOD image or video.
        hdurl: URL of the high-resolution image (if available).
        media_type: Type of media ('image' or 'video').
        service_version: The API service version.
        copyright: The copyright holder for the image (if applicable).
    """

    date: str
    title: str
    explanation: str
    url: str
    hdurl: str | None = None
    media_type: str = "image"
    service_version: str | None = None
    copyright: str | None = None

    def download(
        self,
        filepath: str | Path,
        use_hd: bool = True,
        timeout: float = 30.0,
    ) -> Path:
        """Download the image asset to local disk.

        Args:
            filepath: Destination file path.
            use_hd: If True and hdurl is available, download high definition image.
            timeout: Download timeout in seconds.

        Returns:
            The Path where the file was saved.

        Raises:
            NasaError: If media_type is not 'image' or downloading fails.
        """
        if self.media_type != "image":
            raise NasaError(
                f"Cannot download non-image media type '{self.media_type}'. Direct URL: {self.url}"
            )

        target_url = self.hdurl if (use_hd and self.hdurl) else self.url
        dest = Path(filepath).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            with httpx.stream("GET", target_url, timeout=timeout) as response:
                response.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
            return dest
        except Exception as exc:
            raise NasaError(f"Failed to download image from {target_url}: {exc}") from exc

    async def adownload(
        self,
        filepath: str | Path,
        use_hd: bool = True,
        timeout: float = 30.0,
    ) -> Path:
        """Asynchronously download the image asset to local disk.

        Args:
            filepath: Destination file path.
            use_hd: If True and hdurl is available, download high definition image.
            timeout: Download timeout in seconds.

        Returns:
            The Path where the file was saved.

        Raises:
            NasaError: If media_type is not 'image' or downloading fails.
        """
        if self.media_type != "image":
            raise NasaError(
                f"Cannot download non-image media type '{self.media_type}'. Direct URL: {self.url}"
            )

        target_url = self.hdurl if (use_hd and self.hdurl) else self.url
        dest = Path(filepath).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("GET", target_url) as response:
                    response.raise_for_status()
                    with open(dest, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
            return dest
        except Exception as exc:
            raise NasaError(f"Failed to download image from {target_url}: {exc}") from exc
