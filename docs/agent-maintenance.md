# Agent Maintenance Workflows

`ops-copilot` is designed to be maintained through small, reviewable changes. AI coding assistants are useful when they preserve the safety model and produce tests with every tool or incident update.

## Good Agent Tasks

- Add a new reviewed YAML toolpack with parameter validation.
- Add or expand an incident fixture in `examples/incidents/`.
- Add regression tests for sanitizer, command rendering, SSE events, and audit logs.
- Draft release notes from merged PRs and run release scripts.
- Review toolpacks with `ops-copilot review <path>`.

## Safety Rules

- Do not add secrets, private IPs, customer names, or real hostnames.
- Do not add destructive shell commands unless `policy.allow_destructive: true` is explicitly justified and tested.
- Prefer `dry_run: true` for examples that demonstrate command rendering.
- Every parameter interpolated into a command should define `allowed_values` or `pattern` when possible. If both are omitted, a secure-by-default safe pattern will restrict input to safe alphanumerics and basic punctuation to block shell injection.
- Audit logs and streamed events must redact sensitive values before leaving the tool boundary.

## Review Checklist

1. Run `bash scripts/validate-release.sh`.
2. Run `uv run ops-copilot review examples/toolpacks/systemd.yaml`.
3. Replay at least one incident fixture with `uv run ops-copilot replay examples/incidents/disk-full.yaml`.
4. Confirm the PR changes no secrets and no client-specific infrastructure names.
