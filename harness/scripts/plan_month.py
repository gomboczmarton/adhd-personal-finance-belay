#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Draft next month's budget from history + the yearly spending bank.

Usage:
    uv run harness/scripts/plan_month.py <workspace> <YYYY-MM> [--income N]

Deterministic drafting (the agent presents and adjusts, this script computes):
  income_planned   --income override, else average of the last 3 months' income
                   (rule-categorized ledger income, internal transfers excluded)
  per category     average spend of the last 3 full months
                     -> envelope allocation if strategy maps it to an envelope
                        (envelope_adoption, or env_<category> account in full
                        envelope mode), else awareness target
  overlay          yearly-bank items due this month (source: yearly_bank,
                   highlighted at render time); amounts are ADDED to their
                   envelope's allocation so the invariant stays exact
  savings_target   income - allocations - awareness targets (Decimal, floor 0)

Writes months/<YYYY-MM>/budget.md (refusing to overwrite an existing one)
and prints a JSON summary.
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import yaml


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text[4 : text.find("\n---", 4)])


def prev_months(month: str, n: int) -> list[str]:
    y, m = int(month[:4]), int(month[5:7])
    out = []
    for _ in range(n):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        out.append(f"{y:04d}-{m:02d}")
    return out


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    ws, month = Path(sys.argv[1]), sys.argv[2]
    income_override = Decimal(sys.argv[sys.argv.index("--income") + 1]) if "--income" in sys.argv else None

    out_path = ws / "months" / month / "budget.md"
    if out_path.exists():
        sys.exit(f"error: {out_path} already exists — edit it instead of re-drafting")

    strategy = frontmatter(ws / "strategy.md")
    accounts = frontmatter(ws / "accounts.md")["accounts"]
    envelope_ids = {a["id"] for a in accounts if a.get("type") == "envelope"}
    adoption = strategy.get("envelope_adoption") or {}
    mode = strategy["mode"]
    currency = next((a["currency"] for a in accounts), "EUR")

    events = [json.loads(l) for l in (ws / "ledger" / "events.jsonl")
              .read_text(encoding="utf-8").splitlines() if l.strip()]
    matched: set[str] = set()
    cats: dict[str, dict] = {}
    for ev in events:
        if ev["type"] == "txn.matched":
            matched.update(ev["hashes"])
        elif ev["type"] == "txn.categorized":
            cats[ev["hash"]] = ev

    window = prev_months(month, 3)
    income_by_month: dict[str, Decimal] = {m: Decimal(0) for m in window}
    spend: dict[str, Decimal] = {}
    for ev in events:
        if ev["type"] != "txn.imported" or ev["date"][:7] not in window:
            continue
        if ev["hash"] in matched:
            continue
        cat = cats.get(ev["hash"])
        if cat is None or cat["kind"] == "internal_transfer":
            continue
        amount = Decimal(str(ev["amount"]))
        if cat["kind"] == "income":
            income_by_month[ev["date"][:7]] += amount
        elif cat["kind"] in ("expense", "refund"):
            spend[cat["category"]] = spend.get(cat["category"], Decimal(0)) - amount

    income = income_override if income_override is not None else \
        (sum(income_by_month.values()) / len(window)).quantize(Decimal("0.01"))

    def envelope_for(category: str) -> str | None:
        if category in adoption:
            return adoption[category]["envelope"]
        if mode == "envelopes" and f"env_{category}" in envelope_ids:
            return f"env_{category}"
        return None

    allocations: dict[str, Decimal] = {}
    awareness: dict[str, Decimal] = {}
    for category, total in sorted(spend.items()):
        avg = (total / len(window)).quantize(Decimal("0.01"))
        if avg <= 0:
            continue
        env = envelope_for(category)
        if env:
            allocations[env] = allocations.get(env, Decimal(0)) + avg
        else:
            awareness[category] = avg

    overlay = []
    yearly_path = ws / "knowledge" / "yearly-bank.md"
    if yearly_path.exists():
        for item in frontmatter(yearly_path).get("items", []):
            if int(month[5:7]) in item["due_months"]:
                amount = Decimal(str(item["typical_amount"]))
                entry = {"name": item["name"], "amount": float(amount),
                         "category": item["category"], "source": "yearly_bank",
                         "yearly_bank_id": item["id"], "done": False}
                env = envelope_for(item["category"])
                if env:
                    entry["envelope"] = env
                    allocations[env] = allocations.get(env, Decimal(0)) + amount
                else:
                    awareness[item["category"]] = awareness.get(item["category"], Decimal(0)) + amount
                overlay.append(entry)

    committed = sum(allocations.values(), Decimal(0)) + sum(awareness.values(), Decimal(0))
    savings = max(income - committed, Decimal(0)).quantize(Decimal("0.01"))

    fm = {"schema_version": 1, "month": month, "currency": currency,
          "income_planned": float(income)}
    if allocations:
        fm["allocations"] = {k: float(v) for k, v in allocations.items()}
    if awareness:
        fm["awareness_targets"] = {k: float(v) for k, v in awareness.items()}
    if overlay:
        fm["overlay"] = overlay
    fm["savings_target"] = float(savings)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    body = (f"# {month} plan (draft)\n\n"
            f"Drafted from the average of {', '.join(reversed(window))}. "
            f"Yearly-bank items due this month are in the overlay (highlighted in the "
            f"Excel export). Adjust in conversation, then verify.\n")
    out_path.write_text(
        "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---\n\n" + body,
        encoding="utf-8")

    print(json.dumps({
        "month": month, "income_planned": float(income),
        "allocations": {k: float(v) for k, v in allocations.items()},
        "awareness_targets": {k: float(v) for k, v in awareness.items()},
        "overlay_items": [o["name"] for o in overlay],
        "savings_target": float(savings), "written": str(out_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
