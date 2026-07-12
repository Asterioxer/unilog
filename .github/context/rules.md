Context-Version: 1

# Repository Invariant Rules

When introducing changes to the code, the reviewer must check against the following repository invariants. Any violation must trigger a risk warning.

## Parser Invariants
Every log parser format introduced or modified must:
1. **Register itself**: Must use `@register_parser` decorator and register inside `unilog/parsers/`.
2. **Add unit tests**: Must have corresponding test cases under `tests/test_parsers.py` (or similar tests).
3. **Format Support**: Must support CLI commands (`cli.py`), streaming parsing API, and statistics parsing engines.
4. **Update Detector**: Heuristics in `unilog/detector.py` must be updated to detect the new format with high confidence (>0.75).
5. **Update README**: Update list of supported formats in the root `README.md` if the change is user-facing.

## API & CLI Invariants
1. **Compatibility**: Keep output formats backwards-compatible.
2. **Type-Safety**: Enforce Pydantic input limits on all log payload fields.
3. **Security Constraints**: Decompressions must use the safe chunk stream. No standard XML or raw Gzip decompressions should bypass security helpers.
