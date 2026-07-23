#!/usr/bin/env bash
# Verifier: LLM judge over the target reply against tests/rubric.md.
# REPLY_FILE must point at the reply to grade (the agent's welcome-back
# message). Exit semantics from evals/lib/judge.py: 0 pass, 1 fail,
# 3 infrastructure (judge unavailable / invalid output — never reward 0).
set -uo pipefail
cd "$REPO"
if [ -z "${REPLY_FILE:-}" ] || [ ! -f "${REPLY_FILE:-}" ]; then
  echo "judge task: set REPLY_FILE to the reply to grade" >&2
  exit 3
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$REPO/evals/lib/judge.py" "$(dirname "$script_dir")" "$REPLY_FILE" \
  > "$REWARD_DIR/judge.json" 2>&1
rc=$?
if [ "$rc" -eq 3 ]; then cat "$REWARD_DIR/judge.json"; exit 3; fi
if [ "$rc" -eq 0 ]; then echo 1 > "$REWARD_DIR/reward.txt"; else echo 0 > "$REWARD_DIR/reward.txt"; fi
cat "$REWARD_DIR/judge.json"
exit 0
