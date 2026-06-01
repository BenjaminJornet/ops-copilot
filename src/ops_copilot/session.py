from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.messages import BaseMessage


@dataclass
class InvestigationSession:
    session_id: str
    history: list[BaseMessage] = field(default_factory=list)


class InMemorySessionStore:
    """Small in-memory session store for server integrations and demos."""

    def __init__(self, *, max_messages: int = 20) -> None:
        self.max_messages = max_messages
        self._sessions: dict[str, InvestigationSession] = {}

    def get_history(self, session_id: str | None) -> list[BaseMessage]:
        if not session_id:
            return []
        return list(self._sessions.get(session_id, InvestigationSession(session_id)).history)

    def append(self, session_id: str | None, messages: list[BaseMessage]) -> None:
        if not session_id or not messages:
            return
        session = self._sessions.setdefault(session_id, InvestigationSession(session_id))
        session.history.extend(messages)
        if len(session.history) > self.max_messages:
            session.history = session.history[-self.max_messages :]

    def list_ids(self) -> list[str]:
        return list(self._sessions.keys())
