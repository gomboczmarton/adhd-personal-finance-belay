#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "openpyxl>=3.1"]
# ///
"""Tier 1 eval runner (D10): deterministic, no-LLM checks. Run on every change.

Usage:
    uv run evals/run_evals.py [--persona <id>]

Reads every persona in evals/personas/, runs the checks its expect: block asks
for plus the always-on fixture/workspace checks, and prints a PASS/FAIL/SKIP
table. Checks that need harness components not yet built are SKIPped with the
component named; the moment the component file appears, the check activates
and FAILS until genuinely implemented — that is the TDD-red handover to Step 4.

Exit code: 1 if any FAIL, else 0 (SKIPs don't fail the run).
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
PERSONA_DIR = ROOT / "evals" / "personas"
FIXTURE_DIR = ROOT / "evals" / "fixtures"

# harness components Tier 1 checks depend on; existence gates activation
COMPONENTS = {
    "ingest": ROOT / "harness" / "scripts" / "ingest.py",
    "match": ROOT / "harness" / "scripts" / "match_transfers.py",
    "reconcile": ROOT / "harness" / "scripts" / "reconcile.py",
    "plan": ROOT / "harness" / "scripts" / "plan_month.py",
    "excel": ROOT / "harness" / "scripts" / "export_excel.py",
    "validate": ROOT / "harness" / "scripts" / "validate_workspace.py",
    "install": ROOT / "install.py",
}

EXPECTED_SKILLS = {"onboarding", "monthly-prep", "reconcile-month", "purchase-check", "welcome-back"}

DIALECT_ENCODING = {"eu_csv": "utf-8", "hu_csv": "cp1250"}

# ingestion mapping configs for the fixture dialects (mirror of generator presets)
DIALECT_INGESTION = {
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

# dialects whose fixture files must be auto-identified by suggest_mapping.py;
# simple_xlsx deliberately maps to None (the wizard fallback path)
PRESET_EXPECT = {"eu_csv": "eu_csv", "hu_csv": "hu_csv", "revolut_csv": "revolut_csv",
                 "wise_csv": "wise_csv", "monzo_csv": "monzo_csv", "n26_csv": "n26_csv",
                 "otp_xlsx": "otp_xlsx", "simple_xlsx": None}


def load_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text[4 : text.find("\n---", 4)])


def fixture_rows(persona: dict) -> list[dict]:
    """Minimal fixture reader for fixture-sanity checks ONLY.

    Deliberately not the ingestion engine: once harness/scripts/ingest.py exists,
    ingestion-dependent checks must go through it, not through this reader.
    """
    rows = []
    pdir = FIXTURE_DIR / persona["id"]
    for account in persona["accounts"]:
        if account["dialect"] in DIALECT_ENCODING:
            enc = DIALECT_ENCODING[account["dialect"]]
            for f in sorted(pdir.glob(f"{account['id']}_*.csv")):
                with open(f, encoding=enc, newline="") as fh:
                    for row in list(csv.reader(fh, delimiter=";"))[1:]:
                        rows.append({
                            "account": account["id"], "file": f.name,
                            "amount": float(row[1].replace(",", ".")), "desc": row[2],
                        })
        else:
            for f in sorted(pdir.glob(f"{account['id']}_*.xlsx")):
                ws = load_workbook(f).active
                for r in ws.iter_rows(min_row=2, values_only=True):
                    rows.append({
                        "account": account["id"], "file": f.name,
                        "amount": float(r[1]), "desc": str(r[2]),
                    })
    return rows


# ---------------------------------------------------------------- checks

def check_fixtures_present(persona: dict) -> tuple[str, str]:
    pdir = FIXTURE_DIR / persona["id"]
    if not pdir.is_dir():
        return "FAIL", f"no fixture dir {pdir}"
    months = persona["fixtures"]["months"]
    missing = []
    for account in persona["accounts"]:
        ext = "xlsx" if account["dialect"].endswith("xlsx") else "csv"
        n = len(list(pdir.glob(f"{account['id']}_*.{ext}")))
        if n != months:
            missing.append(f"{account['id']}: {n}/{months}")
    if not (pdir / "manifest.json").exists():
        missing.append("manifest.json")
    return ("FAIL", "; ".join(missing)) if missing else ("PASS", f"{months} months × {len(persona['accounts'])} accounts")


def check_transfers_net_zero(persona: dict) -> tuple[str, str]:
    if persona.get("internal_transfers", "none") == "none":
        return "SKIP", "persona has no internal transfers"
    legs = [r for r in fixture_rows(persona) if "REFILL" in r["desc"]]
    net = round(sum(r["amount"] for r in legs), 2)
    if net != 0:
        return "FAIL", f"{len(legs)} legs net to {net}, expected 0"
    return "PASS", f"{len(legs)} legs net to zero"


def check_yearly_items_due_months(persona: dict) -> tuple[str, str]:
    items = persona.get("yearly_items", [])
    if not items:
        return "SKIP", "persona has no yearly items"
    manifest = json.loads((FIXTURE_DIR / persona["id"] / "manifest.json").read_text())
    bad = []
    for item in items:
        hits = sorted(k for k, v in manifest["months"].items() if item["name"] in v["yearly_items"])
        expected = sorted(k for k in manifest["months"] if int(k[5:7]) == item["month"])
        if hits != expected:
            bad.append(f"'{item['name']}': {hits} != {expected}")
    return ("FAIL", "; ".join(bad)) if bad else ("PASS", f"{len(items)} items in exactly their due months")


def check_mapping_presets_detected(persona: dict) -> tuple[str, str]:
    """suggest_mapping.py must identify each account's dialect from its first export
    (known bank shapes -> exact preset; simple_xlsx -> None = wizard fallback)."""
    script = ROOT / "harness" / "scripts" / "suggest_mapping.py"
    if not script.exists():
        return "SKIP", "needs harness component 'suggest_mapping' (roadmap B5)"
    pdir = FIXTURE_DIR / persona["id"]
    bad = []
    for account in persona["accounts"]:
        ext = "xlsx" if account["dialect"].endswith("xlsx") else "csv"
        files = sorted(pdir.glob(f"{account['id']}_*.{ext}"))
        if not files:
            bad.append(f"{account['id']}: no fixtures")
            continue
        proc = subprocess.run(["uv", "run", "--quiet", str(script), str(files[0])],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            bad.append(f"{account['id']}: suggest_mapping failed: {proc.stderr.strip()[:80]}")
            continue
        got = json.loads(proc.stdout)["preset"]
        want = PRESET_EXPECT[account["dialect"]]
        if got != want:
            bad.append(f"{account['id']}: preset {got!r} != {want!r}")
    if bad:
        return "FAIL", "; ".join(bad)
    return "PASS", f"{len(persona['accounts'])} accounts identified (or wizard-fallback) correctly"


def check_manifest_consistency(persona: dict) -> tuple[str, str]:
    manifest = json.loads((FIXTURE_DIR / persona["id"] / "manifest.json").read_text())
    known = {s["category"] for s in persona["spending"]} | {y["category"] for y in persona.get("yearly_items", [])}
    problems = []
    for month, truth in manifest["months"].items():
        if truth["income"] < 0:
            problems.append(f"{month}: negative income")
        unknown = set(truth["spend"]) - known
        if unknown:
            problems.append(f"{month}: unknown categories {unknown}")
    return ("FAIL", "; ".join(problems[:5])) if problems else ("PASS", f"{len(manifest['months'])} months consistent")


# ---------------------------------------------------------- Step 4 pipeline

_PIPELINE_CACHE: dict[str, dict] = {}
_TMPROOT = tempfile.TemporaryDirectory(prefix="harness-evals-")


def run_script(script: str, *args: str) -> dict:
    """Run a harness script via uv, return its JSON stdout (raises on failure)."""
    proc = subprocess.run(
        ["uv", "run", "--quiet", str(COMPONENTS[script]), *args],
        capture_output=True, text=True,
    )
    try:
        out = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        out = None
    if out is None and proc.returncode != 0:
        raise RuntimeError(f"{script} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return {"code": proc.returncode, "out": out or {}}


def build_eval_workspace(persona: dict, ws: Path) -> None:
    """Materialize a minimal workspace for a persona: accounts + merchant map."""
    accounts = []
    for a in persona["accounts"]:
        accounts.append({
            "id": a["id"], "name": a["id"], "type": a["type"],
            "currency": persona["income"]["currency"],
            "ingestion": DIALECT_INGESTION[a["dialect"]],
        })
    merchants = [
        {"pattern": m, "category": s["category"], "kind": "expense", "by": "rule", "confirmed": True}
        for s in persona["spending"] for m in s["merchants"]
    ]
    merchants += [
        {"pattern": y["name"].upper(), "category": y["category"], "kind": "expense",
         "by": "rule", "confirmed": True}
        for y in persona.get("yearly_items", [])
    ]
    merchants.append({"pattern": persona["income"].get("employer_desc", "INCOME"),
                      "category": "income", "kind": "income", "by": "rule", "confirmed": True})
    merchants.append({"pattern": "REFILL", "category": "internal", "kind": "internal_transfer",
                      "by": "rule", "confirmed": True})
    fx = persona["fixtures"]
    if fx.get("sub_accounts") or fx.get("savings_sweep"):
        # one-legged transfers to own sub-accounts: descriptions carry entropy, so
        # the rule matches the stable counterparty instead (real-data finding #3)
        merchants.append({"pattern": "OWN ACCOUNT", "field": "counterparty",
                          "category": "internal", "kind": "internal_transfer",
                          "by": "rule", "confirmed": True})
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "knowledge").mkdir(exist_ok=True)
    (ws / "accounts.md").write_text(
        "---\n" + yaml.safe_dump({"schema_version": 1, "accounts": accounts},
                                 allow_unicode=True, sort_keys=False) + "---\n", encoding="utf-8")
    (ws / "knowledge" / "merchant-map.md").write_text(
        "---\n" + yaml.safe_dump({"schema_version": 1, "merchants": merchants},
                                 allow_unicode=True, sort_keys=False) + "---\n", encoding="utf-8")


def pipeline(persona: dict) -> dict:
    """ingest twice -> match -> reconcile, once per persona; cached for all checks."""
    pid = persona["id"]
    if pid in _PIPELINE_CACHE:
        return _PIPELINE_CACHE[pid]
    ws = Path(_TMPROOT.name) / pid
    build_eval_workspace(persona, ws)
    pdir = FIXTURE_DIR / pid
    ingest: dict[str, dict] = {}
    for account in persona["accounts"]:
        ext = "xlsx" if account["dialect"].endswith("xlsx") else "csv"
        files = [str(f) for f in sorted(pdir.glob(f"{account['id']}_*.{ext}"))]
        first = run_script("ingest", str(ws), account["id"], *files)["out"]
        again = run_script("ingest", str(ws), account["id"], *files)["out"]  # overlap re-import
        ingest[account["id"]] = {"first": first, "again": again}
    match = run_script("match", str(ws))["out"]
    reconcile = run_script("reconcile", str(ws))["out"]
    events = [json.loads(l) for l in (ws / "ledger" / "events.jsonl")
              .read_text(encoding="utf-8").splitlines() if l.strip()]
    result = {"ws": ws, "ingest": ingest, "match": match,
              "reconcile": reconcile, "events": events}
    _PIPELINE_CACHE[pid] = result
    return result


def gated(component: str):
    def decorate(fn):
        def run(persona: dict) -> tuple[str, str]:
            if not COMPONENTS[component].exists():
                return "SKIP", f"needs harness component '{component}' (Step 4)"
            try:
                return fn(persona)
            except Exception as e:  # a crashing component is a failing eval
                return "FAIL", f"{type(e).__name__}: {e}"
        return run
    return decorate


@gated("ingest")
def check_no_double_count(persona: dict) -> tuple[str, str]:
    p = pipeline(persona)
    problems = []
    total = 0
    for acct, r in p["ingest"].items():
        if r["first"]["imported"] != r["first"]["rows"]:
            problems.append(f"{acct}: first import {r['first']['imported']}/{r['first']['rows']} rows")
        if r["again"]["imported"] != 0 or r["again"]["duplicates"] != r["again"]["rows"]:
            problems.append(f"{acct}: re-import created {r['again']['imported']} new txns")
        total += r["first"]["imported"]
    imported_events = sum(1 for e in p["events"] if e["type"] == "txn.imported")
    if imported_events != total:
        problems.append(f"ledger has {imported_events} imported events, expected {total}")
    return ("FAIL", "; ".join(problems)) if problems else \
        ("PASS", f"{total} txns; full re-import of every file added 0")


@gated("match")
def check_transfers_matched(persona: dict) -> tuple[str, str]:
    if persona.get("internal_transfers", "none") == "none":
        return "SKIP", "persona has no internal transfers"
    p = pipeline(persona)
    txn = {e["hash"]: e for e in p["events"] if e["type"] == "txn.imported"}
    refill_hashes = {h for h, e in txn.items() if "REFILL" in e["desc"]}
    matched_hashes: set[str] = set()
    false_pairs = []
    for e in p["events"]:
        if e["type"] != "txn.matched":
            continue
        matched_hashes.update(e["hashes"])
        if not all(h in refill_hashes for h in e["hashes"]):
            false_pairs.append([txn[h]["desc"] for h in e["hashes"]])
    unmatched = refill_hashes - matched_hashes
    problems = []
    if unmatched:
        problems.append(f"{len(unmatched)} refill legs unmatched")
    if false_pairs:
        problems.append(f"{len(false_pairs)} false pairs, e.g. {false_pairs[0]}")
    return ("FAIL", "; ".join(problems)) if problems else \
        ("PASS", f"{len(refill_hashes)} legs -> {len(refill_hashes)//2} pairs, no false pairs")


@gated("reconcile")
def check_reconciliation_balances(persona: dict) -> tuple[str, str]:
    p = pipeline(persona)
    manifest = json.loads((FIXTURE_DIR / persona["id"] / "manifest.json").read_text())
    problems = []
    for month, truth in manifest["months"].items():
        got = p["reconcile"]["months"].get(month)
        if got is None:
            problems.append(f"{month}: missing from reconciliation")
            continue
        if got["uncategorized"]:
            problems.append(f"{month}: {len(got['uncategorized'])} uncategorized txns")
        if abs(got["income"] - truth["income"]) > 0.011:
            problems.append(f"{month}: income {got['income']} != {truth['income']}")
        for cat, amount in truth["spend"].items():
            if abs(got["spend"].get(cat, 0) - amount) > 0.011:
                problems.append(f"{month}: {cat} {got['spend'].get(cat, 0)} != {amount}")
        extra = set(got["spend"]) - set(truth["spend"])
        if extra:
            problems.append(f"{month}: unexpected categories {extra}")
        if abs(got["transfers"] - truth["transfers"]) > 0.011:
            problems.append(f"{month}: transfers {got['transfers']} != {truth['transfers']}")
    if problems:
        return "FAIL", "; ".join(problems[:4]) + (f" (+{len(problems)-4} more)" if len(problems) > 4 else "")
    n = len(manifest["months"])
    return "PASS", f"{n} months: income, per-category spend, transfers all equal ground truth"


@gated("reconcile")
def check_envelopes_sum_to_income(persona: dict) -> tuple[str, str]:
    if persona.get("expect", {}).get("mode_suggestion") != "envelopes":
        return "SKIP", "persona not in envelope mode"
    p = pipeline(persona)
    manifest = json.loads((FIXTURE_DIR / persona["id"] / "manifest.json").read_text())
    month = max(m for m, t in manifest["months"].items() if t["income"] > sum(t["spend"].values()))
    truth = manifest["months"][month]
    allocations = {f"env_{cat}": amount for cat, amount in truth["spend"].items()}
    savings = round(truth["income"] - sum(allocations.values()), 2)
    mdir = p["ws"] / "months" / month
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "budget.md").write_text(
        "---\n" + yaml.safe_dump({
            "schema_version": 1, "month": month,
            "currency": persona["income"]["currency"],
            "income_planned": truth["income"], "allocations": allocations,
            "savings_target": savings,
        }, allow_unicode=True, sort_keys=False) + "---\n", encoding="utf-8")
    verdict = run_script("reconcile", str(p["ws"]), "--verify-budget", month)
    if verdict["code"] != 0 or not verdict["out"].get("balanced"):
        return "FAIL", f"{month}: difference {verdict['out'].get('difference')}"
    return "PASS", f"{month}: allocations + savings == income (Decimal-exact)"


def full_workspace(persona: dict, ws: Path) -> None:
    """Extend the minimal eval workspace into a complete one (as onboarding would)."""
    build_eval_workspace(persona, ws)
    currency = persona["income"]["currency"]
    cats = sorted({s["category"] for s in persona["spending"]}
                  | {y["category"] for y in persona.get("yearly_items", [])})
    mode = persona.get("expect", {}).get("mode_suggestion", "awareness")
    journey = persona.get("expect", {}).get("journey", {})

    # envelope accounts + adoption per mode
    accounts_fm = yaml.safe_load((ws / "accounts.md").read_text(encoding="utf-8")
                                 .split("---")[1])
    adoption = {}
    if mode == "envelopes":
        for c in cats:
            accounts_fm["accounts"].append(
                {"id": f"env_{c}", "name": f"{c} envelope", "type": "envelope",
                 "currency": currency})
    elif journey.get("adopts_envelope"):
        c = journey["adopts_envelope"]
        accounts_fm["accounts"].append(
            {"id": f"env_{c}", "name": f"{c} envelope", "type": "envelope",
             "currency": currency})
        adoption[c] = {"since": "2026-06", "envelope": f"env_{c}"}
        mode = "hybrid"
    (ws / "accounts.md").write_text(
        "---\n" + yaml.safe_dump(accounts_fm, allow_unicode=True, sort_keys=False) + "---\n",
        encoding="utf-8")

    (ws / "knowledge" / "categories.md").write_text(
        "---\n" + yaml.safe_dump({
            "schema_version": 1,
            "categories": [{"key": c} for c in cats + ["income", "internal"]],
        }, allow_unicode=True, sort_keys=False) + "---\n", encoding="utf-8")
    (ws / "knowledge" / "yearly-bank.md").write_text(
        "---\n" + yaml.safe_dump({
            "schema_version": 1,
            "items": [{"id": y["name"].lower().replace(" ", "-"), "name": y["name"],
                       "category": y["category"], "due_months": [y["month"]],
                       "typical_amount": y["amount"], "currency": currency,
                       "source": "detected"}
                      for y in persona.get("yearly_items", [])],
        }, allow_unicode=True, sort_keys=False) + "---\n", encoding="utf-8")
    strategy_fm = {"schema_version": 1, "mode": mode,
                   "language": persona["profile"].get("language", "en")}
    if adoption:
        strategy_fm["envelope_adoption"] = adoption
    (ws / "strategy.md").write_text(
        "---\n" + yaml.safe_dump(strategy_fm, allow_unicode=True, sort_keys=False) +
        "---\n\n# Strategy\n\nSynthetic lifecycle workspace.\n", encoding="utf-8")


@gated("plan")
def check_lifecycle_end_to_end(persona: dict) -> tuple[str, str]:
    """Install into a fresh repo, run the full monthly lifecycle mechanically."""
    pid = persona["id"]
    target = Path(_TMPROOT.name) / f"lifecycle-{pid}"
    if target.exists():
        return _PIPELINE_CACHE[f"lc-{pid}"]

    # 1. install
    proc = subprocess.run(["uv", "run", "--quiet", str(COMPONENTS["install"]), str(target)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return "FAIL", f"install failed: {proc.stderr.strip()}"
    manifest = json.loads(proc.stdout)
    got_skills = set(manifest["installed"]["skills"])
    if got_skills != EXPECTED_SKILLS or "finance-coach" not in manifest["installed"]["agents"]:
        return "FAIL", f"installed skills/agents wrong: {sorted(got_skills)}"
    for rel in [".claude/skills/onboarding/SKILL.md", ".claude/agents/finance-coach.md",
                "harness/scripts/reconcile.py", "harness/schemas/budget.schema.json",
                "finance/inbox"]:
        if not (target / rel).exists():
            return "FAIL", f"missing after install: {rel}"

    # 2. workspace as onboarding would leave it, 3. full data pipeline
    fin = target / "finance"
    full_workspace(persona, fin)
    pdir = FIXTURE_DIR / pid
    for account in persona["accounts"]:
        ext = "xlsx" if account["dialect"].endswith("xlsx") else "csv"
        files = [str(f) for f in sorted(pdir.glob(f"{account['id']}_*.{ext}"))]
        subprocess.run(["uv", "run", "--quiet", str(target / "harness/scripts/ingest.py"),
                        str(fin), account["id"], *files], capture_output=True, text=True, check=True)
    subprocess.run(["uv", "run", "--quiet", str(target / "harness/scripts/match_transfers.py"),
                    str(fin)], capture_output=True, text=True, check=True)

    # 3b. pattern detection must rediscover the persona's ground truth (onboarding evidence)
    pat = json.loads(subprocess.run(
        ["uv", "run", "--quiet", str(target / "harness/scripts/detect_patterns.py"), str(fin)],
        capture_output=True, text=True, check=True).stdout)
    # groups key on counterparty when present ("EMPLOYER" in fixtures), else on the
    # digit-stripped description — accept any of those spellings (real-data finding #1)
    employer = persona["income"].get("employer_desc", "INCOME").upper()
    income_keys = {employer, "EMPLOYER", " ".join(re.sub(r"\d+", " ", employer).split())}
    income_hit = next((i for i in pat["income_pattern"] if i["desc"] in income_keys), None)
    if income_hit is None or not set(persona["income"]["days"]) <= set(income_hit["days"]):
        return "FAIL", f"income pattern missed: {pat['income_pattern']}"
    # detected coverage must be reported (real-data finding #4)
    months_present = pat.get("coverage", {}).get("months_present")
    if months_present != persona["fixtures"]["months"]:
        return "FAIL", f"coverage reports {months_present} months, fixtures have {persona['fixtures']['months']}"
    # yearly proposals require >=13 months of history (real-data finding #2):
    # below the gate the list must be EMPTY, above it every yearly item must appear
    yearly_descs = {y["desc"]: y["due_months"] for y in pat["yearly_candidates"]}
    if persona["fixtures"]["months"] < 13:
        if pat["yearly_candidates"]:
            return "FAIL", f"yearly proposed on {persona['fixtures']['months']} months of history: " \
                           f"{sorted(yearly_descs)}"
    else:
        for item in persona.get("yearly_items", []):
            if yearly_descs.get(item["name"].upper()) != [item["month"]]:
                return "FAIL", f"yearly candidate missed: {item['name']}"
    expected_monthly = sum(len(s["merchants"]) for s in persona["spending"] if s["freq"] == "monthly")
    if len(pat["monthly_recurring"]) < expected_monthly:
        return "FAIL", f"monthly recurring {len(pat['monthly_recurring'])} < {expected_monthly}"

    rec = subprocess.run(["uv", "run", "--quiet", str(target / "harness/scripts/reconcile.py"),
                          str(fin)], capture_output=True, text=True, check=True)
    rec_dir = fin / "months" / "2026-06" / "reports"
    rec_dir.mkdir(parents=True, exist_ok=True)
    (rec_dir / "reconcile_2026-06.json").write_text(rec.stdout, encoding="utf-8")

    # 4. plan next month; yearly-bank July items must land in the overlay
    plan = subprocess.run(["uv", "run", "--quiet", str(target / "harness/scripts/plan_month.py"),
                           str(fin), "2026-07"], capture_output=True, text=True)
    if plan.returncode != 0:
        return "FAIL", f"plan_month failed: {plan.stderr.strip()}"
    plan_out = json.loads(plan.stdout)
    expected_overlay = sorted(y["name"] for y in persona.get("yearly_items", []) if y["month"] == 7)
    if sorted(plan_out["overlay_items"]) != expected_overlay:
        return "FAIL", f"overlay {plan_out['overlay_items']} != due-in-July {expected_overlay}"
    if plan_out["savings_target"] < 0:
        return "FAIL", "negative savings target"

    # 5. envelope invariant, 6. excel views, 7. workspace validity
    if persona.get("expect", {}).get("mode_suggestion") == "envelopes":
        v = subprocess.run(["uv", "run", "--quiet", str(target / "harness/scripts/reconcile.py"),
                            str(fin), "--verify-budget", "2026-07"], capture_output=True, text=True)
        if v.returncode != 0:
            return "FAIL", f"drafted budget not balanced: {v.stdout.strip()}"
    for args, expect_file in [
        (("2026-07", "budget"), fin / "months/2026-07/reports/budget_2026-07.xlsx"),
        (("2026-06", "reconciliation", "--data", str(rec_dir / "reconcile_2026-06.json")),
         fin / "months/2026-06/reports/reconciliation_2026-06.xlsx"),
    ]:
        subprocess.run(["uv", "run", "--quiet", str(target / "harness/scripts/export_excel.py"),
                        str(fin), *args], capture_output=True, text=True, check=True)
        if not expect_file.exists():
            return "FAIL", f"excel view missing: {expect_file.name}"
    # 6b. D13 HTML report for June (plan June first so meters have a budget;
    # reconcile already ran its categorization pass, so averages are available)
    june_plan = subprocess.run(["uv", "run", "--quiet", str(target / "harness/scripts/plan_month.py"),
                                str(fin), "2026-06"], capture_output=True, text=True)
    if june_plan.returncode != 0:
        return "FAIL", f"plan_month 2026-06 failed: {june_plan.stderr.strip()}"
    subprocess.run(["uv", "run", "--quiet", str(target / "harness/scripts/render_report.py"),
                    str(fin), "2026-06", "--data", str(rec_dir / "reconcile_2026-06.json")],
                   capture_output=True, text=True, check=True)
    report_file = fin / "months/2026-06/reports/report_2026-06.html"
    if not report_file.exists():
        return "FAIL", "HTML report missing"
    report_html = report_file.read_text(encoding="utf-8")
    for needle, what in [("class=\"track\"", "meters"), ("The full statement", "table layer"),
                         ("2026-06", "month")]:
        if needle not in report_html:
            return "FAIL", f"HTML report missing {what}"

    val = subprocess.run(["uv", "run", "--quiet", str(target / "harness/scripts/validate_workspace.py"),
                          str(fin)], capture_output=True, text=True)
    if val.returncode != 0:
        return "FAIL", f"final workspace invalid: {val.stdout.strip().splitlines()[-1]}"

    result = ("PASS", "install → onboard → ingest → match → reconcile → plan → excel → valid")
    _PIPELINE_CACHE[f"lc-{pid}"] = result
    return result


CHECKS = {
    # always-on fixture/workspace sanity
    "fixtures_present": check_fixtures_present,
    "transfers_net_zero": check_transfers_net_zero,
    "yearly_items_due_months": check_yearly_items_due_months,
    "manifest_consistency": check_manifest_consistency,
    "mapping_presets_detected": check_mapping_presets_detected,
    # Step 4 invariants (run the real harness scripts on the fixtures)
    "no_double_count": check_no_double_count,
    "reconciliation_balances": check_reconciliation_balances,
    "envelopes_sum_to_income": check_envelopes_sum_to_income,
    "transfers_matched": check_transfers_matched,
    "lifecycle_end_to_end": check_lifecycle_end_to_end,
}

# expect: fields owned by Tier 2 (persona-bot), never Tier 1
TIER2_FIELDS = ["onboarding_detects", "mode_suggestion", "journey"]


def main() -> int:
    only = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--persona" else None
    results = []
    for pfile in sorted(PERSONA_DIR.glob("*.md")):
        persona = load_frontmatter(pfile)
        if only and persona["id"] != only:
            continue
        wanted = ["fixtures_present", "transfers_net_zero",
                  "yearly_items_due_months", "manifest_consistency",
                  "mapping_presets_detected", "lifecycle_end_to_end"]
        wanted += [i for i in persona.get("expect", {}).get("invariants", []) if i not in wanted]
        if persona.get("internal_transfers", "none") != "none":
            wanted.append("transfers_matched")
        for name in wanted:
            if name not in CHECKS:
                results.append((persona["id"], name, "FAIL", "unknown check name"))
                continue
            status, detail = CHECKS[name](persona)
            results.append((persona["id"], name, status, detail))
        for field in TIER2_FIELDS:
            if field in persona.get("expect", {}):
                results.append((persona["id"], field, "SKIP", "Tier 2 (persona-bot, milestone runs)"))

    width = max(len(f"{p}: {c}") for p, c, _, _ in results) + 2
    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    for pid, check, status, detail in results:
        counts[status] += 1
        print(f"{f'{pid}: {check}':<{width}} {status:<5} {detail}")
    print(f"\n{counts['PASS']} passed, {counts['FAIL']} failed, {counts['SKIP']} skipped")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
