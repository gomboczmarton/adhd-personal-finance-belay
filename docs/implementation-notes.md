# Implementation Notes

Living build log for the ADHD Personal Finance Harness, per Phase 5 of the Fable Flow
(`docs/fable.md`). Fable maintains this file continuously during builds; Marci reviews
it at loop touchpoints. Deviations from the plan land under **Deviations** — conservative
option chosen, logged, work continues; Marci may overrule any entry.

## Context

- **Spec:** `docs/plan.md` · **Unknowns:** `docs/blindspot-pass-plan.md` ·
  **Decisions:** `docs/decisions.md` (D1–D7 + D2a) · **Protocol:** `docs/fable.md`
- **Reference repo:** `adhd-personal-finances` (read-only clone at
  `/workspace/adhd-personal-finances`). Rule: **semantics cross, data never** — no
  personal data, account names, amounts, or real CSV fragments enter this repository.
- **Spine:** the ADHD coaching skill system is the primary extraction target (D2a);
  envelope budgeting is a pluggable strategy module, mode is a journey not a switch.
- **Stack:** Python 3.11+/uv deterministic core (D4), write-only Excel (D5),
  generic column-mapping ingestion wizard for CSV+XLSX (D3), English core with user
  language as config (D6).
- **Goal:** full-lifecycle stakeholder demo on a synthetic persona (D7).

## Build order (agreed 2026-07-09)

1. **Schemas** — harness-owned data files (account config, category taxonomy, yearly
   spending bank, monthly budget, persona/life-situation config), versioned from the
   first commit; must support partial/gradual strategy adoption (D2a).
   *Opens with a branching moment: 3 wildly different data-architecture directions.*
2. **Fixture generator + first personas** — synthetic banks and exports; feeds both the
   eval system and the demo (critical path, D7).
   *Branching moment: persona profile styles.*
3. **Eval skeleton** — persona-bot + invariant checks (envelopes sum to income,
   reconciliation balances to zero, no transaction double-counted, yearly-bank items
   surface in the right month) + the journey scenario (awareness → partial envelopes).
   *Branching moment: persona-bot scripting/judging approaches.*
4. **Core scripts** — ingestion wizard engine, transfer matcher, reconciliation math —
   each built against the evals.
5. **Skills/onboarding** — the conversational shell on top; branching again at
   report/dashboard design.

## Status

- 2026-07-09 — Step 5 FULLY COMPLETE (stop condition met, D13 implemented):
  installable harness, 5 skills + coach agent, `render_report.py` shipping the D13
  report (letter shell → energy meters → statement table; awareness rows render a
  reference tick, never a fill). Lifecycle eval extended: plans June after the
  categorization pass, renders the June report, asserts meters/table/month present.
  Tier 1: 23 PASS / 0 FAIL. Sample report generated from the example workspace by the
  real scripts and published as the `d13-report-sample` artifact.
- 2026-07-09 — FIRST TIER 2 MILESTONE RUN executed and PASSED (D10's milestone
  trigger for Step 5): sam-freelancer × onboarding, live persona-bot vs the installed
  skill in a fresh sandbox, orchestrated agent↔agent, judged per evals/bot/judge.md.
  Layer 1 all-pass (mode, 7 subscriptions, both yearly items, workspace green,
  6 exchanges — persona fatigue never triggered). Layer 2: 5/5 across the rubric with
  two factual-consistency flags → backlog: (1) onboarding should state income
  patterns precisely first time (steady size vs variable count), (2) avoid
  anachronistic balance framing; plus fixture `savings_sweep` for realistic cushion
  math. Archived: evals/runs/2026-07-09-sam-onboarding/. Next frontier: fix the two
  flags, remaining Tier 2 personas/flows, stakeholder demo packaging.

## Progress

- 2026-07-09 — Go received. Step 1 branching moment: 3 data-architecture directions
  (`docs/design/schema-directions.md`); Marci chose the **Notebook + Ledger hybrid** → D8.
