from __future__ import annotations

import shlex
from dataclasses import dataclass

DEFAULT_DANGEROUS_TOKENS = frozenset(
    {
        "dd",
        "mkfs",
        "mount",
        "reboot",
        "shutdown",
        "poweroff",
        "halt",
        "init",
        "rm",
    }
)

DEFAULT_DANGEROUS_PATTERNS = (
    ("docker", "rm"),
    ("docker", "rmi"),
    ("docker", "prune"),
    ("docker", "system", "prune"),
    ("systemctl", "restart"),
    ("systemctl", "stop"),
    ("systemctl", "disable"),
)


@dataclass(frozen=True)
class CommandPolicy:
    """Conservative command policy for reviewed YAML shell tools."""

    allow_destructive: bool = False
    dangerous_tokens: frozenset[str] = DEFAULT_DANGEROUS_TOKENS
    dangerous_patterns: tuple[tuple[str, ...], ...] = DEFAULT_DANGEROUS_PATTERNS

    @classmethod
    def from_meta(cls, meta: dict) -> CommandPolicy:
        policy = meta.get("policy") or {}
        return cls(allow_destructive=bool(policy.get("allow_destructive", False)))

    def validate(self, command: str) -> None:
        if self.allow_destructive:
            return
        try:
            tokens = shlex.split(command)
        except ValueError as exc:
            raise ValueError(f"Command cannot be parsed safely: {exc}") from exc

        lowered = [token.lower() for token in tokens]
        for token in lowered:
            base = token.rsplit("/", 1)[-1]
            if base in self.dangerous_tokens:
                raise ValueError(f"Command contains blocked token: {base}")

        for pattern in self.dangerous_patterns:
            if _contains_sequence(lowered, pattern):
                raise ValueError(f"Command matches blocked pattern: {' '.join(pattern)}")


def _contains_sequence(tokens: list[str], pattern: tuple[str, ...]) -> bool:
    if len(pattern) > len(tokens):
        return False
    for start in range(0, len(tokens) - len(pattern) + 1):
        window = tokens[start : start + len(pattern)]
        if all(
            token.rsplit("/", 1)[-1] == expected
            for token, expected in zip(window, pattern, strict=True)
        ):
            return True
    return False
