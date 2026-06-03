from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ops_copilot.cli import main as cli_main
from ops_copilot.replay import load_fixture, render_replay
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


def test_replay_helpers_render_fixture():
    fixture = load_fixture(Path("examples/incidents/disk-full.yaml"))
    output = render_replay(fixture)

    assert "incident=disk-full" in output
    assert "safe_next_steps:" in output


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


def test_packaged_cli_replays_slow_api_fixture():
    result = subprocess.run(
        ["uv", "run", "ops-copilot", "replay", "examples/incidents/slow-api.yaml"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "incident=slow-api" in result.stdout
    assert "search route p95 latency" in result.stdout


def test_cli_main_review_and_replay(capsys):
    assert cli_main(["review", "examples/toolpacks/systemd.yaml"]) == 0
    assert "toolpack_review status=ok" in capsys.readouterr().out

    assert cli_main(["replay", "examples/incidents/disk-full.yaml"]) == 0
    assert "incident=disk-full" in capsys.readouterr().out


def test_cli_main_returns_error_for_bad_toolpack(tmp_path, capsys):
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

    assert cli_main(["review", str(path)]) == 1
    assert "template parameter" in capsys.readouterr().out


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
