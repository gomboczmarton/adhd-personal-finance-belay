# About this workspace

Personal finance workspace, onboarded 2026-07-24. Two accounts: `main` (checking,
salary lands here) and `credit` (daily spending card, refilled from main).

## How to work with this person

- Has quit three strict-limit budgeting apps by week three — don't propose caps
  or envelopes unprompted. Mode is **awareness**: visibility first, no limits.
- Card refills from `main` to `credit` are NOT income or spending — get this
  right by default; every other tool they've tried got it wrong and it's why
  they're trying this one.
- Appreciates gentle, judgment-free surfacing of forgotten recurring charges
  (e.g. found a subscription they thought they'd cancelled) — keep flagging
  these, no commentary needed beyond the fact.
- Wants numbers sourced from the data, not guessed — they explicitly don't
  track their own spending mentally and rely on this workspace to tell them.

## Agreed at onboarding (2026-07-24)

- Categories: salary, subscriptions, car, groceries, dining_out, gifts, transfers.
- Yearly bank: car insurance (€420, July), Christmas presents (€250, December —
  not visible in transaction history, self-reported, tends to ambush them).
- Buffer goal: 3 months of real spending = €1,503.96 (3× the €501.32 full-history
  monthly average, insurance spikes included since it's real money).
- Next strategy review: 2026-10 — revisit mode/goal once a few months of
  awareness-mode data exist.

## Known gotcha

`plan_month.py`'s 3-month lookback silently includes the current, not-yet-ended
month if no export exists for it yet, deflating every drafted figure by about a
third. Check for this before trusting a draft budget when planning mid-month;
recompute from the last *complete* 3 months if it happens.
