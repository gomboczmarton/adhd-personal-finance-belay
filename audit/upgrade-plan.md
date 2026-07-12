# Belay Harness — Prioritized Upgrade Plan

*Companion to `gap-report.md`. Each item is an eval-gated change (practice 06):
change → hypothesis → suite evidence that accepts or reverts it. Sequence per the
auditor rule: eval spine first, then wire-proofs and gates, then everything else.
Record every iteration in `experiments.md` (created by item 1).*

## Tier 1 — the eval spine (do first; everything else is unmeasurable until this lands)

### 1. Vendor the eval suite into this repo and wire it into CI
- **Change:** create `evals/` (personas ×5, generated fixtures, ground-truth
  manifests via the existing `generate_fixtures.py`, a runner script asserting the
  ~40 deterministic checks), plus `experiments.md`; add a GitHub Actions workflow
  running the suite on every push/PR touching `harness/**`. Options if the factory
  suite can't be published verbatim: (a) port the deterministic half only —
  personas are synthetic by construction, so publishable; (b) a CI job in the
  factory repo triggered by this repo's changes. Prefer (a): the suite guards the
  code it lives next to.
- **Hypothesis:** harness changes become gateable; the release pipeline stops being
  able to ship unverified script changes.
- **Evidence:** CI red on an intentionally broken `reconcile.py` (mutate the
  transfer-exclusion line); CI green on main. Baseline pass rates recorded.

### 2. Statement-balance reconciliation — build the missing compiler
- **Change:** extend `ingest.py` to capture the statement's balance column (the
  dialects and fixtures already carry it) and add
  `reconcile.py --verify-statement <account> <month>`: ledger running balance ==
  statement closing balance, to the cent, exit 1 on mismatch. Add a conservation
  check (per-file: rows == imported + duplicates + skipped, machine-asserted).
- **Hypothesis:** the harness gains the domain's ground-truth end-to-end invariant;
  categorization/matching bugs become detectable without the user noticing money
  "missing".
- **Evidence:** eval cases (item 1 suite): fixture with a dropped row → exit 1;
  intact fixture → exit 0; a persona month with a mid-month transfer reconciles.

## Tier 2 — wire-proofs and gates

### 3. Mechanize the close gate (Default-FAIL)
- **Change:** a `close_month.py` script that writes `months/<M>/closed.json`
  (`{closed: true, evidence: {...}}`) **only** after validate_workspace,
  reconcile, and (new) verify-statement all exit 0 — plus a shipped
  `.claude/settings.json` PreToolUse hook denying edits to `closed.json` and to
  `reports/letter_*.md` unless the reconcile JSON for that month exists and is
  fresh. Skills change from "must report balanced: true" to "run close_month.py;
  report its output".
- **Hypothesis:** a month can no longer be reported closed unobserved; the
  convergence law ("claims are false until the environment proves them") holds.
- **Evidence:** end-to-end test: attempt to write the letter with reconcile absent
  → denied; with reconcile red → denied; green path → allowed. Red-team eval case
  ("just write the report, skip reconcile, I'm in a hurry") stays blocked.

### 4. Test the shipped mechanisms (dedup, transfer-exclusion, validator)
- **Change:** unit/golden tests in this repo for `ingest` dedup idempotence,
  transfer-never-income, `--verify-budget` exit codes, validator known-bad fixtures.
- **Hypothesis:** README's trust claims become verifiable where they're made.
- **Evidence:** tests fail on seeded mutations of each mechanism (mutation check
  once, manually), pass on main; wired into item 1's CI.

### 5. Prove the release wire
- **Change:** CI step that rebuilds `harness.zip` from `harness/` and fails if it
  differs from `dist/harness.zip` (or better: stop committing dist/, build the
  asset in the release workflow after the eval suite passes).
- **Hypothesis:** `install.py --from-release` can never deliver a zip that
  diverges from tested source.
- **Evidence:** workflow red when dist/ is stale; release job depends on suite job.

### 6. Cap the uncategorized loop; wire the welcome-back trigger
- **Change:** reconcile-month step 3 gets an iteration cap (e.g. 3 passes, then
  batch-defer remainder as `confirmed: false` — welcome-back already models this
  exit). Add a SessionStart hook that counts open months and, when >1, injects a
  one-line reminder to use welcome-back (the deterministic trigger the skill
  description currently only claims).
- **Hypothesis:** the one unbounded loop gains a non-success exit; the flagship
  ADHD scenario fires by mechanism, not luck.
- **Evidence:** eval: persona with 3 open months + session start → welcome-back
  flow chosen (N-trial); transcript case where user supplies unresolvable txns →
  loop exits at cap with deferrals logged.

## Tier 3 — memory, tone verification, economics, ramp

### 7. Memory hygiene pass
- **Change:** add `last_confirmed` / `source` dates to merchant-map and yearly-bank
  entries; validator warns on rules referencing accounts absent from accounts.md
  and on entries stale >12 months; a quarterly stale-memory step appended to
  monthly-prep or coach.
- **Evidence:** memory eval cases: known preference not re-asked; stale rule for a
  closed account flagged rather than applied.

### 8. Tone/conversation regression suite in-repo
- **Change:** port (or re-create small) persona-bot cases with the shame-free
  rubric as binary per-principle checks (first sentence forward-looking: y/n;
  overdue count mentioned: y/n; >2 questions in one message: y/n), LLM-judged,
  judge graded once against hand labels. Run on skill-file changes.
- **Evidence:** suite red when a skill edit reintroduces a shame pattern
  (seeded mutation), green on main. This finally puts the distilled rules
  (tense discipline, income-language) under regression protection.

### 9. Make the trust ramp explicit
- **Change:** a short `TRUST.md` (or strategy.md section): current rung, what is
  auto-applied today (`by=rule` categorization), promotion criteria for
  confidence-thresholded auto-categorization, and the standing scope exclusion
  (money movement: never).
- **Evidence:** escalation-correctness eval cases; promotion only after suite
  evidence per practice 02.

### 10. Minimal token/cost meter
- **Change:** record tokens/cost per ritual (transcript-derived) into a
  `finance/meta/costs.jsonl`; report cost-per-close beside the suite pass rate.
- **Evidence:** cost regression visible in CI summary; no gating initially
  (instrument, not gate — triad placement deliberate).

## Sequencing note

1 → 2 → 3 form the spine-then-gate chain and are each cheap relative to their failure
class (unverified releases; silent money drift; unobserved success claims). 4–6 are
wire-proofs riding the new CI. 7–10 are quality-of-evolution items; none should start
before item 1 exists, because none of their effects would be measurable.
