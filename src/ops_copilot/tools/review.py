from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from ops_copilot.tools.policy import CommandPolicy


def review_toolpack(path: str | Path) -> list[dict[str, str]]:
    config_path = Path(path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    findings: list[dict[str, str]] = []
    for tool in _iter_tools(config):
        name = str(tool.get("name", "unknown"))
        command = str(tool.get("command", ""))
        if not command:
            continue
        try:
            CommandPolicy.from_meta(tool).validate(command)
        except ValueError as exc:
            findings.append({"level": "error", "tool": name, "message": str(exc)})

        policy = tool.get("policy") or {}
        if policy.get("allow_destructive"):
            findings.append(
                {
                    "level": "warning",
                    "tool": name,
                    "message": "destructive command policy is explicitly allowed",
                }
            )

        parameters = tool.get("parameters") or {}
        for field_name in _template_fields(command):
            definition = parameters.get(field_name)
            if definition is None:
                findings.append(
                    {
                        "level": "error",
                        "tool": name,
                        "message": f"template parameter {field_name!r} is not defined",
                    }
                )
                continue
            if definition.get("type") == "string" and not (
                definition.get("allowed_values") or definition.get("pattern")
            ):
                findings.append(
                    {
                        "level": "warning",
                        "tool": name,
                        "message": (
                            f"string parameter {field_name!r} has no allowed_values or pattern"
                        ),
                    }
                )
    return findings


def format_findings(findings: list[dict[str, str]]) -> str:
    if not findings:
        return "toolpack_review status=ok"
    return "\n".join(
        f"toolpack_review level={item['level']} tool={item['tool']} msg={item['message']!r}"
        for item in findings
    )


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("Usage: python -m ops_copilot.tools.review path/to/toolpack.yaml")
        return 2
    findings = review_toolpack(args[0])
    print(format_findings(findings))
    return 1 if any(item["level"] == "error" for item in findings) else 0


def _iter_tools(config: dict[str, Any]) -> list[dict[str, Any]]:
    if "tools" in config:
        return list(config.get("tools") or [])
    tools: list[dict[str, Any]] = []
    for category in (config.get("categories") or {}).values():
        tools.extend(category.get("tools") or [])
    return tools


def _template_fields(command: str) -> list[str]:
    import string

    return [field_name for _, field_name, _, _ in string.Formatter().parse(command) if field_name]


if __name__ == "__main__":
    raise SystemExit(main())
