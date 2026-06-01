from __future__ import annotations

import asyncio
from pathlib import Path

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from ops_copilot import InvestigationGraph, ToolRegistry


class FakeSSHClient:
    async def run(self, command: str, timeout: int | None = None) -> str:
        return f"ok command={command}"


async def main() -> None:
    registry = ToolRegistry(FakeSSHClient(), config_path=Path("examples/tools.yaml"))
    tools = registry.load()
    graph = InvestigationGraph(
        FakeListChatModel(responses=["done"]),
        tools,
        system_prompt="Investigate safely.",
    )
    result = await graph.run("check host")
    assert result["messages"][0].content == "done"
    print("smoke ok")


if __name__ == "__main__":
    asyncio.run(main())
