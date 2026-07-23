# Bank transaction-export format survey (roadmap B5)

Research for ingestion dialect presets + eval fixtures for the ADHD Personal Finance Harness.
Date: 2026-07-10. All information from public documentation, developer docs, and open-source
parsers/fixtures — no personal data. Where a field could not be confirmed from a public source
it is marked "undocumented". Confidence notes are inline.

Method note: the session's egress proxy only allows GitHub and a few registries, so most
evidence comes from (a) GitHub code search over open-source importers and their committed
synthetic fixtures, and (b) web-search result summaries of official help pages (URLs cited even
where the page body could not be fetched directly).

---

### Wise (TransferWise) CSV statement export
- container: csv (one file per currency balance/jar; filename pattern `statement_<id>_<CCY>_<date>_<date>.csv`)
- encoding UTF-8 (BOM sometimes present — parsers strip it); delimiter `,`; decimal `.`; thousands: none
- date format(s): observed both `DD-MM-YYYY` (classic export, e.g. `23-01-2022`) and `YYYY-MM-DD`
  (newer exports / API-generated statements). Presets should sniff which one is present.
- header: 1 header row, no preamble. Columns in order:
  `TransferWise ID, Date, Amount, Currency, Description, Payment Reference, Running Balance,
  Exchange From, Exchange To, Exchange Rate, Payer Name, Payee Name, Payee Account Number,
  Merchant, Card Last Four Digits, Card Holder Full Name, Attachment, Note, Total fees`
  (some newer exports append `Exchange To Amount`).
- amount sign: single signed `Amount` column (negative = money out); no debit/credit split.
  `Total fees` is a separate positive column and is already included in `Amount`.
- counterparty: `Payer Name` / `Payee Name` / `Merchant` (mutually sparse depending on type);
  balance: `Running Balance` (after the transaction); transaction id: `TransferWise ID`
  (e.g. `CARD-123456789`, `TRANSFER-...`, `BALANCE-...` — type prefix is informative).
- quirks: one CSV per currency, so a multi-currency account yields several files; FX conversions
  appear with `Exchange From/To/Rate` filled; card rows carry `Card Last Four Digits`; many
  columns are usually empty; Wise also offers an alternative "accounting" CSV with a different
  schema — the preset should key on the exact header row above.
- sources:
  https://wise.com/help/articles/2736049/how-do-i-download-a-statement (official download flow);
  https://github.com/ammar-qazi/HisaabFlow/blob/main/configs/wise.conf (full expected header, BOM note, filename pattern);
  https://github.com/BananaAccounting/Universal/blob/master/extensions/import/wise/ch.banana.uni.import.wise.js (header + synthetic sample rows with DD-MM-YYYY dates);
  https://github.com/egh/ledger-autosync/blob/master/examples/plugins/wise.py; https://github.com/useVenice/venice/blob/main/connectors/connector-spreadsheet/formats/format-wise.ts

### Revolut CSV statement export (personal account)
- container: csv
- encoding UTF-8; delimiter `,` (tab-separated variants observed by some importers — sniff);
  decimal `.`; thousands: none
- date format(s): `YYYY-MM-DD HH:MM:SS` in both date columns
- header: 1 header row, no preamble. Columns in order:
  `Type, Product, Started Date, Completed Date, Description, Amount, Fee, Currency, State, Balance`
- amount sign: single signed `Amount` (negative = money out); `Fee` is a separate column
  (positive number, already reflected in `Balance` but NOT included in `Amount` — net effect is
  `Amount − Fee`; importers commonly subtract it). No debit/credit split.
- counterparty: only via free-text `Description`; balance: `Balance` (running, after transaction);
  transaction id: none in personal CSV export (dedup must be synthesized from date+amount+desc).
