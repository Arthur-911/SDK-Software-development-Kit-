"""Tests for sync and async NeoWs endpoints."""

from __future__ import annotations

from datetime import date

import httpx
import pytest

from nasa_sdk import AsyncNasaClient, NasaClient
from nasa_sdk.exceptions import ValidationError

SAMPLE_NEO = {
    "id": "3542519",
    "neo_reference_id": "3542519",
    "name": "(2010 PK9)",
    "nasa_jpl_url": "http://ssd.jpl.nasa.gov/sbdb.cgi?sstr=3542519",
    "absolute_magnitude_h": 21.8,
    "is_potentially_hazardous_asteroid": True,
}

SAMPLE_FEED = {
    "element_count": 1,
    "near_earth_objects": {
        "2026-10-04": [SAMPLE_NEO],
    },
}


def test_sync_neows_feed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/neo/rest/v1/feed"
        assert "start_date=2026-10-04" in str(request.url)
        assert "end_date=2026-10-05" in str(request.url)
        return httpx.Response(200, json=SAMPLE_FEED)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        feed = nasa.neows.feed(start_date=date(2026, 10, 4), end_date="2026-10-05")
        assert feed.element_count == 1
        assert "2026-10-04" in feed.near_earth_objects


def test_sync_neows_feed_validation_errors() -> None:
    with NasaClient() as nasa:
        with pytest.raises(ValidationError, match="'start_date' is required"):
            nasa.neows.feed(start_date="")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["not_dict"])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        with pytest.raises(ValidationError, match="Unexpected feed response format"):
            nasa.neows.feed(start_date="2026-10-04")


def test_sync_neows_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/neo/rest/v1/neo/3542519"
        return httpx.Response(200, json=SAMPLE_NEO)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        # Pass integer ID
        neo = nasa.neows.get(asteroid_id=3542519)
        assert neo.id == "3542519"
        assert neo.is_potentially_hazardous_asteroid is True

        with pytest.raises(ValidationError, match="asteroid_id cannot be empty"):
            nasa.neows.get(asteroid_id="   ")

    def bad_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["not_dict"])

    bad_client = httpx.Client(transport=httpx.MockTransport(bad_handler))
    with NasaClient(http_client=bad_client) as nasa:
        with pytest.raises(ValidationError, match="Unexpected asteroid response format"):
            nasa.neows.get(asteroid_id=3542519)


@pytest.mark.asyncio
async def test_async_neows_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "/neo/3542519" in request.url.path:
            return httpx.Response(200, json=SAMPLE_NEO)
        return httpx.Response(200, json=SAMPLE_FEED)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncNasaClient(http_client=client) as nasa:
        feed = await nasa.neows.feed(start_date="2026-10-04", end_date="2026-10-05")
        assert feed.element_count == 1

        neo = await nasa.neows.get(asteroid_id="3542519")
        assert neo.id == "3542519"


@pytest.mark.asyncio
async def test_async_neows_validation_errors() -> None:
    async with AsyncNasaClient() as nasa:
        with pytest.raises(ValidationError, match="'start_date' is required"):
            await nasa.neows.feed(start_date="")

        with pytest.raises(ValidationError, match="asteroid_id cannot be empty"):
            await nasa.neows.get(asteroid_id="")

    def bad_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json="bad")

    bad_client = httpx.AsyncClient(transport=httpx.MockTransport(bad_handler))
    async with AsyncNasaClient(http_client=bad_client) as nasa:
        with pytest.raises(ValidationError, match="Unexpected feed response format"):
            await nasa.neows.feed(start_date="2026-10-04")

        with pytest.raises(ValidationError, match="Unexpected asteroid response format"):
            await nasa.neows.get(asteroid_id="3542519")
