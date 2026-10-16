#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Where the user is in the monthly rhythm — the view-model every display reads.

Usage:
    uv run harness/scripts/status.py <workspace> [--today YYYY-MM-DD] [--line]

One source for every surface: the terminal mod (belay-ui) and the status line
both render this JSON and do no math or judgement of their own. This script
only READS the workspace (budgets, reconcile reports, onboarding state); the
numbers come from reconcile.py's report and the budget's frontmatter, compared
here in Decimal.

Situations:
  empty         no workspace yet                    -> /onboarding
  onboarding    a non-done stage in onboarding-state.md -> resume it
  welcome_back  two or more months open since the last closed one. Displays
                show no list, count or numbers here (welcome-back iron rules).
  rhythm        everything else: plan / close / buy-check

Ambient surfaces (band, status line) carry rhythm, never amounts: Belay's
envelope experiment is designed with "no mid-month alerts", so numbers live
only on pull surfaces (the /belay pane, the HTML report). `closed_month` holds
the last reconciled month's meters for those.

--line prints one status-line string (ANSI) instead of JSON. Exit code is
always 0: a display is never a gate.
"""

from __future__ import annotations

import datetime
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml

SCHEMA = "belay-status/1"
TEAL, WARM, DIM, END = "\033[38;2;47;158;146m", "\033[38;2;217;140;79m", "\033[2m", "\033[0m"
STAGES = ["exports", "mapping", "meanings", "patterns", "yearly", "mode_goals", "first_budget"]


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    return yaml.safe_load(text[4: text.find("\n---", 4)]) or {}


def month_of(day: datetime.date) -> str:
    return f"{day.year}-{day.month:02d}"


def prev_month(m: str) -> str:
    y, mo = map(int, m.split("-"))
    return f"{y - 1}-12" if mo == 1 else f"{y}-{mo - 1:02d}"


def month_name(m: str) -> str:
    return datetime.date(int(m[:4]), int(m[5:]), 1).strftime("%B")


def whole(x) -> str:
    """Display form, as the HTML report shows meters: whole currency units."""
    return str(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def closed_months(ws: Path) -> list[str]:
    root = ws / "months"
    if not root.is_dir():
        return []
    return sorted(m.name for m in root.iterdir()
                  if (m / "reports" / f"reconcile_{m.name}.json").exists())


def meters(ws: Path, month: str) -> list[dict]:
    data = json.loads((ws / "months" / month / "reports" / f"reconcile_{month}.json")
                      .read_text(encoding="utf-8"))
    spend = data.get("months", {}).get(month, {}).get("spend", {})
    budget = ws / "months" / month / "budget.md"
    fm = frontmatter(budget) if budget.exists() else {}
    plans = [("envelope", fm.get("allocations") or {}),
             ("awareness", fm.get("awareness_targets") or {})]
    out = []
    for kind, plan in plans:
        for cat, target in plan.items():
            actual = Decimal(str(spend.get(cat, 0)))
            target = Decimal(str(target))
            out.append({
                "category": cat, "kind": kind,
                "actual": str(actual), "plan": str(target),
                "actual_display": whole(actual), "plan_display": whole(target),
                # envelopes can run over; awareness targets are a reference,
                # never a limit ("full is not bad", D2a) — no over flag there
                "over": kind == "envelope" and actual > target,
            })
    return out


def status(ws: Path, today: datetime.date) -> dict:
    month = month_of(today)
    out = {"schema": SCHEMA, "today": today.isoformat(), "month": month,
           "month_name": month_name(month), "situation": "empty",
           "onboarding": None, "rhythm": None, "overlay": [],
           "closed_month": None, "next_step": {"command": "/onboarding",
                                               "label": "drop your bank exports in finance/inbox/ to begin"}}
    if not ws.is_dir():
        return out

    onb = ws / "onboarding-state.md"
    if onb.exists():
        fm = frontmatter(onb)
        stages = fm.get("stages", fm)
        open_stage = next((s for s in STAGES if stages.get(s) not in (None, "done")), None)
        if open_stage is not None:
            out["situation"] = "onboarding"
            out["onboarding"] = {"next_stage": open_stage}
            out["next_step"] = {"command": "/onboarding",
                                "label": f"pick up where you left off: {open_stage.replace('_', ' ')}"}
            return out

    closed = closed_months(ws)
    if not closed and not (ws / "months").is_dir():
        return out
    last = closed[-1] if closed else None
    gap, m = [], prev_month(month)
    while last is not None and m > last:
        gap.append(m)
        m = prev_month(m)
    if len(gap) >= 2:
        out["situation"] = "welcome_back"
        out["next_step"] = {"command": "/welcome-back",
                            "label": "a five-minute catch-up, whenever you like"}
        return out

    budget = ws / "months" / month / "budget.md"
    plan_ready = budget.exists()
    previous_closed = prev_month(month) in closed or last == month
    out["situation"] = "rhythm"
    out["rhythm"] = {"plan_ready": plan_ready, "previous_closed": previous_closed,
                     "last_closed": last}
    if plan_ready:
        out["overlay"] = [{"name": o.get("name", ""), "amount": str(o.get("amount", "")),
                           "amount_display": whole(o.get("amount", 0)),
                           "done": bool(o.get("done"))}
                          for o in frontmatter(budget).get("overlay") or []]
    if last is not None:
        out["closed_month"] = {"month": last, "month_name": month_name(last),
                               "meters": meters(ws, last)}
    if not previous_closed:
        prev = prev_month(month)
        out["next_step"] = {"command": "/reconcile-month",
                            "label": f"close {month_name(prev)} when its exports are in"}
    elif not plan_ready:
        out["next_step"] = {"command": "/monthly-prep", "label": f"plan {month_name(month)}"}
    else:
        out["next_step"] = {"command": "/purchase-check",
                            "label": "thinking about a buy? a quick, factual picture"}
    return out


def line(s: dict) -> str:
    head = f"{TEAL}◉ Belay{END}"
    if s["situation"] == "welcome_back":
        return f"{head} {DIM}· good to see you · {s['next_step']['command']}{END}"
    if s["situation"] in ("empty", "onboarding"):
        return f"{head} {DIM}· {s['next_step']['label']} · {s['next_step']['command']}{END}"
    r = s["rhythm"]
    plan = f"{TEAL}plan ✓{END}" if r["plan_ready"] else f"{DIM}plan ○{END}"
    return f"{head} · {s['month_name']} · {plan} · {DIM}next {s['next_step']['command']}{END}"


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print(__doc__, file=sys.stderr)
        return 0
    today = (datetime.date.fromisoformat(args[args.index("--today") + 1])
             if "--today" in args else datetime.date.today())
    try:
        s = status(Path(args[0]), today)
    except (OSError, ValueError, KeyError, yaml.YAMLError) as e:
        s = {"schema": SCHEMA, "today": today.isoformat(), "situation": "unreadable",
             "error": f"{type(e).__name__}: {e}",
             "next_step": {"command": "/welcome-back", "label": "let's look at it together"}}
    if "--line" in args:
        print(line(s) if s["situation"] != "unreadable"
              else f"{TEAL}◉ Belay{END} {DIM}· let's look at it together{END}")
    else:
        print(json.dumps(s, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
