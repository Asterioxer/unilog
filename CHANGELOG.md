# Changelog

All notable changes to this project will be documented in this file.

## [0.3.1] - 2026-07-12
### Added
- Created `SECURITY.md` defining supported versions and reporting policy.
- Created `docs/security.md` guiding configure parameters operations.
- Added `defusedxml` secure XML parser dependency.
- Integrated Dependabot automated weekly package updates.
- Added CodeQL static application security testing scanning.
- Added Dependency Review pull request workflow.
- Created comprehensive security test suite threat folders under `tests/security/`.

### Fixed
- Fixed Gzip bomb decompression vulnerability via chunk-limit streaming.
- Hardened Windows XML parser mapping DTD recursive expansions to parse errors.
- Mitigated task queue memory leaks via time-to-live (TTL) and capacity eviction.
- Enforced input boundary limits on Pydantic JSON schemas.

## [0.1.0] - 2026-07-10
### Added
- Initial scaffold and project structure.
