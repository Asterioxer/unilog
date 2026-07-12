# Maintainer Intelligence Benchmark Suite

This directory contains the regression and quality benchmarking framework used to evaluate **Maintainer Intelligence** (v0.3.3) pull request reviews and analysis engines.

---

## 1. Directory Structure

* **`runner.py`**: CLI orchestrator loading versioned manifests and driving reviews.
* **`evaluator.py`**: Weighted assertions evaluator scoring responses against ground truth.
* **`engines/`**: decoupled reviews executors plugins:
  - `base_engine.py`: Base class interface.
  - `mock_engine.py`: Dynamic mock returning predicted JSON shapes for CI checks.
  - `gemini_engine.py`: Live AI caller communicating with Gemini API.
* **`reports/`**: Historical YYYY-MM-DD-HHMMSS.json evaluation results.
* **`fixtures/`**: Simulated input and expected output shapes, versioned and tag-based.

---

## 2. Manifest & Scenario Schema

Scenarios are explicitly listed inside the versioned manifest `fixtures/v1/manifest.json`.

Each scenario directory (e.g. `fixtures/v1/hard/security_vuln/`) has:
- **`metadata.json`**: Simplified PR details (title, description, commits, changed files).
- **`pr.diff`**: simulated patch code diff content.
- **`expected.json`**: Ground truth schema assertions:
  ```json
  {
    "schema_version": 1,
    "expected": {
      "risk": "medium" | "high",
      "tests_missing": true | false,
      "documentation_missing": true | false,
      "recommendation": "ready" | "needs_review" | "major_changes",
      "security_keywords": ["xml", "shell", "eval"]
    }
  }
  ```

---

## 3. Weighted Evaluation Formula

Review accuracy is scored out of 100.0 based on the following weights:
- **Risk classification**: 25%
- **Missing tests detection**: 20%
- **Missing documentation detection**: 15%
- **Security keywords recall check**: 25%
- **Recommendation classification**: 15%

---

## 4. How to Execute Benchmarks

### Local Mock Mode (Fast, Free, Offline)
Used inside standard pull request CI checks:
```bash
python benchmarks/runner.py --engine mock --fixtures v1
```

### Live AI Mode (Requires GEMINI_API_KEY)
Executes a real benchmark using Gemini 2.5 Flash, saving a historical report:
```bash
python benchmarks/runner.py --engine gemini --fixtures v1 --report
```

### Run Specific Tagged Scenarios
```bash
python benchmarks/runner.py --engine mock --fixtures v1 --tag security
```
