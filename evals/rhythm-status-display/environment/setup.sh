#!/usr/bin/env bash
# Build the task environment: the persona's post-onboarding workspace, then the
# harness's own pipeline up to "June closed, June and July planned". Idempotent.
set -euo pipefail
if [ ! -f "$MANIFEST" ]; then
  (cd "$REPO" && uv run harness/scripts/generate_fixtures.py "$PERSONA" "$(dirname "$(dirname "$MANIFEST")")")
fi
uv run "$REPO/evals/lib/build_workspace.py" "$PERSONA" "$WS" --inbox "$(dirname "$MANIFEST")"
cd "$REPO"
for f in "$WS"/inbox/*.*; do
  base="$(basename "$f")"
  uv run --quiet harness/scripts/ingest.py "$WS" "${base%%_*}" "$f" > /dev/null
done
uv run --quiet harness/scripts/match_transfers.py "$WS" > /dev/null
mkdir -p "$WS/months/$MONTH/reports"
uv run --quiet harness/scripts/reconcile.py "$WS" --month "$MONTH" \
  > "$WS/months/$MONTH/reports/reconcile_$MONTH.json"
for m in 2026-06 2026-07; do
  [ -f "$WS/months/$m/budget.md" ] || uv run --quiet harness/scripts/plan_month.py "$WS" "$m" > /dev/null
done
