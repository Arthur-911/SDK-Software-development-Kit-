"""Tests for sync and async Mars Rover endpoints."""

from __future__ import annotations

from datetime import date

import httpx
import pytest

from nasa_sdk import AsyncNasaClient, NasaClient
from nasa_sdk.endpoints.mars_rover import _format_date
from nasa_sdk.exceptions import ValidationError


def test_format_date_helper() -> None:
    assert _format_date(None) is None
    assert _format_date(date(2026, 1, 1)) == "2026-01-01"
    assert _format_date(" 2026-01-01 ") == "2026-01-01"


SAMPLE_PHOTO = {
    "id": 102693,
    "sol": 1000,
    "camera": {"id": 20, "name": "FHAZ", "rover_id": 5, "full_name": "Front Hazard Avoidance"},
    "img_src": "http://mars.jpl.nasa.gov/msl-raw-images/image.jpg",
    "earth_date": "2015-05-30",
    "rover": {"id": 5, "name": "Curiosity"},
}

SAMPLE_MANIFEST = {
    "photo_manifest": {
        "name": "Curiosity",
        "landing_date": "2012-08-06",
        "launch_date": "2011-11-26",
        "status": "active",
        "max_sol": 3500,
        "max_date": "2022-06-01",
        "total_photos": 500000,
        "photos": [{"sol": 1, "total_photos": 10, "cameras": ["FHAZ"]}],
    }
}


def test_sync_mars_photos_by_sol() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/rovers/curiosity/photos" in request.url.path
        assert "sol=1000" in str(request.url)
        assert "camera=fhaz" in str(request.url)
        assert "page=2" in str(request.url)
        return httpx.Response(200, json={"photos": [SAMPLE_PHOTO]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        photos = nasa.mars_rover.get_photos(rover="Curiosity", sol=1000, camera="FHAZ", page=2)
        assert len(photos) == 1
        assert photos[0].id == 102693


def test_sync_mars_photos_by_earth_date() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "earth_date=2015-05-30" in str(request.url)
        return httpx.Response(200, json={"photos": [SAMPLE_PHOTO]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        photos = nasa.mars_rover.get_photos(rover="curiosity", earth_date=date(2015, 5, 30))
        assert len(photos) == 1

        # Test passing string directly
        photos_str = nasa.mars_rover.get_photos(rover="curiosity", earth_date=" 2015-05-30 ")
        assert len(photos_str) == 1


def test_sync_mars_photos_validation_errors() -> None:
    with NasaClient() as nasa:
        with pytest.raises(ValidationError, match="Invalid rover 'unknown'"):
            nasa.mars_rover.get_photos(rover="unknown", sol=100)

        with pytest.raises(ValidationError, match="Either 'sol' or 'earth_date' must be provided"):
            nasa.mars_rover.get_photos(rover="curiosity")

        with pytest.raises(ValidationError, match="'sol' must be a non-negative integer"):
            nasa.mars_rover.get_photos(rover="curiosity", sol=-1)

        with pytest.raises(ValidationError, match="'page' must be greater than or equal to 1"):
            nasa.mars_rover.get_photos(rover="curiosity", sol=10, page=0)

    # Invalid JSON structure
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"not_photos": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        with pytest.raises(ValidationError, match="Unexpected response format"):
            nasa.mars_rover.get_photos(rover="curiosity", sol=100)


def test_sync_mars_manifest() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/manifests/curiosity" in request.url.path
        return httpx.Response(200, json=SAMPLE_MANIFEST)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        manifest = nasa.mars_rover.get_manifest(rover="curiosity")
        assert manifest.name == "Curiosity"
        assert manifest.total_photos == 500000

        with pytest.raises(ValidationError, match="Invalid rover 'invalid'"):
            nasa.mars_rover.get_manifest(rover="invalid")

    # Invalid manifest format
    def bad_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"wrong_key": {}})

    bad_client = httpx.Client(transport=httpx.MockTransport(bad_handler))
    with NasaClient(http_client=bad_client) as nasa:
        with pytest.raises(ValidationError, match="Unexpected manifest format"):
            nasa.mars_rover.get_manifest(rover="curiosity")


@pytest.mark.asyncio
async def test_async_mars_rover_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "manifests" in request.url.path:
            return httpx.Response(200, json=SAMPLE_MANIFEST)
        return httpx.Response(200, json={"photos": [SAMPLE_PHOTO]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncNasaClient(http_client=client) as nasa:
        photos = await nasa.mars_rover.get_photos(rover="curiosity", sol=1000)
        assert len(photos) == 1

        photos_earth = await nasa.mars_rover.get_photos(
            rover="curiosity", earth_date="2015-05-30", camera="FHAZ", page=2
        )
        assert len(photos_earth) == 1

        manifest = await nasa.mars_rover.get_manifest(rover="perseverance")
        assert manifest.name == "Curiosity"


@pytest.mark.asyncio
async def test_async_mars_rover_validation_errors() -> None:
    async with AsyncNasaClient() as nasa:
        with pytest.raises(ValidationError, match="Invalid rover"):
            await nasa.mars_rover.get_photos(rover="invalid", sol=1)

        with pytest.raises(ValidationError, match="Either 'sol' or 'earth_date'"):
            await nasa.mars_rover.get_photos(rover="curiosity")

        with pytest.raises(ValidationError, match="'sol' must be a non-negative"):
            await nasa.mars_rover.get_photos(rover="curiosity", sol=-5)

        with pytest.raises(ValidationError, match="'page' must be greater"):
            await nasa.mars_rover.get_photos(rover="curiosity", sol=1, page=0)

        with pytest.raises(ValidationError, match="Invalid rover"):
            await nasa.mars_rover.get_manifest(rover="invalid")

    def bad_photos_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"bad": "structure"})

    bad_client = httpx.AsyncClient(transport=httpx.MockTransport(bad_photos_handler))
    async with AsyncNasaClient(http_client=bad_client) as nasa:
        with pytest.raises(ValidationError, match="Unexpected response format"):
            await nasa.mars_rover.get_photos(rover="curiosity", sol=1)

    def bad_manifest_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"bad": "manifest"})

    bad_manifest_client = httpx.AsyncClient(transport=httpx.MockTransport(bad_manifest_handler))
    async with AsyncNasaClient(http_client=bad_manifest_client) as nasa:
        with pytest.raises(ValidationError, match="Unexpected manifest format"):
            await nasa.mars_rover.get_manifest(rover="curiosity")
