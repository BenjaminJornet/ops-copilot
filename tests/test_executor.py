from __future__ import annotations

from typing import Any

import pytest

from ops_copilot.tools.base import RemoteTool, ToolResult
from ops_copilot.tools.executor import LangChainToolWrapper, _build_schema


class DummyTool(RemoteTool):
    name = "dummy"
    description = "Dummy tool"

    async def execute(self, **kwargs: Any) -> ToolResult:
        if kwargs.get("fail"):
            raise RuntimeError("boom")
        return ToolResult(output=str(kwargs))


class FakeSSH:
    async def run(self, command: str, timeout: int | None = None) -> str:
        return command


def test_build_schema_handles_optional_integer():
    tool = DummyTool(FakeSSH())
    schema = _build_schema(
        tool,
        {"parameters": {"count": {"type": "integer", "required": False}}},
    )

    parsed = schema()
    assert parsed.count is None
    assert schema(count=2).count == 2


def test_build_schema_adds_no_input_sentinel_for_zero_param_tool():
    tool = DummyTool(FakeSSH())
    schema = _build_schema(tool, {})

    assert schema().no_input is None


@pytest.mark.asyncio
async def test_wrapper_returns_tool_error_on_exception():
    wrapper = LangChainToolWrapper(
        DummyTool(FakeSSH()),
        {"parameters": {"fail": {"type": "boolean"}}},
    )

    result = await wrapper._arun(fail=True)

    assert result.startswith("[TOOL ERROR] RuntimeError: boom")
