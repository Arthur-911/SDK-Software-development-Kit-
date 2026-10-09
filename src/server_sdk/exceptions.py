"""Exception hierarchy for the Server Developer Kit."""

from __future__ import annotations

from typing import Any


class ServerSDKError(Exception):
    """Base exception for all Server SDK errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r})"


class APIError(ServerSDKError):
    """Raised when the server returns an HTTP error status code."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(status_code={self.status_code}, message={self.message!r})"
        )


class AuthenticationError(APIError):
    """Raised when authentication credentials are missing, invalid, or expired (HTTP 401/403)."""


class NotFoundError(APIError):
    """Raised when a requested resource is not found (HTTP 404)."""


class RateLimitError(APIError):
    """Raised when server rate limit has been exceeded (HTTP 429)."""

    def __init__(
        self,
        message: str,
        status_code: int = 429,
        retry_after: float | None = None,
        response_body: Any = None,
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


class ServerError(APIError):
    """Raised when the backend server returns a 5xx error."""


class TimeoutError(ServerSDKError):
    """Raised when an HTTP request times out."""


class ValidationError(ServerSDKError):
    """Raised when client-side parameter validation fails before sending a request."""


class SecurityError(ServerSDKError):
    """Base exception for security violations detected by the SDK."""


class SSRFError(SecurityError):
    """Raised when a request targets a blocked or private IP/host (SSRF prevention)."""


class PayloadTooLargeError(SecurityError):
    """Raised when response body size exceeds maximum allowed bytes (OOM/bomb mitigation)."""


class CircuitBreakerOpenError(ServerSDKError):
    """Raised when requests fail fast because the circuit breaker is in OPEN state."""
