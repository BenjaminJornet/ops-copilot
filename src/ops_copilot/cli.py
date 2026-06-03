from __future__ import annotations

import argparse
import json
from pathlib import Path

from ops_copilot.tools.review import format_findings, review_toolpack


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ops-copilot", description="ops-copilot utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    review_parser = subparsers.add_parser("review", help="review a YAML toolpack")
    review_parser.add_argument("toolpack", type=Path)
    review_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    replay_parser = subparsers.add_parser("replay", help="replay a fake incident fixture")
    replay_parser.add_argument("fixture", type=Path)

    args = parser.parse_args(argv)
    if args.command == "review":
        findings = review_toolpack(args.toolpack)
        if args.json:
            status = "error" if any(item["level"] == "error" for item in findings) else "ok"
            print(json.dumps({"status": status, "findings": findings}, sort_keys=True))
        else:
            print(format_findings(findings))
        return 1 if any(item["level"] == "error" for item in findings) else 0
    if args.command == "replay":
        from ops_copilot.replay import load_fixture, render_replay

        print(render_replay(load_fixture(args.fixture)))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
