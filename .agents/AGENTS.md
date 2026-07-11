# Project-Scoped Customization Rules

## Dependency Management Rule

Whenever adding, removing, or upgrading dependencies:
1. Update the corresponding manifest (`pyproject.toml` or `package.json`).
2. Regenerate the lockfile (`uv.lock` or `package-lock.json`).
3. Verify a clean install (`uv sync` or `npm ci`).
4. Commit the manifest and lockfile together.
5. Do not rely on CI to regenerate lockfiles.
