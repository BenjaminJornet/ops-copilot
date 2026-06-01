from __future__ import annotations

from pathlib import Path

import pytest
import yaml

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


@pytest.mark.asyncio
async def test_shell_tool_rejects_control_characters(tmp_path):
    config = tmp_path / "tools.yaml"
    config.write_text(
        """
tools:
  - name: logs
    type: shell
    description: Logs.
    command: journalctl -u {service}
    parameters:
      service:
        type: string
""",
        encoding="utf-8",
    )
    tool = ToolRegistry(FakeSSH(), config_path=config).load()[0]

    result = await tool._arun(service="api\nwhoami")

    assert result.startswith("[TOOL ERROR]")
    assert "forbidden control characters" in result


@pytest.mark.asyncio
async def test_shell_tool_enforces_allowed_values(tmp_path):
    config = tmp_path / "tools.yaml"
    config.write_text(
        """
tools:
  - name: logs
    type: shell
    description: Logs.
    command: journalctl -u {service}
    parameters:
      service:
        type: string
        allowed_values: [api, worker]
""",
        encoding="utf-8",
    )
    tool = ToolRegistry(FakeSSH(), config_path=config).load()[0]

    assert "journalctl -u api" in await tool._arun(service="api")
    result = await tool._arun(service="database")
    assert result.startswith("[TOOL ERROR]")
    assert "allowed values" in result


@pytest.mark.asyncio
async def test_shell_tool_enforces_regex_pattern(tmp_path):
    config = tmp_path / "tools.yaml"
    config.write_text(
        r"""
tools:
  - name: logs
    type: shell
    description: Logs.
    command: journalctl -u {service}
    parameters:
      service:
        type: string
        pattern: "[a-z][a-z0-9_-]{0,31}"
""",
        encoding="utf-8",
    )
    tool = ToolRegistry(FakeSSH(), config_path=config).load()[0]

    assert "journalctl -u api-1" in await tool._arun(service="api-1")
    result = await tool._arun(service="../../etc/passwd")
    assert result.startswith("[TOOL ERROR]")
    assert "required pattern" in result


@pytest.mark.asyncio
async def test_shell_tool_blocks_destructive_commands(tmp_path):
    config = tmp_path / "tools.yaml"
    config.write_text(
        """
tools:
  - name: remove_logs
    type: shell
    description: Unsafe example.
    command: rm -rf /var/log/app
""",
        encoding="utf-8",
    )
    tool = ToolRegistry(FakeSSH(), config_path=config).load()[0]

    result = await tool._arun(no_input="")

    assert result.startswith("[TOOL ERROR]")
    assert "blocked token" in result


@pytest.mark.asyncio
async def test_shell_tool_allows_destructive_commands_only_with_policy_opt_in(tmp_path):
    config = tmp_path / "tools.yaml"
    config.write_text(
        """
tools:
  - name: restart_service
    type: shell
    description: Explicitly reviewed restart.
    command: systemctl restart api.service
    policy:
      allow_destructive: true
""",
        encoding="utf-8",
    )
    tool = ToolRegistry(FakeSSH(), config_path=config).load()[0]

    result = await tool._arun(no_input="")

    assert "systemctl restart api.service" in result


@pytest.mark.asyncio
async def test_shell_tool_dry_run_renders_without_executing(tmp_path):
    config = tmp_path / "tools.yaml"
    config.write_text(
        """
tools:
  - name: docker_ps
    type: shell
    description: Dry-run example.
    command: docker ps --filter name={service}
    dry_run: true
    parameters:
      service:
        type: string
        pattern: "[a-z][a-z0-9_-]{0,31}"
""",
        encoding="utf-8",
    )
    tool = ToolRegistry(FakeSSH(), config_path=config).load()[0]

    result = await tool._arun(service="api")

    assert result == "[DRY RUN] docker ps --filter name=api"


def test_example_toolpacks_load():
    root = Path(__file__).resolve().parents[1]
    for name in ["linux-host.yaml", "systemd.yaml", "docker.yaml"]:
        tools = ToolRegistry(
            FakeSSH(),
            config_path=root / "examples" / "toolpacks" / name,
        ).load()
        assert tools, f"expected {name} to define at least one tool"


def test_incident_fixtures_are_safe_and_structured():
    root = Path(__file__).resolve().parents[1]
    for path in (root / "examples" / "incidents").glob("*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["question"]
        assert data["fake_outputs"]
        assert data["expected_evidence"]
        serialized = path.read_text(encoding="utf-8").lower()
        assert "100.64" not in serialized
        assert "api_key=" not in serialized


@pytest.mark.asyncio
async def test_systemd_toolpack_rejects_unsafe_service_name():
    root = Path(__file__).resolve().parents[1]
    tools = ToolRegistry(
        FakeSSH(),
        config_path=root / "examples" / "toolpacks" / "systemd.yaml",
    ).load()
    status_tool = next(tool for tool in tools if tool.name == "systemd_status")

    result = await status_tool._arun(service="../../etc/passwd")

    assert result.startswith("[TOOL ERROR]")
