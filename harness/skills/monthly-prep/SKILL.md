---
name: monthly-prep
description: >
  Plan the upcoming month: draft the budget from recent history, surface yearly-bank
  items due this month (highlighted), capture month-specific priorities, verify the
  arithmetic, and export the Excel budget. Use at the start of a month, when salaries
  arrive, or when the user asks to "plan the month" / "allocate".
---

# Monthly Prep

Start-of-month ritual: turn history + the yearly bank + this month's real life into a
verified budget. Keep it under ten minutes of the user's attention.

## Flow

1. **Draft** — `uv run harness/scripts/plan_month.py finance <YYYY-MM>`; it averages
   the last 3 months and pulls due yearly-bank items into the overlay (their amounts
   already added to the right envelope/target). If income is known (salary just
   landed), pass `--income <amount>`.
2. **Present** — show the draft compactly: income, each envelope/target with its
   3-month evidence, overlay items flagged "due this month" (these render yellow in
   Excel). One line each.
3. **This month's reality** — ask ONE open question: "Anything unusual this month?"
   (trip, birthday, repair…). Add answers to the overlay (`source: user`), adjusting
   the target envelope amounts accordingly. Edit `finance/months/<M>/budget.md`.
4. **Verify** — envelope/hybrid users:
   `uv run harness/scripts/reconcile.py finance --verify-budget <M>` must report
   `balanced: true`; if not, show the exact difference and adjust with the user.
   Then `uv run harness/scripts/validate_workspace.py finance` — green required.
5. **Deliver** — `uv run harness/scripts/export_excel.py finance <M> budget`; for
   envelope users, list the transfer checklist (which envelope gets what) so they can
   execute it in their banking app in one sitting.

## Tone

Propose, don't impose; every number carries its evidence ("groceries averaged 412
over Apr–Jun"). If last month went badly, that's data, not failure — say so at most
once, briefly, and move to the plan.
