# Security Model

`ops-copilot` is designed for self-hosted SRE workflows where an LLM can request operational evidence through reviewed tools.

It is not a sandbox. YAML tools and custom `RemoteTool` classes are privileged code.

## Assets to protect

- SSH credentials and private keys.
- Hostnames and network topology.
- Command output containing tokens, passwords, JWTs, API keys, or image data URLs.
- Operational context that should not be exposed to an LLM provider.
- Availability of the target host.

## Trust boundaries

```text
User prompt -> LLM -> tool call -> reviewed tool definition -> SSH host -> redacted output -> LLM/UI
```

The critical boundary is between the LLM-generated tool input and the command executed on the remote host.

## What the project does

- Requires tools to be declared explicitly in YAML or Python.
- Redacts common secret shapes from tool output.
- Collapses large inline image data URLs.
- Removes system reminder and image placeholder artifacts from prompts.
- Emits structured stream events so UIs can distinguish tool starts, tool ends, errors, and model tokens.
- Supports per-tool command timeouts and output-size limits for reviewed shell tools.

## What the project does not do

- It does not make arbitrary shell commands safe.
- It does not prevent a bad YAML file from running a bad command.
- It does not replace SSH least-privilege configuration.
- It does not guarantee that every possible secret shape is redacted.
- It does not provide network isolation or process sandboxing.

## Recommended deployment controls

- Use a dedicated SSH user with least-privilege access.
- Review every command in `tools.yaml` before deployment.
- Avoid destructive commands and broad shell fragments.
- Prefer fixed commands with narrow parameters.
- Avoid sending sensitive prompts to hosted model providers.
- Keep `OPS_COPILOT_API_KEY` enabled when exposing the FastAPI server.
- Review logs and SSE consumers for accidental sensitive data retention.

## Safer tool patterns

Prefer:

```yaml
command: journalctl -u {service} --since '{since}' --no-pager
parameters:
  service:
    type: string
  since:
    type: string
    default: "30 minutes ago"
```

Avoid:

```yaml
command: "{arbitrary_shell}"
```

The second form gives the LLM too much control over the shell.

## Parameter validation & shell injection prevention

All string parameters in YAML tools are validated. If a parameter defines neither a custom regex `pattern` nor a list of `allowed_values`, it is validated against a conservative default pattern that permits only safe characters: letters, numbers, spaces, and minor SRE characters such as `-`, `_`, `.`, `/`, `:`, `@`, `=`, and `+`.

Any parameter input containing characters like `;`, `&`, `|`, `<`, `>`, `$()`, or backticks is rejected by default to prevent shell injection, even if the developer forgot to define validation constraints.

If a tool requires metacharacters (e.g. for complex log filtering), the developer must explicitly define a custom `pattern` in the YAML definition to bypass the default constraint. This ensures the system remains **Secure by Default**.

## Per-tool execution limits

Reviewed shell tools can define `timeout_seconds` and `max_output_chars` metadata. Timeouts reduce the chance that a slow command blocks an investigation indefinitely. Output limits reduce accidental prompt/log bloat and append a truncation marker when content is omitted.

These controls are guardrails, not a sandbox. Operators should still keep SSH users least-privilege and prefer narrow, read-only commands.
