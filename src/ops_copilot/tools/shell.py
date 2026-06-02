from __future__ import annotations

import re
import string
from typing import Any

from ops_copilot.tools.base import RemoteTool, ToolResult
from ops_copilot.tools.policy import CommandPolicy


class ShellTool(RemoteTool):
    name = "shell"
    description = "Run a configured shell command over SSH."

    def __init__(self, ssh_client, *, meta: dict[str, Any] | None = None) -> None:
        super().__init__(ssh_client, meta=meta)
        self.name = self.meta.get("name", self.name)
        self.description = self.meta.get("description", self.description)
        self.command = self.meta.get("command", "")
        self.timeout = self._positive_int_meta("timeout_seconds", fallback_key="timeout")
        self.max_output_chars = self._positive_int_meta("max_output_chars")
        self.dry_run = bool(self.meta.get("dry_run", False))
        self.policy = CommandPolicy.from_meta(self.meta)
        if not self.command:
            raise ValueError("ShellTool requires a command in tool metadata")

    async def execute(self, **kwargs: Any) -> ToolResult:
        try:
            self._validate_parameters(kwargs)
            command = self._render_command(kwargs)
            self.policy.validate(command)
            if self.dry_run:
                return ToolResult(output=f"[DRY RUN] {command}")
            output = await self._run_cmd(command, timeout=self.timeout)
            if output.startswith("[ERROR]"):
                return ToolResult(success=False, error=output)
            return ToolResult(output=self._limit_output(output))
        except KeyError as exc:
            return ToolResult(success=False, error=f"Missing command parameter: {exc.args[0]}")
        except ValueError as exc:
            return ToolResult(success=False, error=str(exc))

    def _validate_parameters(self, values: dict[str, Any]) -> None:
        definitions = self.meta.get("parameters", {})
        for name, value in values.items():
            if value is None or name == "no_input":
                continue
            text = str(value)
            if "\x00" in text or "\n" in text or "\r" in text:
                raise ValueError(f"Parameter {name!r} contains forbidden control characters")

            definition = definitions.get(name, {})
            allowed_values = definition.get("allowed_values")
            if (
                allowed_values is not None
                and value not in allowed_values
                and text not in allowed_values
            ):
                raise ValueError(f"Parameter {name!r} is not in the allowed values list")

            pattern = definition.get("pattern")
            if pattern and re.fullmatch(str(pattern), text) is None:
                raise ValueError(f"Parameter {name!r} does not match the required pattern")

            if allowed_values is None and not pattern:
                # Secure by default: restrict unvalidated string parameters
                safe_pattern = r"^[a-zA-Z0-9_\-\.\/\s\:\@\=\+]*$"
                if re.fullmatch(safe_pattern, text) is None:
                    raise ValueError(
                        f"Parameter {name!r} contains forbidden shell characters. "
                        "Define an explicit 'pattern' in YAML to override this safety constraint."
                    )

    def _render_command(self, values: dict[str, Any]) -> str:
        formatter = string.Formatter()
        names = [field_name for _, field_name, _, _ in formatter.parse(self.command) if field_name]
        missing = [name for name in names if name not in values or values[name] is None]
        if missing:
            raise KeyError(missing[0])
        return self.command.format(**values)

    def _limit_output(self, output: str) -> str:
        if self.max_output_chars is None or len(output) <= self.max_output_chars:
            return output
        omitted = len(output) - self.max_output_chars
        return output[: self.max_output_chars] + f"\n\n[...truncated {omitted} chars]"

    def _positive_int_meta(
        self,
        key: str,
        *,
        fallback_key: str | None = None,
    ) -> int | None:
        value = self.meta.get(key)
        if value is None and fallback_key:
            value = self.meta.get(fallback_key)
        if value is None:
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be a positive integer") from exc
        if parsed <= 0:
            raise ValueError(f"{key} must be a positive integer")
        return parsed
