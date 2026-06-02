from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ops_copilot.tools.review import format_findings, review_toolpack


def test_review_toolpack_flags_missing_parameter_definition(tmp_path):
    path = tmp_path / "tools.yaml"
    path.write_text(
        """
tools:
  - name: logs
    type: shell
    description: Logs.
    command: journalctl -u {service}
""",
        encoding="utf-8",
    )

    findings = review_toolpack(path)

    assert findings == [
        {
            "level": "error",
            "tool": "logs",
            "message": "template parameter 'service' is not defined",
        }
    ]


def test_review_toolpack_flags_weak_string_parameter(tmp_path):
    path = tmp_path / "tools.yaml"
    path.write_text(
        """
tools:
  - name: logs
    type: shell
    description: Logs.
    command: journalctl -u {service}
    parameters:
      service:
        type: string
""",
        encoding="utf-8",
    )

    findings = review_toolpack(path)

    assert findings[0]["level"] == "warning"
    assert "allowed_values or pattern" in findings[0]["message"]


def test_format_findings_reports_ok_for_clean_toolpack():
    assert format_findings([]) == "toolpack_review status=ok"


def test_replay_incident_script_runs():
    result = subprocess.run(
        ["uv", "run", "python", "examples/replay_incident.py", "examples/incidents/disk-full.yaml"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "incident=disk-full" in result.stdout
    assert "root filesystem at 97 percent" in result.stdout


def test_packaged_cli_reviews_toolpack():
    result = subprocess.run(
        ["uv", "run", "ops-copilot", "review", "examples/toolpacks/systemd.yaml"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "toolpack_review status=ok"


def test_packaged_cli_replays_incident():
    result = subprocess.run(
        ["uv", "run", "ops-copilot", "replay", "examples/incidents/disk-full.yaml"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "incident=disk-full" in result.stdout
    assert "safe_next_steps:" in result.stdout


def test_packaged_cli_replays_bad_env_var_fixture():
    result = subprocess.run(
        ["uv", "run", "ops-copilot", "replay", "examples/incidents/bad-env-var.yaml"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "incident=bad-env-var" in result.stdout
    assert "DATABASE_URL is missing" in result.stdout


def test_orchestrated_demo_runs():
    root = Path(__file__).resolve().parents[2]
    if not (root / "ollama-orchestra").exists():
        pytest.skip("ollama-orchestra repository is not checked out side-by-side")

    result = subprocess.run(
        ["uv", "run", "python", "examples/orchestrated_demo.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Starting Coordinated Local Investigation" in result.stdout
    assert "Orchestrated Events Emitted" in result.stdout
    assert "semaphore_acquired" in result.stdout
    assert "endpoint_score_updated" in result.stdout
