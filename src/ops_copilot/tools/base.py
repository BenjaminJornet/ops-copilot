from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from ops_copilot.secrets import redact_secrets
from ops_copilot.ssh import SSHClient, SSHError


class ToolResult(BaseModel):
    success: bool = True
    output: str = ""
    error: str | None = None


class RemoteTool(ABC):
    name: str
    description: str

    def __init__(self, ssh_client: SSHClient, *, meta: dict[str, Any] | None = None) -> None:
        self.ssh = ssh_client
        self.meta = meta or {}

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        ...

    async def _run_cmd(self, command: str, timeout: int | None = None) -> str:
        try:
            return redact_secrets(await self.ssh.run(command, timeout=timeout))
        except SSHError as exc:
            return redact_secrets(f"[ERROR] {exc} | stderr: {exc.stderr}")
