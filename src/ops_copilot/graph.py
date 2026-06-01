from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator, Callable, Sequence
from typing import Annotated, Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from lc_content_normalizer import (
    build_human_message_content,
    extract_text_content,
    normalize_tool_output,
)
from typing_extensions import TypedDict

from ops_copilot.report import IncidentReport
from ops_copilot.sanitizers import sanitize_agent_output

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    tools_used: list[str]
    iteration: int


class InvestigationGraph:
    """Two-node LangGraph investigation loop: agent -> tools -> agent."""

    def __init__(
        self,
        llm: BaseChatModel,
        tools: list,
        *,
        system_prompt: str,
        vision_format: str = "openai",
        sanitize_output: Callable[[str], str] = sanitize_agent_output,
        audit_log: Any | None = None,
    ) -> None:
        if not system_prompt:
            raise ValueError("system_prompt is required")
        self._system_prompt = system_prompt
        self._vision_format = vision_format
        self._sanitize_output = sanitize_output
        self._audit_log = audit_log
        self._tool_node = ToolNode(tools, handle_tool_errors=True)
        try:
            self._llm_with_tools = llm.bind_tools(tools) if tools else llm
        except NotImplementedError:
            self._llm_with_tools = llm
        self._graph = self._build_graph()

    @property
    def vision_format(self) -> str:
        return self._vision_format

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("agent", self._agent_node)
        graph.add_node("tools", self._tool_node_wrapper)
        graph.set_entry_point("agent")
        graph.add_conditional_edges("agent", self._should_continue, {"tools": "tools", "end": END})
        graph.add_edge("tools", "agent")
        return graph.compile()

    async def _agent_node(self, state: AgentState) -> dict[str, Any]:
        iteration = state.get("iteration", 0) + 1
        response = await self._llm_with_tools.ainvoke(list(state["messages"]))
        logger.debug(
            "agent_iteration iteration=%d tool_calls=%d",
            iteration,
            len(response.tool_calls),
        )
        return {"messages": [response], "iteration": iteration}

    async def _tool_node_wrapper(self, state: AgentState) -> dict[str, Any]:
        result = await self._tool_node.ainvoke(state)
        tools_used = list(state.get("tools_used", []))
        for message in result.get("messages", []):
            if isinstance(message, ToolMessage):
                if message.name and message.name not in tools_used:
                    tools_used.append(message.name)
                content = extract_text_content(message.content)
                if content.startswith("[TOOL ERROR]"):
                    logger.warning("tool_error name=%s output=%s", message.name, content[:300])
                message.content = self._sanitize_output(content)
        return {**result, "tools_used": tools_used}

    def _should_continue(self, state: AgentState) -> str:
        last = state["messages"][-1]
        return "tools" if isinstance(last, AIMessage) and last.tool_calls else "end"

    async def run(
        self,
        user_message: str,
        *,
        history: list[BaseMessage] | None = None,
        images: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        messages = self._build_messages(user_message, history=history, images=images)
        start = time.monotonic()
        self._audit("investigation_started", {"message": user_message, "images": len(images or [])})
        final_state = await self._graph.ainvoke(
            {"messages": messages, "tools_used": [], "iteration": 0}
        )
        duration = time.monotonic() - start
        new_messages = list(final_state["messages"])[len(messages) :]
        for message in new_messages:
            if isinstance(message, AIMessage) and message.content:
                message.content = self._sanitize_output(extract_text_content(message.content))
        result = {
            "messages": new_messages,
            "tools_used": final_state.get("tools_used", []),
            "duration": duration,
        }
        result["report"] = self._build_report(result)
        self._audit(
            "investigation_completed",
            {"tools_used": result["tools_used"], "duration": result["duration"]},
        )
        return result

    def _build_report(self, result: dict[str, Any]) -> IncidentReport:
        text_messages = [
            self._sanitize_output(extract_text_content(getattr(message, "content", "")))
            for message in result.get("messages", [])
            if extract_text_content(getattr(message, "content", ""))
        ]
        summary = text_messages[-1] if text_messages else "Investigation completed."
        evidence = [message for message in text_messages if message != summary]
        return IncidentReport(
            summary=summary,
            evidence=evidence,
            next_steps=[],
            tools_used=list(result.get("tools_used", [])),
            duration=float(result.get("duration", 0.0)),
        )

    async def stream(
        self,
        user_message: str,
        *,
        history: list[BaseMessage] | None = None,
        images: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        messages = self._build_messages(user_message, history=history, images=images)
        try:
            async for event in self._graph.astream_events(
                {"messages": messages, "tools_used": [], "iteration": 0},
                version="v2",
            ):
                event_name = event["event"]
                if event_name == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    text = extract_text_content(getattr(chunk, "content", None)) if chunk else ""
                    if text:
                        yield {"event": "token", "data": self._sanitize_output(text)}
                elif event_name == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    call_id = event.get("run_id") or event.get("data", {}).get("id") or ""
                    step_id = (
                        f"{tool_name}:{call_id}"
                        if call_id
                        else f"{tool_name}:{time.monotonic_ns()}"
                    )
                    yield {
                        "event": "tool_start",
                        "data": {
                            "tool": tool_name,
                            "input": event.get("data", {}).get("input", {}),
                            "call_id": str(call_id),
                            "step_id": step_id,
                        },
                    }
                    self._audit(
                        "tool_start",
                        {"tool": tool_name, "input": event.get("data", {}).get("input", {})},
                    )
                elif event_name == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    call_id = event.get("run_id") or event.get("data", {}).get("id") or ""
                    step_id = f"{tool_name}:{call_id}" if call_id else ""
                    output = self._sanitize_output(
                        normalize_tool_output(event.get("data", {}).get("output", ""))
                    )
                    yield {
                        "event": "tool_end",
                        "data": {
                            "tool": tool_name,
                            "output": output,
                            "call_id": str(call_id),
                            "step_id": step_id,
                        },
                    }
                    self._audit("tool_end", {"tool": tool_name, "output": output})
        except Exception as exc:
            logger.error("stream_investigation_failed", exc_info=True)
            self._audit("error", {"error": str(exc)})
            yield {"event": "error", "data": {"error": str(exc)}}
            return
        self._audit("done", {})
        yield {"event": "done", "data": {}}

    def _build_messages(
        self,
        user_message: str,
        *,
        history: list[BaseMessage] | None = None,
        images: list[dict[str, str]] | None = None,
    ) -> list[BaseMessage]:
        messages: list[BaseMessage] = [SystemMessage(content=self._system_prompt)]
        if history:
            messages.extend(history)
        messages.append(
            HumanMessage(
                content=build_human_message_content(user_message, images, self._vision_format)
            )
        )
        return messages

    def _audit(self, event: str, data: dict[str, Any]) -> None:
        if not self._audit_log:
            return
        try:
            self._audit_log.record(event, data)
        except Exception:
            logger.exception("audit_log_record_failed")
