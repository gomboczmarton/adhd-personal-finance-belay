#!/usr/bin/env bash
set -euo pipefail
if [ ! -f "$MANIFEST" ]; then
  (cd "$REPO" && uv run harness/scripts/generate_fixtures.py "$PERSONA" "$(dirname "$(dirname "$MANIFEST")")")
fi
uv run "$REPO/evals/lib/build_workspace.py" "$PERSONA" "$WS" --inbox "$(dirname "$MANIFEST")"
