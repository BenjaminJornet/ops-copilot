# Incident Fixtures

The fixtures in `examples/incidents/` document fake, credential-free incidents that can be used for demos and regression tests.

Each fixture includes:

- `question`: the user prompt for the investigation.
- `fake_outputs`: command outputs a fake SSH client can return.
- `expected_evidence`: facts the copilot should cite.
- `safe_next_steps`: actions that are safe to recommend after evidence is collected.

These fixtures intentionally avoid real hostnames, private IPs, credentials, and customer-specific names.

## Included Fixtures

- `bad-env-var.yaml`: a service fails because a required environment variable is missing after deploy.
- `disk-full.yaml`: root filesystem pressure caused by large application logs.
- `failing-systemd-service.yaml`: service-level failure evidence from systemd-style output.
- `high-cpu.yaml`: host-level CPU pressure evidence.
- `slow-api.yaml`: route-level latency and dependency pressure despite healthy service status.
