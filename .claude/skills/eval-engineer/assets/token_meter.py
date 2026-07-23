#!/usr/bin/env python3
"""token_meter.py — turn Claude Code transcript usage into an optimization-loop signal.

Reads the per-message `usage` blocks Claude Code writes into session/agent
transcript JSONL (the same source ccusage parses) and emits a JSON cost report.
Optionally joins Harbor-style reward files so the report carries the metric the
optimization loop gates on: TOKENS PER SUCCESS, not tokens per attempt
(practices/08-token-economics.md).

Usage:
  python3 token_meter.py <transcript.jsonl | dir-of-jsonl> [--label NAME]
      [--rewards <jobs-dir>]  # dir containing */verifier/reward.txt (Harbor layout)
      [--baseline <prior cost_report.json>]  # emit deltas vs a prior run

Exit code is always 0; this is a meter, not a gate. Wire the gate in the
optimization loop: keep a change only if pass rate did not drop AND
tokens_per_success did not rise (both, conjunctively).

Notes:
- Deduplicates by message id: streamed assistant messages repeat the same usage
  block across JSONL lines; counting each line would overstate output tokens.
- Cache reads are billed differently from fresh input; they are reported
  separately and NOT summed into `billable_proxy` at full weight (weight 0.1,
  the common cache-read discount — adjust to your price sheet).
- This measures the sessions on this machine only; it is an approximation, not
  billing truth. For quota truth, pair with the OAuth usage endpoint pattern
  (see research/references/2026-07-23-token-usage-tooling-landscape.md).
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

CACHE_READ_WEIGHT = 0.1


def iter_jsonl(target: Path):
    files = [target] if target.is_file() else sorted(target.rglob("*.jsonl"))
    for f in files:
        with open(f, errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def collect(target: Path) -> dict:
    per_model = defaultdict(lambda: defaultdict(int))
    seen = {}  # message id -> usage (last write wins; streamed lines repeat usage)
    for rec in iter_jsonl(target):
        msg = rec.get("message") or {}
        usage = msg.get("usage") or rec.get("usage")
        if not isinstance(usage, dict):
            continue
        mid = msg.get("id") or rec.get("uuid") or id(usage)
        seen[mid] = (msg.get("model", "unknown"), usage)
    for model, usage in seen.values():
        m = per_model[model]
        m["input_tokens"] += usage.get("input_tokens", 0)
        m["output_tokens"] += usage.get("output_tokens", 0)
        m["cache_read_tokens"] += usage.get("cache_read_input_tokens", 0)
        m["cache_creation_tokens"] += usage.get("cache_creation_input_tokens", 0)
        m["messages"] += 1
    totals = defaultdict(int)
    for m in per_model.values():
        for k, v in m.items():
            totals[k] += v
    totals["billable_proxy"] = int(
        totals["input_tokens"]
        + totals["output_tokens"]
        + totals["cache_creation_tokens"]
        + CACHE_READ_WEIGHT * totals["cache_read_tokens"]
    )
    return {"per_model": {k: dict(v) for k, v in per_model.items()},
            "totals": dict(totals)}


def collect_rewards(jobs_dir: Path) -> dict:
    rewards = {}
    for rf in sorted(jobs_dir.rglob("reward.txt")):
        try:
            rewards[str(rf.parent.parent.name)] = float(rf.read_text().strip())
        except ValueError:
            continue
    return rewards


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path)
    ap.add_argument("--label", default=None)
    ap.add_argument("--rewards", type=Path, default=None)
    ap.add_argument("--baseline", type=Path, default=None)
    args = ap.parse_args()

    report = collect(args.target)
    report["label"] = args.label or args.target.name

    if args.rewards and args.rewards.exists():
        rewards = collect_rewards(args.rewards)
        successes = sum(1 for v in rewards.values() if v >= 1.0)
        report["rewards"] = {"tasks": len(rewards), "successes": successes}
        bp = report["totals"]["billable_proxy"]
        report["tokens_per_success"] = round(bp / successes) if successes else None
        report["tokens_per_attempt"] = round(bp / len(rewards)) if rewards else None

    if args.baseline and args.baseline.exists():
        base = json.loads(args.baseline.read_text())
        deltas = {}
        for key in ("billable_proxy",):
            b = base.get("totals", {}).get(key)
            n = report["totals"].get(key)
            if b:
                deltas[key] = {"before": b, "after": n,
                               "pct": round(100.0 * (n - b) / b, 1)}
        b_tps = base.get("tokens_per_success")
        if b_tps and report.get("tokens_per_success"):
            deltas["tokens_per_success"] = {
                "before": b_tps, "after": report["tokens_per_success"],
                "pct": round(100.0 * (report["tokens_per_success"] - b_tps) / b_tps, 1)}
        report["deltas_vs_baseline"] = deltas

    json.dump(report, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
