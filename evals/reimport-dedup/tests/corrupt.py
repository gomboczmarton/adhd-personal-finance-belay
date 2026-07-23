#!/usr/bin/env python3
"""Plausible-but-wrong fixture: broken dedup. Duplicates the final month's
checking txn.imported events (as a naive hash-less ingester would on
re-import), doubling June income and spend. The verifier MUST fail this
workspace.

Usage: corrupt.py <workspace>
"""
import json
import sys
from pathlib import Path

ledger = Path(sys.argv[1]) / "ledger" / "events.jsonl"
lines = ledger.read_text(encoding="utf-8").splitlines()
dupes = [l for l in lines
         if '"txn.imported"' in l
         and json.loads(l)["account"] == "main"
         and json.loads(l)["date"].startswith("2026-06")]
ledger.write_text("\n".join(lines + dupes) + "\n", encoding="utf-8")
print(f"corrupted: appended {len(dupes)} duplicate imported events")
