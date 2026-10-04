"""Tests for client configuration and overrides."""

from __future__ import annotations

import pytest

from server_sdk.auth import ApiKeyAuth, BearerAuth
from server_sdk.config import (
    DEFAULT_BASE_URL,
    DEFAULT_RETRY_METHODS,
    DEFAULT_USER_AGENT,
    ClientConfig,
)


def test_default_config() -> None:
    config = ClientConfig()
    assert config.base_url == DEFAULT_BASE_URL
    assert config.timeout == 30.0
    assert config.max_retries == 3
    assert config.backoff_factor == 0.5
    assert config.headers == {}
    assert config.retry_methods == DEFAULT_RETRY_METHODS
    assert config.jitter is True

    headers = config.get_headers()
    assert headers["User-Agent"] == DEFAULT_USER_AGENT
    assert headers["Accept"] == "application/json"


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVER_BASE_URL", "https://api.internal.network")
    custom_cfg = ClientConfig(base_url="https://api.internal.network")
    assert custom_cfg.base_url == "https://api.internal.network"


def test_config_auth_from_api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVER_API_KEY", "env-secret-key")
    monkeypatch.delenv("SERVER_BEARER_TOKEN", raising=False)
    config = ClientConfig()
    assert isinstance(config.auth, ApiKeyAuth)
    assert config.auth.api_key == "env-secret-key"


def test_config_auth_from_bearer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SERVER_API_KEY", raising=False)
    monkeypatch.setenv("SERVER_BEARER_TOKEN", "env-jwt-token")
    config = ClientConfig()
    assert isinstance(config.auth, BearerAuth)
    assert config.auth.token == "env-jwt-token"


def test_config_timeout_and_retries_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVER_TIMEOUT", "45.0")
    monkeypatch.setenv("SERVER_MAX_RETRIES", "5")
    config = ClientConfig()
    assert config.timeout == 45.0
    assert config.max_retries == 5


def test_config_invalid_timeout_and_retries_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVER_TIMEOUT", "invalid-float")
    monkeypatch.setenv("SERVER_MAX_RETRIES", "invalid-int")
    config = ClientConfig()
    assert config.timeout == 30.0
    assert config.max_retries == 3


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
        retry_methods=("get", "post"),
        jitter=False,
    )

    assert overridden.base_url == "https://production.api.com"
    assert overridden.auth is auth
    assert overridden.timeout == 12.0
    assert overridden.max_retries == 5
    assert overridden.backoff_factor == 1.0
    assert overridden.headers == {"X-Client": "Custom"}
    assert overridden.retry_methods == ("GET", "POST")
    assert overridden.jitter is False

    # Partial overrides
    partial = overridden.with_overrides(timeout=20.0)
    assert partial.timeout == 20.0
    assert partial.base_url == "https://production.api.com"
    assert partial.retry_methods == ("GET", "POST")
    assert partial.jitter is False
