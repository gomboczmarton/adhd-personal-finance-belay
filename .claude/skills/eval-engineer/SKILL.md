---
name: eval-engineer
description: Build, run, and audit evals for an agentic harness — interactively, one Harbor task at a time (the default, LangChain-style workflow), or route to a Darwin-style evolution loop when its preconditions hold. Use when the user asks to create evals, an eval suite, benchmark/regression tasks, test scenarios for a harness, verifier design, trace-informed evals, or asks which eval approach to use, or wants to optimize/evolve a harness against its evals. Complements harness-designer (day-zero eval system) and harness-auditor (eval gap audit) by doing the eval authoring itself.
---

# Eval Engineer

You are building evals for a harness in a target repo, using this store's practices
(`practices/01` evaluation-first, `06` optimization loop, `07` deterministic
verifiers) plus the incorporated LangChain eval-engineering workflow. Build in the
target repo; treat this store as read-only reference.

## Step 0 — Route the approach

Two workflows exist. Decide (and tell the user) which applies:

**Default: interactive Harbor-task authoring (the LangChain way).** Use whenever
evals don't exist, don't cover a capability, or aren't trusted. This is almost
always the answer, and it is mandatory before the second route is ever allowed.

**Darwin-style evolution loop** (autonomous harness optimization against a fixed
suite — reference implementation: github.com/ruvnet/metaharness, `darwin-mode` +
`flywheel` packages). Route here ONLY when every precondition holds:

1. Trusted suite exists: fixture-tested verifiers, N-trial pass rates, thresholds.
2. A human-curated holdout AND a frozen anchor suite (never optimized against).
3. Bounded mutation surface: revertible config/policy files whose levers are enums
   or clamped numbers — never free prose.
4. Frozen, conjunctive promotion gate (beats parent ∧ safety floor ∧ no
   regression), fingerprinted, not modifiable by the loop it gates.
5. Sandboxed, budget-metered runs.

If any precondition fails, fall back to the default route and build the missing
piece first. Read
`research/2026-07-22-eval-engineering-langchain-vs-metaharness.md` for the full
comparison and the fitness/gate templates worth copying (Darwin's
weighted-fitness-minus-safety-penalties, four-clause gate, tree archive).

## The default route — six steps, one task at a time

Read [references/harbor.md](references/harbor.md) before creating or running any
task. The flow:

```text
inspect agent and interview user -> propose directions -> user chooses
-> approve runtime and environment -> build, run, audit -> review and repeat
```

### 1. Map the agent (read-only)

Inspect the target harness: runtime (entrypoints, prompts, models, hooks, memory),
actions (tools, failures, effects), backing data, state, purpose, and evidence
(existing tests, fixtures, verifier scripts, documented failures). Do NOT start
services, install packages, or touch credentials before the user approves the
runtime. Reuse what the repo already has: existing deterministic verifier scripts
become `tests/` gates; existing fixture generators seed `environment/`; an
existing case format (personas, scenarios) maps onto task instructions.

Summarize the map in conversation, then ask only what the repo cannot answer:
"Which user job matters most?", "What failure should never happen?"

If the user provides traces, read
[references/trace-sourcing.md](references/trace-sourcing.md) — traces supply
realistic requests and dependency behavior, never hidden truth.

### 2. Propose 2–3 eval directions

For each: `Name / Example request / Tests (behavior distinguished) / Needs`.
Recommend one; **wait for the user to choose**. Interactive choice is the quality
mechanism — one-shot generated evals don't get trusted or adopted.

### 3. Checkpoint: approve runtime and environment (≤150 words)

Read [references/task-design.md](references/task-design.md) and
[references/environment-building.md](references/environment-building.md).
State: task, runtime (active entrypoint vs. labeled reconstruction), each
dependency live / frozen / simulated, success definition, recommendation. Never
write to production; isolate mutations.

### 4. Build one Harbor task

