# Threat Model

This document summarizes the main security risks for `ops-copilot` and the current mitigations.

`ops-copilot` is not a sandbox. It is a safer orchestration layer for reviewed operational tools.

## Scope

In scope:

- YAML shell tools loaded by `ToolRegistry`.
- Custom Python `RemoteTool` implementations.
- SSH command execution on hosts controlled by the operator.
- LangGraph investigation flows.
- Optional FastAPI JSON and SSE endpoints.
- Redacted audit logs and incident reports.

Out of scope:

- Hardening the remote host itself.
- Sandboxing shell commands after they are executed.
- Preventing all possible secret exfiltration from a malicious tool definition.
- Securing hosted LLM providers or third-party logging systems.

## Assets

- SSH private keys and credentials.
- Hostnames, service names, and topology.
- Command output containing secrets, tokens, passwords, or incident data.
- Availability of target hosts and critical services.
- Integrity of YAML toolpacks and custom tools.
- Audit logs and incident reports.

## Trust Boundaries

```text
User/UI -> API/Graph -> LLM -> tool input -> reviewed tool -> SSH host
                                  ^                         |
                                  |                         v
                            redacted output <- command output
```

The highest-risk boundary is `LLM -> tool input -> command rendering`.

## STRIDE Summary

| Risk | Example | Mitigation |
| --- | --- | --- |
| Spoofing | Unauthenticated client calls `/investigate` | `OPS_COPILOT_API_KEY` gates the optional API server |
| Tampering | Prompt injects shell metacharacters into `{service}` | string parameters require `allowed_values`, `pattern`, or default safe validation |
| Repudiation | Operator cannot reconstruct which tool was called | stream events, `JsonlAuditLog`, and incident reports record redacted evidence |
| Information disclosure | Tool output includes Bearer tokens or JWTs | redaction runs before output returns to the LLM/UI/audit log |
| Denial of service | Tool restarts or removes services | command policy blocks obvious destructive commands by default |
| Elevation of privilege | YAML tool invokes privileged shell path | YAML is treated as privileged code; deployment must use least-privilege SSH users |

## Current Controls

- Explicit tool registry: models can only call registered tools.
- Conservative parameter validation for unconstrained string inputs.
- Command policy blocks dangerous command families unless `allow_destructive` is explicit.
- `dry_run: true` supports preflight rendering.
- Redaction covers common token and secret shapes.
- Optional API key protects the FastAPI server.
- Toolpack review CLI flags missing template parameters and weak string constraints.
- Incident fixtures make security-sensitive behavior testable without real hosts.

## Residual Risks

- A reviewed but malicious YAML command can still exfiltrate data.
- Redaction is pattern-based and cannot guarantee complete coverage.
- A least-privilege SSH user can still damage resources it is allowed to access.
- API key authentication is simple shared-secret auth, not a complete identity system.
- Long-running commands are not yet governed by per-tool timeout policies.
- Audit logs are redacted but may still contain sensitive operational context.

## Recommended Operator Controls

- Use a dedicated SSH user with minimal permissions.
- Keep toolpacks in source control and require review before deployment.
- Prefer `allowed_values` for service names, namespaces, environments, and clusters.
- Use `pattern` only when the allowed value space is too large to enumerate.
- Run `ops-copilot review <toolpack.yaml>` before exposing a toolpack.
- Keep `OPS_COPILOT_API_KEY` enabled for any network-exposed API server.
- Store audit logs in a restricted location and rotate them.
- Test destructive or restart-like workflows outside `ops-copilot` first.

## Future Hardening

- Per-tool timeout and output-size policies.
- SQLite-backed sessions with explicit retention controls.
- More sanitizer regression fixtures for unusual secret shapes.
- Type-checking and coverage gates in CI.
- Signed or checksummed toolpack distribution for shared environments.
