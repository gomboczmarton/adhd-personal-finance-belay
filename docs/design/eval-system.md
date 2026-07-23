# Eval System (Step 3) — Design

Two tiers per **D10**. The gnuplot-loop from plan.md §8 lives in Tier 1: iterate on a
component until the suite converges to green, then move on.

## Tier 1 — deterministic, every change

`uv run evals/run_evals.py` — no LLM, seconds to run, exit 1 on any FAIL.

- **Always-on fixture/workspace sanity**: fixtures present and complete, transfer legs
  net to zero, yearly items in exactly their due months, manifest consistency,
  (via `validate_workspace.py`) schema + referential integrity.
- **Component-gated invariants** from each persona's `expect.invariants`: they SKIP
  while the harness component is missing and flip to FAIL the moment the component file
  appears without an implemented check — a deliberate TDD-red handover. Step 4 is done
  when these are green:
  | Invariant | Gated on | Meaning |
  |---|---|---|
  | `no_double_count` | `harness/scripts/ingest.py` | importing overlapping exports twice yields each txn exactly once |
  | `transfers_matched` | `harness/scripts/match_transfers.py` | all manifest transfer pairs found, zero false pairs |
  | `reconciliation_balances` | `harness/scripts/reconcile.py` | every txn categorized exactly once; totals equal manifest ground truth |
  | `envelopes_sum_to_income` | `harness/scripts/reconcile.py` | allocations + savings = income in envelope mode |

## Tier 2 — persona-bot, milestones only

Specs in `evals/bot/`. An LLM subagent roleplays the persona (story = voice, quirks =
behavioral directives, never sees `expect:`) through onboarding/monthly flows in a
sandboxed workspace seeded with that persona's fixtures. Judging is artifacts-first:
Layer 1 mechanical (produced workspace validates; `expect.onboarding_detects`,
`mode_suggestion` resolved by scripts; Tier 1 re-run), Layer 2 an LLM rubric only for
what scripts can't measure (shame-free tone, propose-don't-impose, question economy,
robustness to quirk friction) with mandatory transcript evidence.

Cost posture: Tier 2 at milestones (component done, pre-demo, pre-release);
Tier 1 always.

## Dynamic Workflows — plan.md item 4, answered

Tier 2 is where Claude Code's orchestration earns its keep: fan out persona × flow
sessions in parallel, then judge each as it completes (pipeline, no barrier), loop
until all verdicts pass — the multi-agent version of the gnuplot convergence loop.
Tier 1 needs none of it, and the user-facing harness must not depend on it (any vanilla
Claude Code must run the harness).

## Adding a scenario

Add one persona file → generator makes its fixtures → runner picks it up by itself.
The eval matrix grows by files, not code (D9).
