from __future__ import annotations

import argparse
from pathlib import Path

from ops_copilot.replay import load_fixture, render_replay


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay a fake incident fixture.")
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    print(render_replay(load_fixture(args.fixture)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
