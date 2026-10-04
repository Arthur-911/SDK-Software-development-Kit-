"""Asynchronous concurrency example for Server Developer Kit."""

from __future__ import annotations

import asyncio

from server_sdk import ApiKeyAuth, AsyncServerClient


async def main() -> None:
    async with AsyncServerClient(
        base_url="https://httpbin.org",
        auth=ApiKeyAuth(api_key="internal-service-key"),
    ) as client:
        print("Sending concurrent server requests...")

        task_a = client.get("/get", params={"request": "profile"})
        task_b = client.get("/get", params={"request": "permissions"})

        result_a, result_b = await asyncio.gather(task_a, task_b)

        print(f"Request A URL: {result_a.get('args')}")
        print(f"Request B URL: {result_b.get('args')}")


if __name__ == "__main__":
    asyncio.run(main())
