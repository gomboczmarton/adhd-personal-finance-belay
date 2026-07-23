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

## 2026-07-23 — token_meter.py installed (tokens-per-success signal)

Per the store's `practices/08` §"Closing the loop": installed
`.claude/skills/eval-engineer/assets/token_meter.py` and verified the full
pipeline — suite run with `--keep` (3/3 PASS), then
`token_meter.py ~/.claude/projects/<slug> --rewards evals/jobs/<job>` joined
transcript usage with the reward files and emitted `tokens_per_success`
(demo run: 3 successes; the token side covered the whole session, since the
deterministic suite spends zero model tokens — scope the meter to the run's
own transcripts for real-agent runs). **Standing rule from this entry on:**
every recorded iteration carries pass rate AND tokens-per-success; a change is
kept only if neither worsens.

## 2026-07-23 — Consolidation migration (D16): factory content in, suite 8/8

Executed per `docs/migration-plan.md` phases A–C (decision: harness-engineering
docs/19–25; recorded here as the lab-notebook trail):

- **Personas p03–p07 migrated** from the factory (ids renumbered; fixtures
  regenerated, not copied — seeded generator; 1,822 transactions / 195 export
  files across 7 personas).
- **Five new Harbor tasks authored**, one distinct capability each:
  `backlog-catchup-two-years` (24-month ingest + refill matching),
  `entropy-hidden-sweeps` (unique-ref descriptions + one-legged sweeps,
  `--own-account-internal`), `family-yearly-items` (March car-tax spike),
  `multibank-dialect-dedup` (Revolut/Wise/Monzo/OTP-preamble, dup hashes),
  `feast-famine-income` (irregular income, anti-smoothing).
- **The fixture rule earned its keep during authoring**: two first-draft
  corrupt.py scripts flipped `txn.categorized` kinds that the independent
  recomputation deliberately ignores — verifier passed the "corrupted"
  workspaces, run_local reported BROKEN, and both fixtures were redesigned to
  mutate what actually matters (June matched-events dropped; largest June
  income import erased). A third failure surfaced a real capability gap:
  `build_workspace.py` had no ingestion mappings for the four real-bank
  dialects — added (revolut/wise/monzo/n26/otp incl. the 9-row OTP preamble
  via `header_rows`).
- **Gate B+C evidence**: full suite 8/8 deterministic tasks PASS at reward
  1.0, fixture rule OK on all; judge task correctly SKIPPED outside a judge
  run (job `20260723-182618`, kept).
- **Frozen anchor designated** (`evals/ANCHOR`): `family-yearly-items` +
  `multibank-dialect-dedup` — excluded from PR CI, release-workflow only.

### Factory Tier-2 run archive (summaries; raw runs stay in the archived factory repo)

Nine judged persona-bot sessions, 2026-07-09/10 format: persona × skill,
orchestrated per `evals/lib/rubrics/persona-bot.md`, judged per
`evals/lib/rubrics/judge.md`:

- `sam-onboarding` (×3 iterations) — onboarding flow hardened across three
  judged reruns (resumability, evidence-backed questions).
- `sam-purchase-check` — €920 standing-desk ask during a no-income month;
  judged for factual-mirror behavior, no moralizing.
- `sam-welcome-back` — gap re-entry, shame-free contract.
- `alex-journey` — the multi-month hybrid arc (awareness → first envelope).
- `alex-reconcile-month` — end-of-month reconcile conversation.
- `kovacs-monthly-prep` — family month planning with yearly items.
- `private-data-simulation` — **summary not migrated pending owner review**
  (D16 open item).

## 2026-07-23 — Phases D+E: activation planes built, release train wired

- **`/extend` shipped** (`harness/skills/extend/`): the meta-plane flow
  builder — explicit-invocation-only description; builds flow + wired
  guardrails + component evals + trigger cases as ONE deliverable; staged
  adoption; instance-local namespace rules.
- **Meta descriptions hardened**: eval-engineer and skill-optimizer now carry
  the plane guard ("only on explicit engineering request — never during
  finance flows").
- **Trigger-isolation suite authored** (`evals/trigger-isolation/`): 17 cases
  (11 domain incl. 5 near-misses like "optimize my spending" and "test my
  budget"; 6 meta incl. the case-7/17 complaint-vs-request pair). Verification
  method: skill-creator behavioral trigger evals. **Status: authored, not yet
  verified** — `claude -p` subprocess spawning is blocked in this cloud
  session; run interactively/locally and record here.
- **Release train** (`.github/workflows/release.yml`): tag-triggered — full
  suite incl. anchor → fresh-seed regeneration gate → sanitization scan →
  package → GitHub release. PR CI (`evals.yml`) now runs `--exclude-anchor`.
- **Gate E dry-runs, all green in this session**: fresh-seed gate GREEN
  (offset 1: all 8 deterministic tasks passed on brand-new ground truth,
  baseline restored); sanitization scan + packaging OK (26 files; committed
  dist/ zips restored to the published v0.1.0 artifacts afterwards); PR-CI
  mode green with anchor excluded (6/6).
- **Remaining before the factory archives (owner)**: review the
  private-data-simulation run summary; demo pipeline in/out; run the
  trigger-isolation verification; flip the GitHub template-repo flag; archive
  `adhd-personal-finance-harness`.
