#!/usr/bin/env bash
# Oracle solution: full import, then deliberately re-import the final month's
# checking export (the capability under test), then match and reconcile.
# Both ingest summaries for the re-imported file are kept as artifacts so the
# verifier can grade the observed dedup behavior, not a claimed one.
set -euo pipefail
cd "$REPO"
for f in "$WS"/inbox/*.*; do
  base="$(basename "$f")"
  acct="${base%%_*}"
  summary="$(uv run harness/scripts/ingest.py "$WS" "$acct" "$f")"
  if [ "$base" = "main_${MONTH}.csv" ]; then
    echo "$summary" > "$ARTIFACTS/ingest_first.json"
  fi
done
uv run harness/scripts/ingest.py "$WS" main "$WS/inbox/main_${MONTH}.csv" \
  > "$ARTIFACTS/ingest_reimport.json"
uv run harness/scripts/match_transfers.py "$WS"
uv run harness/scripts/reconcile.py "$WS" --month "$MONTH" > "$ARTIFACTS/reconcile.json"
cat "$ARTIFACTS/ingest_reimport.json"
