#!/usr/bin/env python3
"""Plausible-but-wrong fixture for the verifier's own test (fixture rule).

Simulates the realistic agent failure of skipping transfer matching: strips
every txn.matched event from the ledger, so refill legs count as spending and
the transfer volume is zero. The verifier MUST fail this workspace.

Usage: corrupt.py <workspace>
"""
import sys
from pathlib import Path

ledger = Path(sys.argv[1]) / "ledger" / "events.jsonl"
lines = [l for l in ledger.read_text(encoding="utf-8").splitlines()
         if '"txn.matched"' not in l]
ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"corrupted: removed txn.matched events from {ledger}")
