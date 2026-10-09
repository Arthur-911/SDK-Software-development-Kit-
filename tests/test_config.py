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


def test_config_insecure_http_warning() -> None:
    with pytest.warns(UserWarning, match="Insecure HTTP base_url"):
        ClientConfig(base_url="http://insecure.example.com", auth=BearerAuth("token123"))


def test_config_bounds_validation() -> None:
    with pytest.raises(ValueError, match="timeout must be positive"):
        ClientConfig(timeout=-1.0)

    with pytest.raises(ValueError, match="timeout must be positive"):
        ClientConfig(timeout=0.0)

    with pytest.raises(ValueError, match="max_retries must be non-negative"):
        ClientConfig(max_retries=-1)

    with pytest.raises(ValueError, match="max_response_bytes must be positive"):
        ClientConfig(max_response_bytes=0)

    with pytest.raises(ValueError, match="connect_timeout must be positive"):
        ClientConfig(connect_timeout=-1.0)

    with pytest.raises(ValueError, match="read_timeout must be positive"):
        ClientConfig(read_timeout=0.0)

    with pytest.raises(ValueError, match="write_timeout must be positive"):
        ClientConfig(write_timeout=-2.0)

    with pytest.raises(ValueError, match="pool_timeout must be positive"):
        ClientConfig(pool_timeout=0.0)

    with pytest.raises(ValueError, match="circuit_breaker_failure_threshold must be > 0"):
        ClientConfig(circuit_breaker_failure_threshold=0)

    with pytest.raises(ValueError, match="circuit_breaker_recovery_time must be > 0"):
        ClientConfig(circuit_breaker_recovery_time=-5.0)

    with pytest.raises(ValueError, match="ssl_min_version must be 'TLSv1_2' or 'TLSv1_3'"):
        ClientConfig(ssl_min_version="TLSv1_0")

    with pytest.raises(ValueError, match="contains CRLF control characters"):
        ClientConfig(headers={"Injected\r\nHeader": "val"})

    with pytest.raises(ValueError, match="contains CRLF control characters"):
        ClientConfig(headers={"X-Test": "val\nNewline"})


def test_config_granular_timeouts() -> None:
    config = ClientConfig(
        timeout=25.0,
        connect_timeout=3.0,
        read_timeout=15.0,
        write_timeout=8.0,
        pool_timeout=4.0,
    )
    t = config.get_timeout()
    assert t.connect == 3.0
    assert t.read == 15.0
    assert t.write == 8.0
    assert t.pool == 4.0


def test_config_security_overrides() -> None:
    base = ClientConfig()
    overridden = base.with_overrides(
        max_response_bytes=2048,
        allow_private_ips=True,
        allow_localhost=False,
        connect_timeout=2.0,
        read_timeout=10.0,
        write_timeout=5.0,
        pool_timeout=2.0,
        circuit_breaker_enabled=True,
        circuit_breaker_failure_threshold=10,
        circuit_breaker_recovery_time=60.0,
        verify_ssl=False,
        ssl_ca_bundle="/path/to/bundle.crt",
        ssl_min_version="TLSv1_3",
    )
    assert overridden.max_response_bytes == 2048
    assert overridden.allow_private_ips is True
    assert overridden.allow_localhost is False
    assert overridden.connect_timeout == 2.0
    assert overridden.read_timeout == 10.0
    assert overridden.write_timeout == 5.0
    assert overridden.pool_timeout == 2.0
    assert overridden.circuit_breaker_enabled is True
    assert overridden.circuit_breaker_failure_threshold == 10
    assert overridden.circuit_breaker_recovery_time == 60.0
    assert overridden.verify_ssl is False
    assert overridden.ssl_ca_bundle == "/path/to/bundle.crt"
    assert overridden.ssl_min_version == "TLSv1_3"
