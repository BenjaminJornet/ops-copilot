# Security Policy

## Supported versions

Only the latest minor release receives security fixes while the project is pre-1.0.

## Reporting a vulnerability

Please open a private GitHub security advisory if available, or contact the maintainer through GitHub.

## Security model summary

`ops-copilot` executes commands over SSH on systems you control. The project reduces accidental exposure with secret redaction, input/output sanitizers, and explicit tool definitions, but it does not make arbitrary shell commands safe.

Review `docs/security-model.md` before deploying the server or exposing tools to an LLM.
