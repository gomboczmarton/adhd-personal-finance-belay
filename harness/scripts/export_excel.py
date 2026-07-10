#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "openpyxl>=3.1"]
# ///
"""Generate write-only Excel views (D5): humans read these, machines never do.

Usage:
    uv run harness/scripts/export_excel.py <workspace> <YYYY-MM> budget
    uv run harness/scripts/export_excel.py <workspace> <YYYY-MM> reconciliation --data <reconcile.json>

budget          renders months/<M>/budget.md: allocations + awareness targets +
                overlay (yearly-bank rows highlighted yellow, per plan.md) +
                savings target + income check line.
reconciliation  renders plan vs actual per envelope/category from budget.md and
                a reconcile.py JSON output file (pass the month's entry source).

Output: months/<M>/reports/<kind>_<M>.xlsx. Prints JSON {"written": path}.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

YELLOW = PatternFill(start_color="FFF3B0", end_color="FFF3B0", fill_type="solid")
BOLD = Font(bold=True)
HEADER = Font(bold=True, size=12)


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text[4 : text.find("\n---", 4)])


def autosize(ws) -> None:
    for column in ws.columns:
        width = max((len(str(c.value)) for c in column if c.value is not None), default=8)
        ws.column_dimensions[column[0].column_letter].width = min(width + 2, 44)


def render_budget(ws_dir: Path, month: str) -> Path:
    fm = frontmatter(ws_dir / "months" / month / "budget.md")
    wb = Workbook()
    sheet = wb.active
    sheet.title = f"Budget {month}"
    sheet.append([f"Budget {month}", "", fm.get("currency", "")])
    sheet["A1"].font = HEADER
    sheet.append([])
    sheet.append(["Item", "Planned", "Note"])
    for c in sheet[3]:
        c.font = BOLD

    overlay = fm.get("overlay") or []
    overlay_by_target: dict[str, list[dict]] = {}
    for o in overlay:
        overlay_by_target.setdefault(o.get("envelope") or o.get("category", ""), []).append(o)

    for env, amount in (fm.get("allocations") or {}).items():
        sheet.append([env, amount, "envelope"])
        for o in overlay_by_target.get(env, []):
            row = sheet.max_row + 1
            sheet.append([f"  ↳ {o['name']}", o["amount"], "due this month (yearly bank)"])
            for cell in sheet[row]:
                cell.fill = YELLOW
    for cat, amount in (fm.get("awareness_targets") or {}).items():
        sheet.append([cat, amount, "awareness target"])
        for o in overlay_by_target.get(cat, []):
            row = sheet.max_row + 1
            sheet.append([f"  ↳ {o['name']}", o["amount"], "due this month (yearly bank)"])
            for cell in sheet[row]:
                cell.fill = YELLOW

    sheet.append([])
    sheet.append(["Savings target", fm.get("savings_target", 0), ""])
    sheet[sheet.max_row][0].font = BOLD
    sheet.append(["Income planned", fm.get("income_planned", 0), ""])
    sheet[sheet.max_row][0].font = BOLD
    autosize(sheet)
    out = ws_dir / "months" / month / "reports" / f"budget_{month}.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


def render_reconciliation(ws_dir: Path, month: str, data_path: Path) -> Path:
    fm = frontmatter(ws_dir / "months" / month / "budget.md") \
        if (ws_dir / "months" / month / "budget.md").exists() else {}
    rec = json.loads(data_path.read_text(encoding="utf-8"))
    month_data = rec["months"][month] if "months" in rec else rec

    # planned per category: awareness targets directly; envelope allocations mapped
    # back to categories is ambiguous, so envelope rows are compared as envelopes
    planned_awareness = fm.get("awareness_targets") or {}
    planned_env = fm.get("allocations") or {}

    wb = Workbook()
    sheet = wb.active
    sheet.title = f"Reconciliation {month}"
    sheet.append([f"Reconciliation {month}"])
    sheet["A1"].font = HEADER
    sheet.append([])
    sheet.append(["Category", "Planned", "Actual", "Difference"])
    for c in sheet[3]:
        c.font = BOLD

    spend = month_data["spend"]
    for cat, actual in sorted(spend.items()):
        planned = planned_awareness.get(cat)
        row = [cat, planned if planned is not None else "", round(actual, 2),
               round(planned - actual, 2) if planned is not None else ""]
        sheet.append(row)
    for env, planned in sorted(planned_env.items()):
        sheet.append([env, planned, "", "see envelope statement"])

    sheet.append([])
    sheet.append(["Income", "", round(month_data["income"], 2), ""])
    sheet.append(["Internal transfers (excluded)", "", round(month_data["transfers"], 2), ""])
    sheet.append(["Uncategorized", "", len(month_data["uncategorized"]), ""])
    for r in range(sheet.max_row - 2, sheet.max_row + 1):
        sheet[r][0].font = BOLD
    autosize(sheet)
    out = ws_dir / "months" / month / "reports" / f"reconciliation_{month}.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    ws_dir, month, kind = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    if kind == "budget":
        out = render_budget(ws_dir, month)
    elif kind == "reconciliation":
        data = Path(sys.argv[sys.argv.index("--data") + 1])
        out = render_reconciliation(ws_dir, month, data)
    else:
        sys.exit(f"error: unknown kind '{kind}'")
    print(json.dumps({"written": str(out)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
