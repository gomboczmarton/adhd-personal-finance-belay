#!/bin/bash
# Stage self-contained Docker build contexts for real Harbor runs.
#
# Harbor builds each task image with evals/<task>/environment/ as the build
# context, so everything the image needs must live inside it. This script
# copies the harness, eval lib, personas, and pre-generated fixtures into
# environment/ctx/ (git-ignored) for every containerized task.
#
# In Claude Code cloud containers, outbound HTTPS is transparently
# intercepted by the session proxy; if the proxy CA bundle exists it is
# staged too so uv/pip inside the build can verify TLS (never disable
# verification).
#
# Usage: bash evals/prepare_containers.sh   (then: harbor run -p evals ...)
set -euo pipefail
cd "$(dirname "$0")/.."

uv run harness/scripts/generate_fixtures.py --all evals/personas evals/fixtures

for task_dir in evals/*/; do
  [ -f "$task_dir/task.toml" ] || continue
  [ -f "$task_dir/environment/Dockerfile" ] || continue
  task_name="$(basename "$task_dir")"
  ctx="$task_dir/environment/ctx"
  rm -rf "$ctx"
  mkdir -p "$ctx/evals/$task_name/environment"
  cp -r harness "$ctx/harness"
  cp -r evals/lib evals/personas evals/fixtures "$ctx/evals/"
  # copy the task itself, skipping the ctx dir we are writing into
  for entry in "$task_dir"*; do
    name="$(basename "$entry")"
    if [ "$name" = "environment" ]; then
      for sub in "$entry"/*; do
        [ "$(basename "$sub")" = "ctx" ] && continue
        cp -r "$sub" "$ctx/evals/$task_name/environment/"
      done
    else
      cp -r "$entry" "$ctx/evals/$task_name/"
    fi
  done
  if [ -f /root/.ccr/ca-bundle.crt ]; then
    cp /root/.ccr/ca-bundle.crt "$ctx/ca-bundle.crt"
  else
    : > "$ctx/ca-bundle.crt"   # empty file keeps the Dockerfile COPY valid
  fi
  echo "staged $ctx"
done
