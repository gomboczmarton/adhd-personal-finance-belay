---
name: purchase-check
description: >
  "Should I buy this?" — quick consequence modeling for a purchase decision. Use when
  the user names an amount and a thing they're considering buying, or asks about
  affordability. Shows impact on this month's envelopes/targets and savings goals,
  with numbers from the scripts, judgment-free.
---

# Purchase Check

ADHD-friendly decision support: replace gut-feel and guilt with a 30-second factual
picture. The user stays the decision-maker; you are the mirror, not the parent.

## Flow

1. Get amount + what it is (one question max if not given).
2. Read `finance/months/<current>/budget.md` and the month's reconcile JSON if present
   (else run `uv run harness/scripts/reconcile.py finance --month <current>`).
3. Locate the purchase's category → its envelope/target. Present, in four short lines:
   - room left in that envelope/target this month (planned − actual so far);
   - what the purchase does to that room;
   - effect on this month's savings target if it overflows;
   - if a goal exists in `finance/strategy.md`, the goal-timeline effect in plain
     words ("pushes the car fund ~2 weeks").
4. Close with options, not advice: "fits if X", "fits next month", "trade against Y".
   The user decides; whatever they decide is fine and said to be fine.
5. If they buy: no action needed — it reconciles naturally at month end. If they
   decide against it and want credit for that, log a `decision.logged` event (a small
   win worth remembering).

## Hard rules

Numbers only from budget.md + reconcile output — never estimate mentally (D4).
Never moralize; never bring up past purchases unasked.
