# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-10-04

### Added
- **Synchronous & Asynchronous Clients**: Dual `NasaClient` and `AsyncNasaClient` architecture.
- **Astronomy Picture of the Day (APOD)**:
  - `apod.get()` for today or specific dates.
  - `apod.get_range()` for date ranges.
  - `apod.get_random()` for random sample exploration.
  - Built-in `.download()` and `.adownload()` image utilities on `ApodItem`.
- **Mars Rover Photos API**:
  - `mars_rover.get_photos()` supporting Curiosity, Opportunity, Spirit, and Perseverance.
  - Filter by sol, earth date, and camera instruments.
  - `mars_rover.get_manifest()` for mission manifests.
- **Near Earth Object Web Service (NeoWs)**:
  - `neows.feed()` for asteroid close-approach tracking.
  - `neows.get()` for individual asteroid JPL lookups.
- **Resilient Transport Engine**:
  - Automatic exponential backoff with jitter on 429 and 5xx responses.
  - Configurable timeouts and custom headers.
  - Comprehensive typed exception hierarchy (`RateLimitError`, `AuthenticationError`, `ServerError`, `NotFoundError`).
- **100% Test Coverage Suite**:
  - Exhaustive mock tests covering sync, async, retries, and edge cases.
- **Developer Tooling**:
  - PEP 561 `py.typed` marker.
  - Multi-OS GitHub Actions CI workflow.
