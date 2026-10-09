# 🚀 Server Developer Kit (server-sdk)

> **A friendly, resilient, and ultra-secure Python messenger for talking to backend servers and REST APIs.**

[![CI](https://img.shields.io/badge/CI-Passing-2ea44f?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/Arthur-911/SDK-Software-development-Kit-/actions)
[![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen?style=flat-square)](https://github.com/Arthur-911/SDK-Software-development-Kit-)
[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=flat-square)](https://pypi.org/project/server-sdk/)
[![Type Checked](https://img.shields.io/badge/Mypy-Strict-informational?style=flat-square)](https://mypy-lang.org/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-black?style=flat-square)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

---

## 💡 What is this? (In Plain English)

Whenever your Python program needs to talk to a website or backend server, things can get tricky:
- You have to remember passwords, API keys, and headers for every single request.
- If the server has a tiny connection hiccup or asks you to wait 2 seconds, your script might immediately crash.
- Hackers can trick applications into leaking private cloud keys or sending giant files that freeze your computer.

**Think of this library as your smart Helper Robot 🤖.**  
Instead of writing dozens of lines of repetitive code, you give your robot your destination and password once. It handles the talking, waits patiently if the server is busy, defends your app against malicious input, and hands you back clean, organized results.

---

## ✨ Key Superpowers

- 🛡️ **Built-in Security Armor:** Blocks attacks targeting private cloud metadata (SSRF guard), stops decompression bombs from freezing memory, and enforces strict TLS 1.2+ encryption.
- 🔁 **Automatic Patience (Retries):** If the server is temporarily overloaded (HTTP 429) or blips for a moment (5xx), the SDK waits and tries again automatically without crashing.
- ⚡ **Circuit Breaker:** If the remote server completely crashes, the client fails fast so your application doesn't freeze waiting for a dead server.
- 🪪 **Pluggable Passwords:** Easily use Bearer tokens (JWT), API Keys, or Basic Auth in just 1 line.
- 🏎️ **Fast & Flexible:** Works synchronously for simple scripts, or asynchronously (`async`/`await`) for high-speed apps like FastAPI.
- 📦 **Clean Output:** Automatically turns messy server replies into neat, verified Python objects using Pydantic.

---

## 📦 Installation

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

## ⚡ Quickstart (2-Minute Guide)

### 1. Simple Request (Sync)
```python
from server_sdk import BearerAuth, ServerClient

# 1. Connect to any server
with ServerClient(base_url="https://api.example.com", auth=BearerAuth("my-secret-token")) as client:
    # 2. Check if the server is online
    status = client.health.check()
    print(f"Server status: {status.status}")

    # 3. Fetch data (GET)
    users = client.get("/users")
    print(users)
```

### 2. High-Speed Parallel Requests (Async)
Need to fetch multiple endpoints at the same time without waiting? Use `AsyncServerClient`:

```python
import asyncio
from server_sdk import AsyncServerClient, BearerAuth

async def main():
    async with AsyncServerClient(base_url="https://api.example.com", auth=BearerAuth("token")) as client:
        # Fetch profile and settings at the exact same time!
        profile_task = client.get("/profile")
        settings_task = client.get("/settings")

        profile, settings = await asyncio.gather(profile_task, settings_task)
        print("Done:", profile, settings)

asyncio.run(main())
```

---

## 🪪 Easy Authentication

Never copy-paste secret headers manually again:

```python
from server_sdk import ApiKeyAuth, BasicAuth, BearerAuth, NoAuth, ServerClient

# 1. Bearer Token (JWT / OAuth2)
client = ServerClient(base_url="https://api.example.com", auth=BearerAuth("your-jwt-token"))

# 2. API Key Header (X-API-Key)
client = ServerClient(base_url="https://api.example.com", auth=ApiKeyAuth("my-api-key"))

# 3. Username & Password (Basic Auth)
client = ServerClient(base_url="https://api.example.com", auth=BasicAuth("alice", "secret123"))

# 4. Public Server (No login needed)
client = ServerClient(base_url="https://api.example.com", auth=NoAuth())
```

---

## 🛡️ Built-in Security Shield (How it protects you)

Most HTTP clients are completely defenseless out of the box. This SDK comes with enterprise security turned on by default:

| Security Shield | What it prevents |
| :--- | :--- |
| **SSRF & Cloud Key Guard** | Stops malicious requests from accessing internal private IP addresses or cloud metadata (`169.254.169.254`), protecting AWS/GCP/Azure credentials from theft. |
| **Memory Cap (OOM Guard)** | Rejects giant files or compressed "zip-bombs" (`max_response_bytes`) before they crash your computer. |
| **Circuit Breaker** | If the remote server crashes, your app stops hammering it with retries and fails fast instead of freezing. |
| **Log Sanitizer** | Automatically hides passwords and API keys with `[REDACTED]` so they never leak into log files. |
| **Anti-Slowloris Timeouts** | Granular timeouts (`connect`, `read`, `write`, `pool`) so a slow or stalling server cannot hold your app hostage. |
| **Strict TLS 1.2+** | Enforces strong modern encryption and supports custom corporate root certificates (`ssl_ca_bundle`). |

### Customizing Security Settings

```python
from server_sdk import ServerClient

client = ServerClient(
    base_url="https://api.example.com",
    # Block requests to private home/office LANs and cloud metadata:
    allow_private_ips=False,
    # Stop downloading if a response exceeds 5 MB:
    max_response_bytes=5 * 1024 * 1024,
    # Fail fast after 5 consecutive server crashes:
    circuit_breaker_enabled=True,
    circuit_breaker_failure_threshold=5,
    # Separate timeouts for connecting vs reading data:
    connect_timeout=3.0,
    read_timeout=15.0,
)
```

---

## 📚 More Useful Features

### 1. Automatic Pagination (Looping through multiple pages)
```python
with ServerClient(base_url="https://api.example.com") as client:
    # Automatically pulls page 1, page 2, page 3...
    for user in client.paginate("/users", page_size=50, max_pages=5):
        print(user["name"])
```

### 2. Auto-converting into Typed Models (Pydantic)
```python
from pydantic import BaseModel
from server_sdk import ServerClient

class User(BaseModel):
    id: int
    name: str

with ServerClient(base_url="https://api.example.com") as client:
    # Automatically validates and turns raw JSON into a Python User object
    user = client.get("/users/1", response_model=User)
    print(user.name)
```

---

## 🧪 Testing & Verification

This project maintains **100% test coverage** with zero compromises:

```bash
# Run all tests (75 unit & integration tests)
pytest

# Verify code styling & formatting
ruff check src tests
ruff format --check src tests

# Verify strict type safety
mypy src tests
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
