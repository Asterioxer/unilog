Context-Version: 1

# Coding Standards & Guidelines

We follow strict quality standards to maintain code clean and reliable across both backend and frontend layers.

## Backend Guidelines
- **Type Annotations**: All python modules must contain complete type annotations checked by `mypy`.
- **Formatting**: Linting and formatting rules are managed by `ruff`. No unused imports, unused variables, or wildcards allowed.
- **Tests**: Write unit tests under `tests/` using `pytest`. The code coverage must remain at or above **92%**.
- **Exception Safety**: Intercept external exceptions, particularly around file, XML, and gzip handling, mapping them to structured error messages.

## Frontend Guidelines
- **TypeScript**: Complete typing. Avoid the use of `any` types.
- **Components Styling**: Use raw Vanilla CSS for layouts. Tailwinds/external utility classes are forbidden unless requested.
- **Testing**: Frontend logic is verified via `Vitest`. Keep tests decoupled from browser environments.
- **State Management**: Shared table state resides inside React Query or hooks (`useTableState`).
