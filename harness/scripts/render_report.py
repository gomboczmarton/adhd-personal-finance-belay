#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Render the monthly HTML report — D13: coach's-letter shell, energy meters,
kind-statement table one layer down. Write-only human view (D5).

Usage:
    uv run harness/scripts/render_report.py <workspace> <YYYY-MM> --data <reconcile.json> [--letter <file.md>]

--data    reconcile.py output (the month's numbers; this script does NO math
          beyond plan-minus-actual differences, computed in Decimal)
--letter  optional markdown fragment written by the agent during reconcile-month:
          the letter body (one win first, numbers in sentences, ONE decision).
          Without it, a plain factual opening is rendered instead.

Meter semantics (D13/D2a): envelopes render as capacity bars (outline = plan,
fill = actual, warm fill = over). Awareness targets render with a reference
tick, never as a limit — full is not bad.

Output: months/<M>/reports/report_<M>.html. Prints JSON {"written": path}.
"""

from __future__ import annotations

import html
import json
import sys
from decimal import Decimal
from pathlib import Path

import yaml

CSS = """
:root{--paper:#f7f6f2;--ink:#191817;--ink2:#5c5a54;--ink3:#898781;--rule:#e1e0d9;
--card:#fcfcfb;--ring:rgba(11,11,11,.10);--blue:#2a78d6;--aqua:#1baf7a;
--warm:#ec835a;--good:#006300;--goodbg:#0ca30c14;--goodring:#0ca30c55;
--overink:#8a3d14;--overbg:#ec835a1a;--overring:#ec835a66;--cap:#c3c2b7}
@media (prefers-color-scheme: dark){:root{--paper:#121211;--ink:#eceae2;--ink2:#b0aea5;
--ink3:#7c7a73;--rule:#2c2c2a;--card:#1a1a19;--ring:rgba(255,255,255,.10);
--blue:#3987e5;--aqua:#199e70;--warm:#e66767;--good:#0ca30c;--cap:#383835}}
:root[data-theme="dark"]{--paper:#121211;--ink:#eceae2;--ink2:#b0aea5;--ink3:#7c7a73;
--rule:#2c2c2a;--card:#1a1a19;--ring:rgba(255,255,255,.10);--blue:#3987e5;
--aqua:#199e70;--warm:#e66767;--good:#0ca30c;--cap:#383835}
:root[data-theme="light"]{--paper:#f7f6f2;--ink:#191817;--ink2:#5c5a54;--ink3:#898781;
--rule:#e1e0d9;--card:#fcfcfb;--ring:rgba(11,11,11,.10);--blue:#2a78d6;--aqua:#1baf7a;
--warm:#ec835a;--good:#006300;--cap:#c3c2b7}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);
font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}
.page{max-width:760px;margin:0 auto;padding:44px 22px 90px}
.date{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink3)}
h1{font-size:clamp(22px,3.5vw,30px);line-height:1.25;margin:.35em 0 .6em;text-wrap:balance}
.letter p{margin:0 0 12px;max-width:62ch}
.win{border-left:3px solid var(--good);padding:2px 0 2px 14px;color:var(--good);font-weight:550}
.ask{margin:18px 0 0;padding-top:14px;border-top:1px solid var(--rule);color:var(--ink2);font-size:15px}
.ask b{color:var(--ink)}
.meters{margin:34px 0 8px;display:grid;gap:12px}
.mrow{display:grid;grid-template-columns:140px 1fr 96px;gap:10px;align-items:center;font-size:13.5px}
.mrow .lbl{font-weight:600}
.track{position:relative;height:14px}
.cap{position:absolute;inset:0;border:1px solid var(--cap);border-radius:4px}
.fill{position:absolute;top:2px;bottom:2px;left:2px;border-radius:3px;background:var(--blue)}
.fill.over{background:var(--warm)}.fill.save{background:var(--aqua)}
.tick{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--ink);opacity:.5}
.num{font-variant-numeric:tabular-nums;text-align:right;color:var(--ink2);white-space:nowrap}
.legend{font-size:12px;color:var(--ink3);margin:4px 0 0}
details{margin-top:36px}
summary{cursor:pointer;font-weight:650;color:var(--ink2);font-size:14px}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:14px;background:var(--card);
border:1px solid var(--ring);border-radius:8px;overflow:hidden}
th{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink3);text-align:left;
font-weight:650;padding:8px 10px;border-bottom:1px solid var(--cap)}
td{padding:8px 10px;border-bottom:1px solid var(--rule);font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:0}
td.r,th.r{text-align:right}
.chip{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:650;
padding:1px 8px;border-radius:99px;border:1px solid}
.chip::before{content:"";width:7px;height:7px;border-radius:99px;background:currentColor}
.chip.ok{color:var(--good);border-color:var(--goodring);background:var(--goodbg)}
.chip.over{color:var(--overink);border-color:var(--overring);background:var(--overbg)}
@media (prefers-color-scheme: dark){.chip.over{color:var(--warm)}}
:root[data-theme="dark"] .chip.over{color:var(--warm)}
.mrow:hover .fill{filter:brightness(1.12)}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
"""


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text[4 : text.find("\n---", 4)])


def md_to_html(md: str) -> str:
    """Tiny renderer for the letter fragment: paragraphs, **bold**, > win lines."""
    out = []
    for block in md.strip().split("\n\n"):
        block = block.strip()
        if not block:
            continue
        cls = ""
        if block.startswith("> "):
            block, cls = block[2:], ' class="win"'
        text = html.escape(block).replace("\n", " ")
        while "**" in text:
            text = text.replace("**", "<b>", 1).replace("**", "</b>", 1)
        out.append(f"<p{cls}>{text}</p>")
    return "\n".join(out)


def meter(label: str, planned: Decimal, actual: Decimal, kind: str) -> str:
    over = actual > planned and kind == "envelope"
    width = min(int(actual / planned * 100), 100) if planned else 0
    fill_cls = "fill over" if over else ("fill save" if kind == "savings" else "fill")
    if kind == "awareness" and planned:
        # awareness: outline is the reference, tick marks actual — never a "fullness"
        tick = f'<span class="tick" style="left:{min(int(actual / planned * 100), 98)}%"></span>'
        bar = f'<span class="cap"></span>{tick}'
    else:
        bar = f'<span class="cap"></span><span class="{fill_cls}" style="width:{width}%"></span>'
    title = f"{actual} of {planned} planned"
    return (f'<div class="mrow"><span class="lbl">{html.escape(label)}</span>'
            f'<span class="track" title="{title}">{bar}</span>'
            f'<span class="num">{actual:,.0f} / {planned:,.0f}</span></div>')


def main() -> int:
    if len(sys.argv) < 5:
        print(__doc__, file=sys.stderr)
        return 2
    ws, month = Path(sys.argv[1]), sys.argv[2]
    data_path = Path(sys.argv[sys.argv.index("--data") + 1])
    letter_path = Path(sys.argv[sys.argv.index("--letter") + 1]) if "--letter" in sys.argv else None

    rec = json.loads(data_path.read_text(encoding="utf-8"))
    m = rec["months"][month] if "months" in rec else rec
    budget = frontmatter(ws / "months" / month / "budget.md") \
        if (ws / "months" / month / "budget.md").exists() else {}
    strategy = frontmatter(ws / "strategy.md") if (ws / "strategy.md").exists() else {}
    adoption = strategy.get("envelope_adoption") or {}
    env_of = {v["envelope"]: k for k, v in adoption.items()}

    spend = {k: Decimal(str(v)) for k, v in m["spend"].items()}
    income = Decimal(str(m["income"]))
    allocations = {k: Decimal(str(v)) for k, v in (budget.get("allocations") or {}).items()}
    awareness = {k: Decimal(str(v)) for k, v in (budget.get("awareness_targets") or {}).items()}
    savings_target = Decimal(str(budget.get("savings_target", 0)))

    meters, rows = [], []
    for env, planned in allocations.items():
        cat = env_of.get(env, env.removeprefix("env_"))
        actual = spend.get(cat, Decimal(0))
        meters.append(meter(cat, planned, actual, "envelope"))
        diff = planned - actual
        chip = '<span class="chip ok">under</span>' if diff >= 0 else \
               '<span class="chip over">over · worth a look</span>'
        rows.append(f"<tr><td>{html.escape(cat)} (envelope)</td><td class='r'>{planned:,.0f}</td>"
                    f"<td class='r'>{actual:,.0f}</td><td class='r'>{diff:+,.0f}</td><td>{chip}</td></tr>")
    for cat, target in awareness.items():
        actual = spend.get(cat, Decimal(0))
        meters.append(meter(cat, target, actual, "awareness"))
        diff = target - actual
        chip = '<span class="chip ok">within view</span>' if diff >= 0 else \
               '<span class="chip over">above the mark</span>'
        rows.append(f"<tr><td>{html.escape(cat)} (awareness)</td><td class='r'>{target:,.0f}</td>"
                    f"<td class='r'>{actual:,.0f}</td><td class='r'>{diff:+,.0f}</td><td>{chip}</td></tr>")
    if savings_target > 0:
        meters.append(meter("savings", savings_target, savings_target, "savings"))

    if letter_path and letter_path.exists():
        letter_html = md_to_html(letter_path.read_text(encoding="utf-8"))
        headline = f"{month} is closed."
    else:
        n_uncat = len(m.get("uncategorized", []))
        letter_html = (f"<p>Income landed at <b>{income:,.0f}</b>; {m['txns']} transactions are "
                       f"accounted for and {'nothing needs you' if n_uncat == 0 else f'{n_uncat} need a look'}. "
                       f"The meters below show how the month actually went.</p>")
        headline = f"{month} is closed — the numbers are in."

    page = f"""<title>Money report — {month}</title>
<style>{CSS}</style>
<div class="page">
  <div class="date">{month} · read time: about a minute</div>
  <h1>{headline}</h1>
  <div class="letter">{letter_html}</div>
  <div class="meters">{''.join(meters)}</div>
  <div class="legend">outline = planned · fill = actual · warm = over (envelopes only) ·
  tick = where you are (awareness — a reference, not a limit)</div>
  <details><summary>The full statement</summary>
  <table><thead><tr><th>Item</th><th class="r">Planned</th><th class="r">Actual</th>
  <th class="r">Diff</th><th>State</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
  </details>
</div>
"""
    out = ws / "months" / month / "reports" / f"report_{month}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(json.dumps({"written": str(out)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
