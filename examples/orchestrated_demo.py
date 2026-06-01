# ruff: noqa: E402
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from typing import Any

# Support local imports when packages are checked out side-by-side
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "ollama-orchestra" / "src"))
sys.path.insert(0, str(ROOT_DIR / "langchain-content-normalizer" / "src"))

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from lc_content_normalizer import extract_text_content
from ollama_orchestra import OllamaSemaphorePool, OrchestratedChat

from ops_copilot import InvestigationGraph, ToolRegistry


class FakeSSHClient:
    async def run(self, command: str, timeout: int | None = None) -> str:
        if command == "uptime":
            return "12:00 up 10 days, 2 users, load average: 4.85, 4.12, 3.82"
        if command.startswith("ps aux"):
            return "USER       PID %CPU %MEM COMMAND\napp        481 94.2  8.2 python worker.py"
        return f"simulated output: {command}"


class MockOrchestratedChat(OrchestratedChat):
    """Orchestrated chat mock that skips HTTP calls but preserves pool concurrency/scoring."""

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        think: bool = False,
        strip: bool = True,
        **opts: Any,
    ) -> dict[str, Any] | None:
        url = self._ranked_urls()[0]
        start = time.monotonic()

        # Simulate semaphore acquisition and processing latency
        async with self.pool.semaphore(url):
            await asyncio.sleep(0.1)
            latency = time.monotonic() - start
            self._record_endpoint_success(url, latency)
            self._emit_metric({"event": "chat_success", "url": url})

            # Return a simple mock chain of reasoning based on inputs
            last_prompt = messages[-1]["content"] if messages else ""
            if "worker.py" in last_prompt or "ps aux" in last_prompt:
                reply = (
                    "The high CPU is caused by 'python worker.py' (PID 481) "
                    "consuming 94.2% CPU."
                )
            else:
                reply = "Let me check the system uptime and running processes."

            return {"message": {"role": "assistant", "content": reply}}


class OrchestratedLangChainChat(BaseChatModel):
    orchestrator: Any

    @property
    def _llm_type(self) -> str:
        return "orchestrated-ollama"

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        ollama_messages = []
        for msg in messages:
            role = "user"
            if msg.type == "ai":
                role = "assistant"
            elif msg.type == "system":
                role = "system"
            ollama_messages.append({"role": role, "content": extract_text_content(msg.content)})

        response = await self.orchestrator.chat(ollama_messages, think=False)
        content = response["message"]["content"] if response else "Done."
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    def _generate(self, *args, **kwargs):
        raise NotImplementedError("This chat model only supports async generation")


async def main() -> None:
    # 1. Coordinate two simulated local GPU endpoints using ollama-orchestra
    events = []
    pool = OllamaSemaphorePool(local_limit=1, metrics_cb=events.append)
    orchestrator = MockOrchestratedChat(
        model="reasoning-model",
        urls=["http://localhost:11434", "http://gpu-b.local:11434"],
        pool=pool,
        metrics_cb=events.append,
    )

    # 2. Load the ops-copilot reviewed toolpack config
    ssh = FakeSSHClient()
    registry = ToolRegistry(ssh, config_path=Path(__file__).parent / "tools.yaml")
    tools = registry.load()

    # 3. Wrap the orchestrator into a LangChain chat model
    llm = OrchestratedLangChainChat(orchestrator=orchestrator)

    # 4. Compile the LangGraph SRE investigation loop
    graph = InvestigationGraph(
        llm=llm,
        tools=tools,
        system_prompt="You are an SRE copilot. Cite evidence and safe next steps.",
    )

    print("==> Starting Coordinated Local Investigation...")
    print("Question: Why is the host slow?")
    print("")

    # 5. Stream the investigation
    async for event in graph.stream("Why is the host slow?"):
        if event["event"] == "token":
            print(event["data"], end="", flush=True)
        elif event["event"] == "tool_start":
            print(f"\n[TOOL START] running {event['data']['tool']} on remote host...")
        elif event["event"] == "tool_end":
            print(f"[TOOL END] output: {event['data']['output'].strip()}")

    print("\n")
    print("==> Orchestrated Events Emitted:")
    for event in events:
        print(f"  event={event['event']} url={event.get('url')} score={event.get('score')}")


if __name__ == "__main__":
    asyncio.run(main())
