from __future__ import annotations

from typing import Any

from ops_copilot import RemoteTool, ToolResult


class ListRecentDeploys(RemoteTool):
    name = "list_recent_deploys"
    description = "List recent deployment markers from a host."

    async def execute(self, **kwargs: Any) -> ToolResult:
        output = await self._run_cmd("ls -1 /var/deploys 2>/dev/null | tail -20")
        if output.startswith("[ERROR]"):
            return ToolResult(success=False, error=output)
        return ToolResult(output=output or "No deploy markers found.")


CUSTOM_TOOL_CLASSES = {"list_recent_deploys": ListRecentDeploys}
