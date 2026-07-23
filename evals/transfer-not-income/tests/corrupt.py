#!/usr/bin/env python3
"""Plausible-but-wrong fixture: the classic naive-tool failure this task
guards against — one-legged own-account transfers booked as ordinary expenses
(savings counted as spending). Rewrites the internal_transfer categorizations
to kind=expense/category=groceries. The verifier MUST fail this workspace.

Usage: corrupt.py <workspace>
"""
import json
import sys
from pathlib import Path

ledger = Path(sys.argv[1]) / "ledger" / "events.jsonl"
out = []
flipped = 0
for line in ledger.read_text(encoding="utf-8").splitlines():
    ev = json.loads(line)
    if ev.get("type") == "txn.categorized" and ev.get("kind") == "internal_transfer":
        ev["kind"] = "expense"
        ev["category"] = "groceries"
        flipped += 1
    out.append(json.dumps(ev, ensure_ascii=False))
ledger.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"corrupted: flipped {flipped} internal_transfer categorizations to expense")