- quirks: `State` ∈ {COMPLETED, PENDING, REVERTED, FAILED/DECLINED} — REVERTED/PENDING rows have
  empty `Balance` and should be skipped or held; `Type` values include CARD_PAYMENT, TRANSFER,
  TOPUP, EXCHANGE, ATM, FEE; `Product` distinguishes Current/Savings/etc.; internal
  pocket/vault moves appear as rows (analogous to the CelBetet internal-transfer problem);
  one file can mix currencies (Currency column varies per row). Business "expenses" CSV is a
  completely different, much wider schema — do not confuse.
- sources:
  https://github.com/pswierblewski/eye-budget/blob/main/backend/src/services/revolut_csv_parser.py (header list);
  https://github.com/vendelle/financial-tracker/blob/main/lib/services/import/revolut_csv_parser.dart (header incl. Balance);
  https://github.com/lamberttraccard/budget-app (`_bmad-output/implementation-artifacts/2-2-revolut-csv-parser.md`: comma-delimited, `YYYY-MM-DD HH:MM:SS`, dot-decimal);
  https://github.com/egh/ledger-autosync/blob/master/examples/plugins/revolut.py;
  https://community.revolut.com/t/statement-export-csv-date-formatting/75661 (date formatting discussion);
  https://help.revolut.com/en-US/business/help/managing-my-business/expenses/introduction-to-expenses/what-information-does-the-expenses-csv-export-contain/ (business variant, for disambiguation)

### N26 CSV export
- container: csv
- encoding UTF-8; delimiter `,`; string fields double-quoted; decimal `.`; thousands: none
- date format(s): `YYYY-MM-DD`
- header: 1 header row, no preamble.
  Current format (≈2023/2024 onwards, "N26 CSV (2025+)" in importer signatures):
  `"Booking Date","Value Date","Partner Name","Partner Iban",Type,"Payment Reference",
  "Account Name","Amount (EUR)","Original Amount","Original Currency","Exchange Rate"`
  Legacy format (pre-2023): `Date, Payee, Account number, Transaction type, Payment reference,
  Amount (EUR), Amount (Foreign Currency), Type Foreign Currency, Exchange Rate` (some vintages
  also had `Category`).
- amount sign: single signed `Amount (EUR)` (negative = money out); no debit/credit split.
  `Original Amount`/`Original Currency` filled only for FX card transactions ("Presentment" rows).
- counterparty: `Partner Name` + `Partner Iban`; balance: none; transaction id: none
  (dedup must be synthesized).
- quirks: account is EUR-denominated so amount column is hard-named `Amount (EUR)`; `Type` values
  include Credit Transfer, Debit Transfer, Presentment (card), Direct Debit, Fee; "Spaces"
  (sub-account) moves appear via `Account Name`; community reports of exports missing records
  for some date ranges — validate row counts against date span.
- sources:
  https://github.com/c-vigo/beancount-importers/blob/main/beancount_importers/importers/n26.py (exact quoted header);
  https://github.com/xilefmusics/moneyapp/blob/main/backend/src/import/n26new.rs (header + synthetic sample);
  https://github.com/ahsan3274/financial-agent/blob/main/data/transactions/N26.csv (synthetic fixture incl. Presentment/Fee rows);
  https://github.com/leolabs/you-need-a-parser/blob/master/packages/ynap-parsers/src/de/n26/n26.ts (legacy + new fields);
  https://github.com/danielvsantos/bliss/blob/main/prisma/seed.js ("N26 CSV (2025+)" signature, dateFormat YYYY-MM-DD);
  https://blog.lent.ink/2024/n26-export-csv-broken/ (missing-records defect report)

### Monzo CSV export
- container: csv
- encoding UTF-8; delimiter `,`; decimal `.`; thousands: none
- date format(s): `Date` = `DD/MM/YYYY` (not zero-padded consistently, e.g. `10/7/2022`);
  `Time` = `HH:MM:SS` in a separate column (an Android-app time formatting bug was reported
  historically — treat time as best-effort)
