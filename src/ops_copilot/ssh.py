from __future__ import annotations

import asyncio
import os

import asyncssh


class SSHError(Exception):
    def __init__(self, message: str, exit_code: int | None = None, stderr: str = "") -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr


class SSHClient:
    def __init__(
        self,
        host: str,
        user: str,
        *,
        port: int = 22,
        key_path: str | None = None,
        password: str | None = None,
        known_hosts: str | None = None,
        connect_timeout: int = 10,
        command_timeout: int = 30,
    ) -> None:
        self.host = host
        self.user = user
        self.port = port
        self.key_path = key_path
        self.password = password
        self.known_hosts = known_hosts
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout
        self._conn: asyncssh.SSHClientConnection | None = None
        self._lock = asyncio.Lock()

    async def _get_connection(self) -> asyncssh.SSHClientConnection:
        async with self._lock:
            if self._conn is not None:
                return self._conn
            connect_kwargs: dict = {}
            if self.key_path and os.path.exists(self.key_path):
                connect_kwargs["client_keys"] = [self.key_path]
            elif self.password:
                connect_kwargs = {"password": self.password, "client_keys": []}
            else:
                raise SSHError("No SSH credentials configured: provide key_path or password")

            known_hosts = (
                self.known_hosts
                if self.known_hosts and os.path.exists(self.known_hosts)
                else None
            )
            self._conn = await asyncssh.connect(
                host=self.host,
                port=self.port,
                username=self.user,
                known_hosts=known_hosts,
                connect_timeout=self.connect_timeout,
                **connect_kwargs,
            )
            return self._conn

    async def run(self, command: str, timeout: int | None = None) -> str:
        effective_timeout = timeout or self.command_timeout
        for attempt in range(2):
            conn = await self._get_connection()
            try:
                result = await asyncio.wait_for(
                    conn.run(command, check=False), timeout=effective_timeout
                )
                if result.exit_status != 0:
                    raise SSHError("Command failed", result.exit_status, str(result.stderr or ""))
                return str(result.stdout or "")
            except TimeoutError as exc:
                raise SSHError(f"Command timeout after {effective_timeout}s", -1) from exc
            except asyncssh.Error as exc:
                async with self._lock:
                    self._conn = None
                if attempt == 1:
                    raise SSHError(f"SSH connection failed: {exc}") from exc
        raise SSHError("SSH connection failed after retry")

    async def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
