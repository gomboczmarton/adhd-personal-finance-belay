#!/usr/bin/env bash
# Verifier: pure-read recomputation vs ground truth, plus the capability
# clause: every own-account transaction must be classified internal.
set -uo pipefail
cd "$REPO"
fail=0
uv run harness/scripts/validate_workspace.py "$WS" > "$REWARD_DIR/validate.log" 2>&1 || fail=1
uv run evals/lib/ledger_verify.py "$WS" "$MANIFEST" "$MONTH" --own-account-internal \
  > "$REWARD_DIR/verify.json" 2>&1 || fail=1
if [ "$fail" -eq 0 ]; then echo 1 > "$REWARD_DIR/reward.txt"; else echo 0 > "$REWARD_DIR/reward.txt"; fi
cat "$REWARD_DIR/verify.json"
exit 0
