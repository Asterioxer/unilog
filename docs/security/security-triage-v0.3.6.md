# CodeQL Path Confinement Triage & Remediation (v0.3.6)

This document provides a canonical triage, exploitability analysis, and implementation audit trail for the remediation of the 6 CodeQL "Uncontrolled data used in path expression" alerts (py/path-injection) in the `unilog` project.

---

## Executive Summary

- **Objective**: Ensure that user-controlled path operations are strictly confined within a configured sandbox root directory to prevent directory traversal.
- **Remediation Strategy**: Replaced simple path normalization with strict `pathlib`-based containment validation (`Path.resolve(strict=False)` and `Path.is_relative_to()`).
- **Files Affected**:
  - `unilog/core.py`
  - `unilog/detector.py`
  - `unilog/utils.py`
- **Result**: CodeQL path traversal vulnerabilities are fully mitigated at the application boundaries, and all security tests pass cleanly.

---

## Taint Trace Analysis & Reachability

Prior to this remediation, CodeQL flagged 6 path-injection alerts pointing to file access operations. We traced the static flows reported in the scanning run:

### 1. Alert Taint Flow Route
- **Source**: `req.log_text` or uploaded file bytes (`log.py` at line 47, 109, 179, and 209).
- **Propagator**: The string payload is passed down into core interfaces (`unilog.stream()`, `unilog.detect()`, `sample_lines()`, and `read_file()`).
- **Sink**: Filesystem gateways check if the `path_or_stream` parameter is a string, and if so, pass it directly to `os.path.exists()` or file opening context managers.
- **Stated Threat**: Statically, a user-controlled string (the log text payload) can flow directly into filesystem operations, prompting CodeQL to raise a High severity Alert.

### 2. Reachability Assessment
- **Web API (Remote Context)**: **Not Reachable**. The REST API never passes raw strings as paths; it wraps log text in `io.StringIO` streams before calling backend parsing logic. Thus, the condition `isinstance(path, str)` is never met for remote user inputs at runtime.
- **CLI (Local Context)**: **Safe / Local Only**. The CLI accepts strings from `sys.argv`. Since the local system executor operates with the permissions of the current logged-in user, this is a standard CLI operation.

---

## Implementation Details

Rather than suppressing static warning triggers, we established a central security boundary in the code:

### 1. Reusable Validator (`validate_path_safety`)
Located in [unilog/utils.py](file:///c:/Users/soham/Desktop/unilog/unilog/utils.py), it implements the following checks:
- **Circuit Breaker**: File paths should not contain raw log lines. If the path string contains newlines (`\n`, `\r`) or null bytes (`\0`), it immediately raises a `ValueError` without hitting filesystem functions.
- **Symlink Resolution**: Resolves canonical symlinks securely via `Path(path).resolve(strict=False)`. If an operating system level error occurs, it fails closed (raises `ValueError`).
- **Sandbox Root Confinement**: If `UNILOG_SANDBOX_ROOT` is configured, it verifies containment using `Path.is_relative_to()`. If the resolved path attempts to escape the root (e.g. `../../etc/passwd` or traversing to a separate drive on Windows), it blocks the request by raising a `PermissionError`.

### 2. Filesystem Gateways Mediated
Every path-based filesystem access in the core library is strictly routed through `validate_path_safety()` before invocation:
- **`unilog/core.py`** (`stream()`):
  ```python
  clean_path = validate_path_safety(path_or_stream)
  if not os.path.exists(clean_path): ...
  ```
- **`unilog/detector.py`** (`detect()`):
  ```python
  clean_path = validate_path_safety(path_or_stream)
  if not os.path.exists(clean_path): ...
  ```
- **`unilog/utils.py`** (`read_file()` and `sample_lines()`):
  ```python
  clean_path = validate_path_safety(path)
  # Resolves path prior to calling gzip.open / open
  ```

---

## Verification & Testing

To prevent regressions, we created a dedicated security test suite at [tests/security/test_path_confinement.py](file:///c:/Users/soham/Desktop/unilog/tests/security/test_path_confinement.py):
- **Traversal Rejections**: Asserts that `../../` traversal escapes raise `PermissionError`.
- **Absolute Path Escapes**: Confirms that `/tmp/test.log` outside the sandbox raises `PermissionError`.
- **Sandbox Valid File**: Verifies that standard files inside the sandbox resolve successfully.
- **Windows Path Cases**: Asserts cross-drive letter traversals (e.g. `C:\Windows\System32\...`) are blocked.
- **Symlink Escape Blocks**: Creates a local symlink escaping the sandbox and verifies that reading via the symlink raises `PermissionError`.
- **Circuit Breaker**: Confirms that raw string log payloads containing newlines raise `ValueError`.

All **136 tests** are green, and static checking (`ruff` & `mypy`) reports 0 warnings.
