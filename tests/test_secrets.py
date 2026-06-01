from __future__ import annotations

from ops_copilot.secrets import build_secret_key_regex, redact_secrets


def test_redacts_env_style_secret_lines():
    text = "APP_NAME=demo\nAPI_KEY=abc123\nPASSWORD: hunter2"
    result = redact_secrets(text)

    assert "abc123" not in result
    assert "hunter2" not in result
    assert "APP_NAME=demo" in result


def test_redacts_bearer_openai_jwt_and_hex_values():
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signaturepart"
    text = (
        "Authorization: Bearer token-value\n"
        "key sk-abc1234567890abcdef\n"
        f"jwt {jwt}\n"
        "hex a3f8b2d1e4c5f6a7b8c9d0e1f2a3b4c5"
    )
    result = redact_secrets(text)

    assert "token-value" not in result
    assert "1234567890abcdef" not in result
    assert "eyJzdWIi" not in result
    assert "a3f8b2d1" not in result


def test_redacts_image_data_url_payload():
    text = "image=data:image/png;base64,abcdef012345 continues"
    result = redact_secrets(text)

    assert "abcdef012345" not in result
    assert "[REDACTED_IMAGE mime=image/png bytes=12]" in result
    assert "continues" in result


def test_empty_secret_patterns_match_nothing():
    regex = build_secret_key_regex([])

    assert regex.search("PASSWORD") is None
