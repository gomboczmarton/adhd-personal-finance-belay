---
schema_version: 1
id: p03-alex-hybrid-journey
profile:
  age: 31
  household: single
  neurotype: adhd-combined
  language: en
  occupation: software tester
accounts:
  - {id: main, type: checking, dialect: eu_csv}
  - {id: credit, type: credit_card, dialect: simple_xlsx}
income:
  type: regular
  currency: EUR
  amount: [2800, 2800]
  days: [1]
  employer_desc: ACME PAYROLL
spending:
  - {category: groceries, freq: weekly, amount: [40, 120], merchants: [DEMO SUPERMARKET 12, GREEN MARKET], account: credit}
  - {category: eating_out, freq: sporadic, amount: [12, 45], merchants: [PIZZA PRONTO, SUSHI GO], account: credit}
  - {category: subscriptions, freq: monthly, amount: [9, 15], merchants: [STREAMFLIX, CLOUDTUNES], account: credit, day: 5}
  - {category: car, freq: monthly, amount: [60, 90], merchants: [FUEL STATION A1], account: credit, day: 14}
yearly_items:
  - {name: Annual car insurance, month: 7, amount: 420, category: insurance, account: main}
internal_transfers: refill_after_spend
quirks:
  - starts_strong_then_drifts
  - groceries_always_surprise
fixtures:
  months: 24
  end_month: "2026-06"
expect:
  onboarding_detects:
    - salary_day_1
    - regular_income
    - car_insurance_due_july
    - refills_not_income
    - subscriptions_streamflix_cloudtunes
  mode_suggestion: awareness
  journey:
    adopts_envelope: groceries
    by_month: 6
  invariants:
    - no_double_count
    - reconciliation_balances
    - transfers_net_zero
---

# Alex — the journey persona (the reference user's arc, synthetic)

I'm Alex, 31, software tester, diagnosed combined-type ADHD at 28. Money isn't
tight — it's *opaque*. Salary lands on the 1st, and by the 20th I genuinely
cannot tell you where a quarter of it went. Groceries are the worst: every
single month they surprise me, and every single month I'm surprised that I'm
surprised.

I've started three budgeting apps. Week one I categorize everything, week
three I'm gone. What I never wanted: a system that greets me back with red
numbers and overdue tasks after I disappear.

This persona exists to test the D2a journey: the harness should start me
awareness-only, notice with me that groceries is the one category where
visibility isn't enough, and *propose* — not impose — trying a single envelope
for it around month six. If the coaching gets pushy or shamey, I churn.
