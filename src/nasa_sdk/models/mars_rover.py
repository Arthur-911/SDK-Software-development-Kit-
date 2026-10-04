"""Data models for NASA's Mars Rover Photos API."""

from __future__ import annotations

from pydantic import Field

from nasa_sdk.models.base import NasaBaseModel


class MarsCamera(NasaBaseModel):
    """Camera specification on a Mars rover.

    Attributes:
        id: Camera identifier.
        name: Abbreviated camera name (e.g. FHAZ, NAVCAM, MAST).
        rover_id: ID of the rover carrying this camera.
        full_name: Full descriptive name of the camera instrument.
    """

    id: int | None = None
    name: str
    rover_id: int | None = None
    full_name: str | None = None


class MarsRover(NasaBaseModel):
    """Mars Rover vehicle metadata.

    Attributes:
        id: Rover identifier.
        name: Name of the rover (e.g., Curiosity, Opportunity, Spirit, Perseverance).
        landing_date: Earth date the rover landed on Mars (YYYY-MM-DD).
        launch_date: Earth date the rover was launched from Earth (YYYY-MM-DD).
        status: Mission status ('active' or 'complete').
        max_sol: The most recent Martian sol from which photos exist.
        max_date: The most recent Earth date from which photos exist.
        total_photos: Total number of photos taken by this rover.
        cameras: List of camera instrument descriptions on this rover.
    """

    id: int | None = None
    name: str
    landing_date: str | None = None
    launch_date: str | None = None
    status: str | None = None
    max_sol: int | None = None
    max_date: str | None = None
    total_photos: int | None = None
    cameras: list[MarsCamera] = Field(default_factory=list)


class MarsPhoto(NasaBaseModel):
    """An individual photo taken by a Mars Rover instrument.

    Attributes:
        id: Photo unique identifier.
        sol: Martian sol on which the photo was captured.
        camera: Details of the camera used to take the photo.
        img_src: Direct URL to the image asset.
        earth_date: Corresponding Earth date (YYYY-MM-DD).
        rover: Rover details.
    """

    id: int
    sol: int
    camera: MarsCamera
    img_src: str
    earth_date: str
    rover: MarsRover


class MarsManifestPhoto(NasaBaseModel):
    """Photo summary for a specific Martian sol in a rover manifest."""

    sol: int
    total_photos: int
    cameras: list[str] = Field(default_factory=list)


class MarsManifest(NasaBaseModel):
    """Mission manifest summarizing a rover's entire history and photographic record."""

    name: str
    landing_date: str
    launch_date: str
    status: str
    max_sol: int
    max_date: str
    total_photos: int
    photos: list[MarsManifestPhoto] = Field(default_factory=list)
