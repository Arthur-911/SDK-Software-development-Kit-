"""Mars Rover Photos API endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any

from nasa_sdk.endpoints.base import AsyncBaseEndpoint, BaseEndpoint
from nasa_sdk.exceptions import ValidationError
from nasa_sdk.models.mars_rover import MarsManifest, MarsPhoto

VALID_ROVERS = {"curiosity", "opportunity", "spirit", "perseverance"}
DateType = str | date


def _format_date(d: DateType | None) -> str | None:
    if d is None:
        return None
    if isinstance(d, date):
        return d.isoformat()
    return str(d).strip()


class MarsRoverEndpoint(BaseEndpoint):
    """Synchronous interface for NASA's Mars Rover Photos API."""

    def get_photos(
        self,
        rover: str = "curiosity",
        sol: int | None = None,
        earth_date: DateType | None = None,
        camera: str | None = None,
        page: int = 1,
    ) -> list[MarsPhoto]:
        """Query photos taken by a specific Mars rover.

        Args:
            rover: Rover name ('curiosity', 'opportunity', 'spirit', 'perseverance').
            sol: Martian sol (0+). Required if earth_date is not specified.
            earth_date: Earth date of the photo (YYYY-MM-DD or date).
            camera: Camera instrument filter (e.g., 'fhaz', 'rhaz', 'mast', 'navcam').
            page: Pagination page number (default 1).

        Returns:
            List of MarsPhoto objects.
        """
        rover_clean = rover.strip().lower()
        if rover_clean not in VALID_ROVERS:
            raise ValidationError(
                f"Invalid rover '{rover}'. Must be one of: {', '.join(sorted(VALID_ROVERS))}"
            )

        if sol is None and earth_date is None:
            raise ValidationError("Either 'sol' or 'earth_date' must be provided.")

        if sol is not None and sol < 0:
            raise ValidationError("'sol' must be a non-negative integer.")

        if page < 1:
            raise ValidationError("'page' must be greater than or equal to 1.")

        params: dict[str, Any] = {"page": page}
        if sol is not None:
            params["sol"] = sol
        if earth_date is not None:
            params["earth_date"] = _format_date(earth_date)
        if camera:
            params["camera"] = camera.strip().lower()

        data = self._transport.request(
            "GET", f"/mars-photos/api/v1/rovers/{rover_clean}/photos", params=params
        )

        if isinstance(data, dict) and "photos" in data and isinstance(data["photos"], list):
            return [MarsPhoto.model_validate(p) for p in data["photos"]]
        raise ValidationError(f"Unexpected response format: {data}")

    def get_manifest(self, rover: str = "curiosity") -> MarsManifest:
        """Fetch mission details and complete photographic manifest for a rover.

        Args:
            rover: Rover name ('curiosity', 'opportunity', 'spirit', 'perseverance').

        Returns:
            MarsManifest object containing mission timeline and camera lists per sol.
        """
        rover_clean = rover.strip().lower()
        if rover_clean not in VALID_ROVERS:
            raise ValidationError(
                f"Invalid rover '{rover}'. Must be one of: {', '.join(sorted(VALID_ROVERS))}"
            )

        data = self._transport.request("GET", f"/mars-photos/api/v1/manifests/{rover_clean}")
        if isinstance(data, dict) and "photo_manifest" in data:
            return MarsManifest.model_validate(data["photo_manifest"])
        raise ValidationError(f"Unexpected manifest format: {data}")


class AsyncMarsRoverEndpoint(AsyncBaseEndpoint):
    """Asynchronous interface for NASA's Mars Rover Photos API."""

    async def get_photos(
        self,
        rover: str = "curiosity",
        sol: int | None = None,
        earth_date: DateType | None = None,
        camera: str | None = None,
        page: int = 1,
    ) -> list[MarsPhoto]:
        """Query photos taken by a specific Mars rover asynchronously."""
        rover_clean = rover.strip().lower()
        if rover_clean not in VALID_ROVERS:
            raise ValidationError(
                f"Invalid rover '{rover}'. Must be one of: {', '.join(sorted(VALID_ROVERS))}"
            )

        if sol is None and earth_date is None:
            raise ValidationError("Either 'sol' or 'earth_date' must be provided.")

        if sol is not None and sol < 0:
            raise ValidationError("'sol' must be a non-negative integer.")

        if page < 1:
            raise ValidationError("'page' must be greater than or equal to 1.")

        params: dict[str, Any] = {"page": page}
        if sol is not None:
            params["sol"] = sol
        if earth_date is not None:
            params["earth_date"] = _format_date(earth_date)
        if camera:
            params["camera"] = camera.strip().lower()

        data = await self._transport.request(
            "GET", f"/mars-photos/api/v1/rovers/{rover_clean}/photos", params=params
        )

        if isinstance(data, dict) and "photos" in data and isinstance(data["photos"], list):
            return [MarsPhoto.model_validate(p) for p in data["photos"]]
        raise ValidationError(f"Unexpected response format: {data}")

    async def get_manifest(self, rover: str = "curiosity") -> MarsManifest:
        """Fetch mission manifest for a rover asynchronously."""
        rover_clean = rover.strip().lower()
        if rover_clean not in VALID_ROVERS:
            raise ValidationError(
                f"Invalid rover '{rover}'. Must be one of: {', '.join(sorted(VALID_ROVERS))}"
            )

        data = await self._transport.request("GET", f"/mars-photos/api/v1/manifests/{rover_clean}")
        if isinstance(data, dict) and "photo_manifest" in data:
            return MarsManifest.model_validate(data["photo_manifest"])
        raise ValidationError(f"Unexpected manifest format: {data}")
