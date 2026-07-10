#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "jsonschema>=4.21", "openpyxl>=3.1"]
# ///
"""Generate deterministic synthetic bank exports from persona eval packages (D9).

Usage:
    uv run harness/scripts/generate_fixtures.py <persona.md> [<out-dir>]
    uv run harness/scripts/generate_fixtures.py --all evals/personas [<out-dir>]

Default out-dir: evals/fixtures/<persona-id>/
Output: one export file per account per month, in the account's dialect:
    eu_csv       UTF-8, ';', decimal comma, dates %Y.%m.%d, EN headers
    hu_csv       Windows-1250, ';', decimal comma, dates %Y.%m.%d., HU headers
    simple_xlsx  one sheet: Date / Amount / Merchant

Determinism: RNG seeded from the persona id (or fixtures.seed); same persona
file -> byte-identical CSVs. A manifest.json records ground truth per month
(income totals, per-category spend, transfer pairs, yearly items) so evals can
assert against KNOWN answers rather than re-deriving them.
"""

from __future__ import annotations

import csv
import io
import json
import random
import sys
import zlib
from datetime import date
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from openpyxl import Workbook

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "persona.schema.json"

DIALECTS = {
    "eu_csv": {
        "ext": "csv", "encoding": "utf-8", "delimiter": ";", "decimal": ",",
        "date_format": "%Y.%m.%d",
        "headers": ["Booking date", "Amount", "Details", "Partner", "Balance"],
    },
    "hu_csv": {
        "ext": "csv", "encoding": "cp1250", "delimiter": ";", "decimal": ",",
        "date_format": "%Y.%m.%d.",
        "headers": ["Könyvelés dátuma", "Összeg", "Közlemény", "Partner név", "Egyenleg"],
    },
    "simple_xlsx": {"ext": "xlsx", "headers": ["Date", "Amount", "Merchant"]},
    # real-bank shapes from the roadmap-B5 public-format survey (synthetic data,
    # authentic column layout) — each built by a row builder below
    "revolut_csv": {
        "ext": "csv", "encoding": "utf-8", "delimiter": ",", "built": True,
        "headers": ["Type", "Product", "Started Date", "Completed Date", "Description",
                    "Amount", "Fee", "Currency", "State", "Balance"],
    },
    "wise_csv": {
        "ext": "csv", "encoding": "utf-8", "delimiter": ",", "built": True,
        "headers": ["TransferWise ID", "Date", "Amount", "Currency", "Description",
                    "Payment Reference", "Running Balance", "Exchange From", "Exchange To",
                    "Exchange Rate", "Payer Name", "Payee Name", "Payee Account Number",
                    "Merchant", "Card Last Four Digits", "Card Holder Full Name",
                    "Attachment", "Note", "Total fees"],
    },
    "monzo_csv": {
        "ext": "csv", "encoding": "utf-8", "delimiter": ",", "built": True,
        "headers": ["Transaction ID", "Date", "Time", "Type", "Name", "Emoji", "Category",
                    "Amount", "Currency", "Local amount", "Local currency",
                    "Notes and #tags", "Address", "Receipt", "Description",
                    "Category split", "Money Out", "Money In"],
    },
    "n26_csv": {
        "ext": "csv", "encoding": "utf-8", "delimiter": ",", "built": True,
        "headers": ["Booking Date", "Value Date", "Partner Name", "Partner Iban", "Type",
                    "Payment Reference", "Account Name", "Amount (EUR)", "Original Amount",
                    "Original Currency", "Exchange Rate"],
    },
    "otp_xlsx": {
        "ext": "xlsx", "built": True, "preamble_rows": 9,
        "headers": ["Számlaszám", "Ellenoldali számlaszám", "Ellenoldali név",
                    "Forgalom típusa", "Közlemény", "Tranzakció kategória",
                    "Banki azonosító", "Tranzakció időpontja", "Könyvelés dátuma",
                    "Összeg", "Devizanem"],
    },
}


