#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Verifier for rhythm-status-display: independent recomputation + tone rules.

Usage: verify_display.py <workspace>   (exit 0 = pass; JSON findings on stdout)

1. Provenance: every meter in the mid-July view-model equals the June
   reconcile report (actual) and the June budget (plan) exactly, in Decimal;
   the display string is that value rounded half-up; only envelopes may be over.
2. Rhythm: early August asks to close July (/reconcile-month).
3. Return: after the long break the view-model is welcome_back with no month
   view, no extras and no count anywhere.
4. Ambient: no status line carries a digit (no amounts, no counts) or a
   blaming word; the return line opens warmly.
"""
import json
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml

DAYS = {"rhythm": "2026-07-10", "close": "2026-08-02", "return": "2026-11-20"}
BANNED = re.compile(r"missed|overdue|behind|\blate\b|fail|should have|again|sorry|unfortunately", re.I)
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text[4: text.find("\n---", 4)]) or {}


def main() -> int:
    ws = Path(sys.argv[1])
    disp = ws / ".display"
    problems: list[str] = []
    status, lines = {}, {}
    for key, day in DAYS.items():
        try:
            status[key] = json.loads((disp / f"status_{day}.json").read_text(encoding="utf-8"))
            lines[key] = ANSI.sub("", (disp / f"line_{day}.txt").read_text(encoding="utf-8")).strip()
        except (OSError, ValueError) as e:
            problems.append(f"{day}: missing or unreadable output ({type(e).__name__})")
    if problems:
        print(json.dumps({"pass": False, "problems": problems}, indent=2))
        return 1

    # 1. provenance against the files on disk
    s = status["rhythm"]
    if s.get("situation") != "rhythm":
        problems.append(f"mid-July situation is {s.get('situation')!r}, expected 'rhythm'")
    cm = s.get("closed_month") or {}
    month = cm.get("month")
    if month != "2026-06":
        problems.append(f"closed month is {month!r}, expected '2026-06'")
    else:
        report = json.loads((ws / "months" / month / "reports" / f"reconcile_{month}.json")
                            .read_text(encoding="utf-8"))
        spend = report["months"][month]["spend"]
        fm = frontmatter(ws / "months" / month / "budget.md")
        plans = {**{c: ("envelope", v) for c, v in (fm.get("allocations") or {}).items()},
                 **{c: ("awareness", v) for c, v in (fm.get("awareness_targets") or {}).items()}}
        shown = {m["category"]: m for m in cm.get("meters", [])}
        if set(shown) != set(plans):
            problems.append(f"meters {sorted(shown)} != budget categories {sorted(plans)}")
        for cat, (kind, target) in plans.items():
            m = shown.get(cat)
            if m is None:
                continue
            actual, plan = Decimal(str(spend.get(cat, 0))), Decimal(str(target))
            if Decimal(m["actual"]) != actual or Decimal(m["plan"]) != plan:
                problems.append(f"{cat}: shows {m['actual']}/{m['plan']}, files say {actual}/{plan}")
            for field, value in (("actual_display", actual), ("plan_display", plan)):
                want = str(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
                if m[field] != want:
                    problems.append(f"{cat}: {field} {m[field]!r} != {want!r}")
            if m["kind"] != kind:
                problems.append(f"{cat}: kind {m['kind']!r} != {kind!r}")
            if m["over"] != (kind == "envelope" and actual > plan):
                problems.append(f"{cat}: over={m['over']} — awareness targets are never 'over' (D2a)")

    # 2. rhythm
    if status["close"].get("next_step", {}).get("command") != "/reconcile-month":
        problems.append("early August should offer /reconcile-month as the next small step")

    # 3. return after a break
    r = status["return"]
    if r.get("situation") != "welcome_back":
        problems.append(f"after the break situation is {r.get('situation')!r}, expected 'welcome_back'")
    if r.get("closed_month") or r.get("overlay"):
        problems.append("welcome_back must not carry a month view or a list")

    # 4. ambient lines
    for key, line in lines.items():
        if re.search(r"\d", line):
            problems.append(f"{DAYS[key]} status line carries a figure: {line!r}")
        if BANNED.search(line):
            problems.append(f"{DAYS[key]} status line has a blaming word: {line!r}")
    if "good to see you" not in lines["return"].lower():
        problems.append(f"return line does not open warmly: {lines['return']!r}")

    print(json.dumps({"pass": not problems, "problems": problems,
                      "meters_checked": len((cm or {}).get("meters", []))}, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
