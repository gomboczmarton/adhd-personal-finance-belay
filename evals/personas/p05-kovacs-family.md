---
schema_version: 1
id: p05-kovacs-family
profile:
  age: 42
  household: family
  members: 4
  neurotype: adhd-combined
  language: hu
  occupation: engineer + teacher (two earners)
accounts:
  - {id: main, type: checking, dialect: hu_csv}
  - {id: credit, type: credit_card, dialect: simple_xlsx}
income:
  type: regular
  currency: HUF
  amount: [520000, 680000]
  days: [3, 5]
  employer_desc: MUNKABER ATUTALAS
spending:
  - {category: groceries, freq: weekly, amount: [18000, 45000], merchants: [SPAR MAGYARORSZAG, LIDL BUDAPEST, PENNY MARKET], account: credit}
  - {category: subscriptions, freq: monthly, amount: [1990, 4990], merchants: [STREAMFLIX HU, TELEKOM OTTHON], account: credit, day: 10}
  - {category: kids, freq: monthly, amount: [15000, 60000], merchants: [DECATHLON, LIBRI KONYV, GYEREKCIPO BOLT], account: credit, day: 12}
  - {category: car, freq: weekly, amount: [12000, 22000], merchants: [MOL TOLTOALLOMAS, OMV BUDAPEST], account: credit}
  - {category: eating_out, freq: sporadic, amount: [4000, 18000], merchants: [ETTEREM CORVIN, PIZZA FORTE], account: credit}
yearly_items:
  - {name: Home insurance, month: 7, amount: 86000, category: insurance, account: main}
  - {name: Car weight tax, month: 3, amount: 49000, category: car, account: main}
  - {name: School start package, month: 9, amount: 120000, category: kids, account: main}
internal_transfers: refill_after_spend
quirks:
  - one_partner_manages_money
  - end_of_month_credit_gap_panic
  - kids_costs_always_underestimated
fixtures:
  months: 24
  end_month: "2026-06"
expect:
  onboarding_detects:
    - two_salary_days
    - dual_income
    - home_insurance_due_july
    - car_tax_due_march
    - school_package_due_september
    - refills_not_income
  mode_suggestion: envelopes
  invariants:
    - no_double_count
    - reconciliation_balances
    - transfers_net_zero
    - envelopes_sum_to_income
---

# The Kovács family — envelope household, Hungarian bank exports

We're four: two earners, two kids. Salaries land on the 3rd and the 5th.
Practically everything goes on the shared credit card; I (the money-manager
half of the marriage, ADHD and all) refill the card from our sub-accounts
whenever spending happens — so our statements are full of transfer pairs that
are NOT income, and every tool we tried counted them as income anyway.

Our bank exports come in Hungarian, Windows-1250 encoded, decimal commas,
dates like `2026.07.09.` — if the harness survives our files, it survives
most of Central Europe.

This persona tests: the full envelope-control mode (plan.md's family
scenario on synthetic data), dual salary detection, the transfer matcher at
realistic volume, encoding-chaos ingestion, and Hungarian as the configured
language over the English core (D6).
