# Release Process

## Checklist

1. Merge feature PRs to `main` after CI, build, and smoke checks pass.
2. Run `python scripts/prepare-release.py X.Y.Z`.
3. Review `git diff` and commit the release prep.
4. Push `main` and wait for CI, build, and smoke checks to pass.
5. Run `bash scripts/create-release.sh X.Y.Z`.
6. Confirm the `Publish to PyPI` workflow succeeds.
7. Run `bash scripts/run-pypi-install-check.sh`.
8. Run `uv run python examples/local_demo.py` when changing investigation behavior.
9. Scan source and docs for hostnames, private IPs, credentials, and client-specific names.

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
