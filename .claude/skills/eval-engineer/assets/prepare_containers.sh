#!/bin/bash
# Template: stage self-contained Docker build contexts for real Harbor runs.
# Copy to <target-repo>/evals/prepare_containers.sh and set STAGE_PATHS to the
# repo paths every task image needs (Harbor builds each task image with
# evals/<task>/environment/ as the build context, so everything the image
# needs must be staged inside it). Git-ignore evals/*/environment/ctx/.
#
# In Claude Code cloud containers, outbound HTTPS is transparently intercepted
# by the session proxy; the proxy CA bundle is staged so uv/pip inside the
# build can verify TLS (never disable verification). Keep verifiers
# network-free regardless — that is better eval hygiene anyway.
#
# Usage: bash evals/prepare_containers.sh   (then: harbor run -p evals ...)
set -euo pipefail
cd "$(dirname "$0")/.."

# TODO(per-harness): regenerate deterministic fixtures here if the tasks use any.

# TODO(per-harness): repo paths to stage into every task's build context.
STAGE_PATHS=("harness" "evals/lib")

for task_dir in evals/*/; do
  [ -f "$task_dir/task.toml" ] || continue
  [ -f "$task_dir/environment/Dockerfile" ] || continue
  task_name="$(basename "$task_dir")"
  ctx="$task_dir/environment/ctx"
  rm -rf "$ctx"
  mkdir -p "$ctx/evals/$task_name/environment"
  for p in "${STAGE_PATHS[@]}"; do
    mkdir -p "$ctx/$(dirname "$p")"
    cp -r "$p" "$ctx/$p"
  done
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
