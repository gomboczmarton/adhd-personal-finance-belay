#!/usr/bin/env bash
# Verifier: workspace validity + exact totals (unchanged by the re-import)
# + observed re-import idempotence from the run artifact.
set -uo pipefail
cd "$REPO"
fail=0
uv run harness/scripts/validate_workspace.py "$WS" > "$REWARD_DIR/validate.log" 2>&1 || fail=1
uv run evals/lib/ledger_verify.py "$WS" "$MANIFEST" "$MONTH" \
  > "$REWARD_DIR/verify.json" 2>&1 || fail=1
python3 "$REPO/evals/reimport-dedup/tests/test.py" "$ARTIFACTS" \
  > "$REWARD_DIR/dedup.json" 2>&1 || fail=1
if [ "$fail" -eq 0 ]; then echo 1 > "$REWARD_DIR/reward.txt"; else echo 0 > "$REWARD_DIR/reward.txt"; fi
cat "$REWARD_DIR/verify.json" "$REWARD_DIR/dedup.json"
exit 0
