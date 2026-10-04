"""Data models for NASA's Near Earth Object Web Service (NeoWs)."""

from __future__ import annotations

from pydantic import Field

from nasa_sdk.models.base import NasaBaseModel


class VelocityData(NasaBaseModel):
    """Relative velocity figures in different units."""

    kilometers_per_second: str | None = None
    kilometers_per_hour: str | None = None
    miles_per_hour: str | None = None


class DistanceData(NasaBaseModel):
    """Miss distance measurements in astronomical units."""

    astronomical: str | None = None
    lunar: str | None = None
    kilometers: str | None = None
    miles: str | None = None


class CloseApproachData(NasaBaseModel):
    """Details of an asteroid's close approach to Earth or another celestial body."""

    close_approach_date: str
    close_approach_date_full: str | None = None
    epoch_date_close_approach: int | None = None
    relative_velocity: VelocityData | None = None
    miss_distance: DistanceData | None = None
    orbiting_body: str | None = None


class DiameterRange(NasaBaseModel):
    """Min and max diameter estimates."""

    estimated_diameter_min: float
    estimated_diameter_max: float


class EstimatedDiameter(NasaBaseModel):
    """Asteroid size estimates across measurement units."""

    kilometers: DiameterRange | None = None
    meters: DiameterRange | None = None
    miles: DiameterRange | None = None
    feet: DiameterRange | None = None


class NearEarthObject(NasaBaseModel):
    """An individual Near Earth Object (Asteroid / Comet).

    Attributes:
        id: Unique object ID.
        neo_reference_id: Reference ID in JPL Small-Body Database.
        name: Name or provisional designation of the asteroid.
        nasa_jpl_url: NASA JPL Small-Body Database URL.
        absolute_magnitude_h: Absolute magnitude (H value).
        estimated_diameter: Estimated diameter in multiple units.
        is_potentially_hazardous_asteroid: True if classified as a potential hazard.
        close_approach_data: Historical and forecasted close approaches.
        is_sentry_object: Sentry system impact monitoring flag.
    """

    id: str
    neo_reference_id: str | None = None
    name: str
    nasa_jpl_url: str | None = None
    absolute_magnitude_h: float | None = None
    estimated_diameter: EstimatedDiameter | None = None
    is_potentially_hazardous_asteroid: bool = False
    close_approach_data: list[CloseApproachData] = Field(default_factory=list)
    is_sentry_object: bool = False


class NeoFeed(NasaBaseModel):
    """Asteroid feed response grouped by observation date."""

    element_count: int
    near_earth_objects: dict[str, list[NearEarthObject]] = Field(default_factory=dict)
