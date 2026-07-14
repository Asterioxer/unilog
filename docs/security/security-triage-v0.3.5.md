# Dependency & Code Scanning Security Triage (v0.3.5)

This document provides a canonical triage and reachability audit trail of the ecosystem dependencies and static analysis warnings for the `unilog` project prior to the v0.4 release.

---

## CodeQL Path Traversal Alerts (CWE-22)

CodeQL originally flagged 6 findings of **Uncontrolled data used in path expression** in `unilog/core.py`, `unilog/detector.py`, and `unilog/utils.py`.

### 1. Contextual Vulnerability & Exploitability Analysis
- **API Server Context**: No REST API routes accept local filesystem paths as parameters. All files are uploaded as stream content (`UploadFile`) and decoded directly in-memory. Therefore, there is **zero remote web exploitability** for these path alerts.
- **CLI Context**: The CLI accepts a file path parameter from the user. Since the CLI is executed locally by users who already have read permissions on their own files, the threat model is limited to local privilege escalation or arbitrary read (which is expected capability for a log parsing utility).

### 2. Sandbox Mitigation Policy (`UNILOG_SANDBOX_ROOT`)
To fully address path traversal concerns on deployments (e.g., if a wrapper service passes dynamic path arguments to the library), we implemented path containment:
- Introduced the `UNILOG_SANDBOX_ROOT` environment variable.
- When defined, `validate_path_safety(path)` verifies that the canonical resolved path (`os.path.realpath`) is strictly confined within the configured sandbox directory using commonpath validation. If the path escapes the sandbox (e.g. `../../etc/passwd` or crossing drive letters on Windows), a `PermissionError` is immediately raised.
- When not defined (default), the CLI operates normally.

### 3. Triage Matrix

| File Path / Location | Alert Type | Classification | Exploitability in unilog | Remediation Implemented | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [unilog/core.py:25](file:///c:/Users/soham/Desktop/unilog/unilog/core.py#L25) | Path Traversal | Mitigated Finding | **Low (Local CLI Only)** | Enforced path validation via `validate_path_safety()`. | **Resolved** |
| [unilog/detector.py:27](file:///c:/Users/soham/Desktop/unilog/unilog/detector.py#L27) | Path Traversal | Mitigated Finding | **Low (Local CLI Only)** | Enforced path validation via `validate_path_safety()`. | **Resolved** |
| [unilog/utils.py:73](file:///c:/Users/soham/Desktop/unilog/unilog/utils.py#L73) | Path Traversal | Mitigated Finding | **Low (Local CLI Only)** | Enforced path validation via `validate_path_safety()`. | **Resolved** |
| [unilog/utils.py:77](file:///c:/Users/soham/Desktop/unilog/unilog/utils.py#L77) | Path Traversal | Mitigated Finding | **Low (Local CLI Only)** | Enforced path validation via `validate_path_safety()`. | **Resolved** |
| [unilog/utils.py:106](file:///c:/Users/soham/Desktop/unilog/unilog/utils.py#L106) | Path Traversal | Mitigated Finding | **Low (Local CLI Only)** | Enforced path validation via `validate_path_safety()`. | **Resolved** |
| [unilog/utils.py:113](file:///c:/Users/soham/Desktop/unilog/unilog/utils.py#L113) | Path Traversal | Mitigated Finding | **Low (Local CLI Only)** | Enforced path validation via `validate_path_safety()`. | **Resolved** |

---

## Dependency Vulnerability Audit Matrix (Dependabot & pip-audit)

The following matrix records the triage status of all python packages with vulnerability advisories flagged by Dependabot:

| Package | Severity | Category | Direct / Transitive | Exploitability in unilog | Mitigation & Upgrade Version | Blocks v0.4? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **python-multipart** | High | Runtime | Direct | **Medium**: Parser processes multipart headers in file uploads. | Upgraded to `>=0.0.19` (locked to `0.0.20`/`0.0.32`). | ❌ No |
| **starlette** | High | Runtime | Transitive (FastAPI) | **Low**: Form-parsing API routes are exposed, but rate-limited. UNC SSRF is unreachable (StaticFiles not served). | Upgraded to `>=0.38.2` (locked to `0.49.3`/`1.3.1`). | ❌ No |
| **urllib3** | High | Runtime | Transitive | **None (Not Reachable)**: unilog does not make outbound HTTP requests. | Upgraded to `>=2.2.2` (locked to `2.6.3`/`2.7.0`). | ❌ No |
| **msgpack** | High | Tooling | Transitive | **None (Not Reachable)**: Unused in project codebase. | Upgraded to `>=1.0.8` (locked to `1.1.2`/`1.2.1`). | ❌ No |
| **requests** | Moderate | Tooling | Transitive | **None (Not Reachable)**: Unused in runtime code. | Upgraded to `>=2.32.2` (locked to `2.32.5`/`2.34.2`). | ❌ No |
| **filelock** | Moderate | Dev-time | Transitive | **None (Not Reachable)**: Dev-only test dependency. | Upgraded to `>=3.20.1` (locked to `3.19.1`/`3.29.7`). | ❌ No |
| **pytest** | Moderate | Dev-time | Direct | **None**: Used only for local test execution. | Upgraded to `>=8.0.0` (locked to `9.1.1`). | ❌ No |
| **pip** | Moderate | Dev-time | Tooling | **None**: Isolation/build tool only. | Upgraded to `>=26.0.1`. | ❌ No |

### Notes for Future Maintainers
- **Starlette & python-multipart**: If upgrading FastAPI, ensure these packages are locked to safe releases to prevent CPU/memory exhaustion via malicious form/multipart headers.
- **urllib3, msgpack, requests**: These are transitive helper libraries. Since they are not reachable in the application runtime, dependency alerts on these packages do not compromise application security but are upgraded to maintain clean audit reports.
