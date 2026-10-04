"""Tests for sync and async APOD endpoints."""

from __future__ import annotations

from datetime import date

import httpx
import pytest

from nasa_sdk import AsyncNasaClient, NasaClient
from nasa_sdk.exceptions import ValidationError

SAMPLE_APOD_DICT = {
    "date": "2026-10-04",
    "title": "Cosmic Nebula",
    "explanation": "A stellar nursery in deep space.",
    "url": "https://apod.nasa.gov/image.jpg",
    "hdurl": "https://apod.nasa.gov/hd.jpg",
    "media_type": "image",
    "service_version": "v1",
}


def test_sync_apod_get_default() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/planetary/apod"
        return httpx.Response(200, json=SAMPLE_APOD_DICT)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        apod = nasa.apod.get()
        assert apod.title == "Cosmic Nebula"
        assert apod.date == "2026-10-04"


def test_sync_apod_get_with_date_and_thumbs() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "date=2025-01-01" in str(request.url)
        assert "thumbs=True" in str(request.url)
        return httpx.Response(200, json=SAMPLE_APOD_DICT)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        # Pass date as date object
        apod = nasa.apod.get(date=date(2025, 1, 1), thumbs=True)
        assert apod.title == "Cosmic Nebula"


def test_sync_apod_get_invalid_response_format() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["unexpected_list"])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        with pytest.raises(ValidationError, match="Expected single APOD object"):
            nasa.apod.get()


def test_sync_apod_get_range() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "start_date=2025-01-01" in str(request.url)
        assert "end_date=2025-01-02" in str(request.url)
        assert "thumbs=True" in str(request.url)
        return httpx.Response(200, json=[SAMPLE_APOD_DICT, SAMPLE_APOD_DICT])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        results = nasa.apod.get_range(
            start_date=date(2025, 1, 1),
            end_date="2025-01-02",
            thumbs=True,
        )
        assert len(results) == 2


def test_sync_apod_get_range_empty_start_error() -> None:
    with NasaClient() as nasa:
        with pytest.raises(ValidationError, match="start_date cannot be empty"):
            nasa.apod.get_range(start_date="")


def test_sync_apod_get_range_invalid_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "dict"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        with pytest.raises(ValidationError, match="Expected list of APOD objects"):
            nasa.apod.get_range(start_date="2025-01-01")


def test_sync_apod_get_random() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "count=3" in str(request.url)
        assert "thumbs=True" in str(request.url)
        return httpx.Response(200, json=[SAMPLE_APOD_DICT, SAMPLE_APOD_DICT, SAMPLE_APOD_DICT])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        results = nasa.apod.get_random(count=3, thumbs=True)
        assert len(results) == 3


def test_sync_apod_get_random_validation_errors() -> None:
    with NasaClient() as nasa:
        with pytest.raises(
            ValidationError, match="count must be an integer greater than or equal to 1"
        ):
            nasa.apod.get_random(count=0)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "dict"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with NasaClient(http_client=client) as nasa:
        with pytest.raises(ValidationError, match="Expected list of APOD objects"):
            nasa.apod.get_random(count=2)


@pytest.mark.asyncio
async def test_async_apod_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "count" in str(request.url):
            return httpx.Response(200, json=[SAMPLE_APOD_DICT])
        if "start_date" in str(request.url):
            return httpx.Response(200, json=[SAMPLE_APOD_DICT])
        return httpx.Response(200, json=SAMPLE_APOD_DICT)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncNasaClient(http_client=client) as nasa:
        apod = await nasa.apod.get(date="2026-10-04", thumbs=True)
        assert apod.title == "Cosmic Nebula"

        apod_default = await nasa.apod.get()
        assert apod_default.title == "Cosmic Nebula"

        range_apods = await nasa.apod.get_range(
            start_date="2026-10-01", end_date="2026-10-02", thumbs=True
        )
        assert len(range_apods) == 1

        random_apods = await nasa.apod.get_random(count=1, thumbs=True)
        assert len(random_apods) == 1


@pytest.mark.asyncio
async def test_async_apod_validation_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["unexpected_list"])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with AsyncNasaClient(http_client=client) as nasa:
        with pytest.raises(ValidationError, match="Expected single APOD object"):
            await nasa.apod.get()

        with pytest.raises(ValidationError, match="start_date cannot be empty"):
            await nasa.apod.get_range(start_date="")

        with pytest.raises(ValidationError, match="count must be an integer"):
            await nasa.apod.get_random(count=0)

    # Test invalid json responses for range and random
    def dict_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"not": "list"})

    dict_client = httpx.AsyncClient(transport=httpx.MockTransport(dict_handler))
    async with AsyncNasaClient(http_client=dict_client) as nasa:
        with pytest.raises(ValidationError, match="Expected list of APOD objects"):
            await nasa.apod.get_range(start_date="2025-01-01")

        with pytest.raises(ValidationError, match="Expected list of APOD objects"):
            await nasa.apod.get_random(count=1)
