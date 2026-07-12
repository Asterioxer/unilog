# Maintainer Intelligence Operations Guide

This guide describes the architecture, workflows, configurations, and custom rules of **Maintainer Intelligence** (v0.3.3), a reusable, project-aware CI review automation and quality benchmarking subsystem.

---

## 1. System Architecture

The subsystem consists of four core components:

```
[GitHub PR Event]
       │
       ├──► [Reviewdog Workflow] ➔ Ruff / Mypy / ESLint / TSC
       │
       ├──► [Maintainer Intelligence Workflow] ➔ Quality Gates (Run Pytest checks)
       │                                       ➔ Run Benchmarks runner (Mock Mode)
       │
       └──► [Maintainer Intelligence AI Review] 
                  │
                  ├──► 1. SHA Cache check (pr_helper.py)
                  │
                  └──► 2. Compile context & Invoke LLM Client (Gemini API JSON output)
                             │
                             └──► Render MD comment, post/edit comment, apply triage labels (pr_helper.py)
```

---

## 2. Configurations & Files Reference

All operational parameters are defined inside [maintainer-config.yml](file:///c:/Users/soham/Desktop/unilog/.github/maintainer-config.yml):

* **`timeout_seconds` / `retries`**: Set API execution limits.
* **`labels`**: Set label mappings applied during review triages:
  - `high_risk`: Label name for critical findings (e.g. `needs-review`).
  - `missing_tests`: Label name for missing test assets (e.g. `tests`).
  - `missing_docs`: Label name for missing docs assets (e.g. `documentation`).
* **`ignore_paths`**: Excludes build files, lockfiles, and configs from diff analysis, saving token bandwidth.

---

## 3. Custom Repository Knowledge

Review rules are extracted into modular context guides inside `.github/context/`:
* **`rules.md`**: Defines core invariants that parsers must register, contain tests, maintain CLI compatibility, and update format detectors.
* **`architecture.md` / `project-overview.md`**: Educate the reviewer about components and layer relationships.

---

## 4. Swapping LLM Providers

The AI client implements a decoupled vendor-independent layout:
1. **Abstract Interface**: [base.py](file:///c:/Users/soham/Desktop/unilog/.github/scripts/llm/base.py) defines the general LLM interface.
2. **Current client**: [gemini.py](file:///c:/Users/soham/Desktop/unilog/.github/scripts/llm/gemini.py) implements the interface using standard HTTP calls to the Gemini API.

To switch to a different LLM provider (e.g. OpenAI or a local Llama model):
1. Add a new client file (e.g. `openai.py`) under `.github/scripts/llm/` implementing `BaseLLMClient`.
2. Update the review execution scripts ([ai_review.py](file:///c:/Users/soham/Desktop/unilog/.github/scripts/review/ai_review.py) and [dependabot_review.py](file:///c:/Users/soham/Desktop/unilog/.github/scripts/review/dependabot_review.py)) to import your new client class instead of `GeminiClient`.

---

## 5. Benchmarking Platform

The system includes a permanent evaluation benchmark platform under [benchmarks/](file:///c:/Users/soham/Desktop/unilog/benchmarks/):

- **Manifest-driven**: Execution paths are explicitly listed under `fixtures/v1/manifest.json`.
- **Weighted scoring**: Compares generated response outputs against expected properties, calculating scores based on a weighted formula.
- **Mock runner**: Supports executing mock reviews locally during CI checks to prevent API usage overheads:
  ```bash
  python benchmarks/runner.py --engine mock --fixtures v1
  ```
- **Historical telemetry**: Archives latencies and correctness metrics under `reports/` on each run.
