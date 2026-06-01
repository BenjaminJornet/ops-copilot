from __future__ import annotations

import re

from ops_copilot.secrets import redact_secrets

_IMAGE_PLACEHOLDER_RE = re.compile(r"\[Image\s+\d+\]", re.IGNORECASE)
_CLIPBOARD_ERROR_RE = re.compile(
    r"ERROR:\s*Cannot read \"clipboard\" "
    r"\(this model does not support image input\)\.?(?:\s*Inform the user\.?)?",
    re.IGNORECASE,
)
_SYSTEM_REMINDER_RE = re.compile(
    r"<system-reminder>.*?</system-reminder>",
    re.IGNORECASE | re.DOTALL,
)


def sanitize_user_message(message: str) -> str:
    cleaned = _SYSTEM_REMINDER_RE.sub(" ", message)
    cleaned = _CLIPBOARD_ERROR_RE.sub(" ", cleaned)
    cleaned = _IMAGE_PLACEHOLDER_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" ?\n ?", "\n", cleaned)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    return "\n".join(lines)


def sanitize_agent_output(text: str) -> str:
    text = redact_secrets(text)
    text = _SYSTEM_REMINDER_RE.sub("", text)
    if _CLIPBOARD_ERROR_RE.search(text):
        return (
            "The configured model rejected image input. Use a vision-capable model "
            "or paste the alert text instead."
        )
    return text


def build_user_display_message(message: str, image_count: int = 0) -> str:
    cleaned = sanitize_user_message(message)
    if image_count <= 0:
        return cleaned
    prefix = f"[Attached images: {image_count}]"
    return f"{prefix}\n{cleaned}" if cleaned else prefix
