from __future__ import annotations

from pydantic import BaseModel, Field


class IncidentReport(BaseModel):
    """Structured incident investigation summary."""

    summary: str
    evidence: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    duration: float = 0.0
