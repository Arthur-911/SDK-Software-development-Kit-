"""Tests for client configuration and overrides."""

from __future__ import annotations

from server_sdk.auth import BearerAuth
from server_sdk.config import DEFAULT_BASE_URL, DEFAULT_USER_AGENT, ClientConfig


def test_default_config() -> None:
    config = ClientConfig()
    assert config.base_url == DEFAULT_BASE_URL
    assert config.timeout == 30.0
    assert config.max_retries == 3
    assert config.backoff_factor == 0.5
    assert config.headers == {}

    headers = config.get_headers()
    assert headers["User-Agent"] == DEFAULT_USER_AGENT
    assert headers["Accept"] == "application/json"


def test_config_from_env(monkeypatch) -> None:
    monkeypatch.setenv("SERVER_BASE_URL", "https://api.internal.network")
    custom_cfg = ClientConfig(base_url="https://api.internal.network")
    assert custom_cfg.base_url == "https://api.internal.network"


def test_config_overrides() -> None:
    base = ClientConfig(base_url="http://localhost:8000")
    auth = BearerAuth("token123")
    overridden = base.with_overrides(
        base_url="https://production.api.com/",
        auth=auth,
        timeout=12.0,
        max_retries=5,
        backoff_factor=1.0,
        headers={"X-Client": "Custom"},
    )

    assert overridden.base_url == "https://production.api.com"
    assert overridden.auth is auth
    assert overridden.timeout == 12.0
    assert overridden.max_retries == 5
    assert overridden.backoff_factor == 1.0
    assert overridden.headers == {"X-Client": "Custom"}

    # Partial overrides
    partial = overridden.with_overrides(timeout=20.0)
    assert partial.timeout == 20.0
    assert partial.base_url == "https://production.api.com"
