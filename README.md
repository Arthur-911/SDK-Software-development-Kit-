# Server Developer Kit

A typed, resilient Python client library for connecting to backend REST servers and microservices.

[![CI](https://img.shields.io/badge/CI-Passing-2ea44f?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/Arthur-911/SDK-Software-development-Kit-/actions)
[![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen?style=flat-square)](https://github.com/Arthur-911/SDK-Software-development-Kit-)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square)](https://pypi.org/project/server-sdk/)
[![Type Checked](https://img.shields.io/badge/Mypy-Strict-informational?style=flat-square)](https://mypy-lang.org/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-black?style=flat-square)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

---

## Overview

Writing HTTP calls directly in application code often leads to scattered authentication logic, unhandled connection drops, and inconsistent error handling.

This Server Developer Kit (SDK) provides a standardized, production-ready client layer for Python backends:
- Synchronous and asynchronous clients (`ServerClient` and `AsyncServerClient`).
- Pluggable authentication (API keys, Bearer JWT tokens, Basic Auth).
- Automatic retry handling with exponential backoff on HTTP 429 rate limits and 5xx server errors.
- Pre-built health check and system information endpoints.
- Generic request methods with typed response parsing using Pydantic v2.

---

## Installation

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

```python
from server_sdk import BearerAuth, ServerClient

# Connect to any backend server
with ServerClient(base_url="https://api.example.com", auth=BearerAuth("your-token")) as client:
    health = client.health.check()
    print(f"Server status: {health.status}")
```

---

## Authentication Methods

The SDK supports common authentication strategies:

```python
from server_sdk import ApiKeyAuth, BasicAuth, BearerAuth, NoAuth, ServerClient

# 1. Bearer Token (JWT / OAuth2)
client = ServerClient(base_url="https://api.example.com", auth=BearerAuth("jwt-token-here"))

# 2. API Key via Header (Default header: X-API-Key)
client = ServerClient(base_url="https://api.example.com", auth=ApiKeyAuth("my-api-key"))

# 3. API Key via Query Parameter
client = ServerClient(
    base_url="https://api.example.com",
    auth=ApiKeyAuth("my-api-key", query_param="token"),
)

# 4. HTTP Basic Authentication
client = ServerClient(
    base_url="https://api.example.com",
    auth=BasicAuth("username", "password"),
)

# 5. Public / No Authentication
client = ServerClient(base_url="https://api.example.com", auth=NoAuth())
```

---

## Examples

### 1. CRUD Operations

```python
from server_sdk import BearerAuth, ServerClient

with ServerClient(base_url="https://api.example.com", auth=BearerAuth("token")) as client:
    # GET
    users = client.get("/users", params={"active": "true"})

    # POST
    new_user = client.post("/users", json={"name": "Alice", "role": "admin"})

    # PUT
    updated = client.put("/users/1", json={"name": "Alice Smith"})

    # DELETE
    client.delete("/users/1")
```

### 2. Pre-Built Health & System Endpoints

```python
with ServerClient(base_url="https://api.example.com") as client:
    # Full health check response
    status = client.health.check()
    print(f"Status: {status.status}, Uptime: {status.uptime}s")

    # Fast ping check (returns True if reachable)
    is_alive = client.health.ping()

    # System metadata and dependencies
    info = client.system.get_info()
    print(f"Service: {info.name} v{info.version} ({info.environment})")
```

### 3. Async Concurrency

For FastAPI applications, real-time event loops, or background tasks:

```python
import asyncio
from server_sdk import AsyncServerClient, BearerAuth

async def main():
    async with AsyncServerClient(
        base_url="https://api.example.com",
        auth=BearerAuth("token"),
    ) as client:
        # Run multiple server queries in parallel
        task_a = client.get("/metrics")
        task_b = client.get("/status")

        metrics, status = await asyncio.gather(task_a, task_b)
        print(metrics, status)

asyncio.run(main())
```

### 4. Error Handling and Retries

The client automatically retries transient network drops and rate limits. Unresolved issues raise typed exceptions:

```python
from server_sdk import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerClient,
    ServerError,
)

try:
    with ServerClient(base_url="https://api.example.com", max_retries=4) as client:
        client.get("/protected-route")
except AuthenticationError as exc:
    print(f"Auth failed: {exc.message}")
except RateLimitError as exc:
    print(f"Rate limited. Retry after {exc.retry_after} seconds.")
except NotFoundError:
    print("Resource was not found.")
except ServerError as exc:
    print(f"Remote server error: {exc.status_code}")
```

---

## Configuration

```python
from server_sdk import ClientConfig, ServerClient

client = ServerClient(
    base_url="https://api.example.com",
    timeout=15.0,        # In seconds
    max_retries=3,       # Retries on 429 and 5xx errors
    backoff_factor=0.5,  # Exponential backoff multiplier
    headers={"X-App-Client": "Dashboard"},
)
```

---

## Testing

The codebase includes full unit tests with 100% branch and line coverage:

```bash
# Run test suite
pytest

# Check linting and formatting
ruff check src tests
ruff format --check src tests

# Static type verification
mypy src
```

---

## License

This project is licensed under the MIT License.
