---
name: skill-optimizer
description: "Run usage-driven skill/memory optimization for an agentic harness with Microsoft SkillOpt-Sleep — nightly harvest of real sessions, mined recurring tasks, gated bounded edits to SKILL.md/CLAUDE.md, staged adoption checked against the harness's frozen eval suite. Use when the user wants the harness to learn from real usage, asks for a sleep/dream/self-improvement cycle, wants skills tuned from transcripts, asks to install or run SkillOpt/skillopt-sleep, or asks which optimization approach fits. Complements eval-engineer (authors the frozen suite this skill gates adoption on) and its Darwin route (policy-surface evolution). ONLY on an explicit engineering request — never during finance flows (onboarding, reconciling, budgeting, purchase checks, welcome-back): those are the domain plane; this skill is the meta plane (docs/architecture.md activation planes)."
---

# skill-optimizer — gated skill-space optimization from real usage

Operationalizes `practices/06-optimization-loop.md` §"Skill-space optimization" and
`research/2026-07-23-skillopt-skill-space-optimization.md`. The engine is
**Microsoft SkillOpt-Sleep** (MIT, external dependency — we record and install, we
do not vendor). Core idea: the skill/memory document is the trainable state of a
frozen agent; improvement = bounded text edits accepted through a held-out gate,
adopted only explicitly, with backups.

## Step 0 — Route the approach (do not skip)

| Situation | Route |
|---|---|
| No trusted eval suite in the target repo yet | **STOP → eval-engineer first.** Adoption gating (Step 4) needs a frozen suite; day-zero rule. |
| Recurring real-usage tasks; agent repeatedly misses house rules; skills drifting stale | **This skill.** |
| One known deficiency in one skill | Plain practice-06 iteration: edit, run suite, keep/revert. No engine needed. |
| Autonomous improvement of *policy* surfaces (topology, retries, context policy) | eval-engineer's Darwin route (five preconditions). |
| Sensitive transcripts (client data, secrets) | This skill, but **reviewed task-file workflow only** (see references) or `mock`. |

## Step 1 — Install (per target repo / machine)

Follow `references/skillopt-sleep-install.md`. Summary: clone
`microsoft/SkillOpt` (pin the examined commit unless the user wants latest), add
the Claude Code marketplace plugin (`/plugin marketplace add ./plugins/claude-code`
→ `/plugin install skillopt-sleep@skillopt-sleep`), or `pip install skillopt` for
the base CLI (PyPI 0.2.0 lacks handoff mode). Python ≥ 3.10.

## Step 2 — Prove the plumbing before spending anything (all key-free)

```bash
# 1. Mechanism proof: held-out lift + gate blocks an injected harmful edit
python -m skillopt_sleep.experiments.run_experiment --persona researcher --assert-improves
# 2. What would it learn from? (read-only harvest of ~/.claude transcripts)
python -m skillopt_sleep harvest --project "$(pwd)" --scope all
# 3. Full dry cycle, no provider calls, stages an honest report
python -m skillopt_sleep run --project "$(pwd)" --backend mock --progress
```

Expect the mock night to **reject** (no real optimizer → no lift). That is the
gate working, not a failure. If harvest mines 0 tasks, there is nothing to learn
from yet — stop and say so; do not force a run.

## Step 3 — First real night (choose the cheapest sufficient backend)

Backend decision table (full detail in references):

- **`handoff`** — no key, no subprocess; the engine writes prompts, THIS session
  answers each **in an isolated fresh-context subagent** (never inline — you have
  seen the mined tasks; inline answers contaminate the gate). Use the plugin's
  `/skillopt-sleep-handoff` command. Preferred in cloud sessions, where spawning
  `claude -p` subprocesses may be blocked by permission policy (field-verified).
- **`claude`** — authenticated Claude Code CLI subscription, no raw API key.
  Preferred on a local machine. Bound it: `--max-tasks 3-10 --edit-budget 2-4`.
- **Direct API backends** — only when a provisioned, spend-capped key already
  exists for eval work.

Steer with `--preferences "…house rules…"` (main-only flag); preferences remain
subject to the gate.

## Step 4 — Review, adopt, and gate on the FROZEN suite

1. Read the staged `report.md`: held-out baseline → candidate, gate decision,
   exact proposed edits. **Show these to the user before any adoption.**
2. Sleep's gate scores *self-mined* tasks — necessary, not sufficient. After
   `adopt` (or `/skillopt-sleep adopt`), immediately run the harness's own frozen
   eval suite. Regression ⇒ restore from the adoption backup and record why.
3. Record the night in `experiments.md` (practice 06 lab notebook): backend,
   tasks mined, gate scores, decision, suite result after adoption.
4. Nightly schedule (`/skillopt-sleep schedule --hour 3`) only after the manual
   cycle has been green at least once. `--auto-adopt` only after a trust ramp of
   repeated adopt-then-suite-green history — never on day one.

## Hard rules

- **Never hand-edit** the files the engine manages as part of this skill; only
  `adopt` applies proposals (with backup). Harvest is read-only.
- **Fresh-context answering** in handoff mode is the gate's integrity boundary.
- **Data boundary:** real backends send truncated transcript excerpts to the
  provider; for sensitive projects use `harvest --output` → human review/redact →
  `"reviewed": true` → `--tasks-file` (real backends refuse unreviewed files).
- **No hard token budget exists in the engine** — bound every run with
  `--max-tasks`/`--max-sessions`/`--edit-budget` and meter per practice 08.
- The engine's gate is never a substitute for the harness's frozen suite; the
  suite is never modified in the same iteration it gates.
