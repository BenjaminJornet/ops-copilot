from __future__ import annotations

import re
from collections.abc import Iterable

__all__ = ["DEFAULT_SECRET_KEY_PATTERNS", "build_secret_key_regex", "redact_secrets"]

DEFAULT_SECRET_KEY_PATTERNS: tuple[str, ...] = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "credential",
)

_ENV_LINE_RE = re.compile(r"^(\s*[A-Z_][A-Z0-9_]*\s*[=:]\s*)(.+)$", re.MULTILINE)
_BEARER_RE = re.compile(r"(Bearer\s+)[^\s\"']+", re.IGNORECASE)
_OPENAI_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{3})[A-Za-z0-9]{10,}")
_JWT_RE = re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}")
_HEX_RUN_RE = re.compile(r"\b[0-9a-fA-F]{32,}\b")
_DATA_URL_RE = re.compile(r"data:image/([a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=]+)")


def build_secret_key_regex(patterns: Iterable[str] | None = None) -> re.Pattern[str]:
    items = list(patterns) if patterns is not None else list(DEFAULT_SECRET_KEY_PATTERNS)
    items = [item.strip() for item in items if item and item.strip()]
    if not items:
        return re.compile(r"(?!x)x")
    return re.compile("|".join(re.escape(item) for item in items), re.IGNORECASE)


def _redact_image_data_urls(text: str) -> str:
    return _DATA_URL_RE.sub(
        lambda match: (
            f"[REDACTED_IMAGE mime=image/{match.group(1)} bytes={len(match.group(2))}]"
        ),
        text,
    )


_DEFAULT_REGEX = build_secret_key_regex(DEFAULT_SECRET_KEY_PATTERNS)


def redact_secrets(text: str) -> str:
    if not text:
        return text

    def _mask_env_line(match: re.Match[str]) -> str:
        prefix = match.group(1)
        if _DEFAULT_REGEX.search(prefix):
            return f"{prefix}[REDACTED]"
        return match.group(0)

    text = _ENV_LINE_RE.sub(_mask_env_line, text)
    text = _BEARER_RE.sub(r"\1[REDACTED]", text)
    text = _OPENAI_KEY_RE.sub(r"\1...[REDACTED]", text)
    text = _JWT_RE.sub("[REDACTED_JWT]", text)
    text = _HEX_RUN_RE.sub("[REDACTED_HEX]", text)
    return _redact_image_data_urls(text)
