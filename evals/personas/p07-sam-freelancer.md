---
schema_version: 1
id: p07-sam-freelancer
profile:
  age: 34
  household: single
  neurotype: adhd-inattentive
  language: en
  occupation: freelance designer
accounts:
  - {id: checking, type: checking, dialect: eu_csv}
income:
  type: irregular
  currency: EUR
  amount: [600, 3400]
  days: [3, 12, 21]
  employer_desc: CLIENT INVOICE PAYMENT
spending:
  - {category: groceries, freq: weekly, amount: [30, 90], merchants: [CORNER GROCER, DEMO SUPERMARKET 4], account: checking}
  - {category: subscriptions, freq: monthly, amount: [7, 29], merchants: [STREAMFLIX, CLOUDTUNES, FONTKIT PRO, GYMPASS, NOTELY, VPNIFY, PODPLUS], account: checking, day: 8}
  - {category: online_shopping, freq: sporadic, amount: [15, 240], merchants: [MEGASHOP ONLINE, GADGETHUB], account: checking}
  - {category: eating_out, freq: sporadic, amount: [9, 38], merchants: [BURRITO BAR, CAFE MILA], account: checking}
yearly_items:
  - {name: Professional liability insurance, month: 2, amount: 310, category: insurance, account: checking}
  - {name: Tax advisor annual fee, month: 5, amount: 250, category: professional, account: checking}
internal_transfers: none
quirks:
  - forgets_subscriptions
  - impulse_online_shopping
  - abandons_tracking_after_3_weeks
  - feast_or_famine_months
fixtures:
  months: 24
  end_month: "2026-06"
expect:
  onboarding_detects:
    - irregular_income
    - seven_subscriptions
    - liability_insurance_due_february
    - tax_advisor_due_may
  mode_suggestion: awareness
  invariants:
    - no_double_count
    - reconciliation_balances
---

# Sam — irregular income, subscription graveyard

I'm Sam, 34, freelance designer. I get paid whenever clients pay — sometimes
3.4k in a week, then six weeks of almost nothing. Every budgeting tool assumes
a salary day; I don't have one. Their "monthly budget" starts broken.

Subscriptions are my silent killer. Last year I found seven; two I had
completely forgotten existed and one I'd been paying for a tool I stopped
using in 2024. Impulse online shopping spikes when work is stressful, which
is exactly when I'm least likely to open a finance app.

This persona tests: onboarding on income that has no pattern except "it
arrives on invoice-shaped days", subscription detection, and whether the
coaching stays useful when the user vanishes for weeks (the missed-month
recovery scenario is MY scenario).
