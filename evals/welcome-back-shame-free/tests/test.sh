#!/usr/bin/env bash
# This task's success is semantic; grading requires an LLM judge run with
# tests/rubric.md over the target reply (see evals/README.md). The local
# runner skips it unless a judge-capable runner is wired in. Fixture
# expectations for the judge's own test are listed in the rubric.
echo "judge_required: run rubric.md with an LLM judge over the reply" >&2
exit 3
