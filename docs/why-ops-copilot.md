# Why ops-copilot Exists

Production investigation is repetitive but risky.

SREs and maintainers often need the same evidence during incidents:

- service status
- recent logs
- disk and memory pressure
- container health
- upstream availability
- recent deploy markers

LLMs can help organize that evidence, but giving an LLM free-form shell access is not a responsible default.

`ops-copilot` is built around a narrower model:

```text
reviewed YAML tools + typed parameters + SSH execution + redacted output + streamable investigation events
```

## Design goals

- Keep operational tools explicit and reviewable.
- Make outputs safe enough to send through an LLM workflow by defaulting to redaction.
- Let users stream progress to a UI without mixing model tokens and tool results.
- Support self-hosted workflows instead of requiring a proprietary agent platform.
- Make maintenance reviewable with tests, CI, release workflows, and security documentation.

## Non-goals

- Arbitrary autonomous shell access.
- Replacing incident commanders or SRE judgment.
- Hiding unsafe YAML behind a friendly interface.
- Providing a universal sandbox.

## Why this matters for open source maintainers

Many maintainers operate small production services around their projects: docs, package registries, bots, CI runners, demo apps, or self-hosted infra.

`ops-copilot` aims to make that operational work more repeatable while keeping tool definitions visible for review. Codex-style workflows can help maintainers review YAML tools, add edge-case tests, triage issues, and prepare safe releases.