- 2026-07-09 — Step 1 delivered: 6 JSON Schemas (`harness/schemas/`), workspace validator
  (`harness/scripts/validate_workspace.py`, uv script with cross-file referential checks),
  synthetic example workspace (`examples/alex-workspace/finance/`), spec
  (`docs/design/schemas.md`). Verified: positive case green; negative test with 5
  injected defects — all caught (one gap found and fixed during testing: event category
  keys weren't cross-checked against the taxonomy).

- 2026-07-09 — Step 2 branching moment: persona artifact shape → Marci chose
  **eval package** (D9). Delivered: `persona.schema.json`, 3 personas
  (`evals/personas/`: alex-hybrid-journey = D2a journey arc, sam-freelancer =
  irregular income + missed-month, kovacs-family = envelope mode + Windows-1250
  Hungarian exports), deterministic fixture generator
  (`harness/scripts/generate_fixtures.py`), 120 export files + 3 ground-truth
  manifests (`evals/fixtures/`, committed deliberately). Verified: byte-identical
  regeneration, transfer legs net to zero (192/persona), yearly items in exactly
  their due months, irregular income has zero-income months.

- 2026-07-09 — Step 3 branching moment: eval drive → Marci chose **two tiers** (D10).
  Delivered: `evals/run_evals.py` (Tier 1 runner: 11 PASS / 0 FAIL / 17 SKIP with
  named unlock conditions), Tier 2 specs (`evals/bot/persona-bot.md`, `judge.md`),
  `docs/design/eval-system.md` incl. the Dynamic Workflows answer (plan.md item 4).

- 2026-07-09 — Step 4 delivered against the Step 3 stop criterion (Tier 1 fully green):
  `harness/scripts/ingest.py` (mapping-config engine, content-hash identity, dedup),
  `match_transfers.py` (amount+date-window pairing, same-day first, idempotent),
  `reconcile.py` (rule categorization + Decimal-exact monthly totals +
  `--verify-budget`). The 4 gated eval checks implemented in `run_evals.py` via a
  cached per-persona pipeline (ingest twice → match → reconcile). Adversarial
  spot-checks beyond the suite: partial-overlap combined export dedups to 0 new;
  matcher never pairs same-account, is idempotent, and reports leftover ambiguous
  candidates.

- 2026-07-09 — Step 5 delivered (D11 copy installer, D12 data-first onboarding):
  5 skills (`harness/skills/`: onboarding, monthly-prep, reconcile-month,
  purchase-check, welcome-back), `finance-coach` subagent, `install.py`, and 3 new
  scripts (`detect_patterns.py` — one real bug found and fixed via manual verification:
  yearly candidates were gated behind a ≥3-months condition they can never meet;
  `plan_month.py`; `export_excel.py` — yellow overlay highlighting verified in the
  actual workbook). Root README added. Lifecycle eval asserts install manifest,
  pattern rediscovery vs persona ground truth, July overlay contents, envelope
  balance, Excel outputs, and final workspace validity.

- 2026-07-10 — Next-steps step 1 delivered (eval-first per iron rule #1): new
  regression persona `eva-real-shape` — the sanitized synthetic twin of the
  2026-07-09 private-data simulation (9 months history, `desc_entropy` unique refs
  in every description, `sub_accounts` one-legged transfers, `savings_sweep`);
  fixture generator gained those three features (RNG-gated: existing personas'
  CSVs byte-identical). Suite went red exactly on the four real-data findings,
  then green: `detect_patterns.py` groups by counterparty (fallback digit-stripped
  description), reports detected `coverage` (months present vs span), yearly
  proposals gated behind ≥13 months + same month-of-year across years;
  `reconcile.py` merchant rules gained a `field: counterparty` selector (how
  one-legged own-account transfers are recognized). 29 PASS / 0 FAIL.

- 2026-07-10 — Next-steps step 2 delivered: onboarding skill gained four judged-in
  fixes — (1) income language: SIZE vs COUNT as separate facts, first time; (2) tense
  discipline: no past month narrated from a later balance; (3) mode recommendation:
  awareness is the onboarding default, envelopes/hybrid only on data evidence of
  existing envelope practice (buffer goals are awareness goals; D2a journey timing);
  (4) brevity by design. Also: detected-coverage reporting (real-data finding #4) and
  the suggest_mapping preset step wired into stages 4/2. THREE archived Tier 2 runs
  document the loop: run 2 (2026-07-10-sam-onboarding-2) verified flags 1–2 fixed but
  FAILED Layer 1 on a new finding (harness steered sam to hybrid); skill fixed; run 3
  (2026-07-10-sam-onboarding-3) PASSED everything — Layer 1 all-green, Layer 2 4×5/5,
  all four historical flags FIXED, zero new flags. The eval system caught a real
  product-philosophy defect and drove its fix within a day.

- 2026-07-10 — Next-steps step 5 delivered (roadmap B5): public bank-format survey
  archived at `docs/research/bank-formats.md` (Wise/Revolut/N26/Monzo CSV, camt.053,
  OFX, QIF, OTP/K&H/Raiffeisen-HU/MagNet/Gránit). New `suggest_mapping.py` (preset
  layer of the D3 wizard: sniffs encoding/delimiter/header, matches exact header
  signatures, falls back to a sniffed skeleton). Fixture generator + eval runner
  gained authentic-layout synthetic dialects `revolut_csv`, `wise_csv`, `monzo_csv`,
  `n26_csv`, `otp_xlsx` (preamble + Hungarian A–K header; `ingest.py` xlsx path now
  honors `header_rows`). New persona `noor-multibank` (4 banks, 4 formats, 14-month
  window exercising the yearly gate's two-different-years boundary). New Tier 1 check
  `mapping_presets_detected`. Suite: 40 PASS / 0 FAIL.

- 2026-07-10 — Next-steps step 3 delivered: the full Tier 2 matrix, five persona-bot
  runs, ALL PASSED, archived with judged verdicts under `evals/runs/`:
  welcome-back × sam 5/5/5/5 (3-month gap, 2 turns, zombie truth);
  monthly-prep × kovacs 5/5/5/5 (entirely Hungarian, D6; balanced 0 Ft; overlay
  flagged the July-due insurance; swim camp + vacation envelope incorporated);
  purchase-check × sam 5/4/5/5 (balance challenge answered from the raw export);
  reconcile-month × alex 5/5/4/5 (win-first under expectation subversion; the
  auto-draft override disclosure — "no quiet goalpost-moving" — landed as the
  retention moment); journey × alex (D2a, finance-coach) 5/5/4/5 (one envelope
  proposed at month 6 with honest anxiety-container framing — June groceries were
  UNDER; adoption recorded: strategy.adopted + envelope_adoption + account).
  Judge improvement notes queued as future skill changes (purchase-check: explain
  named-buffer vs account balance; coach: confirm-then-record on conditional
  consent; both need their own Tier 2 coverage when made).

- 2026-07-10 — Next-steps step 6 delivered: `demo/` kit — pre-staged snapshot repo
  (installed harness + Alex six months in: June closed with the D13 report, July
  planned with yellow yearly item + user overlay, envelope experiment adopted; July
  exports staged in inbox from a deterministic fixture extension, overlap verified
  byte-identical), `script.md` (6 beats with expected outputs), `talk-track.md`
  (5 minutes), `README.md` (cold-run rules). Cold-run twice: PASS; the first cold
  run caught a real script defect (--verify-budget on an awareness budget) — fixed
  and noted in the script itself.

## Deviations

- 2026-07-09 · **Repo layout** wasn't an agreed decision; needed one to place files.
  Conservative pick: `harness/` (shippable part: schemas, scripts, later skills),
  `examples/` (synthetic workspaces), `docs/design/` (specs). Easy to rename later —
  open for Marci's review.
- 2026-07-09 · **Amount representation**: schemas use plain JSON numbers + ISO currency
  field (not minor-units integers). Conservative for HUF/EUR readability and matches
  bank exports; scripts must use Decimal when summing (noted for Step 4) — open for
  Marci's review.
- 2026-07-09 · **Fixtures committed to git** (not gitignored): deterministic and
  regenerable, but committing makes generator changes reviewable as diffs and the repo
  self-contained. ~120 small files. Open for Marci's review.
- 2026-07-09 · **Checking-account balances grow unrealistically** in fixtures (income
  minus card refills accumulates, no savings sweep). Harmless for ingestion/matching
  evals; a `savings_sweep` fixture feature can be added when a persona needs it. Logged,
  kept conservative (no speculative feature).
- 2026-07-09 · **Transaction identity includes a per-file sequence number** for rows
  identical in (date, amount, desc): two real same-day equal purchases both survive,
  while re-imported overlapping exports dedup exactly. Consequence: if a bank export
  ever lists the same two identical rows in a different ORDER across files, dedup still
  holds (hash set), but a partial export missing one of two identical twins would dedup
  the wrong twin — harmless (they are indistinguishable by content). Open for review.
- 2026-07-09 · **Reconciliation vs manifest tolerance = 0.011**: the fixture generator
  accumulates ground truth with per-step float rounding, while reconcile sums in exact
  Decimal; the two can legitimately differ by <0.01. The harness itself is
  Decimal-exact; the tolerance exists only in the eval comparison. Open for review.
- 2026-07-09 · **Matcher ambiguity policy**: with several equal-amount candidates in
  the window, it pairs greedily (same-day first) and reports remaining candidates in
  `unmatched_candidates` rather than guessing further — the agent asks the user about
  leftovers (conservative). Open for review.
- 2026-07-09 · **Hooks deferred**: plan.md lists hooks among output artifacts, but no
  v1 flow needs one (skills + agent cover the lifecycle; schedules can come via
  Routines/cron later). Conservative: no speculative hook shipped. Open for review.
- 2026-07-09 · **plan_month drafting rule** is a plain 3-month average per category
  (yearly spikes land via the overlay instead of polluting averages). Smarter
  seasonality can replace it behind the same CLI without touching skills. Open for
  review.
- 2026-07-10 · **camt.053 deferred**: the survey ranks it #4, but it needs an XML
  format in the ingestion engine (not just a preset) — deferred to keep step 5 inside
  the preset layer; the wizard remains the path for camt-only banks. Open for review.
- 2026-07-10 · **OTP legacy CSV preset not shipped**: its dialect (ISO-8859-2, `;`,
  comma decimal) rests on a single credible public source; per rule #2 posture it
  needs verification against a real export outside this repo first. The current
  A–K XLSX preset (well-documented via ofxstatement-otp) IS shipped. Open for review.
- 2026-07-10 · **suggest_mapping skill line added after the sam-onboarding-3 session
  started**: the run's sandbox skill lacks the one-line stage-2 preset instruction
  (everything else identical). The mapping-stage conversation is Tier 2-covered by
  the archived runs; the preset path itself is deterministic (Tier 1
  `mapping_presets_detected`). Next onboarding-flow Tier 2 run picks it up. Open for
  review.
- 2026-07-10 · **Public-repo license not chosen** — a Marci decision (MIT vs
  Apache-2.0 vs none). The product repo currently ships without a LICENSE file
  (all rights reserved by default). Open for review.
- 2026-07-10 · **Git proxy blocks tag pushes** in the remote session (branch pushes
  fine). v0.1.0 tag exists locally in the product clone; the GitHub Release UI
  creates the tag on publish, so no history surgery needed. Open for review.
