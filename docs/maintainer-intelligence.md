# Maintainer Intelligence Operations Guide

This guide describes the architecture, workflows, configurations, and custom rules of **Maintainer Intelligence** (v0.3.2), a reusable, project-aware CI review automation subsystem for git repositories.

---

## 1. System Architecture

The subsystem consists of three core components:

```
[GitHub PR Event]
       │
       ├──► [Reviewdog Workflow] ➔ Ruff / Mypy / ESLint / TSC
       │
       └──► [Maintainer Intelligence Workflow] 
                  │
                  ├──► 1. Quality Gates (Run Pytest checks)
                  │
                  ├──► 2. SHA Cache check (pr_helper.py)
                  │
                  └──► 3. Compile context & Invoke LLM Client (Gemini API JSON output)
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

## 5. Disabling Workflows

To temporarily disable AI reviews or static analyses:
* Delete or rename the corresponding workflow file (e.g., rename `.github/workflows/maintainer-intelligence.yml` to `maintainer-intelligence.yml.disabled`).
