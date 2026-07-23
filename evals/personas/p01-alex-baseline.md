---
schema_version: 1
id: p01-alex-baseline
profile:
  age: 34
  household: single
  neurotype: adhd-inattentive
  language: en
  occupation: graphic designer
accounts:
- id: main
  type: checking
  dialect: eu_csv
- id: credit
  type: credit_card
  dialect: simple_xlsx
income:
  type: regular
  currency: EUR
  amount: [2800, 2800]
  days: [1]
  employer_desc: ACME PAYROLL
spending:
- category: groceries
  freq: weekly
  amount: [28, 95]
  merchants: [DEMO SUPERMARKET 12, GREEN MARKET]
  account: credit
- category: eating_out
  freq: sporadic
  amount: [12, 45]
  merchants: [PIZZA PRONTO, SUSHI GO]
  account: credit
- category: subscriptions
  freq: monthly
  amount: [9.99, 15.99]
  merchants: [STREAMFLIX, CLOUDTUNES]
  account: main
  day: 4
yearly_items:
- name: annual car insurance
  month: 5
  amount: 420
  category: insurance
  account: main
internal_transfers: refill_after_spend
quirks:
- forgets_subscriptions
fixtures:
  months: 3
  end_month: "2026-06"
expect:
  onboarding_detects: [salary_days, refills_not_income]
  mode_suggestion: awareness
  invariants: [no_double_count, reconciliation_balances]
---

# Alex — the baseline case

I'm Alex, 34, graphic designer, single. Money mostly works: fixed salary on the
1st, rent by standing order, groceries and takeout on the credit card, and I top
the card up from checking every week or so — those top-ups are just me moving my
own money around, they're not spending and they're definitely not income. Car
insurance lands once a year in May and always surprises me. I don't want a
spreadsheet religion; I want to know where the money actually goes without
feeling judged for the sushi.
