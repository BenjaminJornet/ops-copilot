#!/usr/bin/env bash
set -euo pipefail

printf '\033[1;32m$ uv run ops-copilot replay examples/incidents/disk-full.yaml\033[0m\n'
uv run ops-copilot replay examples/incidents/disk-full.yaml
printf '\n'

printf '\033[1;32m$ uv run ops-copilot review examples/toolpacks/systemd.yaml\033[0m\n'
uv run ops-copilot review examples/toolpacks/systemd.yaml
printf '\n'

printf '\033[1;32m$ uv run python examples/orchestrated_demo.py\033[0m\n'
uv run python examples/orchestrated_demo.py
