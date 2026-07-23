# Belay — optimization-loop lab notebook

Per `practices/06-optimization-loop.md` (harness-engineering store): every
iteration/experiment recorded — change, hypothesis, before/after, decision.

## 2026-07-23 — SkillOpt-Sleep field test (skill-space optimization, key-free paths)

**Hypothesis.** Microsoft SkillOpt-Sleep (see the store's
`research/2026-07-23-skillopt-skill-space-optimization.md` and belay's new
`.claude/skills/skill-optimizer/`) can run its full harvest→mine→replay→gate→stage
cycle in this repo without an API key, and its gate behaves honestly.

**Setup.** Claude cloud container; `pip install skillopt` (PyPI 0.2.0) into a
scratch venv; project = this repo; transcripts = this environment's `~/.claude`.

**Runs and results.**

1. **Deterministic mechanism proof** (no provider calls):
   `python -m skillopt_sleep.experiments.run_experiment --persona researcher --assert-improves`
   → PASS. Held-out 0.3333 → 1.0000 (+0.667) in one night (+2 accepted edits);
   **gate blocked an injected harmful edit**; ~0 tokens.
2. **Harvest/mine on real transcripts:**
   `python -m skillopt_sleep harvest --project "$(pwd)" --scope all`
   → 3 sessions → 3 mined tasks with train/val split. Plumbing works on real
   `~/.claude/projects/*` JSONL.
3. **Full mock night:**
   `python -m skillopt_sleep run --project "$(pwd)" --scope all --backend mock --progress`
   → end-to-end: staged `.skillopt-sleep/staging/20260723-064336/` with
   `report.md` + manifest + diagnostics. Held-out 0.000 → 0.000 ⇒ **gate: reject,
   nothing adopted, 0 tokens**. The honest reject is the success criterion here —
   mock has no optimizer, so any "accept" would have been a red flag.
4. **Belay's own frozen suite, independently:** fixtures regenerated;
   `python3 evals/run_local.py --fixtures` → 3/3 deterministic tasks PASS at
   reward 1.0, fixture rule OK, judge task correctly SKIPPED outside a judge run.
   The suite that must gate any future SkillOpt adoption is green.
5. **Real-backend night (`--backend claude`): not run.** Blocked by the cloud
   session's permission classifier (autonomous `claude -p` subprocess spawning).
   Sanctioned routes recorded in the skill: `/skillopt-sleep-handoff` in-session
   (isolated fresh-context subagents, no key) or `--backend claude` on a local
   machine (CLI subscription, no raw key).

**Decision.** Mechanism and plumbing verified key-free; engine adopted as the
harness's skill-space optimization tool via `.claude/skills/skill-optimizer/`
(install pinned to SkillOpt commit `61735e3`). `.skillopt-sleep/` and
`.skillopt-sleep-handoff/` git-ignored. **Adoption rule:** any future accepted
proposal is adopted only after this repo's deterministic suite re-runs green;
regression ⇒ restore from the engine's backup. Next step (interactive session or
local machine): first real night via handoff or claude backend with
`--max-tasks 3 --edit-budget 2`, then record the night here.
