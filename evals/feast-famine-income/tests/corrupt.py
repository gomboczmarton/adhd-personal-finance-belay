#!/usr/bin/env python3
"""Plausible-but-wrong fixture (fixture rule): the smoothing failure — June
2026 is a feast month, so the agent quietly disappears the largest client
payment to make the month look normal. Deletes the biggest positive June
import and every event referencing its hash. The verifier MUST fail this
workspace (June income diverges from the manifest).

Usage: corrupt.py <workspace>
"""
import json
import sys
from pathlib import Path

ledger = Path(sys.argv[1]) / "ledger" / "events.jsonl"
lines = ledger.read_text(encoding="utf-8").splitlines()
events = [json.loads(l) for l in lines]
june_income = [ev for ev in events
               if ev.get("type") == "txn.imported"
               and str(ev.get("date", "")).startswith("2026-06")
               and float(ev.get("amount", 0)) > 0]
if not june_income:
    sys.exit("corrupt.py: no positive June 2026 imports found — fixture invalid")
target = max(june_income, key=lambda ev: float(ev["amount"]))["hash"]
kept = [ev for ev in events
        if ev.get("hash") != target and target not in ev.get("hashes", [])]
ledger.write_text("\n".join(json.dumps(ev, ensure_ascii=False) for ev in kept) + "\n",
                  encoding="utf-8")
print(f"corrupted: erased the largest June income payment (hash {target})")
