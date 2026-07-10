#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "jsonschema>=4.21"]
# ///
"""Validate a harness finance workspace against the schemas in harness/schemas/.

Usage:
    uv run harness/scripts/validate_workspace.py <workspace-dir>

The workspace layout (D8, Notebook + Ledger hybrid):
    strategy.md accounts.md          knowledge/{categories,yearly-bank,merchant-map}.md
    ledger/events.jsonl              months/YYYY-MM/budget.md

Validates YAML frontmatter of every known .md file and every line of events.jsonl.
Also enforces cross-file referential rules the schemas can't express:
  - envelope ids used in budgets/strategy exist in accounts.md
  - category keys used anywhere exist in categories.md
  - txn.categorized/matched hashes reference imported transactions
Exit code 0 = valid, 1 = violations (all listed), 2 = usage/setup error.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"

# workspace-relative path pattern -> schema file
FRONTMATTER_SCHEMAS = [
    (re.compile(r"^strategy\.md$"), "strategy.schema.json"),
    (re.compile(r"^accounts\.md$"), "accounts.schema.json"),
    (re.compile(r"^knowledge/categories\.md$"), "categories.schema.json"),
    (re.compile(r"^knowledge/yearly-bank\.md$"), "yearly-bank.schema.json"),
    (re.compile(r"^knowledge/merchant-map\.md$"), "merchant-map.schema.json"),
    (re.compile(r"^months/\d{4}-\d{2}/budget\.md$"), "budget.schema.json"),
]

REQUIRED_FILES = ["strategy.md", "accounts.md", "knowledge/categories.md"]


def load_schema(name: str) -> Draft202012Validator:
    with open(SCHEMA_DIR / name, encoding="utf-8") as f:
        return Draft202012Validator(json.load(f))


def parse_frontmatter(path: Path) -> tuple[dict | None, str | None]:
    """Return (frontmatter, error). Frontmatter is the first ---...--- YAML block."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, "missing frontmatter (file must start with ---)"
    end = text.find("\n---", 4)
    if end == -1:
        return None, "unterminated frontmatter block"
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError as e:
        return None, f"frontmatter is not valid YAML: {e}"
    if not isinstance(data, dict):
        return None, "frontmatter must be a YAML mapping"
    return data, None


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    ws = Path(sys.argv[1])
    if not ws.is_dir():
        print(f"error: {ws} is not a directory", file=sys.stderr)
        return 2

    errors: list[str] = []
    docs: dict[str, dict] = {}  # rel path -> frontmatter

    for required in REQUIRED_FILES:
        if not (ws / required).exists():
            errors.append(f"{required}: required file missing")

    # --- frontmatter validation ---
    for md in sorted(ws.rglob("*.md")):
        rel = md.relative_to(ws).as_posix()
        schema_name = next((s for rx, s in FRONTMATTER_SCHEMAS if rx.match(rel)), None)
        if schema_name is None:
            continue  # reports and free-form notes are not validated
        fm, err = parse_frontmatter(md)
        if err:
            errors.append(f"{rel}: {err}")
            continue
        for v_err in load_schema(schema_name).iter_errors(fm):
            loc = "/".join(str(p) for p in v_err.absolute_path) or "(root)"
            errors.append(f"{rel}: {loc}: {v_err.message}")
        docs[rel] = fm

    # --- ledger validation ---
    imported_hashes: set[str] = set()
    referenced: list[tuple[str, str]] = []  # (line ref, hash)
    event_categories: list[tuple[str, str]] = []  # (line ref, category key)
    ledger = ws / "ledger" / "events.jsonl"
    if ledger.exists():
        event_schema = load_schema("event.schema.json")
        for i, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            ref = f"ledger/events.jsonl:{i}"
            try:
                ev = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"{ref}: not valid JSON: {e}")
                continue
            for v_err in event_schema.iter_errors(ev):
                errors.append(f"{ref}: {v_err.message}")
            if ev.get("type") == "txn.imported" and "hash" in ev:
                if ev["hash"] in imported_hashes:
                    errors.append(f"{ref}: duplicate txn.imported hash {ev['hash']}")
                imported_hashes.add(ev["hash"])
            elif ev.get("type") == "txn.categorized" and "hash" in ev:
                referenced.append((ref, ev["hash"]))
                if "category" in ev:
                    event_categories.append((ref, ev["category"]))
            elif ev.get("type") == "txn.matched":
                referenced.extend((ref, h) for h in ev.get("hashes", []))
        for ref, h in referenced:
            if h not in imported_hashes:
                errors.append(f"{ref}: references unknown transaction hash {h}")

    # --- cross-file referential rules ---
    category_keys = {
        c.get("key")
        for c in docs.get("knowledge/categories.md", {}).get("categories", [])
    }
    account_ids = {
        a.get("id") for a in docs.get("accounts.md", {}).get("accounts", [])
    }
    envelope_ids = {
        a.get("id")
        for a in docs.get("accounts.md", {}).get("accounts", [])
        if a.get("type") == "envelope"
    }

    def check_category(rel: str, where: str, key: str) -> None:
        if category_keys and key not in category_keys:
            errors.append(f"{rel}: {where}: unknown category key '{key}'")

    def check_envelope(rel: str, where: str, env: str) -> None:
        if envelope_ids and env not in envelope_ids:
            errors.append(f"{rel}: {where}: unknown envelope id '{env}'")

    for ref, cat in event_categories:
        check_category(ref, "category", cat)

    strategy = docs.get("strategy.md", {})
    for cat, ad in (strategy.get("envelope_adoption") or {}).items():
        check_category("strategy.md", f"envelope_adoption/{cat}", cat)
        check_envelope("strategy.md", f"envelope_adoption/{cat}", ad.get("envelope", ""))

    for a in docs.get("accounts.md", {}).get("accounts", []):
        parent = a.get("parent")
        if parent and parent not in account_ids:
            errors.append(f"accounts.md: account '{a.get('id')}': unknown parent '{parent}'")

    for item in docs.get("knowledge/yearly-bank.md", {}).get("items", []):
        check_category("knowledge/yearly-bank.md", f"item '{item.get('id')}'", item.get("category", ""))
    for m in docs.get("knowledge/merchant-map.md", {}).get("merchants", []):
        check_category("knowledge/merchant-map.md", f"pattern '{m.get('pattern')}'", m.get("category", ""))

    for rel, fm in docs.items():
        if not rel.startswith("months/"):
            continue
        month_dir = rel.split("/")[1]
        if fm.get("month") != month_dir:
            errors.append(f"{rel}: frontmatter month '{fm.get('month')}' != folder '{month_dir}'")
        for env in (fm.get("allocations") or {}):
            check_envelope(rel, f"allocations/{env}", env)
        for cat in (fm.get("awareness_targets") or {}):
            check_category(rel, f"awareness_targets/{cat}", cat)
        for o in fm.get("overlay") or []:
            if o.get("category"):
                check_category(rel, f"overlay '{o.get('name')}'", o["category"])
            if o.get("envelope"):
                check_envelope(rel, f"overlay '{o.get('name')}'", o["envelope"])

    if errors:
        print(f"INVALID: {len(errors)} problem(s) in {ws}")
        for e in errors:
            print(f"  - {e}")
        return 1
    n_docs, n_events = len(docs), len(imported_hashes) + len(referenced)
    print(f"OK: {ws} valid ({n_docs} documents, {n_events} ledger events checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
