"""Tests for top-level sync and async client lifecycles and string representations."""

from __future__ import annotations

import pytest

from nasa_sdk import AsyncNasaClient, NasaClient


def test_sync_client_lifecycle() -> None:
    client = NasaClient(
        api_key="very_long_secret_api_key_12345",
        base_url="https://api.nasa.gov",
        timeout=25.0,
        max_retries=4,
        backoff_factor=0.2,
        headers={"X-Test": "Val"},
    )
    assert client.config.timeout == 25.0
    assert client.config.max_retries == 4
    assert client.config.backoff_factor == 0.2
    assert "very..." in repr(client)

    # Test short api key repr
    short_client = NasaClient(api_key="123")
    assert "api_key='123'" in repr(short_client)
    short_client.close()

    # Context manager
    with client as c:
        assert c is client
    # Client is closed after exit


@pytest.mark.asyncio
async def test_async_client_lifecycle() -> None:
    client = AsyncNasaClient(
        api_key="very_long_secret_async_api_key_9999",
        base_url="https://api.nasa.gov",
        timeout=18.0,
        max_retries=2,
        backoff_factor=0.1,
    )
    assert client.config.timeout == 18.0
    assert "very..." in repr(client)

    # Test short key repr
    short_async = AsyncNasaClient(api_key="abc")
    assert "api_key='abc'" in repr(short_async)
    await short_async.aclose()

    # Async context manager
    async with client as c:
        assert c is client
