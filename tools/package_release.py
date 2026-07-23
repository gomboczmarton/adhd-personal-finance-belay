#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Package the shippable harness for a tagged release (D16; ex-factory D14 tool).

Usage:

Builds dist/harness-v<version>.zip and dist/harness.zip (stable asset name for
`install.py --from-release`) containing ONLY the shippable whitelist:
    harness/skills/  harness/agents/  harness/scripts/  harness/schemas/
    install.py  VERSION

Sanitization gate (iron rule #2, enforced by a script, not by care): every
packaged text file is scanned for patterns that should never exist in this
factory's shippable output — card-number shapes, Hungarian bank account shapes,
IBANs, email addresses, and any absolute path leaking a builder's environment.
Any hit aborts the build with the file and line. The factory's example data is
synthetic by construction; this gate exists so a future mistake cannot ship.
"""

from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WHITELIST = ["harness/skills", "harness/agents", "harness/scripts", "harness/schemas"]
FILES = ["install.py", "VERSION"]

FORBIDDEN = [
    (re.compile(r"\b\d{6}\*+\d{3,4}\b"), "masked card number shape"),
    (re.compile(r"\b\d{16}\b"), "16-digit card-like number"),
    (re.compile(r"\b\d{8}-\d{8}(?:-\d{8})?\b"), "Hungarian bank account shape"),
    (re.compile(r"\b[A-Z]{2}\d{2}(?: ?\d{4}){4,7}\b"), "IBAN shape"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "email address"),
    (re.compile(r"/home/[a-z0-9_-]+/|/Users/[A-Za-z0-9_-]+/"), "absolute home path"),
]


def scan(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, IsADirectoryError):
        return []  # binary or dir — schemas/scripts/skills are all text; xlsx never ships
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        for pattern, label in FORBIDDEN:
            if pattern.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{i}: {label}")
    return hits


def collect() -> list[Path]:
    files: list[Path] = []
    for rel in WHITELIST:
        base = ROOT / rel
        if not base.is_dir():
            sys.exit(f"error: missing shippable dir {rel}")
        files += [p for p in sorted(base.rglob("*")) if p.is_file()
                  and "__pycache__" not in p.parts and not p.name.endswith(".pyc")]
    for rel in FILES:
        p = ROOT / rel
        if not p.is_file():
            sys.exit(f"error: missing shippable file {rel}")
        files.append(p)
    return files


def main() -> int:
    args = sys.argv[1:]
    version = args[args.index("--version") + 1] if "--version" in args else \
        (ROOT / "VERSION").read_text().strip()
    files = collect()

    problems: list[str] = []
    for f in files:
        problems += scan(f)
    if problems:
        print("SANITIZATION GATE FAILED — nothing was packaged:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    versioned = dist / f"harness-v{version}.zip"
    for out in (versioned, dist / "harness.zip"):
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, f.relative_to(ROOT))
    print(f"packaged {len(files)} files -> {versioned} (+ dist/harness.zip)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
