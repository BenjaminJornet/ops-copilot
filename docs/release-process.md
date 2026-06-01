# Release Process

## Checklist

1. Run `uv run ruff check .`.
2. Run `uv run pytest`.
3. Run `uv build`.
4. Run `examples/local_demo.py`.
5. Scan source and docs for hostnames, private IPs, credentials, and client-specific names.
6. Update `CHANGELOG.md`.
7. Tag the release.
8. Create a GitHub release.
9. Publish through the manual `Publish to PyPI` workflow.

## Local development with sibling packages

When `langchain-content-normalizer` is checked out next to this repository:

```bash
PYTHONPATH="../langchain-content-normalizer/src" uv run --no-sync pytest
```

Published releases should depend on the PyPI package, not on a local path.

## Security review before each release

- Review `tools.yaml` examples for destructive commands.
- Review redaction tests.
- Review SSE event payloads for raw tool output handling.
- Confirm `OPS_COPILOT_API_KEY` behavior remains documented.
