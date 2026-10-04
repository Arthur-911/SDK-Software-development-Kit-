"""Asynchronous Concurrency Example for nasa-sdk."""

from __future__ import annotations

import asyncio

from nasa_sdk import AsyncNasaClient


async def main() -> None:
    async with AsyncNasaClient() as client:
        print("Fetching APOD, Mars Rover photos, and Asteroid data concurrently...")

        # Fire multiple requests concurrently with asyncio.gather
        apod_task = client.apod.get()
        mars_task = client.mars_rover.get_photos(rover="curiosity", sol=1000)
        manifest_task = client.mars_rover.get_manifest(rover="perseverance")

        apod, mars_photos, manifest = await asyncio.gather(
            apod_task, mars_task, manifest_task
        )

        print("\n--- Results Received Concurrently ---")
        print(f"APOD: {apod.title} ({apod.date})")
        print(f"Mars Photos Found: {len(mars_photos)} images")
        print(f"Perseverance Status: {manifest.status.upper()} (Total Photos: {manifest.total_photos})")


if __name__ == "__main__":
    asyncio.run(main())
