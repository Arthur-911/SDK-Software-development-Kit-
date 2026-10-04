"""Tests for authentication strategies."""

from __future__ import annotations

from server_sdk.auth import ApiKeyAuth, BasicAuth, BearerAuth, NoAuth


def test_no_auth() -> None:
    auth = NoAuth()
    headers, params = auth.apply({"Content-Type": "application/json"}, {"query": "1"})
    assert headers == {"Content-Type": "application/json"}
    assert params == {"query": "1"}


def test_api_key_auth_header() -> None:
    auth = ApiKeyAuth(api_key="secret123")
    headers, params = auth.apply({}, {})
    assert headers["X-API-Key"] == "secret123"
    assert params == {}

    custom_auth = ApiKeyAuth(api_key="custom123", header_name="Authorization-Key")
    headers, _ = custom_auth.apply({}, {})
    assert headers["Authorization-Key"] == "custom123"


def test_api_key_auth_query_param() -> None:
    auth = ApiKeyAuth(api_key="key_abc", query_param="token")
    headers, params = auth.apply({}, {})
    assert "X-API-Key" not in headers
    assert params["token"] == "key_abc"


def test_bearer_auth() -> None:
    auth = BearerAuth(token="jwt.token.here")
    headers, _ = auth.apply({}, {})
    assert headers["Authorization"] == "Bearer jwt.token.here"


def test_basic_auth() -> None:
    auth = BasicAuth(username="admin", password="password123")
    headers, _ = auth.apply({}, {})
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Basic ")
