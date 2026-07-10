# Contributing to unilog

Thank you for contributing to the `unilog` project! Follow these steps to set up your environment and verify code quality.

## Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Asterioxer/unilog.git
   cd unilog
   ```
2. **Install dependencies using `uv`**:
   Make sure you have `uv` installed (`pip install uv` or via official installer).
   ```bash
   uv sync --all-extras
   ```

## Development Commands

Ensure all checks are run and passed before pushing updates:

### 1. Code Formatting and Linting (Ruff)
Ruff is used to enforce style guides and format imports.
```bash
uv run ruff check .
```
To auto-fix errors:
```bash
uv run ruff check . --fix
```

### 2. Static Typing (Mypy)
Mypy checks static type hints in python source files.
```bash
uv run mypy unilog api
```

### 3. Unit Tests and Coverage (Pytest)
Run the unit test suite and verify that total coverage remains above **92%**:
```bash
uv run pytest --cov=unilog --cov=api --cov-report=term-missing
```

## Git Flow

- Create feature branches named `feature/<name>` or `bugfix/<name>`.
- Keep commit histories clean and semantic:
  - `feat: ...` for new features
  - `fix: ...` for bug fixes
  - `docs: ...` for documentation modifications
- Pushing to the main branch triggers the GitHub Actions matrix verify gates.
