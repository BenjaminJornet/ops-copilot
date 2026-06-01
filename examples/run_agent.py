from __future__ import annotations

import asyncio
import os
from pathlib import Path

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from ops_copilot import InvestigationGraph, SSHClient, ToolRegistry

SYSTEM_PROMPT = """You are an SRE copilot. Investigate production symptoms by using tools.
Summarize evidence, likely causes, and safe next steps. Never expose secrets."""


async def main() -> None:
    ssh = SSHClient(
        host=os.getenv("OPS_COPILOT_SSH_HOST", "localhost"),
        user=os.getenv("OPS_COPILOT_SSH_USER", os.getenv("USER", "root")),
        key_path=os.getenv("OPS_COPILOT_SSH_KEY"),
        password=os.getenv("OPS_COPILOT_SSH_PASSWORD"),
    )
    registry = ToolRegistry(ssh, config_path=Path(__file__).with_name("tools.yaml"))
    tools = registry.load()
    llm = FakeListChatModel(responses=["I would inspect uptime, disk, memory, and recent logs."])
    graph = InvestigationGraph(llm, tools, system_prompt=SYSTEM_PROMPT)

    async for event in graph.stream("The API is slow. Investigate the host."):
        print(event)


if __name__ == "__main__":
    asyncio.run(main())
