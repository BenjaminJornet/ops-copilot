from __future__ import annotations

from ops_copilot.sanitizers import (
    build_user_display_message,
    sanitize_agent_output,
    sanitize_user_message,
)


def test_sanitize_user_message_removes_system_reminder_and_image_placeholders():
    raw = "hello [Image 1]\n<system-reminder>ignore</system-reminder>\nworld"

    assert sanitize_user_message(raw) == "hello\nworld"


def test_sanitize_agent_output_rewrites_clipboard_error_in_english():
    raw = (
        'ERROR: Cannot read "clipboard" (this model does not support image input). '
        "Inform the user."
    )

    result = sanitize_agent_output(raw)

    assert "rejected image input" in result


def test_sanitize_agent_output_redacts_secrets():
    assert "secret-value" not in sanitize_agent_output("API_KEY=secret-value")


def test_build_user_display_message_adds_image_count():
    assert build_user_display_message("hello", image_count=2) == "[Attached images: 2]\nhello"