def build_row(dialect_name: str, r: dict, balance: float, i: int, currency: str) -> list:
    """Cell values for one transaction in a real-bank dialect (synthetic but authentic)."""
    amt = f"{r['amount']:.2f}"
    if dialect_name == "revolut_csv":
        kind = "TOPUP" if r["amount"] > 0 else \
            ("TRANSFER" if "OWN ACCOUNT" in r.get("partner", "") else "CARD_PAYMENT")
        stamp = f"{r['date']:%Y-%m-%d} 10:00:00"
        return [kind, "Current", stamp, stamp, r["desc"], amt, "0.00", currency,
                "COMPLETED", f"{balance:.2f}"]
    if dialect_name == "wise_csv":
        prefix = "TRANSFER" if r["amount"] > 0 else "CARD"
        return [f"{prefix}-{i:09d}", f"{r['date']:%d-%m-%Y}", amt, currency, r["desc"],
                "", f"{balance:.2f}", "", "", "", "", "", "", r.get("partner", ""),
                "", "", "", "", "0.00"]
    if dialect_name == "monzo_csv":
        return [f"tx_{i:012d}", f"{r['date']:%d/%m/%Y}", "10:00:00", "Card payment",
                r.get("partner", ""), "🛒", "", amt, currency, amt, currency,
                "", "", "", r["desc"], "", amt if r["amount"] < 0 else "",
                amt if r["amount"] > 0 else ""]
    if dialect_name == "n26_csv":
        kind = "Credit Transfer" if r["amount"] > 0 else "Debit Transfer"
        d = r["date"].isoformat()
        return [d, d, r.get("partner", ""), "", kind, r["desc"], "Main Account",
                amt, "", "", ""]
    if dialect_name == "otp_xlsx":
        return ["SYNTH-ACCOUNT-1", "", r.get("partner", ""), "Átutalás", r["desc"], "",
                f"OTP{i:012d}", f"{r['date'].isoformat()} 10:00:00", r["date"].isoformat(),
                r["amount"], currency]
    raise ValueError(dialect_name)

TRANSFER_OUT_DESC = "TRANSFER TO CREDIT CARD REFILL"
TRANSFER_IN_DESC = "INCOMING TRANSFER REFILL"


def month_range(end_month: str, months: int) -> list[tuple[int, int]]:
    y, m = int(end_month[:4]), int(end_month[5:7])
    out = []
    for _ in range(months):
        out.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(out))


def days_in_month(y: int, m: int) -> int:
    nm_y, nm_m = (y + 1, 1) if m == 12 else (y, m + 1)
    return (date(nm_y, nm_m, 1) - date(y, m, 1)).days


def fmt_amount(x: float, decimal: str) -> str:
    s = f"{x:.2f}"
    return s.replace(".", decimal)


