"""Configuration options for Server Developer Kit."""

from __future__ import annotations

import os
import urllib.parse
import warnings
from dataclasses import dataclass, field

import httpx

from server_sdk._version import __version__
from server_sdk.auth import ApiKeyAuth, AuthStrategy, BearerAuth, NoAuth

DEFAULT_BASE_URL = os.environ.get("SERVER_BASE_URL", "http://localhost:8000")
DEFAULT_USER_AGENT = f"server-sdk-python/{__version__}"
DEFAULT_RETRY_METHODS = ("GET", "HEAD", "PUT", "DELETE", "OPTIONS", "TRACE")
DEFAULT_MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # 10 MB


def _get_default_auth() -> AuthStrategy:
    """Resolve authentication strategy from environment if present."""
    api_key = os.environ.get("SERVER_API_KEY")
    if api_key:
        return ApiKeyAuth(api_key=api_key)
    bearer_token = os.environ.get("SERVER_BEARER_TOKEN")
    if bearer_token:
        return BearerAuth(token=bearer_token)
    return NoAuth()


def _get_default_timeout() -> float:
    raw = os.environ.get("SERVER_TIMEOUT")
    if raw is not None:
        try:
            return float(raw)
        except ValueError:
            return 30.0
    return 30.0


def _get_default_max_retries() -> int:
    raw = os.environ.get("SERVER_MAX_RETRIES")
    if raw is not None:
        try:
            return int(raw)
        except ValueError:
            return 3
    return 3


