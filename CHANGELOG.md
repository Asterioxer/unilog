# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-24
### Added
- **Incident Correlation Engine (Release 10)**: Integrated `IncidentCorrelator` and `TimelineBuilder` under `unilog/analytics/incidents/` to aggregate co-occurring raw rule alerts into top-level deterministic `Incident` objects (`INC-YYYYMMDD-HHMMSS-XXXX`).
- **Evidence-Based Confidence Rationale**: Implemented evidence checkpoints detailing why threat confidence scores are assigned without arbitrary percentage arithmetic.
- **Multi-Tool Threat Actor Profiling**: Extracted `suspected_tools` (`Nikto`, `Playwright`, `Go-http-client`), capabilities, and observed target endpoints into structured threat profiles.
- **System Health Matrix Calculator**: Added `HealthCalculator` under `unilog/analytics/health.py` to evaluate environment health scores (0-100) across Security, Reliability, Performance, and Traffic dimensions.
- **Frontend SOC UI Components**: Created `SystemHealthCard` and `IncidentBoard` React components rendering health status matrix gauges and consolidated incident cards with expandable timelines.

---

## [0.9.0] - 2026-07-19
### Added
- **Live Monitoring Mode (Release 9)**: Implemented WebSocket log streaming router `api/routers/live.py` (`/api/v1/ws/live`) streaming simulated real-time web log traffic with live anomaly triggers.
- **Live Terminal Frontend (`LiveMonitor.tsx`)**: Built live terminal console UI with auto-scroll, play/pause state controls, and configurable streaming speed intervals (0.1s to 2.0s).

## [0.8.0] - 2026-07-19
### Added
- **AI SRE Assistant (Release 8)**: Added LLM diagnostic router `api/routers/ai.py` (`POST /api/v1/ai/diagnose`) explaining metric anomalies and root causes.
- **Interactive AI Assistant UI (`AIAssistant.tsx`)**: Created frontend assistant component presenting structured root-cause explanations and copyable remediation configurations.

## [0.7.0] - 2026-07-18
### Added
- **Security Intelligence (Release 7)**: Implemented `SecurityAnalyzer` under `unilog/analytics/modules/security_analyzer.py` mapping threat signatures for brute force logins, endpoint directory enumeration, bot fingerprints, vulnerability scanning, and SQLi/XSS code injection.
- **SecurityObserver UI**: Created dedicated security intelligence observer panel rendering threat profile metrics, scanner hits, and attack indicators.

## [0.6.0] - 2026-07-17
### Added
- **Session & Journey Analytics (Release 6)**: Developed `SessionAnalyzer` and `JourneyAnalyzer` under `unilog/analytics/modules/` for user session reconstruction, bounce rate calculation, and multi-step conversion funnel tracking.
- **SessionObserver UI**: Added interactive session behavioral observer UI displaying active user session tables and conversion funnel drop-off visualization.

## [0.5.0] - 2026-07-16
### Added
- **Insight Cards UI (Release 5)**: Created frontend `InsightCard` component rendering structured rule alerts with severity badges, confidence indicators, and actionable remediation guidance.
- **Analytics Endpoint (`POST /api/v1/analyze`)**: Added consolidated backend analysis endpoint running full metrics compilation and rule evaluation.

## [0.4.0] - 2026-07-15
### Added
- **Built-in Rule Engine (Release 4)**: Developed 12 built-in operational rules across 4 core categories (performance, reliability, traffic, security) under `unilog/analytics/rules/`.
- **Typed Insight Schemas**: Enforced typed `Insight` objects with category, severity, confidence, evidence, and recommendations.

---

## [0.3.5] - 2026-07-14


### Changed
- **Minimum Python Version**: Raised the minimum supported Python version constraint to `>=3.10` in `pyproject.toml` and regenerated the locks, dropping compatibility with Python 3.9.
- **Dependency Security Refresh**: Upgraded `python-multipart`, `starlette`, `urllib3`, `msgpack`, `requests`, `filelock`, `pytest`, and `pip` to safe release constraints, clearing all security advisories.

