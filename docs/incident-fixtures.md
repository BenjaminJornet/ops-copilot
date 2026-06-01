# Incident Fixtures

The fixtures in `examples/incidents/` document fake, credential-free incidents that can be used for demos and regression tests.

Each fixture includes:

- `question`: the user prompt for the investigation.
- `fake_outputs`: command outputs a fake SSH client can return.
- `expected_evidence`: facts the copilot should cite.
- `safe_next_steps`: actions that are safe to recommend after evidence is collected.

These fixtures intentionally avoid real hostnames, private IPs, credentials, and customer-specific names.
