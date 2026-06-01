# Demo

`ops-copilot` includes a local demo that does not require a real SSH host or an API key.

It uses:

- a fake SSH client with deterministic host-health outputs
- the example YAML tools in `examples/tools.yaml`
- a fake LangChain chat model
- the same `InvestigationGraph.stream()` path used by real integrations

## Run the local demo

```bash
uv sync --dev
uv run python examples/local_demo.py
uv run python examples/replay_incident.py examples/incidents/disk-full.yaml
```

Expected output shape:

```python
{'event': 'token', 'data': 'The fake host looks healthy. Check app logs next.'}
{'event': 'done', 'data': {}}
```

The exact token event can vary by model implementation, but the demo should finish with a `done` event.

## Run the smoke script

```bash
uv run python scripts/smoke.py
```

Expected output:

```text
smoke ok
```

## What this proves

- YAML tools can be loaded into the registry.
- The investigation graph can run without external services.
- Incident fixtures can be replayed without SSH credentials.
- Stream events are shaped consistently.
- Redaction and sanitization paths are importable in a clean environment.

## What this does not prove

- Real SSH connectivity.
- A hosted LLM provider integration.
- Production deployment hardening.

Those should be tested separately with reviewed tools and least-privilege SSH credentials.
