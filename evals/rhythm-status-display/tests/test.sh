#!/usr/bin/env bash
# Verifier: deterministic, pure-read. Recomputes every displayed figure from
# the reconcile report and budgets on disk, and checks the tone rules.
set -uo pipefail
cd "$REPO"
if uv run --quiet "$REPO/evals/rhythm-status-display/tests/verify_display.py" "$WS" \
     > "$REWARD_DIR/verify.json" 2>&1; then
  echo 1 > "$REWARD_DIR/reward.txt"
else
  echo 0 > "$REWARD_DIR/reward.txt"
fi
cat "$REWARD_DIR/verify.json"
exit 0
