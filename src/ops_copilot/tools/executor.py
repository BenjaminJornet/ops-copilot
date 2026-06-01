from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr, create_model

from ops_copilot.tools.base import RemoteTool

logger = logging.getLogger(__name__)

_TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}


def _build_schema(tool: RemoteTool, tool_meta: dict[str, Any]) -> type[BaseModel]:
    fields: dict[str, Any] = {}
    for name, definition in tool_meta.get("parameters", {}).items():
        ptype = _TYPE_MAP.get(definition.get("type", "string"), str)
        default = definition.get("default", ...)
        description = definition.get("description")
        if default is ... and not definition.get("required", True):
            fields[name] = (ptype | None, Field(default=None, description=description))
        elif default is ...:
            fields[name] = (ptype, Field(description=description))
        else:
            fields[name] = (ptype, Field(default=default, description=description))
    if not fields:
        fields["no_input"] = (str | None, Field(default=None))
    return create_model(f"{tool.name}_Input", **fields)


class LangChainToolWrapper(BaseTool):
    name: str = ""
    description: str = ""
    args_schema: Any = None
    _remote_tool: RemoteTool = PrivateAttr()

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, remote_tool: RemoteTool, tool_meta: dict[str, Any]):
        super().__init__(
            name=remote_tool.name,
            description=remote_tool.description,
            args_schema=_build_schema(remote_tool, tool_meta),
        )
        self._remote_tool = remote_tool

    def _run(self, **kwargs: Any) -> str:
        raise NotImplementedError

    async def _arun(self, **kwargs: Any) -> str:
        kwargs.pop("no_input", None)
        try:
            result = await self._remote_tool.execute(**kwargs)
        except Exception as exc:
            logger.error("tool_execute_exception name=%s", self.name, exc_info=True)
            return f"[TOOL ERROR] {type(exc).__name__}: {exc}"
        if not result.success:
            logger.warning("tool_failed name=%s error=%s", self.name, result.error)
            return f"[TOOL ERROR] {result.error}"
        return result.output
