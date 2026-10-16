#!/usr/bin/env bash
# Oracle solution: the exact script the displays (status line, belay-ui mod)
# run. Proves the task is solvable and exercises the shipped view-model.
set -euo pipefail
cd "$REPO"
mkdir -p "$WS/.display"
for day in 2026-07-10 2026-08-02 2026-11-20; do
  uv run --quiet harness/scripts/status.py "$WS" --today "$day" > "$WS/.display/status_$day.json"
  uv run --quiet harness/scripts/status.py "$WS" --today "$day" --line > "$WS/.display/line_$day.txt"
done
cat "$WS/.display/line_"*.txt
