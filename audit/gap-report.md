# Belay Harness — Gap Report

*Audited 2026-07-12 against the harness-engineering knowledge store (taxonomy 00–01,
practices 01–09, `examples/business/personal-finance-harness.md`). Scope: the contents
of THIS repository — the shipped product. Claims about the private factory repo are
treated as unverifiable from here, per the store's rule that a claimed mechanism
doesn't exist until a test in reach proves the wire.*

## 1. Route (O/V/O classification)

**Business-domain harness, layered.**

- **Run-time layer** — Output: domain artifacts (budget.md, reconcile JSON, letter,
  HTML report, Excel). Verification: business-level — Decimal arithmetic in scripts,
  budget-balance invariant, schema validation, transfer-matching. Outcome: direct
  (a month closed, awareness sustained, the user comes back).
- **Build-time layer** — Output: the harness's own code (10 scripts, 8 schemas,
  5 skills, 1 subagent). Verification: **absent in this repo** (no unit tests, no CI
  beyond release packaging).

Routing verdict: the run-time verification layer is *mostly* at the right (business)
layer — reconciliation-as-compiler was correctly identified and built as deterministic
scripts. Two layer mismatches remain (gaps 3 and 4 below). The build-time layer is
unverified per-layer, violating "classify per layer, verify per layer".

## 2. Eval spine (practice 01) — **the audit-stopping gap**

- **No eval system exists in this repo.** No `evals/` directory, no personas, no
  runner, no thresholds, no CI job that runs anything on change. The only workflow
  (`.github/workflows/release.yml`) packages zips.
- `harness/scripts/generate_fixtures.py --all evals/personas` points at a directory
  that does not exist here — eval *infrastructure* shipped without its eval *content*.
- README claims "five synthetic personas, ground-truth manifests, 40 checks green"
  and persona-bot conversational evals — all in a private factory repo. From this
  repo's standpoint: **"evals that don't run on every change don't exist."** Any
  change to `harness/` in this repo can be zipped and released with zero gating.
- No baseline record, no N-trial statistics, no experiments.md, no holdout — none of
  it visible or wired.

Per the audit sequence, everything downstream of this is unmeasurable until fixed.
The remaining sections are recorded for the plan, but item 1 of the upgrade plan is
the retrofit.

## 3. Prove the wires (practices 07, 09)

| Claimed mechanism | Wire status |
|---|---|
| "Re-importing is always safe" (content-hash dedup) | Code exists (`ingest.py`), **no test in repo proves it** |
| "Internal transfers are never income" | Code exists (`reconcile.py` exclusion), **no test proves it** |
| Budget balance gate (`--verify-budget`, exit 1) | Code exists, exit code correct, **nothing consumes the exit code mechanically** — only SKILL.md prose says "must report balanced: true" |
| Workspace validator (exit 0/1/2, violations listed) | Well-built (errors teach), **nothing gates on it** — "green required" is a prompt instruction |
| **Reconciliation against source statements** | **Missing entirely.** `--verify-budget` checks internal budget arithmetic (allocations + savings == planned income). No script compares the ledger's running balance to the bank statement's closing balance — the fixtures even *generate* a balance column that ingest then ignores. The domain's true compiler (template: "balances must reconcile to the cent" against the statement) is not built |
| Conservation ("no transaction invented or dropped") | Ingest prints `{imported, duplicates, rows}`; the *skill* is told to compare counts. Prompt-level, not a gate |
| `welcome-back` fires "PROACTIVELY … when more than one month is open" | No trigger mechanism exists (no scheduler, no hook, no session-start check) — the skill can only fire when the user shows up and says something matching. Claimed edge with no wire |
| Release asset == source | `dist/harness.zip` is hand-committed; no CI step rebuilds it from `harness/` and diffs. A stale zip ships silently to `install.py --from-release` users |

## 4. Gate reality (practice 02)

Enforcement-triad placement of the harness's own hard rules:

| Constraint | Documented as | Actually enforced by |
|---|---|---|
| D4 "the model never does arithmetic" | Hard rule | **Prompt only** (scripts exist, nothing blocks mental math) |
| "Validator green before closing" | Hard rule | **Prompt only** |
| "balanced: true required" | Hard gate | **Prompt only** |
| Only confirmed facts become state | Hard rule | **Prompt only** (schemas validate shape, not provenance) |
| No money movement executed | Structural | **Genuinely structural** — no payment tool exists. Correct gate ✓ |