### Added
- **Path Traversal Sandboxing**: Enforced directory-isolation container rules via the `UNILOG_SANDBOX_ROOT` environment variable checks inside file gateway utilities.

## [0.4.0-alpha.2] - 2026-07-13
### Added
- **Proxy-Aware Network Module**: Introduced `api/security/network.py` providing proxy-aware client IP extraction (`resolve_client_ip`) and private/loopback address checkers.
- **Security Headers Middleware**: Implemented `SecurityHeadersMiddleware` applying strict HTTP headers (`X-Content-Type-Options`, `X-Frame-Options`, CSP, Permissions, Referrer) configurable via the `UNILOG_CSP` environment variable.
- **System Capability Diagnostics**: Added `GET /api/v1/system/info` route reporting version, active features, registered parsers, and supported formats.
- **Pydantic TaskMetadata Schema**: Enforced structured task parameters (`created_at`, `client_ip`, `owner_id`) using `TaskMetadata` models.
- **Informational CI Auditing**: Integrated `pip-audit` checks inside the Python 3.12 CI job matrix using a `continue-on-error` gate.
- **Safe Error Suppression**: Suppressed raw traceback leakage in route exceptions, returning clean generic descriptions while routing exceptions to structured logs.

## [0.4.0-alpha.1] - 2026-07-13
### Added
- **Operational Intelligence Core (Release 1)**: Integrated abstract `BaseAnalyzer`, structured `AnalyzerContext` parameter bounds, and `@register_analyzer` explicit metadata decorators.
- **Core Metrics Collection (Release 2)**: Developed core operational analyzers under `unilog/analytics/modules/`:
  - `TrafficAnalyzer`: Computes log volume and byte size aggregates.
  - `ErrorAnalyzer`: Isolates level classifications and computes error-to-info ratios.
  - `StatusAnalyzer`: Aggregates response status distributions and categories (2xx, 4xx, etc.).
  - `EndpointAnalyzer`: Ranks requested HTTP routes by frequency.
- **Auto-Discovery Loader**: Registry automatically maps and resolves analyzer plugins at package load time.
- **Pipeline Integration Tests**: Verified full compilation pipeline loops.

## [0.3.4] - 2026-07-12
### Added
- **Release Drafter**: Integrated `.github/release-drafter.yml` and release workflow to automatically catalog draft releases by PR labels.
- **GitHub Issue Forms**: Created structured YAML issue form templates for bug reports and feature requests.
- **Path Labeler**: Added automated labels mappings for incoming pull requests (backend, frontend, documentation, ci).
- **OpenSSF Scorecard**: Standardized weekly analysis scans checking action pins, branch protection, and vulnerability logs.
- **Automated PR Coverage Reports**: Embedded `pytest-coverage-comment` action inside CI quality gates reporting coverage tables directly on pull requests.

## [0.3.3] - 2026-07-12
### Added
- **Benchmarks Abstraction**: Created evaluation runner interfaces (`base_engine.py`, `mock_engine.py`, `gemini_engine.py`) under a dedicated `benchmarks/` directory.
- **Repeatable Regression Fixtures**: Developed simulated input PR metadata and git patch diffs alongside expected output assertions versioned under `fixtures/v1/`.
- **Weighted Quality Assertions**: Evaluates and scores AI review accuracy using a weighted model checking risk levels, missing checks, and security keyword hits.
- **Security Precision & Recall**: Calculates true/false positive and negative metrics for vulnerability alerts.
- **Execution Telemetry Logger**: Records prompt build, inference, and evaluation latency durations, saving logs under `benchmarks/reports/`.
- **CI Benchmarks Check**: Wired the local mock benchmarks runner into the pull requests test check suite.

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
