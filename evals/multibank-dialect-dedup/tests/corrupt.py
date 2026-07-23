#!/usr/bin/env python3
"""Plausible-but-wrong fixture (fixture rule): the double-import failure —
one bank's export gets ingested twice (classic multi-account slip). Re-appends
the first five txn.imported events verbatim, so their hashes appear twice.
The verifier MUST fail this workspace (no_duplicate_hashes breaks).

Usage: corrupt.py <workspace>
"""
import json
import sys
from pathlib import Path

ledger = Path(sys.argv[1]) / "ledger" / "events.jsonl"
lines = ledger.read_text(encoding="utf-8").splitlines()
dups = [l for l in lines if json.loads(l).get("type") == "txn.imported"][:5]
ledger.write_text("\n".join(lines + dups) + "\n", encoding="utf-8")
print(f"corrupted: re-appended {len(dups)} already-imported events (duplicate hashes)")
