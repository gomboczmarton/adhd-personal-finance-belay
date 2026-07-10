#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1"]
# ///
"""Suggest an ingestion mapping for a bank export file (D3 wizard, preset layer).

Usage:
    uv run harness/scripts/suggest_mapping.py <export-file>

Sniffs the file (encoding, delimiter, header row) and matches its header
signature against known bank export presets (public formats surveyed in
roadmap B5: Revolut/Wise/N26/Monzo CSV, OTP netbank XLSX, plus the Erste-like
eu_csv/hu_csv shapes). Prints JSON:

    {"preset": "<name>"|null, "confidence": "exact"|"none",
     "ingestion": {...accounts.md-ready mapping...}, "notes": [...]}

When no preset matches, "ingestion" holds the sniffed skeleton (format,
encoding, delimiter, detected header row) for the agent to complete
interactively — the wizard remains the fallback for every unknown bank.
Pure detection: proposes, never writes.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

# preset = exact header signature -> ready ingestion config (+ human notes)
PRESETS: list[dict] = [
    {
        "name": "revolut_csv",
        "bank": "Revolut (personal CSV)",
        "header": ["Type", "Product", "Started Date", "Completed Date", "Description",
                   "Amount", "Fee", "Currency", "State", "Balance"],
        "ingestion": {
            "format": "csv", "encoding": "utf-8", "delimiter": ",", "decimal": ".",
            "date_format": "%Y-%m-%d %H:%M:%S", "header_rows": 1,
            "columns": {"date": "Completed Date", "amount": "Amount",
                        "description": "Description"},
        },
        "notes": [
            "No counterparty column — description is the only merchant signal.",
            "Rows with State != COMPLETED (PENDING/REVERTED) should be skipped.",
            "Fee column is NOT included in Amount; a nonzero Fee needs a separate row or adjustment.",
            "Pocket/vault moves are internal transfers (same one-legged problem as sub-accounts).",
        ],
    },
    {
        "name": "wise_csv",
        "bank": "Wise (per-currency CSV statement)",
        "header": ["TransferWise ID", "Date", "Amount", "Currency", "Description",
                   "Payment Reference", "Running Balance", "Exchange From", "Exchange To",
                   "Exchange Rate", "Payer Name", "Payee Name", "Payee Account Number",
                   "Merchant", "Card Last Four Digits", "Card Holder Full Name",
                   "Attachment", "Note", "Total fees"],
        "ingestion": {
            "format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "decimal": ".",
            "date_format": "%d-%m-%Y", "header_rows": 1,
            "columns": {"date": "Date", "amount": "Amount",
                        "description": "Description", "counterparty": "Merchant"},
        },
        "notes": [
            "One CSV per currency balance — ask for all of them.",
            "Date is DD-MM-YYYY in classic exports but YYYY-MM-DD in newer ones — verify a sample date.",
            "TransferWise ID is a stable transaction id (future dedup upgrade).",
        ],
    },
    {
        "name": "n26_csv",
        "bank": "N26 (CSV export, current format)",
        "header": ["Booking Date", "Value Date", "Partner Name", "Partner Iban", "Type",
                   "Payment Reference", "Account Name", "Amount (EUR)", "Original Amount",
                   "Original Currency", "Exchange Rate"],
        "ingestion": {
            "format": "csv", "encoding": "utf-8", "delimiter": ",", "decimal": ".",
            "date_format": "%Y-%m-%d", "header_rows": 1,
            "columns": {"date": "Booking Date", "amount": "Amount (EUR)",
                        "description": "Payment Reference", "counterparty": "Partner Name"},
        },
        "notes": [
            "EUR-only amount column; Original Amount/Currency only filled for FX card rows.",
            "Spaces (sub-account) moves are internal transfers.",
            "No balance column — no statement-level integrity check available.",
        ],
    },
    {
        "name": "monzo_csv",
        "bank": "Monzo (CSV export)",
        "header": ["Transaction ID", "Date", "Time", "Type", "Name", "Emoji", "Category",
                   "Amount", "Currency", "Local amount", "Local currency", "Notes and #tags",
                   "Address", "Receipt", "Description", "Category split", "Money Out", "Money In"],
        "ingestion": {
            "format": "csv", "encoding": "utf-8", "delimiter": ",", "decimal": ".",
            "date_format": "%d/%m/%Y", "header_rows": 1,
            "columns": {"date": "Date", "amount": "Amount",
                        "description": "Description", "counterparty": "Name"},
        },
        "notes": [
            "Transaction ID is a stable dedup key (future upgrade).",
            "Pot transfers (Type = 'Pot transfer') are internal transfers.",
            "0.00 'Active card check' rows exist; Emoji column carries multi-byte UTF-8.",
            "Business/newer exports append Balance + Balance currency columns.",
        ],
    },
    {
        "name": "otp_xlsx",
        "bank": "OTP Bank (netbank XLSX, post-2026-06 format)",
        "header": ["Számlaszám", "Ellenoldali számlaszám", "Ellenoldali név",
                   "Forgalom típusa", "Közlemény", "Tranzakció kategória", "Banki azonosító",
                   "Tranzakció időpontja", "Könyvelés dátuma", "Összeg", "Devizanem"],
        "ingestion": {
            "format": "xlsx", "date_format": "%Y-%m-%d", "header_rows": 10,
            "columns": {"date": "Könyvelés dátuma", "amount": "Összeg",
                        "description": "Közlemény", "counterparty": "Ellenoldali név"},
        },
        "notes": [
            "Metadata preamble before the header row — header_rows must point at the real header.",
            "Banki azonosító is a stable transaction id (future dedup upgrade).",
            "Devizanem column may be missing — HUF is the default then.",
        ],
    },
    {
        "name": "eu_csv",
        "bank": "Generic EU CSV (semicolon, decimal comma)",
        "header": ["Booking date", "Amount", "Details", "Partner", "Balance"],
        "ingestion": {
            "format": "csv", "encoding": "utf-8", "delimiter": ";", "decimal": ",",
            "date_format": "%Y.%m.%d", "header_rows": 1,
            "columns": {"date": "Booking date", "amount": "Amount",
                        "description": "Details", "counterparty": "Partner"},
        },
        "notes": [],
    },
    {
        "name": "hu_csv",
        "bank": "Hungarian bank CSV (Windows-1250, semicolon)",
        "header": ["Könyvelés dátuma", "Összeg", "Közlemény", "Partner név", "Egyenleg"],
        "ingestion": {
            "format": "csv", "encoding": "cp1250", "delimiter": ";", "decimal": ",",
            "date_format": "%Y.%m.%d.", "header_rows": 1,
            "columns": {"date": "Könyvelés dátuma", "amount": "Összeg",
                        "description": "Közlemény", "counterparty": "Partner név"},
        },
        "notes": [],
    },
]

ENCODINGS = ["utf-8-sig", "utf-8", "cp1250", "iso-8859-2", "cp1252"]
DELIMITERS = [",", ";", "\t"]
MAX_SNIFF_ROWS = 30  # a real header appears within the first rows (preambles are short)


def sniff_csv(path: Path) -> tuple[str, str, list[list[str]]]:
    """Return (encoding, delimiter, rows) with the first working decode."""
    raw = path.read_bytes()
    for enc in ENCODINGS:
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        best, best_delim = None, None
        for delim in DELIMITERS:
            rows = list(csv.reader(io.StringIO(text), delimiter=delim))[:MAX_SNIFF_ROWS]
            width = max((len(r) for r in rows), default=0)
            if width >= 2 and (best is None or width > max(len(r) for r in best)):
                best, best_delim = rows, delim
        if best:
            return enc, best_delim, best
    sys.exit(f"error: cannot decode {path} with any of {ENCODINGS}")


def read_xlsx_rows(path: Path) -> list[list[str]]:
    from openpyxl import load_workbook
    ws = load_workbook(path, read_only=True).active
    out = []
    for row in ws.iter_rows(min_row=1, max_row=MAX_SNIFF_ROWS, values_only=True):
        out.append(["" if c is None else str(c) for c in row])
    return out


def match_presets(rows: list[list[str]], container: str) -> tuple[dict | None, int]:
    """Find a preset whose exact header appears in the first rows; return (preset, row_index)."""
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row]
        for preset in PRESETS:
            want_fmt = preset["ingestion"]["format"]
            if want_fmt != container:
                continue
            sig = preset["header"]
            if cells[: len(sig)] == sig:
                return preset, i
    return None, -1


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        sys.exit(f"error: {path} does not exist")

    if path.suffix.lower() in (".xlsx", ".xls"):
        rows = read_xlsx_rows(path)
        preset, header_idx = match_presets(rows, "xlsx")
        skeleton = {"format": "xlsx"}
        enc = delim = None
    else:
        enc, delim, rows = sniff_csv(path)
        preset, header_idx = match_presets(rows, "csv")
        skeleton = {"format": "csv", "encoding": enc, "delimiter": delim,
                    "header_rows": 1, "columns": {}}

    if preset:
        ingestion = dict(preset["ingestion"])
        ingestion["header_rows"] = header_idx + 1  # actual position beats the preset default
        if enc and ingestion.get("encoding") not in (enc, "utf-8-sig"):
            ingestion["encoding"] = enc
        print(json.dumps({
            "preset": preset["name"], "bank": preset["bank"], "confidence": "exact",
            "header_row": header_idx + 1, "ingestion": ingestion, "notes": preset["notes"],
        }, ensure_ascii=False))
    else:
        # no preset: hand the agent the sniffed skeleton + the first rows as evidence
        print(json.dumps({
            "preset": None, "confidence": "none", "ingestion": skeleton,
            "sample_rows": rows[:5],
            "notes": ["No known bank signature matched — complete the mapping "
                      "interactively (D3 wizard) and save it to accounts.md."],
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
