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
