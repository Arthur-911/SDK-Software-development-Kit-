"""Tests for client configuration and overrides."""

from __future__ import annotations

from nasa_sdk.config import DEFAULT_BASE_URL, DEFAULT_DEMO_KEY, DEFAULT_USER_AGENT, ClientConfig


def test_default_config() -> None:
    config = ClientConfig()
    assert config.api_key == DEFAULT_DEMO_KEY
    assert config.base_url == DEFAULT_BASE_URL
    assert config.timeout == 30.0
    assert config.max_retries == 3
    assert config.backoff_factor == 0.5
    assert config.headers == {}

    headers = config.get_headers()
    assert headers["User-Agent"] == DEFAULT_USER_AGENT
    assert headers["Accept"] == "application/json"


def test_config_from_env(monkeypatch) -> None:
    monkeypatch.setenv("NASA_API_KEY", "env_secret_key_123")
    config = ClientConfig()
    assert config.api_key == "env_secret_key_123"


def test_config_overrides() -> None:
    base = ClientConfig(api_key="base_key")
    overridden = base.with_overrides(
        api_key="new_key",
        base_url="https://custom.nasa.gov/",
        timeout=15.0,
        max_retries=5,
        backoff_factor=1.0,
        headers={"X-Custom": "custom-val"},
    )

    assert overridden.api_key == "new_key"
    assert overridden.base_url == "https://custom.nasa.gov"  # trailing slash stripped
    assert overridden.timeout == 15.0
    assert overridden.max_retries == 5
    assert overridden.backoff_factor == 1.0
    assert overridden.headers == {"X-Custom": "custom-val"}

    # Test partial overrides
    partial = overridden.with_overrides(timeout=20.0)
    assert partial.timeout == 20.0
    assert partial.api_key == "new_key"
    assert partial.base_url == "https://custom.nasa.gov"
