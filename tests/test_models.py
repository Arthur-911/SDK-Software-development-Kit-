"""Tests for Pydantic models serialization and download utilities."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from nasa_sdk.exceptions import NasaError
from nasa_sdk.models.apod import ApodItem
from nasa_sdk.models.base import NasaBaseModel
from nasa_sdk.models.mars_rover import (
    MarsCamera,
    MarsManifest,
    MarsManifestPhoto,
    MarsPhoto,
    MarsRover,
)
from nasa_sdk.models.neows import (
    CloseApproachData,
    DiameterRange,
    DistanceData,
    EstimatedDiameter,
    NearEarthObject,
    NeoFeed,
    VelocityData,
)


def test_base_model_serialization() -> None:
    class DummyModel(NasaBaseModel):
        field_one: str
        field_two: int

    instance = DummyModel(field_one="hello", field_two=42)
    dumped_dict = instance.to_dict()
    assert dumped_dict == {"field_one": "hello", "field_two": 42}

    json_str = instance.to_json()
    parsed = json.loads(json_str)
    assert parsed == dumped_dict


def test_apod_model(tmp_path: Path) -> None:
    apod = ApodItem(
        date="2026-10-04",
        title="Cosmic Web",
        explanation="The large scale structure of the universe.",
        url="https://apod.nasa.gov/image.jpg",
        hdurl="https://apod.nasa.gov/hdimage.jpg",
        media_type="image",
        copyright="Jane Doe",
    )
    assert apod.title == "Cosmic Web"
    assert apod.hdurl == "https://apod.nasa.gov/hdimage.jpg"

    # Test download sync
    dest = tmp_path / "apod_test.jpg"
    with patch("httpx.stream") as mock_stream:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_bytes.return_value = [b"chunk1", b"chunk2"]
        mock_stream.return_value.__enter__.return_value = mock_response

        saved = apod.download(dest, use_hd=True)
        assert saved == dest
        assert dest.read_bytes() == b"chunk1chunk2"
        mock_stream.assert_called_with("GET", "https://apod.nasa.gov/hdimage.jpg", timeout=30.0)

    # Test download standard res when hdurl is False or use_hd is False
    with patch("httpx.stream") as mock_stream:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_bytes.return_value = [b"standard"]
        mock_stream.return_value.__enter__.return_value = mock_response

        saved = apod.download(dest, use_hd=False)
        assert dest.read_bytes() == b"standard"
        mock_stream.assert_called_with("GET", "https://apod.nasa.gov/image.jpg", timeout=30.0)


@pytest.mark.asyncio
async def test_apod_adownload(tmp_path: Path) -> None:
    apod = ApodItem(
        date="2026-10-04",
        title="Async Cosmic Web",
        explanation="Explaining async astronomy.",
        url="https://apod.nasa.gov/image.jpg",
        hdurl="https://apod.nasa.gov/hdimage.jpg",
        media_type="image",
    )
    dest = tmp_path / "apod_async.jpg"

    class AsyncMockStream:
        def raise_for_status(self):
            pass

        async def aiter_bytes(self, chunk_size=8192):
            yield b"async_chunk"

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class AsyncMockClient:
        def __init__(self, *args, **kwargs):
            pass

        def stream(self, method, url):
            return AsyncMockStream()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    with patch("httpx.AsyncClient", AsyncMockClient):
        saved = await apod.adownload(dest)
        assert saved == dest
        assert dest.read_bytes() == b"async_chunk"


def test_apod_download_video_error(tmp_path: Path) -> None:
    video_apod = ApodItem(
        date="2026-10-04",
        title="Space Video",
        explanation="A video from ISS.",
        url="https://youtube.com/watch?v=123",
        media_type="video",
    )
    dest = tmp_path / "video.mp4"
    with pytest.raises(NasaError, match="Cannot download non-image media type"):
        video_apod.download(dest)


@pytest.mark.asyncio
async def test_apod_adownload_video_error(tmp_path: Path) -> None:
    video_apod = ApodItem(
        date="2026-10-04",
        title="Space Video",
        explanation="A video from ISS.",
        url="https://youtube.com/watch?v=123",
        media_type="video",
    )
    dest = tmp_path / "video.mp4"
    with pytest.raises(NasaError, match="Cannot download non-image media type"):
        await video_apod.adownload(dest)


def test_apod_download_network_error(tmp_path: Path) -> None:
    apod = ApodItem(
        date="2026-10-04",
        title="Test",
        explanation="Desc",
        url="https://apod.nasa.gov/image.jpg",
    )
    dest = tmp_path / "fail.jpg"
    with patch("httpx.stream", side_effect=httpx.ConnectError("Network failure")):
        with pytest.raises(NasaError, match="Failed to download image"):
            apod.download(dest)


@pytest.mark.asyncio
async def test_apod_adownload_network_error(tmp_path: Path) -> None:
    apod = ApodItem(
        date="2026-10-04",
        title="Test",
        explanation="Desc",
        url="https://apod.nasa.gov/image.jpg",
    )
    dest = tmp_path / "fail.jpg"

    class FailingAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        def stream(self, method, url):
            raise httpx.ConnectError("Network failure")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    with patch("httpx.AsyncClient", FailingAsyncClient):
        with pytest.raises(NasaError, match="Failed to download image"):
            await apod.adownload(dest)


def test_mars_rover_models() -> None:
    camera = MarsCamera(id=1, name="FHAZ", rover_id=5, full_name="Front Hazard Avoidance")
    rover = MarsRover(
        id=5,
        name="Curiosity",
        landing_date="2012-08-06",
        launch_date="2011-11-26",
        status="active",
        max_sol=3500,
        max_date="2022-06-01",
        total_photos=500000,
        cameras=[camera],
    )
    photo = MarsPhoto(
        id=102693,
        sol=1000,
        camera=camera,
        img_src="http://mars.jpl.nasa.gov/msl-raw-images/proj/msl/redops/ods/surface/sol/01000/image.jpg",
        earth_date="2015-05-30",
        rover=rover,
    )
    assert photo.sol == 1000
    assert photo.camera.name == "FHAZ"
    assert photo.rover.name == "Curiosity"

    manifest = MarsManifest(
        name="Curiosity",
        landing_date="2012-08-06",
        launch_date="2011-11-26",
        status="active",
        max_sol=3500,
        max_date="2022-06-01",
        total_photos=500000,
        photos=[MarsManifestPhoto(sol=1, total_photos=10, cameras=["FHAZ"])],
    )
    assert manifest.name == "Curiosity"
    assert len(manifest.photos) == 1
    assert manifest.photos[0].cameras == ["FHAZ"]


def test_neows_models() -> None:
    neo = NearEarthObject(
        id="2000433",
        neo_reference_id="2000433",
        name="433 Eros (A898 PA)",
        nasa_jpl_url="http://ssd.jpl.nasa.gov/sbdb.cgi?sstr=2000433",
        absolute_magnitude_h=11.16,
        estimated_diameter=EstimatedDiameter(
            kilometers=DiameterRange(estimated_diameter_min=16.8, estimated_diameter_max=37.5),
            meters=DiameterRange(estimated_diameter_min=16800.0, estimated_diameter_max=37500.0),
        ),
        is_potentially_hazardous_asteroid=False,
        close_approach_data=[
            CloseApproachData(
                close_approach_date="2026-10-04",
                close_approach_date_full="2026-Oct-04 12:00",
                epoch_date_close_approach=1791115200000,
                relative_velocity=VelocityData(
                    kilometers_per_second="5.5",
                    kilometers_per_hour="19800",
                    miles_per_hour="12300",
                ),
                miss_distance=DistanceData(
                    astronomical="0.17",
                    lunar="66.5",
                    kilometers="25400000",
                    miles="15800000",
                ),
                orbiting_body="Earth",
            )
        ],
        is_sentry_object=False,
    )
    assert neo.name == "433 Eros (A898 PA)"
    assert neo.estimated_diameter is not None
    assert neo.estimated_diameter.kilometers is not None
    assert neo.estimated_diameter.kilometers.estimated_diameter_min == 16.8
    assert len(neo.close_approach_data) == 1

    feed = NeoFeed(
        element_count=1,
        near_earth_objects={"2026-10-04": [neo]},
    )
    assert feed.element_count == 1
    assert "2026-10-04" in feed.near_earth_objects