def load_persona(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        sys.exit(f"error: {path} has no frontmatter")
    fm = yaml.safe_load(text[4 : text.find("\n---", 4)])
    validator = Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    errors = [
        f"  - {'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
        for e in validator.iter_errors(fm)
    ]
    if errors:
        sys.exit(f"error: {path} violates persona schema:\n" + "\n".join(errors))
    return fm


def generate(persona: dict) -> tuple[dict[str, list[dict]], dict]:
    """Return (rows per account id, ground-truth manifest)."""
    seed = persona["fixtures"].get("seed", zlib.crc32(persona["id"].encode()))
    rng = random.Random(seed)
    months = month_range(persona["fixtures"].get("end_month", "2026-06"),
                         persona["fixtures"]["months"])
    account_ids = [a["id"] for a in persona["accounts"]]
    checking = next(a["id"] for a in persona["accounts"] if a["type"] == "checking")
    credit = next((a["id"] for a in persona["accounts"] if a["type"] == "credit_card"), None)

    rows: dict[str, list[dict]] = {aid: [] for aid in account_ids}
    manifest: dict = {"persona": persona["id"], "seed": seed, "months": {}}
    fx = persona["fixtures"]
    entropy = fx.get("desc_entropy", False)
    sub_accounts = fx.get("sub_accounts", [])
    sweep = fx.get("savings_sweep", False)

    def add(acct: str, d: date, amount: float, desc: str, partner: str = "") -> None:
        if entropy:
            desc = f"{desc} REF {rng.randrange(10**8, 10**9)}"
        rows[acct].append({"date": d, "amount": round(amount, 2), "desc": desc, "partner": partner})

    for y, m in months:
        key = f"{y:04d}-{m:02d}"
        truth = {"income": 0.0, "spend": {}, "transfers": 0.0, "yearly_items": []}
        inc = persona["income"]

        for day in inc["days"]:
            if inc["type"] == "irregular" and rng.random() < 0.35:
                continue  # feast-or-famine: some paydays just don't happen
            amount = round(rng.uniform(*inc["amount"]), 2)
            add(checking, date(y, m, day), amount, inc.get("employer_desc", "INCOME"), "EMPLOYER")
            truth["income"] += amount

        for spend in persona["spending"]:
            acct = spend["account"]
            if spend["freq"] == "monthly":
                merchants = spend["merchants"]  # every merchant bills monthly (subscriptions)
                base_day = spend.get("day", rng.randint(2, 26))
                occurrences = [
                    (min(base_day + i, days_in_month(y, m)), mc)
                    for i, mc in enumerate(merchants)
                ]
            elif spend["freq"] == "weekly":
                occurrences = [
                    (min(7 * w + rng.randint(1, 6), days_in_month(y, m)), rng.choice(spend["merchants"]))
                    for w in range(4)
                ]
            else:  # sporadic
                occurrences = [
                    (rng.randint(1, days_in_month(y, m)), rng.choice(spend["merchants"]))
                    for _ in range(rng.randint(0, 4))
                ]
            for day, merchant in occurrences:
                amount = round(rng.uniform(*spend["amount"]), 2)
                add(acct, date(y, m, day), -amount, merchant, merchant)
                cat = spend["category"]
                truth["spend"][cat] = round(truth["spend"].get(cat, 0) + amount, 2)

        for item in persona.get("yearly_items", []):
            if item["month"] == m:
                add(item["account"], date(y, m, rng.randint(5, 20)),
                    -item["amount"], item["name"].upper(), item["name"].upper())
                truth["yearly_items"].append(item["name"])
                cat = item["category"]
                truth["spend"][cat] = round(truth["spend"].get(cat, 0) + item["amount"], 2)

        if persona.get("internal_transfers", "none") != "none" and credit:
            card_out = [r for r in rows[credit]
                        if r["date"].year == y and r["date"].month == m and r["amount"] < 0]
            if persona["internal_transfers"] == "refill_after_spend":
                # weekly refill covering that week's card spending
                for week in range(4):
                    chunk = [r for r in card_out if (r["date"].day - 1) // 7 == week]
                    if not chunk:
                        continue
                    total = round(-sum(r["amount"] for r in chunk), 2)
                    d = date(y, m, min(7 * (week + 1), days_in_month(y, m)))
                    add(checking, d, -total, TRANSFER_OUT_DESC, "OWN ACCOUNT")
                    add(credit, d, total, TRANSFER_IN_DESC, "OWN ACCOUNT")
                    truth["transfers"] = round(truth["transfers"] + total, 2)
            else:  # monthly_allocation
                total = round(-sum(r["amount"] for r in card_out), 2)
                if total:
                    d = date(y, m, min(max(persona["income"]["days"]) + 2, 28))
                    add(checking, d, -total, TRANSFER_OUT_DESC, "OWN ACCOUNT")
                    add(credit, d, total, TRANSFER_IN_DESC, "OWN ACCOUNT")
                    truth["transfers"] = total
        # one-legged transfers to own sub-accounts: only the checking leg exists
        # (the counterpart lives in an export that is never provided) — recognizable
        # solely by the stable OWN ACCOUNT counterparty (real-world CelBetet shape)
        one_legged = 0.0
        for sub in sub_accounts:
            if truth["income"] <= 0:
                continue
            amount = round(rng.uniform(0.04, 0.12) * truth["income"], 2)
            day = rng.randint(6, 24)
            add(checking, date(y, m, day), -amount,
                "TRANSFER TO OWN ACCOUNT", f"OWN ACCOUNT {sub.upper()}")
            one_legged = round(one_legged + amount, 2)
        if sweep:
            net = round(sum(r["amount"] for r in rows[checking]
                            if r["date"].year == y and r["date"].month == m), 2)
            if net > 0:
                amount = round(0.7 * net, 2)
                add(checking, date(y, m, days_in_month(y, m)), -amount,
                    "SAVINGS SWEEP", "OWN ACCOUNT SAVINGS")
                one_legged = round(one_legged + amount, 2)
        if sub_accounts or sweep:
            truth["one_legged"] = one_legged
        truth["income"] = round(truth["income"], 2)
        manifest["months"][key] = truth

    for acct_rows in rows.values():
        acct_rows.sort(key=lambda r: r["date"])
    return rows, manifest


def write_exports(persona: dict, rows: dict[str, list[dict]], out_dir: Path) -> list[Path]:
    written = []
    for account in persona["accounts"]:
        dialect = DIALECTS[account["dialect"]]
        acct_rows = rows[account["id"]]
        by_month: dict[str, list[dict]] = {}
        for r in acct_rows:
            by_month.setdefault(f"{r['date']:%Y-%m}", []).append(r)
        balance = 0.0
        seq = 0
        currency = persona["income"]["currency"]
        for month_key in sorted(by_month):
            month_rows = by_month[month_key]
            path = out_dir / f"{account['id']}_{month_key}.{dialect['ext']}"
            if dialect.get("built") and dialect["ext"] == "csv":
                buf = io.StringIO()
                w = csv.writer(buf, delimiter=dialect["delimiter"])
                w.writerow(dialect["headers"])
                for r in month_rows:
                    balance = round(balance + r["amount"], 2)
                    seq += 1
                    w.writerow(build_row(account["dialect"], r, balance, seq, currency))
                path.write_bytes(buf.getvalue().encode(dialect["encoding"]))
            elif dialect.get("built"):  # otp_xlsx: metadata preamble + Hungarian header
                wb = Workbook()
                ws = wb.active
                ws.title = "Tranzakciók"
                preamble = [["Számlatörténet"], [], ["Számla:", "SYNTH-ACCOUNT-1"],
                            ["Lekérdezés:", month_key], [], [], [], [], []]
                for row in preamble[: dialect["preamble_rows"]]:
                    ws.append(row)
                ws.append(dialect["headers"])
                for r in month_rows:
                    balance = round(balance + r["amount"], 2)
                    seq += 1
                    ws.append(build_row(account["dialect"], r, balance, seq, currency))
                wb.save(path)
            elif dialect["ext"] == "csv":
                buf = io.StringIO()
                w = csv.writer(buf, delimiter=dialect["delimiter"])
                w.writerow(dialect["headers"])
                for r in month_rows:
                    balance = round(balance + r["amount"], 2)
                    w.writerow([
                        r["date"].strftime(dialect["date_format"]),
                        fmt_amount(r["amount"], dialect["decimal"]),
                        r["desc"], r["partner"],
                        fmt_amount(balance, dialect["decimal"]),
                    ])
                path.write_bytes(buf.getvalue().encode(dialect["encoding"]))
            else:
                wb = Workbook()
                ws = wb.active
                ws.title = "Transactions"
                ws.append(dialect["headers"])
                for r in month_rows:
                    ws.append([r["date"].isoformat(), r["amount"], r["desc"]])
                wb.save(path)
            written.append(path)
    return written


def run_one(persona_path: Path, out_root: Path) -> None:
    persona = load_persona(persona_path)
    out_dir = out_root / persona["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, manifest = generate(persona)
    files = write_exports(persona, rows, out_dir)
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    n_txn = sum(len(v) for v in rows.values())
    print(f"{persona['id']}: {n_txn} transactions -> {len(files)} export files "
          f"+ manifest.json in {out_dir}")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    if args[0] == "--all":
        persona_dir = Path(args[1]) if len(args) > 1 else Path("evals/personas")
        out_root = Path(args[2]) if len(args) > 2 else Path("evals/fixtures")
        for p in sorted(persona_dir.glob("*.md")):
            run_one(p, out_root)
    else:
        out_root = Path(args[1]) if len(args) > 1 else Path("evals/fixtures")
        run_one(Path(args[0]), out_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