@dataclass(frozen=True)
class ClientConfig:
    """Immutable client configuration for backend server communication.

    Attributes:
        base_url: Base URL of the backend server.
        auth: Authentication strategy (ApiKeyAuth, BearerAuth, BasicAuth, or NoAuth).
        timeout: Default request timeout in seconds.
        max_retries: Maximum attempts for transient network or rate-limit failures.
        backoff_factor: Multiplier for exponential backoff delays.
        headers: Additional custom HTTP headers to include with each request.
        retry_methods: HTTP methods eligible for automatic retry.
        jitter: Whether to add randomized full jitter to backoff delay.
        max_response_bytes: Maximum allowed response payload size in bytes.
        allow_private_ips: Whether outbound requests to private network ranges are allowed.
        allow_localhost: Whether requests targeting localhost / loopback are allowed.
        connect_timeout: Granular timeout for TCP connection establishment in seconds.
        read_timeout: Granular timeout for reading response bytes in seconds.
        write_timeout: Granular timeout for sending request payload in seconds.
        pool_timeout: Granular timeout for acquiring a connection from pool in seconds.
        circuit_breaker_enabled: Whether to enable fail-fast circuit breaking.
        circuit_breaker_failure_threshold: Consecutive failures before tripping breaker.
        circuit_breaker_recovery_time: Seconds to wait before testing half-open recovery.
        verify_ssl: Whether to verify upstream SSL/TLS certificates.
        ssl_ca_bundle: Optional path to custom Certificate Authority (CA) bundle file.
        ssl_min_version: Minimum TLS version required ('TLSv1_2' or 'TLSv1_3').
    """

    base_url: str = DEFAULT_BASE_URL
    auth: AuthStrategy = field(default_factory=_get_default_auth)
    timeout: float = field(default_factory=_get_default_timeout)
    max_retries: int = field(default_factory=_get_default_max_retries)
    backoff_factor: float = 0.5
    headers: dict[str, str] = field(default_factory=dict)
    retry_methods: tuple[str, ...] = DEFAULT_RETRY_METHODS
    jitter: bool = True
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES
    allow_private_ips: bool = False
    allow_localhost: bool = True
    connect_timeout: float | None = None
    read_timeout: float | None = None
    write_timeout: float | None = None
    pool_timeout: float | None = None
    circuit_breaker_enabled: bool = False
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_time: float = 30.0
    verify_ssl: bool = True
    ssl_ca_bundle: str | None = None
    ssl_min_version: str = "TLSv1_2"

    def __post_init__(self) -> None:
        """Validate configuration settings and issue security warnings if needed."""
        if self.timeout <= 0:
            raise ValueError(f"Client timeout must be positive, got {self.timeout}")
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {self.max_retries}")
        if self.max_response_bytes <= 0:
            raise ValueError(f"max_response_bytes must be positive, got {self.max_response_bytes}")
        if self.connect_timeout is not None and self.connect_timeout <= 0:
            raise ValueError(f"connect_timeout must be positive, got {self.connect_timeout}")
        if self.read_timeout is not None and self.read_timeout <= 0:
            raise ValueError(f"read_timeout must be positive, got {self.read_timeout}")
        if self.write_timeout is not None and self.write_timeout <= 0:
            raise ValueError(f"write_timeout must be positive, got {self.write_timeout}")
        if self.pool_timeout is not None and self.pool_timeout <= 0:
            raise ValueError(f"pool_timeout must be positive, got {self.pool_timeout}")
        if self.circuit_breaker_failure_threshold <= 0:
            val = self.circuit_breaker_failure_threshold
            raise ValueError(f"circuit_breaker_failure_threshold must be > 0, got {val}")
        if self.circuit_breaker_recovery_time <= 0:
            val_rec = self.circuit_breaker_recovery_time
            raise ValueError(f"circuit_breaker_recovery_time must be > 0, got {val_rec}")
        if self.ssl_min_version not in ("TLSv1_2", "TLSv1_3"):
            raise ValueError(
                f"ssl_min_version must be 'TLSv1_2' or 'TLSv1_3', got {self.ssl_min_version}"
            )

        for k, v in self.headers.items():
            if "\r" in k or "\n" in k or "\r" in v or "\n" in v:
                raise ValueError(f"Header '{k}' contains CRLF control characters")

        parsed = urllib.parse.urlparse(self.base_url)
        if (
            parsed.scheme == "http"
            and parsed.hostname not in ("localhost", "127.0.0.1", "::1", "testserver", None)
            and not isinstance(self.auth, NoAuth)
        ):
            warnings.warn(
                f"Insecure HTTP base_url '{self.base_url}' with authentication enabled transmits "
                "credentials in cleartext (CWE-319). Use HTTPS in non-local environments.",
                UserWarning,
                stacklevel=2,
            )

    def get_timeout(self) -> httpx.Timeout:
        """Construct an httpx.Timeout instance incorporating granular timeout settings."""
        return httpx.Timeout(
            timeout=self.timeout,
            connect=self.connect_timeout,
            read=self.read_timeout,
            write=self.write_timeout,
            pool=self.pool_timeout,
        )

    def get_headers(self) -> dict[str, str]:
        """Construct headers combining default User-Agent with custom headers."""
        combined = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json",
        }
        combined.update(self.headers)
        return combined

    def with_overrides(
        self,
        base_url: str | None = None,
        auth: AuthStrategy | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        backoff_factor: float | None = None,
        headers: dict[str, str] | None = None,
        retry_methods: tuple[str, ...] | None = None,
        jitter: bool | None = None,
        max_response_bytes: int | None = None,
        allow_private_ips: bool | None = None,
        allow_localhost: bool | None = None,
        connect_timeout: float | None = None,
        read_timeout: float | None = None,
        write_timeout: float | None = None,
        pool_timeout: float | None = None,
        circuit_breaker_enabled: bool | None = None,
        circuit_breaker_failure_threshold: int | None = None,
        circuit_breaker_recovery_time: float | None = None,
        verify_ssl: bool | None = None,
        ssl_ca_bundle: str | None = None,
        ssl_min_version: str | None = None,
    ) -> ClientConfig:
        """Return a new ClientConfig with specified fields overridden."""
        return ClientConfig(
            base_url=self.base_url if base_url is None else base_url.rstrip("/"),
            auth=self.auth if auth is None else auth,
            timeout=self.timeout if timeout is None else timeout,
            max_retries=self.max_retries if max_retries is None else max_retries,
            backoff_factor=self.backoff_factor if backoff_factor is None else backoff_factor,
            headers=dict(self.headers if headers is None else headers),
            retry_methods=(
                self.retry_methods
                if retry_methods is None
                else tuple(m.upper() for m in retry_methods)
            ),
            jitter=self.jitter if jitter is None else jitter,
            max_response_bytes=(
                self.max_response_bytes if max_response_bytes is None else max_response_bytes
            ),
            allow_private_ips=(
                self.allow_private_ips if allow_private_ips is None else allow_private_ips
            ),
            allow_localhost=self.allow_localhost if allow_localhost is None else allow_localhost,
            connect_timeout=self.connect_timeout if connect_timeout is None else connect_timeout,
            read_timeout=self.read_timeout if read_timeout is None else read_timeout,
            write_timeout=self.write_timeout if write_timeout is None else write_timeout,
            pool_timeout=self.pool_timeout if pool_timeout is None else pool_timeout,
            circuit_breaker_enabled=(
                self.circuit_breaker_enabled
                if circuit_breaker_enabled is None
                else circuit_breaker_enabled
            ),
            circuit_breaker_failure_threshold=(
                self.circuit_breaker_failure_threshold
                if circuit_breaker_failure_threshold is None
                else circuit_breaker_failure_threshold
            ),
            circuit_breaker_recovery_time=(
                self.circuit_breaker_recovery_time
                if circuit_breaker_recovery_time is None
                else circuit_breaker_recovery_time
            ),
            verify_ssl=self.verify_ssl if verify_ssl is None else verify_ssl,
            ssl_ca_bundle=self.ssl_ca_bundle if ssl_ca_bundle is None else ssl_ca_bundle,
            ssl_min_version=self.ssl_min_version if ssl_min_version is None else ssl_min_version,
        )
