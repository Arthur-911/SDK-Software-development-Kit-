# Server Developer Kit (server-sdk)

> A resilient, typed, and secure Python client library for connecting to backend REST servers and microservices.

[![CI](https://img.shields.io/badge/CI-Passing-2ea44f?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/Arthur-911/SDK-Software-development-Kit-/actions)
[![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen?style=flat-square)](https://github.com/Arthur-911/SDK-Software-development-Kit-)
[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=flat-square)](https://pypi.org/project/server-sdk/)
[![Type Checked](https://img.shields.io/badge/Mypy-Strict-informational?style=flat-square)](https://mypy-lang.org/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-black?style=flat-square)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

---

## Overview

When building applications that communicate with backend APIs or microservices, managing raw HTTP calls quickly leads to repetitive boilerplate code:
- Authentication headers must be manually injected into every request.
- Network blips or rate limits (HTTP 429) can crash scripts unless retry logic is written from scratch.
- Untrusted endpoints can expose applications to security risks like Server-Side Request Forgery (SSRF) or out-of-memory crashes from oversized payloads.

Server SDK solves these challenges by providing a standardized, production-ready client layer. You configure your connection settings and credentials once, and the library manages request lifecycles, automatic retries with exponential backoff, payload validation, and active security protections.

---

## Key Features

- **Built-in Security Defenses:** Active protection against Server-Side Request Forgery (SSRF), response payload size limits, CRLF header injection guards, and strict TLS 1.2+ encryption.
- **Resilient Retry Engine:** Automatically handles transient network drops and rate limits (HTTP 429 / 5xx) with exponential backoff and randomized jitter.
- **Fail-Fast Circuit Breaker:** Detects sustained upstream outages and prevents retry storms by failing fast until the recovery window elapses.
- **Flexible Authentication:** Native support for Bearer tokens (JWT / OAuth2), API keys, and HTTP Basic authentication.
- **Synchronous and Asynchronous:** Offers both `ServerClient` for scripts and `AsyncServerClient` for high-throughput frameworks like FastAPI.
- **Typed Response Parsing:** Direct integration with Pydantic models for structured, validated Python data.
- **Seamless Pagination:** Built-in iterators to navigate multi-page API responses effortlessly.

---

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/Arthur-911/SDK-Software-development-Kit-.git
```

Or install locally for development:

```bash
git clone https://github.com/Arthur-911/SDK-Software-development-Kit-.git
cd SDK-Software-development-Kit-
pip install -e ".[dev]"
```

---

## Quickstart

### Synchronous Client

```python
from server_sdk import BearerAuth, ServerClient

with ServerClient(base_url="https://api.example.com", auth=BearerAuth("your-token")) as client:
    # Check server health
    health = client.health.check()
    print(f"Status: {health.status}")

    # Standard GET request
    users = client.get("/users")
    print(users)
```

### Asynchronous Client

For concurrent operations and modern async frameworks:

```python
import asyncio
from server_sdk import AsyncServerClient, BearerAuth

async def main():
    async with AsyncServerClient(base_url="https://api.example.com", auth=BearerAuth("your-token")) as client:
        # Fetch multiple endpoints concurrently
        profile_task = client.get("/profile")
        settings_task = client.get("/settings")

        profile, settings = await asyncio.gather(profile_task, settings_task)
        print("Results:", profile, settings)

asyncio.run(main())
```

---

## Authentication Methods

Configure authentication once at client initialization:

```python
from server_sdk import ApiKeyAuth, BasicAuth, BearerAuth, NoAuth, ServerClient

# 1. Bearer Token (JWT / OAuth2)
client = ServerClient(base_url="https://api.example.com", auth=BearerAuth("your-jwt-token"))

# 2. API Key via Header (Default: X-API-Key)
client = ServerClient(base_url="https://api.example.com", auth=ApiKeyAuth("your-api-key"))

# 3. HTTP Basic Authentication
client = ServerClient(base_url="https://api.example.com", auth=BasicAuth("username", "password"))

# 4. Public Endpoints (No Authentication)
client = ServerClient(base_url="https://api.example.com", auth=NoAuth())
```

---

## Security and Resilience

The SDK includes defensive safeguards designed to prevent common web client vulnerabilities:

| Protection | Purpose |
| :--- | :--- |
| **SSRF & Metadata Guard** | Blocks outbound requests targeting internal IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local addresses, and cloud metadata services (`169.254.169.254`). |
| **Memory Protection** | Enforces maximum payload size limits (`max_response_bytes`) to prevent memory exhaustion and decompression bombs. |
| **Circuit Breaker** | Automatically halts requests to failing services after repeated 5xx errors to prevent cascading failures. |
| **Log Sanitization** | Automatically redacts sensitive parameter keys (`api_key`, `token`, `secret`, `password`) in debug logging. |
| **Granular Timeouts** | Individual timeout controls for connection, read, write, and connection pool operations. |
| **Strict TLS Standards** | Mandates modern TLS 1.2+ encryption by default and allows configuring custom enterprise Certificate Authority (CA) bundles. |

### Security Configuration Example

```python
from server_sdk import ServerClient

client = ServerClient(
    base_url="https://api.example.com",
    # Disallow requests to private and cloud metadata addresses
    allow_private_ips=False,
    # Cap response size to 5 MB
    max_response_bytes=5 * 1024 * 1024,
    # Trip circuit breaker after 5 consecutive failures
    circuit_breaker_enabled=True,
    circuit_breaker_failure_threshold=5,
    # Granular timeout settings
    connect_timeout=3.0,
    read_timeout=15.0,
)
```

---

## Additional Features

### Automatic Pagination

Navigate paginated endpoints without manually managing page tokens or query parameters:

```python
with ServerClient(base_url="https://api.example.com") as client:
    for user in client.paginate("/users", page_size=50, max_pages=5):
        print(user["name"])
```

### Typed Models with Pydantic

Parse incoming JSON responses directly into validated Pydantic models:

```python
from pydantic import BaseModel
from server_sdk import ServerClient

class UserModel(BaseModel):
    id: int
    name: str

with ServerClient(base_url="https://api.example.com") as client:
    user = client.get("/users/1", response_model=UserModel)
    print(user.name)
```

---

## Testing

The codebase includes an automated test suite with 100% line and branch coverage:

```bash
# Run unit and integration tests
pytest

# Code style and linting
ruff check src tests
ruff format --check src tests

# Static type verification
mypy src tests
```

---

## License

This project is licensed under the [MIT License](LICENSE).
