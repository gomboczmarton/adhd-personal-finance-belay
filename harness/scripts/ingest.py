#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "openpyxl>=3.1"]
# ///
"""Ingest bank export files into the workspace ledger (D3 mapping-wizard engine).

Usage:
    uv run harness/scripts/ingest.py <workspace> <account_id> <export-file>...

Reads the account's ingestion mapping from <workspace>/accounts.md frontmatter
(format, encoding, delimiter, decimal, date_format, column names), normalizes
each row, and appends txn.imported events to <workspace>/ledger/events.jsonl.

Transaction identity = sha256(account|date|amount|description|seq)[:16], where
seq numbers identical rows *within one export file* — so two genuinely equal
purchases on the same day both survive, while re-importing an overlapping
export (same rows again) dedups exactly (blindspot #4).

Prints a JSON summary: {"imported": n, "duplicates": n, "rows": n}.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml
from openpyxl import load_workbook


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        sys.exit(f"error: {path} has no frontmatter")
    return yaml.safe_load(text[4 : text.find("\n---", 4)])


def parse_amount(raw: str | float | int, cfg: dict) -> float:
    if isinstance(raw, (int, float)):
        return float(raw)
    s = raw.strip()
    if thousands := cfg.get("thousands"):
        s = s.replace(thousands, "")
    if cfg.get("decimal", ".") == ",":
        s = s.replace(",", ".")
    return float(s)


def read_rows(path: Path, cfg: dict) -> list[dict]:
    """Return normalized rows: {date, amount, desc, counterparty}."""
    cols = cfg["columns"]
    out = []
    if cfg["format"] == "csv":
        with open(path, encoding=cfg.get("encoding", "utf-8"), newline="") as fh:
            reader = csv.reader(fh, delimiter=cfg.get("delimiter", ";"))
            rows = list(reader)
        header_rows = cfg.get("header_rows", 1)
        header = rows[header_rows - 1] if header_rows else []
        idx = {name: header.index(col) for name, col in cols.items() if col in header}
        missing = [c for c in ("date", "amount", "description") if c not in idx]
        if missing:
            sys.exit(f"error: {path}: mapped columns not found in header: "
                     f"{[cols[c] for c in missing]} (header: {header})")
        for row in rows[header_rows:]:
            if not row or not row[idx["date"]].strip():
                continue
            out.append({
                "date": datetime.strptime(row[idx["date"]].strip(), cfg["date_format"]).date(),
                "amount": round(parse_amount(row[idx["amount"]], cfg), 2),
                "desc": row[idx["description"]].strip(),
                "counterparty": row[idx["counterparty"]].strip() if "counterparty" in idx else "",
            })
    else:  # xlsx
        wb = load_workbook(path, read_only=True)
        ws = wb[cfg["sheet"]] if cfg.get("sheet") else wb.active
        rows = list(ws.iter_rows(values_only=True))
        header_rows = cfg.get("header_rows", 1)  # OTP-style exports have a preamble
        header = [str(c) if c is not None else "" for c in rows[header_rows - 1]]
        idx = {name: header.index(col) for name, col in cols.items() if col in header}
        missing = [c for c in ("date", "amount", "description") if c not in idx]
        if missing:
            sys.exit(f"error: {path}: mapped columns not found in header: "
                     f"{[cols[c] for c in missing]} (header: {header})")
        for row in rows[header_rows:]:
            if row is None or row[idx["date"]] in (None, ""):
                continue
            raw_date = row[idx["date"]]
            if isinstance(raw_date, datetime):
                d = raw_date.date()
            else:
                d = datetime.strptime(str(raw_date).strip(), cfg.get("date_format", "%Y-%m-%d")).date()
            out.append({
                "date": d,
                "amount": round(parse_amount(row[idx["amount"]], cfg), 2),
                "desc": str(row[idx["description"]]).strip(),
                "counterparty": str(row[idx["counterparty"]]).strip() if "counterparty" in idx else "",
            })
    return out


def txn_hash(account: str, row: dict, seq: int) -> str:
    key = f"{account}|{row['date'].isoformat()}|{row['amount']:.2f}|{row['desc']}|{seq}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    ws, account_id, files = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]

    accounts = frontmatter(ws / "accounts.md")["accounts"]
    account = next((a for a in accounts if a["id"] == account_id), None)
    if account is None:
        sys.exit(f"error: account '{account_id}' not in accounts.md")
    cfg = account.get("ingestion")
    if cfg is None:
        sys.exit(f"error: account '{account_id}' has no ingestion mapping")

    ledger = ws / "ledger" / "events.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if line.strip():
                ev = json.loads(line)
                if ev.get("type") == "txn.imported":
                    existing.add(ev["hash"])

    imported = duplicates = rows_total = 0
    currency = account.get("currency", "EUR")
    with open(ledger, "a", encoding="utf-8") as out:
        for f in files:
            path = Path(f)
            rows = read_rows(path, cfg)
            rows_total += len(rows)
            seq_counter: dict[tuple, int] = {}  # reset per file (see docstring)
            for row in rows:
                key = (row["date"], row["amount"], row["desc"])
                seq = seq_counter.get(key, 0)
                seq_counter[key] = seq + 1
                h = txn_hash(account_id, row, seq)
                if h in existing:
                    duplicates += 1
                    continue
                existing.add(h)
                imported += 1
                event = {
                    "v": 1, "ts": row["date"].isoformat(), "type": "txn.imported",
                    "account": account_id, "hash": h, "date": row["date"].isoformat(),
                    "amount": row["amount"], "currency": currency, "desc": row["desc"],
                    "source_file": path.name,
                }
                if row["counterparty"]:
                    event["counterparty"] = row["counterparty"]
                out.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(json.dumps({"imported": imported, "duplicates": duplicates, "rows": rows_total}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
