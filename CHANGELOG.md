# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.2] - 2026-07-12
### Added
- **LLM Abstraction Layer**: Built vendor-independent python client model (`base.py`, `gemini.py`) implementing timeout constraints, retries, and backoffs.
- **Repository Context & Invariants**: Introduced `.github/context/` library (rules, project description, coding standards, architecture layout) automatically pre-pended to system instruction contexts.
- **Structured Review Workflows**: Built JSON schemas forcing models to generate parseable telemetry outputs (summaries, risk scales, missing checks, merge safety recomendations).
- **Single Comment Upsert Caching**: Built `pr_helper.py` which caches PR reviews using head commit SHA tags to prevent duplicate comments.
- **Triage Automation**: Automatically applies triage labels (`needs-review`, `tests`, `documentation`) based on AI findings.
- **Reviewdog Static Pipeline**: Integrated ruff, mypy, eslint, and tsc inline checks.

## [0.3.1] - 2026-07-12
### Added
- **Security Infrastructure**: Added `.github/dependabot.yml` for automated package scanning and updates (pip, npm, and GitHub Actions).
- **Static Analysis & Policies**: Integrated CodeQL workflow (`codeql.yml`) and Dependency Review action (`ci.yml`) on pull requests.
- **Security Documentation**: Created root `SECURITY.md` for disclosure policy and `docs/security.md` for operational environment parameters.
- **Dedicated Security Tests**: Added regression tests under `tests/security/` categorized by threat vector:
  - `archive/`: Gzip bomb, invalid gzip files, and truncated archive tests.
  - `xml/`: Billion laughs XML entity expansion and malformed XML events tests.
  - `payloads/`: Maximum JSON payload string size validation tests.
  - `tasks/`: Ephemeral database TTL and capacity count eviction tests.
  - `api/`: Multi-part upload size limit and empty payload tests.

### Fixed
- **Gzip Bomb Protection**: Replaced full-memory Gzip decompression with a chunk-by-chunk streaming validator (`api/utils/decompression.py`) enforcing size limits and returning HTTP 413.
- **XML Entity Hardening**: Replaced standard XML library imports with `defusedxml` inside `WindowsParser` to intercept entity loops and map them to clean parse errors.
- **Ephemeral Memory Eviction**: Added task scheduler in `background_tasks.py` that automatically purges tasks exceeding TTL (`UNILOG_TASK_TTL_SECONDS`) or capacity limits (`UNILOG_MAX_TASKS`).
- **Payload Constraints**: Added maximum string length validation on JSON schemas (`api/schemas/log.py`).

---

## [0.3.0] - 2026-07-11
### Added
- **Records Explorer Table**: Created custom reusable logs table system with dynamic column metadata, pagination, and sorting logic.
- **Custom Column Renderers**: Added specialized cell formatting components (e.g., status pill color indicators, timestamp formatting, IP mappings).
- **Keyboard Navigation**: Implemented keyboard roving focus and expand/collapse shortcut key triggers for row items.
- **Row Details Expansion**: Added expandable detail rows displaying raw log text and fully formatted JSON fields, with click-to-clipboard functionality.
- **Analysis Filters Toolbar**: Created a composite toolbar featuring search text inputs, filter panel dropdowns, toggle buttons for visible columns, and active filter chips.
- **Dynamic Search Highlighting**: Integrated substring highlight renderers highlighting matching search text inside log lines.
- **Stateless Filtering Engine**: Implemented a pure, React-independent filtering pipeline (`filterRecords.ts`) with robust coverage tests.
- **Data Export Actions**: Integrated CSV and JSON export utilities downloading log files matching active filters, sort orders, and visible columns.

---

## [0.2.0] - 2026-07-10
### Added
- **FastAPI REST Service**: Built backend endpoints (`/parse`, `/detect`, `/stats`, `/stream`, `/upload`) with FastAPI.
- **Asynchronous Task Queue**: Implemented background task poller worker for large file uploads using UUID tasks tracking.
- **Dockerization**: Wrote production-ready `Dockerfile` and `.dockerignore` for containerized environments.
- **CI/CD Pipeline**: Configured GitHub Actions CI running Ruff, Mypy, and Pytest coverage checks alongside Docker build smoke tests.
- **Rate Limiting**: Added SlowAPI middleware rate limiting to protect API endpoints.
- **Interactive React Dashboard**: Developed a client SPA using Vite, TypeScript, and CSS variables.
- **Responsive Charts**: Integrated charts displaying logs timeline line-graphs, status codes distribution, and logs level bar charts.
- **Shared Query Cache**: Incorporated React Query state management for log upload and analysis caching.

---

## [0.1.0] - 2026-07-10
### Added
- **Core Parser Engine**: Implemented `BaseParser`, `RegexParser`, and `StructuredRegexParser`.
- **Automatic Format Detection**: Added heuristic detectors identifying formats based on confidence scoring.
- **Built-in Parsers**: Implemented Nginx, Apache, Syslog (RFC 3164 and 5424), JSON, Python, and Windows Event Log parsers.
- **Streaming Parser API**: Added generator APIs to parse logs line-by-line without loading entire payloads into memory.
- **Pluggable Architecture**: Provided plugin hooks to register custom formats and statistics trackers.
- **Command Line Interface**: Developed a robust Click CLI (`unilog`) supporting multiple pretty print choices (JSON, CSV, and ASCII tables).
- **Core Test Suite**: Built complete coverage tests for built-in formats, detector engines, and CLI subcommands.
