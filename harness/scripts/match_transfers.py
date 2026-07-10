#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Match internal-transfer legs in the ledger (blindspot #2 core algorithm).

Usage:
    uv run harness/scripts/match_transfers.py <workspace> [--window N]

Pairs txn.imported events that look like the two legs of one internal transfer:
different accounts, amounts exactly opposite, dates within N days (default 2).
Same-day pairs are matched first (confidence 0.95), then the window widens by
one day per pass (confidence 0.85, 0.75). Each transaction is used at most
once; already-matched or already-categorized transactions are skipped, so the
matcher is idempotent. Appends txn.matched events.

Prints JSON: {"pairs": n, "unmatched_candidates": n}.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    ws = Path(sys.argv[1])
    window = int(sys.argv[sys.argv.index("--window") + 1]) if "--window" in sys.argv else 2

    ledger = ws / "ledger" / "events.jsonl"
    events = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]

    used: set[str] = set()   # hashes already part of a match
    for ev in events:
        if ev["type"] == "txn.matched":
            used.update(ev["hashes"])

    txns = {
        ev["hash"]: ev for ev in events
        if ev["type"] == "txn.imported" and ev["hash"] not in used
    }

    # candidate legs: group by absolute amount for O(n) pairing
    by_abs: dict[float, list[dict]] = {}
    for t in txns.values():
        by_abs.setdefault(abs(t["amount"]), []).append(t)

    new_matches: list[dict] = []
    for day_diff in range(window + 1):
        confidence = max(0.95 - 0.10 * day_diff, 0.5)
        for group in by_abs.values():
            outs = [t for t in group if t["amount"] < 0 and t["hash"] not in used]
            ins = [t for t in group if t["amount"] > 0 and t["hash"] not in used]
            for o in outs:
                od = date.fromisoformat(o["date"])
                best = None
                for i in ins:
                    if i["hash"] in used or i["account"] == o["account"]:
                        continue
                    if abs((date.fromisoformat(i["date"]) - od).days) == day_diff:
                        best = i
                        break
                if best is None:
                    continue
                used.update((o["hash"], best["hash"]))
                new_matches.append({
                    "v": 1, "ts": max(o["date"], best["date"]), "type": "txn.matched",
                    "hashes": [o["hash"], best["hash"]], "kind": "internal_transfer",
                    "by": "rule", "confidence": confidence,
                })

    with open(ledger, "a", encoding="utf-8") as out:
        for m in sorted(new_matches, key=lambda m: m["ts"]):
            out.write(json.dumps(m, ensure_ascii=False) + "\n")

    remaining = sum(
        1 for t in txns.values()
        if t["hash"] not in used and any(
            u["amount"] == -t["amount"] and u["account"] != t["account"]
            for u in txns.values()
        )
    )
    print(json.dumps({"pairs": len(new_matches), "unmatched_candidates": remaining}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
