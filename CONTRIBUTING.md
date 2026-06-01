# Contributing

Thanks for helping improve `ops-copilot`.

## Development setup

`ops-copilot` depends on `langchain-content-normalizer`. Before that package is published to a package index, use the sibling checkout during local development:

```bash
PYTHONPATH="../langchain-content-normalizer/src" uv run --no-sync ruff check .
PYTHONPATH="../langchain-content-normalizer/src" uv run --no-sync pytest
```

Once the dependency is available through the configured Git URL, the normal workflow is:

```bash
uv sync --dev
uv run ruff check .
uv run pytest
```

## Contribution guidelines

- Treat YAML tool definitions as privileged code.
- Add tests for every new command renderer, sanitizer, or graph event behavior.
- Never add real hostnames, credentials, private IPs, or internal service names.
- Keep tool outputs redacted before they reach the LLM or SSE stream.
- Prefer narrow, explicit parameters over free-form shell fragments.
- Document security assumptions in `docs/security-model.md`.

## Useful PRs

- Safer command policy and allowlist validation.
- Built-in systemd and Docker tool packs.
- More fake incident fixtures for tests.
- Better documentation for custom tools and server deployment.
