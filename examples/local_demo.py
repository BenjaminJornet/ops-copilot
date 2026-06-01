from __future__ import annotations

import asyncio
from pathlib import Path

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from ops_copilot import InvestigationGraph, ToolRegistry


class FakeSSHClient:
    async def run(self, command: str, timeout: int | None = None) -> str:
        if command == "uptime":
            return "12:00 up 10 days, 2 users, load average: 0.42, 0.36, 0.31"
        if command == "df -h":
            return "Filesystem Size Used Avail Use% Mounted on\n/dev/root 50G 18G 32G 36% /"
        if command == "free -m":
            return "Mem: 16000 4200 9800 200 2000 11000"
        if command.startswith("docker ps"):
            return "NAMES STATUS PORTS\napi Up 2 days 0.0.0.0:8000->8000/tcp"
        return f"simulated output for: {command}"


async def main() -> None:
    registry = ToolRegistry(FakeSSHClient(), config_path=Path(__file__).with_name("tools.yaml"))
    tools = registry.load()
    llm = FakeListChatModel(responses=["The fake host looks healthy. Check app logs next."])
    graph = InvestigationGraph(
        llm=llm,
        tools=tools,
        system_prompt="You are an SRE copilot. Report evidence and safe next steps.",
    )

    async for event in graph.stream("The API is slow. Investigate basic host health."):
        print(event)


if __name__ == "__main__":
    asyncio.run(main())
