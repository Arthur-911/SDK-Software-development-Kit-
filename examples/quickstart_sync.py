"""Synchronous Quickstart Example for nasa-sdk."""

from __future__ import annotations

from nasa_sdk import NasaClient


def main() -> None:
    # Initialize the client. Defaults to DEMO_KEY or os.environ["NASA_API_KEY"]
    with NasaClient() as client:
        print("=== 1. Astronomy Picture of the Day ===")
        apod = client.apod.get()
        print(f"Title: {apod.title}")
        print(f"Date:  {apod.date}")
        print(f"URL:   {apod.url}")
        print(f"HD:    {apod.hdurl}")
        print(f"Explanation:\n{apod.explanation[:200]}...\n")

        print("=== 2. Mars Curiosity Rover Photos ===")
        photos = client.mars_rover.get_photos(rover="curiosity", sol=1000, camera="fhaz")
        print(f"Found {len(photos)} photos on Sol 1000 with FHAZ camera.")
        if photos:
            print(f"Sample photo URL: {photos[0].img_src}")
        print()

        print("=== 3. Near-Earth Asteroid Feed ===")
        feed = client.neows.feed(start_date=apod.date)
        print(f"Total asteroids near Earth around {apod.date}: {feed.element_count}")
        for date_str, asteroids in feed.near_earth_objects.items():
            print(f"Date: {date_str} - {len(asteroids)} objects detected.")
            for ast in asteroids[:3]:
                hazard_str = "⚠️ HAZARDOUS" if ast.is_potentially_hazardous_asteroid else "✅ Safe"
                print(f" - {ast.name} ({hazard_str})")


if __name__ == "__main__":
    main()
