from __future__ import annotations

from pathlib import Path

import yaml


def load_fixture(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def render_replay(fixture: dict) -> str:
    lines = [
        f"incident={fixture['name']}",
        f"question={fixture['question']!r}",
        "",
        "evidence:",
    ]
    for tool, output in fixture.get("fake_outputs", {}).items():
        lines.append(f"tool={tool}")
        lines.append(str(output).rstrip())
    lines.append("")
    lines.append("expected_evidence:")
    lines.extend(f"- {item}" for item in fixture.get("expected_evidence", []))
    lines.append("")
    lines.append("safe_next_steps:")
    lines.extend(f"- {item}" for item in fixture.get("safe_next_steps", []))
    return "\n".join(lines)
