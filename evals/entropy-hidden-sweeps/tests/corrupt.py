#!/usr/bin/env python3
"""Plausible-but-wrong fixture (fixture rule): the entropy-defeat failure —
unique reference strings make every description look new, so the agent gives
up and leaves groceries uncategorized. Drops every txn.categorized event whose
category is groceries. The verifier MUST fail this workspace
(all_categorized and per-category spend both break).

Usage: corrupt.py <workspace>
"""
import json
import sys
from pathlib import Path

ledger = Path(sys.argv[1]) / "ledger" / "events.jsonl"
out, dropped = [], 0
for line in ledger.read_text(encoding="utf-8").splitlines():
    ev = json.loads(line)
    if ev.get("type") == "txn.categorized" and ev.get("category") == "groceries":
        dropped += 1
        continue
    out.append(json.dumps(ev, ensure_ascii=False))
ledger.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"corrupted: dropped {dropped} groceries categorizations")
