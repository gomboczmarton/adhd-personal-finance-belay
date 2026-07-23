---
schema_version: 1
id: p02-kim-hidden-transfers
profile:
  age: 29
  household: single
  neurotype: adhd-combined
  language: en
  occupation: freelance illustrator
accounts:
- id: main
  type: checking
  dialect: hu_csv
income:
  type: irregular
  currency: EUR
  amount: [700, 2100]
  days: [3, 17]
  employer_desc: KREATIV STUDIO INVOICE
spending:
- category: groceries
  freq: weekly
  amount: [22, 80]
  merchants: [SPAR 0087, LIDL BP]
  account: main
- category: transport
  freq: monthly
  amount: [49, 49]
  merchants: [BKK PASS]
  account: main
  day: 2
- category: eating_out
  freq: sporadic
  amount: [8, 35]
  merchants: [WOLT BUDAPEST, KIFOZDE 7]
  account: main
internal_transfers: none
quirks:
- abandons_tracking_after_3_weeks
- forgets_subscriptions
fixtures:
  months: 4
  end_month: "2026-06"
  desc_entropy: true
  sub_accounts: [celbetet]
  savings_sweep: true
expect:
  onboarding_detects: [irregular_income, one_legged_transfers_not_expenses]
  mode_suggestion: awareness
  invariants: [no_double_count, one_legged_not_income]
---

# Kim — feast, famine, and invisible savings

I'm Kim, freelance illustrator in Budapest. Some months two invoices land, some
months one, occasionally none on time — feast or famine. My bank statement is
Hungarian, semicolons and decimal commas, and every line has a random reference
number glued to it. The part that always breaks tools: I shovel money into a
"célbetét" savings pot straight from checking, and the pot has no statement of
its own — so naive tools call my savings "spending" and my own top-ups "income",
and then the numbers gaslight me. I quit every tracker after three weeks when
that happens.
