# Maintenance Workflows

`ops-copilot` is designed to be maintained with the same workflows it supports: structured investigation, explicit tools, safety review, and repeatable releases.

## AI-assisted maintenance use cases

- Review pull requests that add YAML tools or custom `RemoteTool` classes.
- Generate edge-case tests for command rendering and redaction.
- Review SSH and command-execution safety boundaries.
- Draft release notes from merged changes.
- Triage issues by reproducing reported tool configurations against fake SSH clients.
- Improve documentation for operational workflows.

## Review checklist for tool PRs

- Is the command read-only or clearly documented?
- Are parameters narrow and typed?
- Could a parameter inject arbitrary shell syntax?
- Is output redacted before it reaches the graph or stream?
- Is there a test for the command template?
- Does the README or docs explain the workflow?

## Release checklist

- Run `uv run ruff check .`.
- Run `uv run pytest`.
- Scan source files for hostnames, private IPs, credentials, and client-specific names.
- Update `CHANGELOG.md`.
- Tag the release.
- Publish release notes.
