---
schema_version: 1
id: p04-eva-real-shape
profile:
  age: 39
  household: couple
  neurotype: adhd-combined
  language: en
  occupation: project manager (two earners)
accounts:
  - {id: checking, type: checking, dialect: hu_csv}
income:
  type: regular
  currency: HUF
  amount: [480000, 560000]
  days: [4, 10]
  employer_desc: SALARY TRANSFER
spending:
  - {category: groceries, freq: weekly, amount: [15000, 40000], merchants: [DEMO SUPERMARKET 7, MARKET CORNER], account: checking}
  - {category: subscriptions, freq: monthly, amount: [2500, 6000], merchants: [STREAMFLIX HU, NETPLUS TELEKOM], account: checking, day: 9}
  - {category: eating_out, freq: sporadic, amount: [3000, 15000], merchants: [BISTRO ANNA, KEBAB KING], account: checking}
yearly_items:
  - {name: Home insurance, month: 12, amount: 78000, category: insurance, account: checking}
internal_transfers: none
quirks:
  - exports_fewer_months_than_filename_claims
  - envelope_system_lives_in_sub_accounts
fixtures:
  months: 9
  end_month: "2026-06"
  desc_entropy: true
  sub_accounts: [kids fund, car fund]
  savings_sweep: true
expect:
  onboarding_detects:
    - nine_month_coverage_reported
    - income_by_counterparty_despite_unique_descriptions
    - one_legged_transfers_not_expenses
    - no_yearly_proposals_on_short_history
  mode_suggestion: awareness
  invariants:
    - no_double_count
    - reconciliation_balances
---

# Éva — the real-world export shape, synthesized

I'm Éva, 39, half of a two-earner couple. My bank does everything the tidy
demo data never does: every single transaction description carries a unique
reference number, so no two rows ever look alike; our envelope system lives
in sub-accounts whose exports I never remember to download — so the harness
only ever sees one leg of every transfer; and at the end of the month
whatever survives gets swept to savings.

Also: the export I hand over says "one year" in the filename, but I actually
only have nine months of history in it. Tools that trust filenames lie to me
about my own data.

This persona is the sanitized regression twin of the 2026-07-09 private-data
simulation (evals/runs/2026-07-09-private-data-simulation/report.md): income
detection must group by counterparty (grouping by description finds nothing —
all descriptions are unique), one-legged OWN ACCOUNT transfers must be
recognized as internal via counterparty rules (not expenses, not left
uncategorized), yearly proposals must stay silent below 13 months of history,
and onboarding must report *detected* coverage, not the filename's claim.
