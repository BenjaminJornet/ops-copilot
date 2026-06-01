from __future__ import annotations

import json
import os
from collections.abc import AsyncGenerator, Callable
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ops_copilot.graph import InvestigationGraph


class ImageInput(BaseModel):
    data_url: str
    mime_type: str
    name: str | None = None


class InvestigateRequest(BaseModel):
    message: str = Field(min_length=1)
    images: list[ImageInput] = Field(default_factory=list)


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("OPS_COPILOT_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


def create_app(graph_factory: Callable[[], InvestigationGraph]) -> FastAPI:
    app = FastAPI(title="ops-copilot", version="0.1.0")

    @app.post("/investigate", dependencies=[Depends(verify_api_key)])
    async def investigate(request: InvestigateRequest) -> dict[str, Any]:
        graph = graph_factory()
        images = [image.model_dump() for image in request.images]
        result = await graph.run(request.message, images=images)
        return {
            "messages": [
                getattr(message, "content", str(message)) for message in result["messages"]
            ],
            "tools_used": result["tools_used"],
            "duration": result["duration"],
        }

    @app.post("/investigate/stream", dependencies=[Depends(verify_api_key)])
    async def investigate_stream(request: InvestigateRequest) -> EventSourceResponse:
        graph = graph_factory()
        images = [image.model_dump() for image in request.images]

        async def event_generator() -> AsyncGenerator[dict[str, str], None]:
            async for event in graph.stream(request.message, images=images):
                data = (
                    event["data"] if isinstance(event["data"], str) else json.dumps(event["data"])
                )
                yield {"event": event["event"], "data": data}

        return EventSourceResponse(event_generator())

    return app
