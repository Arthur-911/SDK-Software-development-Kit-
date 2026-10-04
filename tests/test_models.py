"""Tests for Pydantic models serialization."""

from __future__ import annotations

import json

from server_sdk.models import (
    HealthCheckResponse,
    ServerBaseModel,
    ServerInfoResponse,
)


def test_base_model_serialization() -> None:
    class SampleModel(ServerBaseModel):
        key: str
        count: int

    item = SampleModel(key="test", count=10)
    assert item.to_dict() == {"key": "test", "count": 10}

    json_str = item.to_json()
    parsed = json.loads(json_str)
    assert parsed == {"key": "test", "count": 10}


def test_health_check_response() -> None:
    health = HealthCheckResponse(status="healthy", uptime=3600.5, version="1.2.0")
    assert health.status == "healthy"
    assert health.uptime == 3600.5
    assert health.version == "1.2.0"
    assert health.timestamp is None


def test_server_info_response() -> None:
    info = ServerInfoResponse(
        name="payment-service",
        version="2.0.0",
        environment="staging",
        services={"database": "connected", "redis": "connected"},
    )
    assert info.name == "payment-service"
    assert info.version == "2.0.0"
    assert info.environment == "staging"
    assert info.services["database"] == "connected"