**Default-FAIL / convergence-law check: FAIL.** A month can be reported "closed"
(letter written, report rendered) without any mechanical evidence that reconcile and
validate exited 0. No hooks, no `.claude/settings.json`, no permission rules ship with
the harness. Success is claimable unobserved.

Irreversibility table: largely healthy — prepare/execute split honored (transfer
checklist executed by the human), append-only ledger, idempotent ingest. But the model
edits `budget.md` / `strategy.md` / merchant-map in place with no checkpoint/commit
convention; git is the implied undo but nothing invokes it (autonomy budget ∝ quality
of undo — the undo is unmanaged).

## 5. Verification topology (practice 03)

- No doer/checker split at run time. The deterministic scripts are the checkers for
  *numbers* (good — the strongest form), but the conversational layer (tone rules,
  shame-free iron rules, income-language precision) has no independent verifier
  anywhere in this repo; the persona-bot judge is claimed private and pre-ship only.
- `finance-coach` subagent restricted to `Read, Bash, Grep, Glob` — but **Bash can
  write**, so the read-only intent is not tool-enforced.

## 6. Loop contracts (practice 09)

No standing loops exist (by design — user-triggered rituals). The one implied loop
("re-run reconcile until uncategorized is empty", reconcile-month step 3) has **no
iteration cap and no non-success exit**. The proactive welcome-back trigger is claimed
but unwired (see §3). No scheduler component at all, vs. the template's monthly cron +
statement watchers + self-scheduled follow-ups.

## 7. Capability surface (practice 05)

Strong overall — the best-executed axis:

- Repetition frozen into 10 consolidated, documented scripts; judgment stays with the
  model. Right altitude (`reconcile.py`, not `run_sql`).
- Errors teach: validator lists all violations; ingest returns JSON summaries.
- Skills carry visibly failure-derived rules (tense discipline, income-language
  precision, "never trust filename coverage") — evidence of real trace-driven error
  analysis. But **none of these distilled rules has a visible regression case**, so
  they can silently regress on any skill edit.
- No hooks at all — the entire "every time" tier of the packaging table is unused.

## 8. Context & memory (practice 04)

- Filesystem-as-state done well: resumable `onboarding-state.md`, append-only ledger,
  schema-validated markdown, reconcile JSON persisted then consumed. ✓
- Provenance partially present (`confirmed: false`, `source: user`). ✓
- **No expiry or contradiction checking** on merchant-map/yearly-bank rules; no
  stale-memory audit (template prescribes quarterly). A merchant rule from a closed
  account will be trusted forever (30-day rot datapoint applies).
- No memory-usage eval cases (uses memory / doesn't overuse stale memory).

## 9. Token economics (practice 08)

Nothing. No metering, no attribution, no cost-per-close beside pass rate, no budgets.
For a local personal tool this is low-severity, but "cost per close" is named in the
template's product metrics and nothing here could compute it.

## 10. Trust ramp & interaction (Axis 6)

- Philosophy is a deliberate, well-executed rung-1/2 posture (propose everything;
  evidence-backed single questions; escalations answerable in seconds ✓).
- But the ramp itself is **not explicit**: no documented rungs, no promotion criteria
  ("auto-apply categorizations above confidence X after N corrected months"), so the
  harness can never earn autonomy — permanent rung 1 is a product-philosophy choice
  worth *stating*, and rule-based auto-categorization (`by=rule`) is *already* rung-2
  behavior operating without stated promotion justification.

## What is genuinely good (keep, don't churn)

1. The O/V/O route was taken correctly: deterministic Decimal scripts as the domain
   compiler, model barred (in intent) from arithmetic.
2. Prepare/execute split and no-money-movement are structural, not prompted.
3. Fixture generator with ground-truth manifests is real, high-quality eval
   infrastructure — the retrofit is cheap *because* this exists.
4. Failure-derived skill rules show the error-analysis discipline the store demands.
5. Filesystem-as-state, append-only ledger, idempotent ingest, resumable onboarding.
6. ADHD-first interaction design is a coherent, documented counter-metric ("the win
   is that you came back") — most harnesses never name theirs.
