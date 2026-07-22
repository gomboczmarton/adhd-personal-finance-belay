#!/usr/bin/env python3
"""Deterministic gate for the dedup capability, on top of ledger_verify.

Checks the harness-observed re-import summary (artifact written by the run,
not a claim in prose): the second ingest of the same file must import 0 rows
and report every row as a duplicate.

Usage: test.py <artifacts-dir>   (exit 0 pass / 1 fail)
"""
import json
import sys
from pathlib import Path

artifacts = Path(sys.argv[1])
path = artifacts / "ingest_reimport.json"
if not path.exists():
    print("FAIL: no ingest_reimport.json artifact — re-import was not performed")
    sys.exit(1)
summary = json.loads(path.read_text(encoding="utf-8"))
ok = summary.get("imported") == 0 and summary.get("duplicates", 0) > 0 \
    and summary.get("duplicates") == summary.get("rows")
print(json.dumps({"reimport_summary": summary, "idempotent": ok}))
sys.exit(0 if ok else 1)
