from __future__ import annotations

import pytest

from ops_copilot.tools.registry import ToolRegistry


class FakeSSH:
    async def run(self, command: str, timeout: int | None = None) -> str:
        return f"ran: {command}"


def test_registry_loads_shell_tools_from_yaml(tmp_path):
    config = tmp_path / "tools.yaml"
    config.write_text(
        """
tools:
  - name: uptime
    type: shell
    description: Show uptime.
    command: uptime
""",
        encoding="utf-8",
    )

    registry = ToolRegistry(FakeSSH(), config_path=config)
    tools = registry.load()

    assert len(tools) == 1
    assert registry.list_names() == ["uptime"]
    assert registry.get_tool("uptime") is tools[0]


def test_registry_ignores_unknown_non_shell_tools(tmp_path):
    config = tmp_path / "tools.yaml"
    config.write_text('tools:\n  - name: unknown\n    description: Unknown\n', encoding="utf-8")

    registry = ToolRegistry(FakeSSH(), config_path=config)

    assert registry.load() == []


@pytest.mark.asyncio
async def test_shell_tool_renders_template_command(tmp_path):
    config = tmp_path / "tools.yaml"
    config.write_text(
        """
tools:
  - name: logs
    type: shell
    description: Logs.
    command: journalctl -u {service} --since '{since}'
    parameters:
      service:
        type: string
      since:
        type: string
        required: false
        default: "1 hour ago"
""",
        encoding="utf-8",
    )
    tool = ToolRegistry(FakeSSH(), config_path=config).load()[0]

    result = await tool._arun(service="api", since="5 minutes ago")

    assert "journalctl -u api --since '5 minutes ago'" in result
