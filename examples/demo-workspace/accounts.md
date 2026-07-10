---
schema_version: 1
accounts:
- id: main
  name: main
  type: checking
  currency: EUR
  ingestion:
    format: csv
    encoding: utf-8
    delimiter: ;
    decimal: ','
    date_format: '%Y.%m.%d'
    header_rows: 1
    columns:
      date: Booking date
      amount: Amount
      description: Details
      counterparty: Partner
- id: groceries_envelope
  name: Groceries envelope (2026-07 experiment)
  type: envelope
  currency: EUR
  parent: main
- id: credit
  name: credit
  type: credit_card
  currency: EUR
  ingestion:
    format: xlsx
    date_format: '%Y-%m-%d'
    columns:
      date: Date
      amount: Amount
      description: Merchant
---
