"""Download Today's NASA Astronomy Picture of the Day to disk."""

from __future__ import annotations

from pathlib import Path

from nasa_sdk import NasaClient


def main() -> None:
    output_dir = Path("./downloads")
    output_dir.mkdir(exist_ok=True)

    with NasaClient() as client:
        print("Fetching today's APOD metadata...")
        apod = client.apod.get()
        print(f"APOD: '{apod.title}' ({apod.date})")

        if apod.media_type == "image":
            target_path = output_dir / f"apod_{apod.date}.jpg"
            print(f"Downloading HD wallpaper to: {target_path} ...")
            saved_path = apod.download(target_path, use_hd=True)
            print(f"✅ Successfully saved ({saved_path.stat().st_size // 1024} KB) to {saved_path}")
        else:
            print(f"Today's media is a {apod.media_type}: {apod.url}")


if __name__ == "__main__":
    main()
