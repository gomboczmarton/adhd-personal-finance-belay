#!/usr/bin/env bash
# Build the task environment: deterministic fixtures + frozen post-onboarding
# workspace with exports staged in the inbox. Idempotent.
set -euo pipefail
if [ ! -f "$MANIFEST" ]; then
  (cd "$REPO" && uv run harness/scripts/generate_fixtures.py "$PERSONA" "$(dirname "$(dirname "$MANIFEST")")")
fi
uv run "$REPO/evals/lib/build_workspace.py" "$PERSONA" "$WS" --inbox "$(dirname "$MANIFEST")"
