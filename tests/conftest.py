"""Pytest configuration and shared fixtures for NASA SDK tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure environment is isolated between tests."""
    monkeypatch.delenv("NASA_API_KEY", raising=False)
