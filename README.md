# ops-copilot

Self-hosted SRE investigation copilot for production systems.

`ops-copilot` lets an LLM call tools defined in YAML, execute safe remote commands over SSH, redact secrets from outputs, and stream investigation events through LangGraph or an optional FastAPI SSE server.

## Architecture

```text
User question -> InvestigationGraph -> LLM -> YAML tools -> SSH host
                                      <- redacted tool output <- command result
```

The package is intentionally generic. You can start with shell tools from YAML, then inject custom Python `RemoteTool` classes for richer workflows.

## Install

```bash
uv add ops-copilot
```

Optional extras:

```bash
uv add 'ops-copilot[server]'
uv add 'ops-copilot[openai]'
uv add 'ops-copilot[ollama]'
```

## YAML tools

```yaml
tools:
  - name: disk_usage
    type: shell
    description: Show filesystem usage.
    command: df -h

  - name: journalctl_service
    type: shell
    description: Show recent logs for a systemd service.
    command: journalctl -u {service} --since '{since}' --no-pager
    parameters:
      service:
        type: string
      since:
        type: string
        required: false
        default: "30 minutes ago"
```

## Minimal usage

```python
from ops_copilot import InvestigationGraph, SSHClient, ToolRegistry

ssh = SSHClient(host="server.example.com", user="deploy", key_path="~/.ssh/id_ed25519")
tools = ToolRegistry(ssh, config_path="tools.yaml").load()

graph = InvestigationGraph(
    llm=your_langchain_chat_model,
    tools=tools,
    system_prompt="You are an SRE copilot. Investigate safely and report evidence.",
)

async for event in graph.stream("The API is slow. What should I check?"):
    print(event)
```

## Streaming events

`InvestigationGraph.stream()` yields dictionaries with these event names:

| Event | Meaning |
| --- | --- |
| `token` | streamed model text |
| `tool_start` | tool call started with input and step id |
| `tool_end` | tool call finished with redacted output |
| `error` | graph or stream error |
| `done` | investigation complete |

## Optional FastAPI server

The `ops_copilot.server.create_app()` helper exposes:

- `POST /investigate`
- `POST /investigate/stream`

If `OPS_COPILOT_API_KEY` is set, clients must send `X-API-Key`.

## Security notes

This project executes commands on servers you control. Treat `tools.yaml` as privileged code.

Recommendations:

- Use SSH key auth with least-privilege users.
- Review every command template before exposing it to an LLM.
- Avoid destructive commands in YAML.
- Keep parameterized commands narrow.
- Store no secrets in YAML or prompts.
- Rely on built-in redaction as a safety net, not as your only control.

Built-in redaction covers env-style secret lines, Bearer tokens, OpenAI-style keys, JWTs, long hex runs, and inline image data URLs.

## Development

```bash
uv sync --dev
uv run ruff check .
uv run pytest
```

## License

MIT
