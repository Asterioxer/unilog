Context-Version: 1

# Release Process

`unilog` uses Semantic Versioning (`MAJOR.MINOR.PATCH`) to track versions and release logs.

## Commit Message Conventions
- **feat**: Introducing new features or components.
- **fix**: Resolving bugs or crashes.
- **refactor**: Rearranging existing code without changing logic.
- **docs**: Adjusting documentation, README, or CHANGELOG files.
- **chore**: Maintaining configuration settings.

## Release Steps
1. All changes must be fully tested locally before push.
2. Update the `CHANGELOG.md` file documenting the changes under the corresponding version headers.
3. Update `pyproject.toml` and package configuration files.
4. Merge using Pull Requests only; status checks must remain green.
5. Create a GitHub Release corresponding to the tagged git version.
