---
schema_version: 1
id: p06-noor-multibank
profile:
  age: 29
  household: single
  neurotype: adhd-inattentive
  language: en
  occupation: product designer
accounts:
  - {id: main, type: checking, dialect: revolut_csv}
  - {id: wise, type: checking, dialect: wise_csv}
  - {id: otp, type: checking, dialect: otp_xlsx}
  - {id: monzo, type: checking, dialect: monzo_csv}
income:
  type: regular
  currency: EUR
  amount: [1400, 1600]
  days: [1, 15]
  employer_desc: CLIENT PAYOUT ACME
spending:
  - {category: groceries, freq: weekly, amount: [25, 70], merchants: [FRESH MARKET, DAILY GROCER], account: main}
  - {category: subscriptions, freq: monthly, amount: [8, 20], merchants: [STREAMFLIX, MUSICLOUD], account: monzo, day: 6}
  - {category: car, freq: monthly, amount: [55, 85], merchants: [FUEL POINT], account: otp, day: 16}
  - {category: eating_out, freq: sporadic, amount: [10, 40], merchants: [NOODLE HOUSE, TACO TIME], account: wise}
  - {category: home, freq: monthly, amount: [28, 36], merchants: [STORAGE BOX RENTAL], account: wise, day: 3}
yearly_items:
  - {name: Travel insurance, month: 5, amount: 180, category: insurance, account: main}
internal_transfers: none
quirks:
  - four_banks_no_overview
  - every_app_shows_a_different_truth
fixtures:
  months: 14
  end_month: "2026-06"
expect:
  onboarding_detects:
    - income_on_1st_and_15th
    - four_accounts_reconciled_together
    - travel_insurance_due_may
  mode_suggestion: awareness
  invariants:
    - no_double_count
    - reconciliation_balances
---

# Noor — four banks, four export formats, zero overview

I'm Noor, 29, product designer. My money is *distributed*: salary-ish payouts land
in Revolut, Wise holds what's left of my traveling years, there's a legacy OTP
account that still pays for fuel, and Monzo has my subscriptions because at some
point that seemed organized. Four apps, four export formats, four different truths
about what I spend.

This persona tests the dialect-preset layer from the roadmap-B5 format survey:
Revolut CSV (ISO datetimes, State/Fee columns, no counterparty column — detection
must fall back to digit-stripped descriptions), Wise CSV (DD-MM-YYYY dates,
19 columns, Merchant as counterparty), OTP netbank XLSX (metadata preamble before
a Hungarian A–K header, native date cells), and Monzo CSV (DD/MM/YYYY, an Emoji
column carrying multi-byte UTF-8). The 14-month window also exercises the yearly
gate's boundary: Travel insurance appears in 2025-05 and 2026-05 — two different
years — so it MUST be proposed even though the history barely clears 13 months.

Everything here is synthetic; the account currencies are unified to EUR because
the round-trip mechanics (parse → dedup → categorize → reconcile across four
dialects) are what's under test, not FX.
