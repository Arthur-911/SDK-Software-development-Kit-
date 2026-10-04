# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

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
- 100% test coverage suite across all client methods and error conditions.
- PEP 561 compliance marker (`py.typed`).
