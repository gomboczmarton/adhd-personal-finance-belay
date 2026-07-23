#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Build a frozen eval workspace from a persona package (environment half of a task).

Usage:
    uv run evals/lib/build_workspace.py <persona.md> <workspace-dir> [--inbox <fixtures-dir>]

Creates the post-onboarding state the conversational skills would have produced
(accounts.md with ingestion mappings, categories.md, merchant-map.md rules,
strategy.md, empty ledger) so tasks can measure the pipeline capabilities in
isolation. The merchant map is part of the *environment* (onboarding already
happened); discovering it is a separate capability with its own task. With
--inbox, copies the persona's generated exports into <workspace>/inbox/.

Frozen data: everything derives deterministically from the persona file.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

INGESTION = {
    "eu_csv": {
        "format": "csv", "encoding": "utf-8", "delimiter": ";", "decimal": ",",
        "date_format": "%Y.%m.%d", "header_rows": 1,
        "columns": {"date": "Booking date", "amount": "Amount",
                    "description": "Details", "counterparty": "Partner"},
    },
    "hu_csv": {
        "format": "csv", "encoding": "cp1250", "delimiter": ";", "decimal": ",",
        "date_format": "%Y.%m.%d.", "header_rows": 1,
        "columns": {"date": "Könyvelés dátuma", "amount": "Összeg",
                    "description": "Közlemény", "counterparty": "Partner név"},
    },
    "simple_xlsx": {
        "format": "xlsx", "date_format": "%Y-%m-%d",
        "columns": {"date": "Date", "amount": "Amount", "description": "Merchant"},
    },
    # Real-bank dialects (roadmap-B5 shapes; column names match generate_fixtures.py)
    "revolut_csv": {
        "format": "csv", "encoding": "utf-8", "delimiter": ",", "decimal": ".",
        "date_format": "%Y-%m-%d %H:%M:%S", "header_rows": 1,
        "columns": {"date": "Completed Date", "amount": "Amount",
                    "description": "Description"},
    },
    "wise_csv": {
        "format": "csv", "encoding": "utf-8", "delimiter": ",", "decimal": ".",
        "date_format": "%d-%m-%Y", "header_rows": 1,
        "columns": {"date": "Date", "amount": "Amount",
                    "description": "Description", "counterparty": "Merchant"},
    },
    "monzo_csv": {
        "format": "csv", "encoding": "utf-8", "delimiter": ",", "decimal": ".",
        "date_format": "%d/%m/%Y", "header_rows": 1,
        "columns": {"date": "Date", "amount": "Amount",
                    "description": "Description", "counterparty": "Name"},
    },
    "n26_csv": {
        "format": "csv", "encoding": "utf-8", "delimiter": ",", "decimal": ".",
        "date_format": "%Y-%m-%d", "header_rows": 1,
        "columns": {"date": "Booking Date", "amount": "Amount (EUR)",
                    "description": "Payment Reference", "counterparty": "Partner Name"},
    },
    "otp_xlsx": {
        "format": "xlsx", "date_format": "%Y-%m-%d", "header_rows": 10,
        "columns": {"date": "Könyvelés dátuma", "amount": "Összeg",
                    "description": "Közlemény", "counterparty": "Ellenoldali név"},
    },
}


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 4)
    return yaml.safe_load(text[4:end])


def md(front: dict, body: str) -> str:
    return "---\n" + yaml.safe_dump(front, allow_unicode=True, sort_keys=False) + f"---\n\n{body}\n"


def main() -> int:
    argv = sys.argv[1:]
    inbox_src = None
    if "--inbox" in argv:
        i = argv.index("--inbox")
        inbox_src = Path(argv[i + 1])
        del argv[i:i + 2]
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    persona = frontmatter(Path(argv[0]))
    ws = Path(argv[1])

    currency = persona["income"]["currency"]
    accounts = []
    for acct in persona["accounts"]:
        if acct["dialect"] not in INGESTION:
            sys.exit(f"error: no ingestion mapping template for dialect {acct['dialect']}")
        accounts.append({
            "id": acct["id"], "name": acct["id"], "type": acct["type"],
            "currency": currency, "ingestion": INGESTION[acct["dialect"]],
        })

    categories = sorted(
        {s["category"] for s in persona["spending"]}
        | {y["category"] for y in persona.get("yearly_items", [])}
        | {"income", "internal"}
    )

    merchants = []
    for spend in persona["spending"]:
        for merchant in spend["merchants"]:
            merchants.append({"pattern": merchant, "category": spend["category"],
                              "kind": "expense", "by": "rule", "confirmed": True})
    for item in persona.get("yearly_items", []):
        merchants.append({"pattern": item["name"].upper(), "category": item["category"],
                          "kind": "expense", "by": "rule", "confirmed": True})
    merchants.append({"pattern": persona["income"].get("employer_desc", "INCOME"),
                      "category": "income", "kind": "income", "by": "rule", "confirmed": True})
    # one-legged own-account transfers are recognizable only by counterparty
    merchants.append({"pattern": "OWN ACCOUNT", "field": "counterparty",
                      "category": "internal", "kind": "internal_transfer",
                      "by": "rule", "confirmed": True})

    (ws / "knowledge").mkdir(parents=True, exist_ok=True)
    (ws / "ledger").mkdir(exist_ok=True)
    (ws / "months").mkdir(exist_ok=True)
    (ws / "inbox").mkdir(exist_ok=True)

    (ws / "strategy.md").write_text(md(
        {"schema_version": 1, "mode": "awareness", "language": persona["profile"].get("language", "en")},
        "# Strategy\n\nAwareness mode since onboarding (eval fixture)."), encoding="utf-8")
    (ws / "accounts.md").write_text(md(
        {"schema_version": 1, "accounts": accounts},
        "# Accounts\n\nGenerated by evals/lib/build_workspace.py."), encoding="utf-8")
    (ws / "knowledge" / "categories.md").write_text(md(
        {"schema_version": 1, "categories": [{"key": c} for c in categories]},
        "# Categories"), encoding="utf-8")
    (ws / "knowledge" / "merchant-map.md").write_text(md(
        {"schema_version": 1, "merchants": merchants},
        "# Merchant map\n\nFrozen post-onboarding state for eval runs."), encoding="utf-8")
    (ws / "ledger" / "events.jsonl").touch()

    staged = 0
    if inbox_src:
        for f in sorted(inbox_src.iterdir()):
            if f.suffix in (".csv", ".xlsx"):
                shutil.copy2(f, ws / "inbox" / f.name)
                staged += 1

    print(f"workspace ready at {ws} ({len(accounts)} accounts, "
          f"{len(merchants)} merchant rules, {staged} exports staged)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
