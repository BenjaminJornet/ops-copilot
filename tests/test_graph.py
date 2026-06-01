from __future__ import annotations

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.tools import tool

from ops_copilot.graph import InvestigationGraph


@tool
def ping() -> str:
    """Return a ping result."""
    return "pong"


def test_graph_requires_system_prompt():
    with pytest.raises(ValueError):
        InvestigationGraph(FakeListChatModel(responses=["done"]), [], system_prompt="")


@pytest.mark.asyncio
async def test_graph_run_returns_final_message_without_tools():
    graph = InvestigationGraph(
        FakeListChatModel(responses=["done"]),
        [],
        system_prompt="Investigate safely.",
    )

    result = await graph.run("hello")

    assert result["tools_used"] == []
    assert result["messages"][0].content == "done"


@pytest.mark.asyncio
async def test_graph_stream_emits_done():
    graph = InvestigationGraph(
        FakeListChatModel(responses=["done"]),
        [ping],
        system_prompt="Investigate safely.",
    )

    events = [event async for event in graph.stream("hello")]

    assert events[-1] == {"event": "done", "data": {}}
