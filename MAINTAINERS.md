# Maintainers

## Primary maintainer

- Benjamin Jornet (`@BenjaminJornet`)

## Maintainer responsibilities

- Review pull requests that add tools, command templates, graph behavior, or server endpoints.
- Triage issues with redacted YAML snippets and reproduction steps.
- Maintain the security model for SSH and LLM-driven tool execution.
- Keep examples runnable without private infrastructure.
- Publish releases and maintain `CHANGELOG.md`.

## Review priorities

1. No real hostnames, private IPs, credentials, tokens, or internal service names.
2. Tool output must be redacted before it reaches the LLM or SSE stream.
3. Shell commands should be narrow, documented, and non-destructive.
4. New graph/server behaviors need tests.
5. Security assumptions must be documented.
