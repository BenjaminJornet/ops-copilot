from __future__ import annotations

import json

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.tools import tool

from ops_copilot import JsonlAuditLog
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


@pytest.mark.asyncio
async def test_graph_run_writes_redacted_audit_log(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    graph = InvestigationGraph(
        FakeListChatModel(responses=["API_KEY=secret"]),
        [],
        system_prompt="Investigate safely.",
        audit_log=JsonlAuditLog(log_path),
    )

    await graph.run("API_KEY=secret")

    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert [record["event"] for record in records] == [
        "investigation_started",
        "investigation_completed",
    ]
    assert "secret" not in log_path.read_text(encoding="utf-8")
