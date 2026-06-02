# Writing Tools

Tools can be defined as YAML shell commands or as custom Python classes.

## YAML shell tools

```yaml
tools:
  - name: disk_usage
    type: shell
    description: Show filesystem usage.
    command: df -h
```

Parameterized commands use Python `str.format` placeholders:

```yaml
tools:
  - name: service_logs
    type: shell
    description: Show recent logs for a service.
    command: journalctl -u {service} --since '{since}' --no-pager
    parameters:
      service:
        type: string
        description: systemd service name
      since:
        type: string
        required: false
        default: "30 minutes ago"
```

Supported parameter types:

- `string`
- `integer`
- `number`
- `boolean`

Optional safety constraints:

```yaml
parameters:
  service:
    type: string
    allowed_values: [api, worker]
  since:
    type: string
    pattern: "[0-9]+ (minutes|hours) ago"
```

`ShellTool` rejects parameter values containing newlines, carriage returns, or null bytes. `allowed_values` and `pattern` add narrow validation before command rendering. These checks reduce accidental injection risk, but they do not make arbitrary shell templates safe.

Per-tool execution limits keep reviewed tools bounded:

```yaml
tools:
  - name: recent_logs
    type: shell
    description: Show recent service logs.
    command: journalctl -u {service} --since '30 minutes ago' --no-pager
    timeout_seconds: 10
    max_output_chars: 20000
    parameters:
      service:
        type: string
        allowed_values: [api, worker]
```

- `timeout_seconds` overrides the SSH client's default command timeout for this tool.
- `max_output_chars` truncates oversized output and appends a truncation marker.
- Legacy `timeout` metadata is still accepted as an alias for `timeout_seconds`.

## Custom Python tools

Custom tools subclass `RemoteTool` and return `ToolResult`.

```python
from typing import Any

from ops_copilot import RemoteTool, ToolResult


class ListReleases(RemoteTool):
    name = "list_releases"
    description = "List recent application release markers."

    async def execute(self, **kwargs: Any) -> ToolResult:
        output = await self._run_cmd("ls -1 /var/releases | tail -20")
        return ToolResult(output=output)
```

Inject custom tools into the registry:

```python
registry = ToolRegistry(
    ssh_client,
    tool_classes={"list_releases": ListReleases},
    config_path="tools.yaml",
)
```

## Tool authoring checklist

- Keep commands read-only when possible.
- Prefer narrow parameters over free-form shell fragments.
- Set `timeout_seconds` and `max_output_chars` for commands that can hang or produce large output.
- Keep output concise and useful for diagnosis.
- Return machine-readable evidence when possible.
- Add a test for every new command template or custom tool.
