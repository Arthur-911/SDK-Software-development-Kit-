"""Near Earth Object Web Service (NeoWs) endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any

from nasa_sdk.endpoints.base import AsyncBaseEndpoint, BaseEndpoint
from nasa_sdk.exceptions import ValidationError
from nasa_sdk.models.neows import NearEarthObject, NeoFeed

DateType = str | date


def _format_date(d: DateType | None) -> str | None:
    if d is None:
        return None
    if isinstance(d, date):
        return d.isoformat()
    return str(d).strip()


class NeoWsEndpoint(BaseEndpoint):
    """Synchronous interface for Near Earth Object Web Service (NeoWs)."""

    def feed(
        self,
        start_date: DateType,
        end_date: DateType | None = None,
    ) -> NeoFeed:
        """Retrieve a list of asteroids based on their closest approach date to Earth.

        Args:
            start_date: Starting date for asteroid search (YYYY-MM-DD or date).
            end_date: Ending date for asteroid search. Defaults to 7 days after start_date.

        Returns:
            NeoFeed containing asteroid list and counts.
        """
        start = _format_date(start_date)
        if not start:
            raise ValidationError("'start_date' is required.")

        params: dict[str, Any] = {"start_date": start}
        end = _format_date(end_date)
        if end:
            params["end_date"] = end

        data = self._transport.request("GET", "/neo/rest/v1/feed", params=params)
        if isinstance(data, dict):
            return NeoFeed.model_validate(data)
        raise ValidationError(f"Unexpected feed response format: {data}")

    def get(self, asteroid_id: str | int) -> NearEarthObject:
        """Lookup a specific Near Earth Object by its NASA JPL asteroid ID.

        Args:
            asteroid_id: NASA JPL asteroid ID or SPK-ID (e.g. 3542519).

        Returns:
            NearEarthObject details.
        """
        id_str = str(asteroid_id).strip()
        if not id_str:
            raise ValidationError("asteroid_id cannot be empty.")

        data = self._transport.request("GET", f"/neo/rest/v1/neo/{id_str}")
        if isinstance(data, dict):
            return NearEarthObject.model_validate(data)
        raise ValidationError(f"Unexpected asteroid response format: {data}")


class AsyncNeoWsEndpoint(AsyncBaseEndpoint):
    """Asynchronous interface for Near Earth Object Web Service (NeoWs)."""

    async def feed(
        self,
        start_date: DateType,
        end_date: DateType | None = None,
    ) -> NeoFeed:
        """Retrieve a list of asteroids asynchronously."""
        start = _format_date(start_date)
        if not start:
            raise ValidationError("'start_date' is required.")

        params: dict[str, Any] = {"start_date": start}
        end = _format_date(end_date)
        if end:
            params["end_date"] = end

        data = await self._transport.request("GET", "/neo/rest/v1/feed", params=params)
        if isinstance(data, dict):
            return NeoFeed.model_validate(data)
        raise ValidationError(f"Unexpected feed response format: {data}")

    async def get(self, asteroid_id: str | int) -> NearEarthObject:
        """Lookup a specific Near Earth Object asynchronously."""
        id_str = str(asteroid_id).strip()
        if not id_str:
            raise ValidationError("asteroid_id cannot be empty.")

        data = await self._transport.request("GET", f"/neo/rest/v1/neo/{id_str}")
        if isinstance(data, dict):
            return NearEarthObject.model_validate(data)
        raise ValidationError(f"Unexpected asteroid response format: {data}")
