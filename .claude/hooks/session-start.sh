#!/bin/bash
# SessionStart hook: make full Harbor eval runs possible in Claude Code
# cloud containers. The remote image ships dockerd/containerd/runc but does
# not start the Docker daemon; Harbor needs it for containerized tasks.
# Deliberately resilient: a failed step degrades to evals/run_local.py
# instead of blocking session startup.
set -uo pipefail

# Local sessions manage their own Docker; do nothing there.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# 1. Start the Docker daemon if present and not already running (idempotent).
if command -v dockerd >/dev/null 2>&1 && ! docker info >/dev/null 2>&1; then
  nohup dockerd >/var/log/dockerd.log 2>&1 &
  for _ in $(seq 1 30); do
    docker info >/dev/null 2>&1 && break
    sleep 1
  done
fi
if docker info >/dev/null 2>&1; then
  echo "docker: daemon ready"
else
  echo "docker: daemon unavailable — use evals/run_local.py (Harbor phase semantics, no containers)"
fi

# 2. Harbor CLI via uv tool (cached in the container snapshot after first run).
if ! command -v harbor >/dev/null 2>&1 && ! [ -x "$HOME/.local/bin/harbor" ]; then
  uv tool install harbor >/dev/null 2>&1 || echo "harbor: install failed — evals still run via evals/run_local.py"
fi
echo "harbor: $("$HOME/.local/bin/harbor" --version 2>/dev/null || harbor --version 2>/dev/null || echo not-installed)"

# 3. Make uv tool shims visible to the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi

exit 0
