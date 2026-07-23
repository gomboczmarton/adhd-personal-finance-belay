#!/usr/bin/env python3
"""Plausible-but-wrong fixture (fixture rule): the yearly-spike misfile — the
agent treats March's car weight tax as ordinary car spending is correct, but a
sloppier failure is filing car costs under eating_out when volume is high.
Rewrites every car categorization in the ledger to eating_out. The verifier
MUST fail this workspace (two per-category totals diverge from the manifest).

Usage: corrupt.py <workspace>
"""
import json
import sys
from pathlib import Path

ledger = Path(sys.argv[1]) / "ledger" / "events.jsonl"
out, moved = [], 0
for line in ledger.read_text(encoding="utf-8").splitlines():
    ev = json.loads(line)
    if ev.get("type") == "txn.categorized" and ev.get("category") == "car":
        ev["category"] = "eating_out"
        moved += 1
    out.append(json.dumps(ev, ensure_ascii=False))
ledger.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"corrupted: moved {moved} car categorizations to eating_out")
