"""Exception hierarchy for the NASA Python SDK."""

from __future__ import annotations

from typing import Any


class NasaError(Exception):
    """Base exception for all NASA SDK errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r})"


class NasaAPIError(NasaError):
    """Raised when the NASA API returns an HTTP error status code."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(status_code={self.status_code}, message={self.message!r})"
        )


class AuthenticationError(NasaAPIError):
    """Raised when the API key is missing, invalid, or unauthorized (HTTP 401 / 403)."""


class NotFoundError(NasaAPIError):
    """Raised when a requested resource is not found (HTTP 404)."""


class RateLimitError(NasaAPIError):
    """Raised when the API rate limit has been exceeded (HTTP 429)."""

    def __init__(
        self,
        message: str,
        status_code: int = 429,
        retry_after: float | None = None,
        response_body: Any | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)
        self.retry_after = retry_after

    def __repr__(self) -> str:
        return (
            f"RateLimitError("
            f"status_code={self.status_code}, "
            f"retry_after={self.retry_after}, "
            f"message={self.message!r})"
        )


class ServerError(NasaAPIError):
    """Raised when NASA's servers return a 5xx error."""


class TimeoutError(NasaError):
    """Raised when an HTTP request times out."""


class ValidationError(NasaError):
    """Raised when client-side parameter validation fails before sending the request."""
