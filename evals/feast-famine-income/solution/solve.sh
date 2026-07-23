#!/usr/bin/env bash
# Oracle solution: the deterministic pipeline the conversational skills
# orchestrate (reconcile-month skill, steps 1-3). Proves the task is solvable
# and exercises the exact scripts the agent must use.
set -euo pipefail
cd "$REPO"
for f in "$WS"/inbox/*.*; do
  base="$(basename "$f")"
  acct="${base%%_*}"
  uv run harness/scripts/ingest.py "$WS" "$acct" "$f"
done
uv run harness/scripts/match_transfers.py "$WS"
uv run harness/scripts/reconcile.py "$WS" --month "$MONTH" > "$ARTIFACTS/reconcile.json"
cat "$ARTIFACTS/reconcile.json"