`evals/<task-id>/` = `task.toml` + `instruction.md` + `environment/` + `tests/`.
One capability per task. Keep hidden truth and judge criteria out of the
environment the target can see. One primary reward; LLM judge only for semantic
success, deterministic code for objective facts — read
[references/verifier-design.md](references/verifier-design.md).

### 5. Test, run, audit

Verifier fixtures FIRST: one clearly-valid result must pass, one
plausible-but-wrong result must fail — before any agent run. Then run through
Harbor, and inspect both agent and verifier trajectories for reward hacking
(claimed-but-unexecuted actions, exploiting exposed answers, proxy satisfaction).
If the environment leaked the answer before the target exercised the capability,
revise the task. Wrong agent work = reward 0; build/timeout/judge/credential
failures = infrastructure error, no score.

**No Docker available?** Keep the Harbor directory layout and `task.toml`
(portable to real Harbor runs later), and add a thin local runner that executes
`tests/` directly against a workspace fixture. Say explicitly that containerized
isolation is deferred, and never let the local path diverge from the task format.

### 6. Review and repeat

Explain task path, run command, verifier decision, and limitations. User approves,
revises, or drops; then propose a *distinct* capability (a new case must add an
obstacle, state, or failure mode — not just new names).

## Store integration (what the upstream skill doesn't say)

- **Day-zero rule**: if the target repo has no eval system at all, this skill's
  output IS the first commit (`practices/01`). Seed 10–30 scenarios; partition
  smoke / full / holdout; wire into CI — "evals that don't run on every change
  don't exist."
- **Statistics**: report N-trial pass rates, never single runs; choose pass@k vs
  pass^k per capability (pass^k for autonomous delegation).
- **Thresholds are gates**: every task gets a numeric threshold with a written
  justification.
- **Grade the graders**: the fixture rule above is the minimal form; LLM-judge
  rubrics additionally need a human-agreement check before their scores are
  trusted.
- **Record the loop**: every accepted/dropped eval and every optimization
  iteration goes in the target repo's `experiments.md` lab notebook
  (`practices/06`).

## Runtime installation (Claude cloud sessions)

If the target repo will run Harbor evals in Claude Code cloud sessions,
install the runtime on day zero — the remote container ships dockerd but does
not start it, and the Harbor CLI is absent:

1. Copy `assets/session-start.sh` → target `.claude/hooks/session-start.sh`
   (`chmod +x`) and merge `assets/settings.json` into the target's
   `.claude/settings.json`.
2. Adapt `assets/prepare_containers.sh` (set `STAGE_PATHS`) so each task's
   Docker build context is self-contained; git-ignore
   `evals/*/environment/ctx/` and `evals/jobs/`.
3. Read [references/claude-cloud-containers.md](references/claude-cloud-containers.md)
   BEFORE the first `harbor run` — it records the TLS-interception fix, the
   Harbor 0.20 task.toml gotchas (silently dropped on validation failure), and
   the hook validation commands. All field-verified.
4. **Wire the suite into CI**: copy `assets/evals-ci.yml` to the target's
   `.github/workflows/evals.yml` and fill the two TODO steps (fixtures +
   local runner with `--fixtures`). Deterministic tasks gate every push/PR;
   judge tasks run from Claude Code sessions.
5. **Judge tasks**: install `assets/judge.py` as the target's LLM-judge runner
   (default judge command `claude -p`, works in any Claude Code session;
   `JUDGE_CMD` to pin a model). Calibrate before trusting: the judge must
   pass the task's `pass_reply` fixture and fail its `fail_reply` fixture
   (`run_local.py --judge` pattern). Judge exit semantics: 0 pass, 1 fail,
   3 infrastructure error (invalid judge output is never reward 0).

## Invariants

- One capability per task under `evals/`.
- No production writes; reset mutable state between trials.
- Hidden truth and judge credentials unavailable to the target.
- The suite that gates a change is never modified in the same iteration as the
  change (`practices/06`); the holdout stays human-curated.
