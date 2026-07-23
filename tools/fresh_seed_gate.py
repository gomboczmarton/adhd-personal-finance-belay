#!/usr/bin/env python3
"""Fresh-seed release gate (D16): the structural defense against suite overfitting.

Regenerates every persona's fixtures with a DIFFERENT seed and requires the
full deterministic suite (fixture rule included) to stay green on the brand-new
ground truth. A harness that only memorized the published manifests fails here;
a harness that actually implements the capabilities passes with any seed.

Usage:
    python3 tools/fresh_seed_gate.py [--offset N]   # default offset: 1

Mechanism: personas are copied to a temp dir with `fixtures.seed` forced to
crc32(id) + offset (the generator's default is crc32(id)); fixtures are
regenerated from the copies into evals/fixtures/, the suite runs, and baseline
fixtures are regenerated from the original personas afterwards (always, even
on failure). Exit code = the suite's exit code.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PERSONAS = REPO / "evals" / "personas"
FIXTURES = REPO / "evals" / "fixtures"


def reseed(text: str, pid: str, offset: int) -> str:
    seed = zlib.crc32(pid.encode()) + offset
    if re.search(r"^\s*seed:", text, flags=re.M):
        return re.sub(r"^(\s*)seed:.*$", rf"\g<1>seed: {seed}", text, flags=re.M)
    return re.sub(r"^fixtures:\s*$", f"fixtures:\n  seed: {seed}", text, flags=re.M)


def generate(personas_dir: Path) -> int:
    return subprocess.run(
        ["uv", "run", str(REPO / "harness/scripts/generate_fixtures.py"),
         "--all", str(personas_dir), str(FIXTURES)], cwd=REPO).returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offset", type=int, default=1)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="fresh-seed-") as tmp:
        tmpdir = Path(tmp)
        for p in sorted(PERSONAS.glob("*.md")):
            text = p.read_text(encoding="utf-8")
            m = re.search(r"^id: (.+)$", text, flags=re.M)
            if not m:
                sys.exit(f"error: no id in {p}")
            (tmpdir / p.name).write_text(reseed(text, m.group(1), args.offset),
                                         encoding="utf-8")
        print(f"== fresh-seed gate: offset {args.offset}, "
              f"{len(list(tmpdir.glob('*.md')))} personas reseeded")
        if generate(tmpdir) != 0:
            print("fresh-seed generation failed", file=sys.stderr)
            rc = 1
        else:
            rc = subprocess.run(
                [sys.executable, str(REPO / "evals/run_local.py"), "--fixtures",
                 "--job-name", f"fresh-seed-{args.offset}"], cwd=REPO).returncode
    print("== restoring baseline fixtures")
    if generate(PERSONAS) != 0:
        print("warning: baseline fixture regeneration failed", file=sys.stderr)
        rc = rc or 1
    print(f"== fresh-seed gate: {'GREEN' if rc == 0 else 'RED'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
