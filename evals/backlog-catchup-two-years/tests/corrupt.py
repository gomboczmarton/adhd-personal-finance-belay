#!/usr/bin/env python3
"""Plausible-but-wrong fixture (fixture rule): the backlog-fatigue failure —
after two years of imports the agent stops matching transfers for the final
month ("almost done, the last refills can wait"). Drops every txn.matched
event whose ts falls in 2026-06, so June's refill legs are no longer paired
and the month's transfer volume diverges from the manifest. The verifier MUST
fail this workspace.

Usage: corrupt.py <workspace>
"""
import json
import sys
from pathlib import Path

ledger = Path(sys.argv[1]) / "ledger" / "events.jsonl"
out, dropped = [], 0
for line in ledger.read_text(encoding="utf-8").splitlines():
    ev = json.loads(line)
    if ev.get("type") == "txn.matched" and str(ev.get("ts", "")).startswith("2026-06"):
        dropped += 1
        continue
    out.append(json.dumps(ev, ensure_ascii=False))
if not dropped:
    sys.exit("corrupt.py: no June 2026 txn.matched events found — fixture invalid")
ledger.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"corrupted: dropped {dropped} June-2026 transfer matches")
