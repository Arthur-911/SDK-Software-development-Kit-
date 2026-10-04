"""Synchronous usage example for Server Developer Kit."""

from __future__ import annotations

from server_sdk import BearerAuth, ServerClient


def main() -> None:
    # Initialize client with backend base URL and auth
    with ServerClient(
        base_url="https://httpbin.org",
        auth=BearerAuth("demo-token-xyz"),
        timeout=10.0,
    ) as client:
        print("1. Checking connection to server...")
        response = client.get("/get", params={"service": "payment-api"})
        print(f"Status: {response.get('url')}")

        print("\n2. Sending payload to server...")
        post_response = client.post(
            "/post",
            json={"user_id": 42, "action": "login"},
        )
        print(f"Server acknowledged payload: {post_response.get('json')}")


if __name__ == "__main__":
    main()
