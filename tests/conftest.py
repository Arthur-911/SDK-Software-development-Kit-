"""Pytest configuration and shared fixtures for Server SDK tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure environment is isolated between tests."""
    monkeypatch.delenv("SERVER_BASE_URL", raising=False)
