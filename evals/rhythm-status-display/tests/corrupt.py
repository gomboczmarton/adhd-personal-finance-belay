#!/usr/bin/env python3
"""Plausible-but-wrong fixture for the verifier's own test (fixture rule).

Simulates the realistic display failure of a "helpful" dashboard: the return
line counts what piled up, and an awareness category that ran past its
reference is flagged as over. Both read as information to a designer and as
blame to an ADHD user. The verifier MUST fail this workspace.

Usage: corrupt.py <workspace>
"""
import json
import sys
from pathlib import Path

disp = Path(sys.argv[1]) / ".display"
line = disp / "line_2026-11-20.txt"
line.write_text(line.read_text(encoding="utf-8").rstrip("\n") + " · 4 months to catch up\n",
                encoding="utf-8")
status = disp / "status_2026-07-10.json"
s = json.loads(status.read_text(encoding="utf-8"))
for m in s["closed_month"]["meters"]:
    if m["kind"] == "awareness" and m["actual"] > m["plan"]:
        m["over"] = True
        break
status.write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
print(f"corrupted: backlog count in {line.name}, awareness 'over' in {status.name}")