- header: 1 header row, no preamble. Columns in order (current personal export):
  `Transaction ID, Date, Time, Type, Name, Emoji, Category, Amount, Currency, Local amount,
  Local currency, Notes and #tags, Address, Receipt, Description, Category split, Money Out,
  Money In` — Business (and newer personal) exports append `Balance, Balance currency`.
- amount sign: signed `Amount` (negative = out) AND redundant `Money Out` (negative) /
  `Money In` (positive) columns; prefer `Amount`.
- counterparty: `Name` (cleaned merchant) + raw `Description`; balance: `Balance` only in
  business/newer exports; transaction id: `Transaction ID` (`tx_...` / `mm_...` — stable, ideal dedup key).
- quirks: `Emoji` column may contain multi-byte emoji (UTF-8 handling test case!);
  `Local amount`/`Local currency` differ from `Amount`/`Currency` for foreign card payments;
  `Category split` holds multi-category splits; pot transfers appear as `Type` = "Pot transfer";
  0.00-amount "Active card check" rows exist; column set has drifted over the years
  (older exports: `id, created, amount, ...`) — key preset on header row.
- sources:
  https://github.com/simonmichael/hledger/blob/master/examples/csv/banking/monzo.csv.rules (full 20-column header + sample row, %d/%m/%Y);
  https://github.com/its-the-vibe/stmt2redis/blob/main/internal/parser/monzo.go (18-column header);
  https://github.com/morrisondavid/finance-app/blob/main/server/parsers/monzo.ts (20-column joint-account header);
  https://github.com/bilmak/mini_projects/blob/main/monzo_july_sample.csv (synthetic fixture);
  https://community.monzo.com/t/we-ve-added-a-running-balance-to-monzo-business-csv-exports/164885 (Balance column announcement);
  https://community.monzo.com/t/bug-incorrectly-formatted-transaction-time-in-csv-export-from-the-android-app/28341

