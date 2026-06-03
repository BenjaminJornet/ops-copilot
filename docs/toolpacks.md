# Toolpacks

Toolpacks are reviewed YAML files with ready-to-load shell tools.

They are examples, not a default security policy. Review every command before using a toolpack on a real host.

## Available toolpacks

- `examples/toolpacks/linux-host.yaml`: host-level uptime, disk, memory, and process snapshots.
- `examples/toolpacks/systemd.yaml`: systemd status and recent journal logs.
- `examples/toolpacks/docker.yaml`: Docker container list, stats, and logs.
- `examples/toolpacks/nginx.yaml`: nginx config validation and recent access/error logs.

## Loading a toolpack

```python
from ops_copilot import SSHClient, ToolRegistry

ssh = SSHClient(host="server.example.com", user="deploy", key_path="~/.ssh/id_ed25519")
tools = ToolRegistry(ssh, config_path="examples/toolpacks/linux-host.yaml").load()
```

## CI review

Use the CLI to review toolpacks in text or JSON form:

```bash
ops-copilot review examples/toolpacks/nginx.yaml
ops-copilot review examples/toolpacks/nginx.yaml --json
```

## Safety notes

- Prefer read-only commands.
- Prefer `pattern` or `allowed_values` on user-provided parameters.
- Avoid free-form shell fragments.
- Use least-privilege SSH users.
- Keep tool output short enough for LLM context windows.

## Combining toolpacks

`ToolRegistry` loads one YAML file at a time. Applications can instantiate multiple registries and concatenate the returned tools if they want several packs in one graph.
