"""Astronomy Picture of the Day (APOD) endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any

from nasa_sdk.endpoints.base import AsyncBaseEndpoint, BaseEndpoint
from nasa_sdk.exceptions import ValidationError
from nasa_sdk.models.apod import ApodItem

DateType = str | date


def _format_date(d: DateType | None) -> str | None:
    if d is None:
        return None
    if isinstance(d, date):
        return d.isoformat()
    return str(d).strip()


class ApodEndpoint(BaseEndpoint):
    """Synchronous interface for NASA's APOD API."""

    def get(
        self,
        date: DateType | None = None,
        thumbs: bool = False,
    ) -> ApodItem:
        """Fetch the Astronomy Picture of the Day for today or a specific date.

        Args:
            date: Target date (YYYY-MM-DD or datetime.date). Defaults to today.
            thumbs: Return video thumbnail URL if the APOD is a video.

        Returns:
            ApodItem model instance.
        """
        params: dict[str, Any] = {}
        formatted_date = _format_date(date)
        if formatted_date:
            params["date"] = formatted_date
        if thumbs:
            params["thumbs"] = "True"

        data = self._transport.request("GET", "/planetary/apod", params=params)
        if isinstance(data, dict):
            return ApodItem.model_validate(data)
        raise ValidationError(f"Expected single APOD object, got {type(data).__name__}")

    def get_range(
        self,
        start_date: DateType,
        end_date: DateType | None = None,
        thumbs: bool = False,
    ) -> list[ApodItem]:
        """Fetch a range of APOD entries.

        Args:
            start_date: Start of date range (YYYY-MM-DD or datetime.date).
            end_date: End of date range. Defaults to today.
            thumbs: Return video thumbnail URL if media is a video.

        Returns:
            List of ApodItem objects.
        """
        start = _format_date(start_date)
        if not start:
            raise ValidationError("start_date cannot be empty")

        params: dict[str, Any] = {"start_date": start}
        end = _format_date(end_date)
        if end:
            params["end_date"] = end
        if thumbs:
            params["thumbs"] = "True"

        data = self._transport.request("GET", "/planetary/apod", params=params)
        if isinstance(data, list):
            return [ApodItem.model_validate(item) for item in data]
        raise ValidationError(f"Expected list of APOD objects, got {type(data).__name__}")

    def get_random(
        self,
        count: int = 1,
        thumbs: bool = False,
    ) -> list[ApodItem]:
        """Fetch a randomly chosen collection of APOD items.

        Args:
            count: Number of random images to retrieve (must be >= 1).
            thumbs: Return video thumbnail URL if media is a video.

        Returns:
            List of randomly chosen ApodItem objects.
        """
        if count < 1:
            raise ValidationError("count must be an integer greater than or equal to 1")

        params: dict[str, Any] = {"count": count}
        if thumbs:
            params["thumbs"] = "True"

        data = self._transport.request("GET", "/planetary/apod", params=params)
        if isinstance(data, list):
            return [ApodItem.model_validate(item) for item in data]
        raise ValidationError(f"Expected list of APOD objects, got {type(data).__name__}")


class AsyncApodEndpoint(AsyncBaseEndpoint):
    """Asynchronous interface for NASA's APOD API."""

    async def get(
        self,
        date: DateType | None = None,
        thumbs: bool = False,
    ) -> ApodItem:
        """Fetch the Astronomy Picture of the Day asynchronously.

        Args:
            date: Target date (YYYY-MM-DD or datetime.date). Defaults to today.
            thumbs: Return video thumbnail URL if the APOD is a video.

        Returns:
            ApodItem model instance.
        """
        params: dict[str, Any] = {}
        formatted_date = _format_date(date)
        if formatted_date:
            params["date"] = formatted_date
        if thumbs:
            params["thumbs"] = "True"

        data = await self._transport.request("GET", "/planetary/apod", params=params)
        if isinstance(data, dict):
            return ApodItem.model_validate(data)
        raise ValidationError(f"Expected single APOD object, got {type(data).__name__}")

    async def get_range(
        self,
        start_date: DateType,
        end_date: DateType | None = None,
        thumbs: bool = False,
    ) -> list[ApodItem]:
        """Fetch a range of APOD entries asynchronously."""
        start = _format_date(start_date)
        if not start:
            raise ValidationError("start_date cannot be empty")

        params: dict[str, Any] = {"start_date": start}
        end = _format_date(end_date)
        if end:
            params["end_date"] = end
        if thumbs:
            params["thumbs"] = "True"

        data = await self._transport.request("GET", "/planetary/apod", params=params)
        if isinstance(data, list):
            return [ApodItem.model_validate(item) for item in data]
        raise ValidationError(f"Expected list of APOD objects, got {type(data).__name__}")

    async def get_random(
        self,
        count: int = 1,
        thumbs: bool = False,
    ) -> list[ApodItem]:
        """Fetch a randomly chosen collection of APOD items asynchronously."""
        if count < 1:
            raise ValidationError("count must be an integer greater than or equal to 1")

        params: dict[str, Any] = {"count": count}
        if thumbs:
            params["thumbs"] = "True"

        data = await self._transport.request("GET", "/planetary/apod", params=params)
        if isinstance(data, list):
            return [ApodItem.model_validate(item) for item in data]
        raise ValidationError(f"Expected list of APOD objects, got {type(data).__name__}")
