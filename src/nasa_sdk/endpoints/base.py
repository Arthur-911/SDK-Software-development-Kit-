"""Base endpoint classes for sync and async operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nasa_sdk._transport import AsyncTransport, SyncTransport


class BaseEndpoint:
    """Base class for synchronous resource endpoints."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport


class AsyncBaseEndpoint:
    """Base class for asynchronous resource endpoints."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport
