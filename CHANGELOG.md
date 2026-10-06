# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [0.1.1] - 2026-10-06

### Security & Hardening
- **SSRF & Credential Exfiltration Protection**: Requests targeting external origins differing from configured `base_url` automatically strip authentication credentials (CWE-201 / CWE-918).
- **Sensitive Parameter Redaction**: Query parameters containing secrets, tokens, or custom auth parameters are masked as `[REDACTED]` in debug logs (CWE-532).
- **Denial of Service & Sleep Bounds**: Clamped `Retry-After` sleep values between `0.0` and `300.0s`, eliminating unhandled crashes on negative numbers and blocking on malicious delays (CWE-400). Added parsing support for RFC 7231 / RFC 9110 HTTP-date formats.
- **Insecure Transport Warnings**: Added security warnings when transmitting credentials over cleartext HTTP on remote hosts (CWE-319) or passing API keys in query parameters (CWE-598).
- **RFC 7617 Compliance**: Added validation rejecting colons in `BasicAuth` usernames to prevent authentication confusion.
- **Log Flooding Mitigation**: Bounded raw server error response strings in exception messages to 500 characters.
- **Pagination Precedence Fix**: Corrected dictionary key extraction in `paginate()` to prevent empty items list from incorrectly falling back to other keys.
- **Test Configuration**: Added `pythonpath = ["src"]` to `pyproject.toml` for seamless standalone test execution.

---

## [0.1.0] - 2026-10-04

### Added
- Synchronous and asynchronous clients: `ServerClient` and `AsyncServerClient`.
- Authentication strategies:
  - `ApiKeyAuth` (header or query parameter).
  - `BearerAuth` (OAuth2 / JWT).
  - `BasicAuth` (HTTP Basic authentication).
  - `NoAuth` (for public endpoints).
- Pre-built health check and system information endpoints.
- Generic HTTP methods (`get`, `post`, `put`, `patch`, `delete`, `request`).
- Automatic retry engine with exponential backoff on HTTP 429 and 5xx server errors.
- Strongly typed exception hierarchy (`ServerSDKError`, `APIError`, `AuthenticationError`, `RateLimitError`, `NotFoundError`, `ServerError`, `TimeoutError`, `ValidationError`).
- Typed response parsing with generic Pydantic models (`response_model`).
- Built-in multi-page pagination iterators (`paginate`).
- Safe HTTP 204 No Content and empty payload handling.
- Randomized full jitter on backoff retries.
- 100% test coverage suite across all client methods and error conditions.
- PEP 561 compliance marker (`py.typed`).
