#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Detect financial patterns in the ledger — the onboarding analysis engine (D12).

Usage:
    uv run harness/scripts/detect_patterns.py <workspace>

Reads txn.imported (+ categorized/matched) events and reports, as JSON:
  coverage           months actually PRESENT in the data (first, last, count, span)
                     — onboarding reports this instead of trusting filename claims
  income_pattern     candidate income streams with typical days-of-month, average
                     amount, regularity score
  monthly_recurring  ~monthly recurrences (subscription candidates)
  yearly_candidates  yearly recurrences; only proposed on >=13 months of history
                     AND a repeat in the same month-of-year across different years
  transfer_stats     matched pair volume, plus unmatched opposite-amount candidates

Grouping key: the counterparty when present, else the digit-stripped description
(real banks write a unique reference into every description — 2026-07-09
private-data simulation, finding #1). Each entry reports grouped_by.

Pure detection — proposes, never writes. The onboarding skill presents these
as evidence-backed questions; only user-confirmed facts become workspace state.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

YEARLY_MIN_MONTHS = 13  # below this, yearly proposals are noise (finding #2)


def group_key(t: dict) -> tuple[str, str]:
    """(key, grouped_by): counterparty if present, else digit-stripped desc."""
    cp = (t.get("counterparty") or "").strip().upper()
    if cp:
        return cp, "counterparty"
    stripped = " ".join(re.sub(r"\d+", " ", t["desc"].upper()).split())
    return stripped or t["desc"].upper(), "desc"


def month_span(first: str, last: str) -> int:
    fy, fm = int(first[:4]), int(first[5:7])
    ly, lm = int(last[:4]), int(last[5:7])
    return (ly - fy) * 12 + (lm - fm) + 1


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    ws = Path(sys.argv[1])
    events = [json.loads(l) for l in (ws / "ledger" / "events.jsonl")
              .read_text(encoding="utf-8").splitlines() if l.strip()]

    matched: set[str] = set()
    for ev in events:
        if ev["type"] == "txn.matched":
            matched.update(ev["hashes"])
    txns = [e for e in events if e["type"] == "txn.imported" and e["hash"] not in matched]

    months_present = sorted({t["date"][:7] for t in txns})
    n_months = len(months_present) or 1
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for t in txns:
        groups[group_key(t)].append(t)

    income, monthly, yearly = [], [], []
    for (key, grouped_by), group in sorted(groups.items()):
        months = sorted({t["date"][:7] for t in group})
        amounts = [t["amount"] for t in group]
        days = sorted({int(t["date"][8:10]) for t in group})
        coverage = len(months) / n_months

        if all(a > 0 for a in amounts) and len(group) >= 3 and coverage >= 0.5:
            income.append({
                "desc": key, "grouped_by": grouped_by, "count": len(group),
                "days": days[:5],
                "avg_amount": round(mean(amounts), 2),
                "regularity": round(coverage, 2),
                "months_covered": len(months),
            })
        elif all(a < 0 for a in amounts) and len(group) >= 2:
            per_month = len(group) / len(months)
            due = sorted({int(m[5:7]) for m in months})
            years_by_due = {mo: {m[:4] for m in months if int(m[5:7]) == mo} for mo in due}
            repeats_across_years = any(len(ys) >= 2 for ys in years_by_due.values())
            if len(months) >= 3 and 0.9 <= per_month <= 1.1 and coverage >= 0.6 and len(days) <= 3:
                monthly.append({
                    "desc": key, "grouped_by": grouped_by, "count": len(group),
                    "typical_day": days[0],
                    "avg_amount": round(-mean(amounts), 2),
                    "months_covered": len(months),
                })
            elif (n_months >= YEARLY_MIN_MONTHS and repeats_across_years
                  and coverage <= 0.25 and len(due) <= 2 and per_month <= 1.1):
                yearly.append({
                    "desc": key, "grouped_by": grouped_by, "count": len(group),
                    "due_months": due,
                    "avg_amount": round(-mean(amounts), 2),
                })

    all_imported = [e for e in events if e["type"] == "txn.imported"]
    unmatched_pairs = 0
    by_abs: dict[float, list[dict]] = defaultdict(list)
    for t in all_imported:
        if t["hash"] not in matched:
            by_abs[abs(t["amount"])].append(t)
    for group in by_abs.values():
        outs = [t for t in group if t["amount"] < 0]
        ins = [t for t in group if t["amount"] > 0]
        unmatched_pairs += min(len(outs), len(ins)) if outs and ins and \
            any(o["account"] != i["account"] for o in outs for i in ins) else 0

    print(json.dumps({
        "months_analyzed": n_months,
        "coverage": {
            "first_month": months_present[0] if months_present else None,
            "last_month": months_present[-1] if months_present else None,
            "months_present": len(months_present),
            "span_months": month_span(months_present[0], months_present[-1])
            if months_present else 0,
        },
        "income_pattern": sorted(income, key=lambda x: -x["avg_amount"]),
        "monthly_recurring": sorted(monthly, key=lambda x: -x["avg_amount"]),
        "yearly_candidates": sorted(yearly, key=lambda x: -x["avg_amount"]),
        "transfer_stats": {
            "matched_legs": len(matched),
            "unmatched_opposite_candidates": unmatched_pairs,
        },
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
