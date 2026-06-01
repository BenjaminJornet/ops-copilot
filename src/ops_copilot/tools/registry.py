from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from ops_copilot.ssh import SSHClient
from ops_copilot.tools.base import RemoteTool
from ops_copilot.tools.executor import LangChainToolWrapper
from ops_copilot.tools.shell import ShellTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(
        self,
        ssh_client: SSHClient,
        tool_classes: dict[str, type[RemoteTool]] | None = None,
        config_path: str | Path = "tools.yaml",
    ) -> None:
        self._ssh = ssh_client
        self._tool_classes = tool_classes or {}
        self._config_path = Path(config_path)
        self._tools: dict[str, LangChainToolWrapper] = {}
        self._meta: dict[str, dict[str, Any]] = {}

    def load(self) -> list[LangChainToolWrapper]:
        with self._config_path.open(encoding="utf-8") as fh:
            config = yaml.safe_load(fh) or {}

        loaded: list[LangChainToolWrapper] = []
        for definition in self._iter_tool_definitions(config):
            name = definition["name"]
            tool_cls = self._resolve_tool_class(definition)
            if tool_cls is None:
                logger.warning("tool_unknown name=%s", name)
                continue
            instance = tool_cls(ssh_client=self._ssh, meta=definition)
            instance.name = name
            instance.description = definition.get("description", instance.description)
            wrapper = LangChainToolWrapper(remote_tool=instance, tool_meta=definition)
            self._tools[name] = wrapper
            self._meta[name] = definition
            loaded.append(wrapper)
        return loaded

    def get_tool(self, name: str) -> LangChainToolWrapper | None:
        return self._tools.get(name)

    def get_all_meta(self) -> dict[str, dict[str, Any]]:
        return dict(self._meta)

    def list_names(self) -> list[str]:
        return list(self._tools.keys())

    def _resolve_tool_class(self, definition: dict[str, Any]) -> type[RemoteTool] | None:
        if definition.get("type") == "shell" or "command" in definition:
            return ShellTool
        return self._tool_classes.get(definition["name"])

    @staticmethod
    def _iter_tool_definitions(config: dict[str, Any]) -> list[dict[str, Any]]:
        if "tools" in config:
            return list(config.get("tools") or [])
        definitions: list[dict[str, Any]] = []
        for category in (config.get("categories") or {}).values():
            definitions.extend(category.get("tools") or [])
        return definitions
