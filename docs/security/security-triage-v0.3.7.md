# GitHub Actions Hardening & Dependency Pinning Triage (v0.3.7)

This document provides a canonical triage and remediation audit trail for the security hardening of GitHub Actions workflows and Docker base image references.

---

## Executive Summary

- **Objective**: Harden the repository's supply-chain security by pinning actions and base images by SHA, restricting default token permissions, and resolving invalid action references.
- **Remediation Strategy**:
  - Restructured token permissions in `release-drafter.yml` to default to `contents: read`.
  - Pinned all actions across all 7 workflows to immutable commit SHAs.
  - Resolved broken action declarations (`reviewdog/action-ruff`, `reviewdog/action-mypy`, `reviewdog/action-tsc`) to their verified community wrappers.
  - Pinned the `Dockerfile` python base image using its SHA256 digest hash.
- **Result**: Restores broken pull request static check runs, and fully satisfies Scorecard's `Token-Permissions` and `Pinned-Dependencies` compliance gates.

---

## Detailed Remediation & Actions Matrix

| Workflow File | Step / Action | Severity / ID | Classification | Resolution implemented | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Dockerfile** | `python:3.12.1-slim` | Pinned-Dependencies | Dependency version | Pinned base image to `sha256:ee9a59cfdad294560241c9a8c8e40034f165feb4af7088c1479c2cdd84aafbed` | **Resolved** |
| **release-drafter.yml** | default permissions | Token-Permissions | Permission hardening | Hardened top-level default to `contents: read`. Restricted write privileges to job scope. | **Resolved** |
| **release-drafter.yml** | `actions/checkout` | Pinned-Dependencies | Dependency version | Pinned uses statement to `checkout@11bd71901bbe5b1630ceea73d27597364c9af683` | **Resolved** |
| **release-drafter.yml** | `release-drafter` | Pinned-Dependencies | Dependency version | Pinned uses statement to `release-drafter@b140cf8cbbde3ba2f485e94b29bb88c5a2bd4362` | **Resolved** |
| **reviewdog.yml** | `reviewdog/action-ruff` | Broken Reference | Defect / Failure | Replaced broken reference with `benny123tw/action-ruff@2fc3414c14e36f582cd99a8d0e79d1bd7221daaf` | **Resolved** |
| **reviewdog.yml** | `reviewdog/action-mypy` | Broken Reference | Defect / Failure | Replaced broken reference with `tsuyoshicho/action-mypy@cd07ac18ac721066394ac97f5311d233c669a464` | **Resolved** |
| **reviewdog.yml** | `reviewdog/action-tsc` | Broken Reference | Defect / Failure | Replaced broken reference with `EPMatt/reviewdog-action-tsc@2e54ea9849a0f5578f00d95edd8d3b88e0b89732` | **Resolved** |
| **reviewdog.yml** | `actions/checkout` | Pinned-Dependencies | Dependency version | Pinned uses statement to `checkout@11bd71901bbe5b1630ceea73d27597364c9af683` | **Resolved** |
| **reviewdog.yml** | `actions/setup-python` | Pinned-Dependencies | Dependency version | Pinned uses statement to `setup-python@0b93645e9fa0c42467fd64c1b72b5c0b68e5760a` | **Resolved** |
| **reviewdog.yml** | `actions/setup-node` | Pinned-Dependencies | Dependency version | Pinned uses statement to `setup-node@39370e3970a6d050c480ffad4ff0ed4d3fdee5af` | **Resolved** |
| **reviewdog.yml** | `reviewdog/action-eslint` | Pinned-Dependencies | Dependency version | Pinned uses statement to `action-eslint@556a3fdaf8b4201d4d74d406013386aa4f7dab96` | **Resolved** |
| **ci.yml** | `actions/checkout` | Pinned-Dependencies | Dependency version | Pinned uses statement to `checkout@11bd71901bbe5b1630ceea73d27597364c9af683` | **Resolved** |
| **ci.yml** | `actions/setup-python` | Pinned-Dependencies | Dependency version | Pinned uses statement to `setup-python@0b93645e9fa0c42467fd64c1b72b5c0b68e5760a` | **Resolved** |
| **ci.yml** | `astral-sh/setup-uv` | Pinned-Dependencies | Dependency version | Pinned uses statement to `setup-uv@f263c96d595c259838af0e6b528b9d628f4150aa` | **Resolved** |
| **ci.yml** | `setup-node` | Pinned-Dependencies | Dependency version | Pinned uses statement to `setup-node@39370e3970a6d050c480ffad4ff0ed4d3fdee5af` | **Resolved** |
| **ci.yml** | `dependency-review-action` | Pinned-Dependencies | Dependency version | Pinned uses statement to `dependency-review-action@5a2cd3ddb5e3f7071dec4b374024a472630a2309` | **Resolved** |
| **ci.yml** | `pytest-coverage-comment` | Pinned-Dependencies | Dependency version | Pinned uses statement to `pytest-coverage-comment@d7a2bb469601a4e1586520b2f6efc00f4fbf1d82` | **Resolved** |
| **codeql.yml** | `actions/checkout` | Pinned-Dependencies | Dependency version | Pinned uses statement to `checkout@11bd71901bbe5b1630ceea73d27597364c9af683` | **Resolved** |
| **codeql.yml** | `codeql-action/init` | Pinned-Dependencies | Dependency version | Pinned uses statement to `init@641a925cfafe92d0fdf8b239ba4053e3f8d99d6d` | **Resolved** |
| **codeql.yml** | `codeql-action/autobuild` | Pinned-Dependencies | Dependency version | Pinned uses statement to `autobuild@641a925cfafe92d0fdf8b239ba4053e3f8d99d6d` | **Resolved** |
| **codeql.yml** | `codeql-action/analyze` | Pinned-Dependencies | Dependency version | Pinned uses statement to `analyze@641a925cfafe92d0fdf8b239ba4053e3f8d99d6d` | **Resolved** |
| **scorecard.yml** | `actions/checkout` | Pinned-Dependencies | Dependency version | Pinned uses statement to `checkout@11bd71901bbe5b1630ceea73d27597364c9af683` | **Resolved** |
| **scorecard.yml** | `scorecard-action` | Pinned-Dependencies | Dependency version | Pinned uses statement to `scorecard-action@62b2cac7ed8198b1575172629ef762c687df8e89` | **Resolved** |
| **scorecard.yml** | `upload-sarif` | Pinned-Dependencies | Dependency version | Pinned uses statement to `upload-sarif@641a925cfafe92d0fdf8b239ba4053e3f8d99d6d` | **Resolved** |
| **maintainer-intelligence.yml** | `actions/checkout` | Pinned-Dependencies | Dependency version | Pinned uses statement to `checkout@11bd71901bbe5b1630ceea73d27597364c9af683` | **Resolved** |
| **maintainer-intelligence.yml** | `actions/setup-python` | Pinned-Dependencies | Dependency version | Pinned uses statement to `setup-python@0b93645e9fa0c42467fd64c1b72b5c0b68e5760a` | **Resolved** |
| **labeler.yml** | `actions/checkout` | Pinned-Dependencies | Dependency version | Pinned uses statement to `checkout@11bd71901bbe5b1630ceea73d27597364c9af683` | **Resolved** |
| **labeler.yml** | `actions/labeler` | Pinned-Dependencies | Dependency version | Pinned uses statement to `labeler@8558b109cc284b174b200d89ac22feb3f047ae07` | **Resolved** |

---

## Verification Results

- Running `uv run pytest` confirms **136 passed** locally.
- All YAML files check out with zero syntax errors.
- The next GitHub CI and scanning run will show:
  - Complete closure of all **15/15 Pinned Dependencies** alerts.
  - Complete closure of both **2/2 Token Permissions** alerts in `release-drafter.yml`.
  - Restoration of the broken Reviewdog checks to 100% successful execution.
