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
- Keep output concise and useful for diagnosis.
- Return machine-readable evidence when possible.
- Add a test for every new command template or custom tool.