### ISO 20022 camt.053 (bank-to-customer statement)
- container: xml (`Document/BkToCstmrStmt`, namespace `urn:iso:std:iso:20022:tech:xsd:camt.053.001.NN`, v02 and v08 most deployed)
- encoding: UTF-8 XML; decimal `.` fixed by schema; dates ISO 8601 (`YYYY-MM-DD`)
- structure relevant to an importer — one `Stmt` per account per statement, containing:
  - `Stmt/Acct/Id/IBAN` — account; `Stmt/Bal` — opening (`OPBD`) / closing (`CLBD`) balances
    (`Bal/Amt @Ccy` + `Bal/CdtDbtInd`) → strong integrity check for an append-only ledger
  - repeated `Stmt/Ntry` (one booked entry each):
    - `Ntry/Amt @Ccy` — always positive decimal; currency in attribute
    - `Ntry/CdtDbtInd` — `CRDT` | `DBIT` → sign comes from here, never from Amt
    - `Ntry/RvslInd` — true marks a reversal (flip semantics)
    - `Ntry/Sts` — `BOOK` (booked) | `PDNG` — importers should take BOOK only
    - `Ntry/BookgDt/Dt` and `Ntry/ValDt/Dt` — booking vs value date
    - `Ntry/AcctSvcrRef` — bank's entry reference (best dedup id at entry level)
    - `Ntry/BkTxCd` — coded transaction type (domain/family/subfamily)
    - `Ntry/NtryDtls/TxDtls` (0..n — batch entries can contain many transactions):
      `TxDtls/Refs/EndToEndId` (payer's reference), `TxDtls/AmtDtls`,
      `TxDtls/RltdPties/Dbtr|Cdtr/Nm` (+ `DbtrAcct|CdtrAcct/Id/IBAN`) — counterparty,
      `TxDtls/RmtInf/Ustrd` (free-text memo, ≈ "Közlemény") or `RmtInf/Strd`
- amount sign convention: unsigned amount + CdtDbtInd (see above); separate debit/credit: n/a
- counterparty: RltdPties; balance: OPBD/CLBD `Bal` blocks; transaction id: AcctSvcrRef / EndToEndId
- quirks: one entry may aggregate a batch (must descend into TxDtls); banks differ in how much
  of NtryDtls they populate (bank "implementation guidelines" PDFs per bank); Hungarian corporate
  channels (Electra at K&H/Gránit, OTP Electra) can emit camt.053 or close relatives.
- sources:
  https://www.sepaforcorporates.com/swift-for-corporates/a-practical-guide-to-the-bank-statement-camt-053-format/;
  https://validatefin.com/en/blog/camt053-bank-statement (field-by-field reading guide);
  https://www.betaalvereniging.nl/wp-content/uploads/2026/03/IG-Bank-to-Customer-Statement-CAMT-053-v2.0.pdf (implementation guideline);
  https://images.em.bankofamerica.com/GTS/ISO_20022/ReferenceGuideBanktoCustomerStatement(CAMT.053).pdf

### OFX (Open Financial Exchange) — STMTTRN
- container: sgml (OFX 1.x: SGML-ish, no closing tags, plain-text `OFXHEADER` preamble) or
  xml (OFX 2.x: proper XML with `<?xml?>` declaration). `.qfx`/`.qbo` are branded OFX.
- encoding: declared in the header (`CHARSET:1252` / `ENCODING:USASCII|UTF-8` in 1.x; XML decl in 2.x);
  decimal `.` (spec) but sloppy producers use `,` — tolerate; thousands: none
- date format: `YYYYMMDD` or `YYYYMMDDHHMMSS[.mmm][gmt offset[:tz]]`, e.g. `20260710120000[+2:CEST]`
- structure: `OFX/BANKMSGSRSV1/STMTTRNRS/STMTRS` → `CURDEF`, `BANKACCTFROM/ACCTID`,
  `BANKTRANLIST/DTSTART,DTEND` then repeated `STMTTRN`:
  - `TRNTYPE` — CREDIT, DEBIT, INT, DIV, FEE, SRVCHG, DEP, ATM, POS, XFER, CHECK, PAYMENT,
    CASH, DIRECTDEP, DIRECTDEBIT, REPEATPMT, OTHER
  - `DTPOSTED` (required), `TRNAMT` (required, signed from the customer's perspective,
    decimal point), `FITID` (required — bank-unique transaction id, the canonical dedup key)
  - optional: `NAME` (max 32 chars) or `PAYEE` aggregate, `MEMO` (max 255), `CHECKNUM`, `REFNUM`,
    `SIC`, `CURRENCY`/`ORIGCURRENCY`
  - `LEDGERBAL/BALAMT+DTASOF` after the list — closing balance check
- amount sign: signed TRNAMT (negative = money out); no debit/credit split
- counterparty: NAME/PAYEE; balance: LEDGERBAL (statement-level, not per row); id: FITID
- quirks: banks notoriously swap NAME↔MEMO content; 1.x needs a lenient SGML parser (no end
  tags); header key/value block before the `<OFX>` root must be skipped.
- sources:
  https://www.xml.coverpages.org/OFEXFIN2.html (OFX message-set spec);
  https://financeconvert.com/what-is-ofx-format (field summary incl. required/optional and length limits);
  https://www.online.fnb.co.za/rhelp_0_15/OBE_SA_Downloads/assets/docs/Statement_Type_-_OFX.pdf (bank file-layout spec);
  https://github.com/ftomassetti/ofx-java/blob/master/src/test/resources/example.ofx (example file);
  https://bugs.launchpad.net/homebank/+bug/2092778 (NAME/MEMO swap in the wild)

### QIF — transaction record format
- container: text (line-oriented records)
- encoding: unspecified by the format (ASCII/locale — sniff); no delimiter; decimal `.` with
  optional `,` thousands separators inside amounts (e.g. `-1,000.00`)
- date format(s): `M/D/YY` or `M/D/YYYY`, sometimes space-padded (`6/ 1/94`); post-2000 Quicken
  wrote `D'YY` (e.g. `1/1'02`); European producers emit `DD/MM/YYYY` — AMBIGUOUS, needs user
  confirmation or heuristics. This is QIF's biggest ingestion hazard.
- header: file starts with `!Type:Bank` (or `!Type:CCard`, `!Type:Cash`, `!Type:Oth A/L`,
  `!Type:Invst`, `!Account` blocks). No column names — single-letter field codes, one per line:
  `D` date, `T` amount (also `U` in some producers), `C` cleared status, `N` check/ref number,
  `P` payee, `M` memo, `A` address (up to 5 lines), `L` category or [transfer account],
  `S`/`E`/`$` split category/memo/amount (repeatable, must stay adjacent), `^` end of record.
- amount sign: signed `T` amount (negative = money out); no debit/credit split
- counterparty: `P`; balance: none; transaction id: none (dedup must be synthesized)
- quirks: fields optional and order-free; `L` uses `[Account Name]` brackets for transfers;
  no currency anywhere (single-currency assumption); Raiffeisen HU is a live QIF producer and
  swaps P/M content vs. convention (see YAFFA profile below).
- sources:
  https://en.wikipedia.org/wiki/Quicken_Interchange_Format;
  https://github.com/jemmyw/Qif/blob/master/QIF_references (collected format references);
  https://stuff.mit.edu/afs/sipb/project/gnucash-test/src/gnucash/src/import-export/qif-import/file-format.txt (GnuCash notes);
  https://www.w3.org/2000/10/swap/pim/qif-doc/QIF-doc.htm

---

## Hungarian banks beyond Erste

Public documentation is thin; the best sources are open-source importers by Hungarian devs and
accounting-software import manuals. Erste itself is already handled in-repo (George CSV/XLSX,
fields like `Könyvelés dátuma`, `Összeg`, `Partner név` per the reference project's docs).

### OTP Bank — netbank XLSX export (current, post-2026-June)
- container: xlsx (sheet name `Tranzakciók`)
- encoding n/a (xlsx); delimiter n/a; decimal: native numeric cells; thousands n/a
- date format(s): date cells are either strings or native datetime cells (`Tranzakció időpontja`
  is a datetime, `Könyvelés dátuma` a date) — parse both
- header: metadata preamble rows 1–~14 (title `Számlatörténet`, account numbers, query date
  range) before the transaction table. Columns A–K:
  `Számlaszám, Ellenoldali számlaszám, Ellenoldali név, Forgalom típusa, Közlemény,
  Tranzakció kategória, Banki azonosító, Tranzakció időpontja, Könyvelés dátuma, Összeg, Devizanem`
- amount sign: signed `Összeg` (negative = out); no debit/credit split
- counterparty: `Ellenoldali név` + `Ellenoldali számlaszám`; balance: none in export;
  transaction id: `Banki azonosító` (used as OFX FITID by the plugin — good dedup key)
- quirks: currency defaults to HUF when column K missing; hidden rows exist and should be
  skipped; format changed in June 2026 — the legacy XLSX (data from row 2, columns A–L:
  transaction datetime, booking date, description, in/out indicator, partner name, partner
  account, OTP category, memo, account name, account number, amount, currency; account id in
  cell D8) still circulates. OTP additionally offers a legacy CSV ("hagyományos OTP formátum",
  official template `CSV_v01.xlsx` on otpbank.hu) and an authenticated XML statement; a
  third-party research doc records the CSV as ISO-8859-2, `;`-delimited, double-quoted,
  comma-decimal with header `"Tranzakció dátuma";"Értéknap";"Összeg";"Pénznem";"Partner név";
  "Partner számlaszám";"Közlemény";…` (single credible source — verify against a real export
  outside this repo before shipping a preset).
- sources:
  https://github.com/gyp/ofxstatement-otp (CLAUDE.md + src/ofxstatement_otp/otp.py, otp_legacy.py — column layouts, preamble, FITID);
  https://www.otpbank.hu/static/portal/sw/file/CSV_v01.xlsx (official CSV template);
  https://www.otpbank.hu/static/portal/sw/file/OTPdirekt_Electra_Terminal_interfesz_leiras_2_1.pdf (Electra export/import interface spec);
  https://github.com/siposzoltan03/condo-manager/blob/main/docs/plans/2026-04-28-banking-integrations-research.md (CSV dialect notes: ISO-8859-2, `;`, comma decimal)

### K&H Bank — e-bank CSV export
- container: csv (e-bank also offers XLSX; corporate Electra has its own fixed formats, PDF-documented)
- encoding: undocumented (UTF-8 reported); delimiter: TAB (`excel-tab` dialect per the only
  open-source consumer); decimal: undocumented (HU-locale comma likely); thousands: undocumented
- date format(s): `YYYY.MM.DD` (`%Y.%m.%d`)
- header: 1 header row; known columns (lowercase Hungarian):
  `könyvelés dátuma, típus, partner elnevezése, összeg, összeg devizaneme, könyvelési számla, közlemény`
  (order not fully confirmed; additional columns likely)
- amount sign: signed `összeg` presumed; separate debit/credit: undocumented
- counterparty: `partner elnevezése`; balance: undocumented; transaction id: undocumented
- quirks: tab-delimited despite .csv extension — delimiter sniffing mandatory; Electra channel
  formats are documented in an official PDF ("Electra export_import formátum leírása") which is
  the authoritative reference for the corporate variant.
- sources:
  https://github.com/abalage/whatsthedamage (K&H-tested analyzer; config.yml.default has dialect/columns/date format);
  https://www.kh.hu/documents/20184/148525/Electra+export_import+form%C3%A1tum+le%C3%ADr%C3%A1sa.pdf (official Electra format spec);
  https://supportathena.zendesk.com/hc/hu-hu/articles/22919380290833-K-H-Bank-CSV;
  https://www.trustwise.hu/kh-bankszamla-csv-letoltes (download walkthrough)

### Raiffeisen Bank Hungary — myRaiffeisen CSV export
- container: csv (QIF also offered)
- encoding: undocumented; delimiter `;`; decimal `,`; thousands: space
- date format(s): `YYYY.MM.DD.` (`Y.m.d.` with trailing dot)
- header: 1 header row; publicly confirmed columns (full order undocumented):
  `Értéknap, Összeg, Típus, Közlemény/1, Közlemény/2, Közlemény/3`
- amount sign: signed `Összeg` (negative = out); no debit/credit split
- counterparty: no dedicated column — embedded in `Közlemény/1–3` free text (the YAFFA profile
  ships regexes to pull payee out of card-payment/transfer/ATM memo lines); balance:
  undocumented; transaction id: undocumented
- quirks: three memo columns must be concatenated; the bank's QIF export swaps payee (`P`) and
  memo (`M`) relative to convention.
- sources:
  https://github.com/kantorge/yaffa/blob/main/app/Services/Import/SystemFileImportProfileRegistry.php ("Raiffeisen Hungary v1" CSV profile + QIF swap profile)

### MagNet Bank — NetBank export
- container: xml (documented "MagNet XML formátum"); XLS/CSV export exists per accounting-software
  import lists but its column structure is publicly undocumented
- encoding, delimiter, decimal, thousands: undocumented
- date format(s): undocumented
- header/columns: undocumented (NetBank user manual PDF is the closest public reference)
- amount sign / debit-credit, counterparty, balance, transaction id: undocumented
- quirks: accounting tools (Novitax, Infotéka Kontír) list "MagNet XML" as an importable
  statement format, so the XML is the stable interchange surface, not the CSV.
- sources:
  https://www.magnetbank.hu/sw/static/file/NetBankFelhasznaloikezikonyv_2024_12_12.pdf (NetBank manual);
  https://tudastar.novitax.hu/elektronikus-bankkivonat-import-es-export-lehetosegek/ (lists MagNet XML among importable formats);
  http://dokumentacio.infoteka.hu/kontirdotnet/bankifeldolgozas.html (bank-export processing matrix)

### Gránit Bank — eBank/Electra export
- container: xml and "Excel formátum" (xls) from Számlainformációk → Számlatörténet; the netbank
  is an Electra derivative (netbank.granitbank.hu/eibpublic_granit) so Electra-family export
  formats apply; column structure publicly undocumented
- encoding, delimiter, decimal, thousands: undocumented
- date format(s): undocumented
- header/columns: undocumented
- amount sign / counterparty / balance / transaction id: undocumented
- quirks: accounting-software import lists include Gránit XML; because the backend is Electra,
  the K&H/OTP Electra interface PDFs are the nearest public analogue.
- sources:
  https://netbank.granitbank.hu/eibpublic_granit/help/hu/ALL.hu.html (Electra Internet Banking help);
  https://tudastar.novitax.hu/elektronikus-bankkivonat-import-es-export-lehetosegek/;
  http://dokumentacio.infoteka.hu/kontirdotnet/bankifeldolgozas.html

(Related: MBH Bank publishes an official export/import format PDF —
https://www.mbhbank.hu/sw/static/file/export_import_formatumok_mbh_bank.pdf — useful precedent
if MBH support is ever requested.)

---

## Priority recommendation

Highest coverage per unit of work for an EU/Hungarian-centric personal-finance harness:

1. **Revolut personal CSV** — rock-stable 10-column English header, ISO datetimes, dot decimal,
   running balance for integrity checks. Huge Hungarian user base. Cheapest preset to build and
   the pending/REVERTED + fee-column semantics map directly onto our dedup/ledger scripts.
2. **Wise CSV** — same effort class, multi-currency incl. HUF, has a real transaction id and
   running balance. Only wrinkle: sniff `DD-MM-YYYY` vs `YYYY-MM-DD` dates and per-currency files.
3. **OTP netbank XLSX (current A–K format)** — largest Hungarian retail bank; format is
   concretely pinned down by the ofxstatement-otp plugin (preamble skip, `Banki azonosító` as
   dedup id). Ship the current format as the preset; treat the legacy XLSX as a second header
   signature of the same preset.
4. **camt.053 XML** — one parser covers "every bank that offers ISO 20022", including the
   Electra-family corporate channels (K&H, Gránit) and future-proofs the harness; unsigned
   Amt+CdtDbtInd and OPBD/CLBD balances suit the script-core validation model perfectly.

Better served by the **generic mapping wizard** than a preset:
- **K&H, Raiffeisen HU, MagNet, Gránit CSV/XLS** — partially or wholly undocumented, HU-locale
  quirks (tab-in-.csv, trailing-dot dates, 3 memo columns), and they drift; the wizard plus a
  saved per-user mapping is safer than a preset we cannot verify from public sources. Promote to
  presets only after sanitized findings from real exports (rule 2: findings only, no data).
- **QIF** — trivial record parser but the M/D/Y-vs-D/M/Y ambiguity means the wizard must confirm
  the date order anyway; implement as a small standalone parser behind the wizard, not a dialect.
- **OFX** — worth a lenient standalone parser eventually (FITID is the best dedup key in the
  industry), but SGML 1.x handling is real work and no priority bank here emits it natively.
- **Monzo / N26** — clean formats but low relevance for a Hungarian household; their documented
  header signatures above make them cheap wizard auto-suggestions and good synthetic eval
  fixtures (Monzo's emoji column and N26's Presentment FX rows are excellent edge-case tests).
