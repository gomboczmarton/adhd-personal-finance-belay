---
name: reconcile-month
description: >
  Close a month: ingest fresh bank exports, match internal transfers, categorize,
  compare actuals against the plan, and deliver a shame-free reconciliation report
  with the Excel view. Use at month end, when new exports land in finance/inbox/,
  or when the user asks to "reconcile" / "close the month" / "how did we do".
---

# Reconcile Month

End-of-month ritual: exports in, truth out, no judgment. The scripts do every number;
you do the meaning.

## Flow

1. **Ingest** — for each account with new files in `finance/inbox/`:
   `uv run harness/scripts/ingest.py finance <account_id> finance/inbox/<files>`.
   Overlapping exports are safe (dedup); report only "N new transactions".
2. **Match & categorize** — `uv run harness/scripts/match_transfers.py finance`, then
   `uv run harness/scripts/reconcile.py finance --month <M>` (rule pass runs inside).
   Save the JSON to `finance/months/<M>/reports/reconcile_<M>.json`.
3. **Resolve leftovers** — for each `uncategorized` hash, show the transaction and ask
   what it was; write confirmed patterns into the merchant map (they auto-categorize
   forever after), then re-run reconcile until uncategorized is empty. For ambiguous
   transfer candidates the matcher reported, confirm pairs with the user.
4. **Report** — compare actuals to `finance/months/<M>/budget.md` and tell the story
   in this order: (1) one thing that went well, (2) the plan-vs-actual picture
   (per envelope/target, biggest deviations first, each with its number), (3) new or
   unplanned items discovered, (4) at most TWO suggested adjustments for next month —
   proposals, not verdicts. Write that story (2–4 short paragraphs, `> ` prefix on
   the win line, `**bold**` for numbers, ending with ONE decision) to
   `finance/months/<M>/reports/letter_<M>.md`, then render the D13 report and Excel:
   `uv run harness/scripts/render_report.py finance <M> --data finance/months/<M>/reports/reconcile_<M>.json --letter finance/months/<M>/reports/letter_<M>.md`
   `uv run harness/scripts/export_excel.py finance <M> reconciliation --data finance/months/<M>/reports/reconcile_<M>.json`.
5. **Learn** — append anything structural the user confirmed (new recurring item →
   yearly bank or merchant map; a category consistently exploding → note it for
   monthly-prep's next draft; a strategy insight → `decision.logged` event).
6. **Validate** — `uv run harness/scripts/validate_workspace.py finance` green before
   closing. Offer monthly-prep for the next month as the natural next step.

## Tone

Overspend is information, never failure — "groceries came in 96 over; want the
envelope raised, or was this month special?" One win first, always. If the user
vanished for a while, use the welcome-back skill's catch-up flow instead of listing
everything they missed.
