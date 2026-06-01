from __future__ import annotations

import string
from typing import Any

from ops_copilot.tools.base import RemoteTool, ToolResult


class ShellTool(RemoteTool):
    name = "shell"
    description = "Run a configured shell command over SSH."

    def __init__(self, ssh_client, *, meta: dict[str, Any] | None = None) -> None:
        super().__init__(ssh_client, meta=meta)
        self.name = self.meta.get("name", self.name)
        self.description = self.meta.get("description", self.description)
        self.command = self.meta.get("command", "")
        self.timeout = self.meta.get("timeout")
        if not self.command:
            raise ValueError("ShellTool requires a command in tool metadata")

    async def execute(self, **kwargs: Any) -> ToolResult:
        try:
            command = self._render_command(kwargs)
            output = await self._run_cmd(command, timeout=self.timeout)
            if output.startswith("[ERROR]"):
                return ToolResult(success=False, error=output)
            return ToolResult(output=output)
        except KeyError as exc:
            return ToolResult(success=False, error=f"Missing command parameter: {exc.args[0]}")

    def _render_command(self, values: dict[str, Any]) -> str:
        formatter = string.Formatter()
        names = [field_name for _, field_name, _, _ in formatter.parse(self.command) if field_name]
        missing = [name for name in names if name not in values or values[name] is None]
        if missing:
            raise KeyError(missing[0])
        return self.command.format(**values)
