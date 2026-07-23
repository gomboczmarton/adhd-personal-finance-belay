#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Verify a ledger month against a fixture ground-truth manifest (verifier half).

Usage:
    uv run evals/lib/ledger_verify.py <workspace> <manifest.json> <month> [flags]

Flags:
    --own-account-internal   additionally require every imported txn whose
                             counterparty mentions OWN ACCOUNT to be classified
                             as an internal transfer (matched or categorized),
                             never income/expense
    --allow-uncategorized    skip the uncategorized-must-be-empty check

Pure read: this script never appends events; it independently recomputes the
month from ledger/events.jsonl with the same classification semantics as
reconcile.py (matched legs and kind=internal_transfer excluded from income and
spend; only positive legs count toward transfer volume) and compares against
the KNOWN answers in manifest.json. Independent recomputation means a broken
reconcile.py cannot grade itself.

Output: JSON {"checks": {...}, "pass": bool}; exit 0 iff every check passes.
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path


def cents(x) -> int:
    return int((Decimal(str(x)) * 100).to_integral_value())


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    ws, manifest_path, month = Path(args[0]), Path(args[1]), args[2]
    truth = json.loads(manifest_path.read_text(encoding="utf-8"))["months"][month]

    events = [json.loads(l) for l in
              (ws / "ledger" / "events.jsonl").read_text(encoding="utf-8").splitlines()
              if l.strip()]
    matched: set[str] = set()
    categorized: dict[str, dict] = {}
    for ev in events:
        if ev["type"] == "txn.matched":
            matched.update(ev["hashes"])
        elif ev["type"] == "txn.categorized":
            categorized[ev["hash"]] = ev

    income = Decimal(0)
    spend: dict[str, Decimal] = {}
    transfers = Decimal(0)
    uncategorized: list[str] = []
    own_account_misclassified: list[str] = []
    seen_hashes: set[str] = set()
    duplicate_hashes: list[str] = []

    for ev in events:
        if ev["type"] != "txn.imported":
            continue
        if ev["hash"] in seen_hashes:
            duplicate_hashes.append(ev["hash"])
        seen_hashes.add(ev["hash"])
        if ev["date"][:7] != month:
            continue
        amount = Decimal(str(ev["amount"]))
        cat = categorized.get(ev["hash"])
        is_internal = ev["hash"] in matched or (cat and cat["kind"] == "internal_transfer")
        if "OWN ACCOUNT" in ev.get("counterparty", "").upper() and not is_internal:
            own_account_misclassified.append(ev["hash"])
        if is_internal:
            if amount > 0:
                transfers += amount
        elif cat and cat["kind"] == "income":
            income += amount
        elif cat and cat["kind"] in ("expense", "refund"):
            spend[cat["category"]] = spend.get(cat["category"], Decimal(0)) - amount
        else:
            uncategorized.append(ev["hash"])

    truth_spend = {k: cents(v) for k, v in truth["spend"].items()}
    actual_spend = {k: cents(v) for k, v in spend.items()}
    checks = {
        "income_matches": {
            "expected": truth["income"], "actual": float(income),
            "ok": cents(truth["income"]) == cents(income)},
        "spend_matches": {
            "expected": truth["spend"], "actual": {k: float(v) for k, v in sorted(spend.items())},
            "ok": truth_spend == actual_spend},
        "transfer_volume_matches": {
            "expected": truth.get("transfers", 0.0), "actual": float(transfers),
            "ok": cents(truth.get("transfers", 0.0)) == cents(transfers)},
        "no_duplicate_hashes": {"violations": duplicate_hashes, "ok": not duplicate_hashes},
    }
    if "--allow-uncategorized" not in sys.argv:
        checks["all_categorized"] = {"violations": uncategorized, "ok": not uncategorized}
    if "--own-account-internal" in sys.argv:
        checks["own_account_is_internal"] = {
            "violations": own_account_misclassified, "ok": not own_account_misclassified}

    ok = all(c["ok"] for c in checks.values())
    print(json.dumps({"checks": checks, "pass": ok}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
