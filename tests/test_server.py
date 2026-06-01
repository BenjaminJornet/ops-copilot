from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from ops_copilot.server import create_app


class FakeGraph:
    async def run(self, message: str, *, history=None, images=None):
        assert message == "check host"
        return {
            "messages": [AIMessage(content="host looks healthy")],
            "tools_used": ["uptime"],
            "duration": 0.1,
            "report": FakeReport(),
        }

    async def stream(self, message: str, *, history=None, images=None):
        assert message == "check host"
        yield {"event": "token", "data": "host looks healthy"}
        yield {"event": "done", "data": {}}


class FakeReport:
    def model_dump(self):
        return {
            "summary": "host looks healthy",
            "evidence": [],
            "next_steps": [],
            "tools_used": ["uptime"],
            "duration": 0.1,
        }


def test_investigate_endpoint_returns_result(monkeypatch):
    monkeypatch.delenv("OPS_COPILOT_API_KEY", raising=False)
    app = create_app(lambda: FakeGraph())
    client = TestClient(app)

    response = client.post("/investigate", json={"message": "check host"})

    assert response.status_code == 200
    assert response.json()["messages"] == ["host looks healthy"]
    assert response.json()["tools_used"] == ["uptime"]
    assert response.json()["report"]["summary"] == "host looks healthy"


def test_investigate_endpoint_enforces_api_key(monkeypatch):
    monkeypatch.setenv("OPS_COPILOT_API_KEY", "expected")
    app = create_app(lambda: FakeGraph())
    client = TestClient(app)

    assert client.post("/investigate", json={"message": "check host"}).status_code == 401
    assert (
        client.post(
            "/investigate",
            json={"message": "check host"},
            headers={"X-API-Key": "expected"},
        ).status_code
        == 200
    )


def test_stream_endpoint_emits_sse_events(monkeypatch):
    monkeypatch.delenv("OPS_COPILOT_API_KEY", raising=False)
    app = create_app(lambda: FakeGraph())
    client = TestClient(app)

    with client.stream("POST", "/investigate/stream", json={"message": "check host"}) as response:
        body = response.read().decode()

    assert response.status_code == 200
    assert "event: token" in body
    assert "host looks healthy" in body
    assert "event: done" in body


@pytest.mark.parametrize("payload", [{}, {"message": ""}])
def test_investigate_rejects_invalid_payload(monkeypatch, payload):
    monkeypatch.delenv("OPS_COPILOT_API_KEY", raising=False)
    app = create_app(lambda: FakeGraph())
    client = TestClient(app)

    assert client.post("/investigate", json=payload).status_code == 422
