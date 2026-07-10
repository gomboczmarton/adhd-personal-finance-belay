#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Reconcile ledger months: rule-categorize, then compute exact totals.

Usage:
    uv run harness/scripts/reconcile.py <workspace> [--month YYYY-MM] [--verify-budget YYYY-MM]

Default: apply merchant-map rules to uncategorized transactions (appending
txn.categorized events, by=rule), then report per month (or one --month):
income, spend per category, internal-transfer volume, uncategorized hashes.
All arithmetic in Decimal (D4: the model never does math; this script does,
exactly).

Matched internal-transfer legs and kind=internal_transfer categorizations are
excluded from income and spend — refills are never income (blindspot #2).

--verify-budget: check months/YYYY-MM/budget.md arithmetic:
sum(allocations) + savings_target == income_planned (envelope-mode invariant).

Prints JSON. Exit 1 if --verify-budget fails, else 0.
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import yaml


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        sys.exit(f"error: {path} has no frontmatter")
    return yaml.safe_load(text[4 : text.find("\n---", 4)])


def load_events(ws: Path) -> list[dict]:
    ledger = ws / "ledger" / "events.jsonl"
    return [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]


def verify_budget(ws: Path, month: str) -> int:
    fm = frontmatter(ws / "months" / month / "budget.md")
    income = Decimal(str(fm.get("income_planned", 0)))
    allocations = sum((Decimal(str(v)) for v in (fm.get("allocations") or {}).values()), Decimal(0))
    savings = Decimal(str(fm.get("savings_target", 0)))
    diff = income - allocations - savings
    ok = diff == 0
    print(json.dumps({
        "month": month, "income_planned": str(income), "allocations": str(allocations),
        "savings_target": str(savings), "difference": str(diff), "balanced": ok,
    }))
    return 0 if ok else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    ws = Path(sys.argv[1])
    if "--verify-budget" in sys.argv:
        return verify_budget(ws, sys.argv[sys.argv.index("--verify-budget") + 1])
    only_month = sys.argv[sys.argv.index("--month") + 1] if "--month" in sys.argv else None

    events = load_events(ws)
    merchants = frontmatter(ws / "knowledge" / "merchant-map.md")["merchants"] \
        if (ws / "knowledge" / "merchant-map.md").exists() else []

    matched_hashes: set[str] = set()
    categorized: dict[str, dict] = {}
    for ev in events:
        if ev["type"] == "txn.matched":
            matched_hashes.update(ev["hashes"])
        elif ev["type"] == "txn.categorized":
            categorized[ev["hash"]] = ev

    # rule categorization pass: merchant-map patterns, case-insensitive substring
    # against the rule's field — description (default) or counterparty (how
    # one-legged own-account transfers are recognized; real-data finding #3)
    def rule_matches(rule: dict, ev: dict) -> bool:
        target = ev.get("counterparty", "") if rule.get("field") == "counterparty" \
            else ev["desc"]
        return bool(target) and rule["pattern"].upper() in target.upper()

    new_events = []
    for ev in events:
        if ev["type"] != "txn.imported" or ev["hash"] in categorized or ev["hash"] in matched_hashes:
            continue
        rule = next((m for m in merchants if rule_matches(m, ev)), None)
        if rule:
            cat_event = {
                "v": 1, "ts": ev["date"], "type": "txn.categorized", "hash": ev["hash"],
                "category": rule["category"], "kind": rule["kind"], "by": "rule",
                "rule": rule["pattern"], "confidence": 1.0,
            }
            categorized[ev["hash"]] = cat_event
            new_events.append(cat_event)
    if new_events:
        with open(ws / "ledger" / "events.jsonl", "a", encoding="utf-8") as out:
            for ev in new_events:
                out.write(json.dumps(ev, ensure_ascii=False) + "\n")

    # exact totals per month
    report: dict[str, dict] = {}
    for ev in events:
        if ev["type"] != "txn.imported":
            continue
        month = ev["date"][:7]
        if only_month and month != only_month:
            continue
        r = report.setdefault(month, {
            "income": Decimal(0), "spend": {}, "transfers": Decimal(0),
            "uncategorized": [], "txns": 0,
        })
        r["txns"] += 1
        amount = Decimal(str(ev["amount"]))
        cat = categorized.get(ev["hash"])
        if ev["hash"] in matched_hashes or (cat and cat["kind"] == "internal_transfer"):
            if amount > 0:
                r["transfers"] += amount
        elif cat and cat["kind"] == "income":
            r["income"] += amount
        elif cat and cat["kind"] in ("expense", "refund"):
            key = cat["category"]
            r["spend"][key] = r["spend"].get(key, Decimal(0)) - amount
        else:
            r["uncategorized"].append(ev["hash"])

    out = {
        "rule_categorized": len(new_events),
        "months": {
            m: {
                "income": float(r["income"]),
                "spend": {k: float(v) for k, v in sorted(r["spend"].items())},
                "transfers": float(r["transfers"]),
                "txns": r["txns"],
                "uncategorized": r["uncategorized"],
            }
            for m, r in sorted(report.items())
        },
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
