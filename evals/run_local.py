#!/usr/bin/env python3
"""Local Harbor-compatible eval runner (no Docker required).

Usage:
    python3 evals/run_local.py [task-id ...] [--fixtures] [--keep] [--job-name NAME]

Phases per task (Harbor semantics, executed locally):
    setup    environment/setup.sh   builds the frozen workspace
    solve    solution/solve.sh      oracle run (proves solvability; exercises
                                    the exact scripts the skills orchestrate)
    test     tests/test.sh          verifier -> reward.txt (1/0)

--fixtures additionally runs the verifier's own test (the fixture rule from
the eval-engineer skill): after a passing oracle run, tests/corrupt.py mutates
the workspace into a plausible-but-wrong result and the verifier must fail it.

Tasks with metadata.judge_required = true are reported as SKIPPED(judge):
their rubric needs an LLM-judge runner (see evals/README.md).

Run evidence lands in evals/jobs/<job-name>/<task>/ (git-ignored). Exit 0 iff
every executed task's reward meets its metadata.threshold (and, with
--fixtures, every corrupted workspace was rejected).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EVALS = REPO / "evals"
NON_TASK_DIRS = {"personas", "fixtures", "lib", "jobs"}


def discover() -> list[Path]:
    return sorted(d for d in EVALS.iterdir()
                  if d.is_dir() and d.name not in NON_TASK_DIRS
                  and (d / "task.toml").exists())


def sh(script: Path, env: dict, log: Path) -> int:
    with open(log, "w", encoding="utf-8") as out:
        return subprocess.run(["bash", str(script)], env=env,
                              stdout=out, stderr=subprocess.STDOUT).returncode


def run_judge_calibration(task_dir: Path) -> dict:
    """The fixture rule applied to the judge itself: the rubric-driven judge
    must pass the clearly-capable fixture reply and fail the plausible-but-
    wrong one, before it is trusted to grade real replies."""
    result = {"task": task_dir.name, "threshold": 1.0}
    outcomes = {}
    for fixture, expected_rc in (("pass_reply.md", 0), ("fail_reply.md", 1)):
        proc = subprocess.run(
            [sys.executable, str(EVALS / "lib" / "judge.py"), str(task_dir),
             str(task_dir / "tests" / "fixtures" / fixture)],
            capture_output=True, text=True)
        if proc.returncode == 3:
            result["status"] = "INFRA_ERROR(judge)"
            result["detail"] = proc.stdout.strip()[:200]
            return result
        outcomes[fixture] = "ok" if proc.returncode == expected_rc \
            else f"unexpected verdict ({proc.stdout.strip()[:120]})"
    ok = all(v == "ok" for v in outcomes.values())
    result["status"] = "PASS" if ok else "FAIL"
    result["reward"] = 1.0 if ok else 0.0
    result["fixture_rule"] = "OK" if ok else "BROKEN(judge misgraded a fixture)"
    return result


def run_task(task_dir: Path, job_dir: Path, fixtures: bool, judge: bool) -> dict:
    meta = tomllib.loads((task_dir / "task.toml").read_text(encoding="utf-8"))
    md = meta.get("metadata", {})
    result = {"task": task_dir.name, "threshold": md.get("threshold", 1.0)}
    if md.get("judge_required"):
        if judge:
            return run_judge_calibration(task_dir)
        result["status"] = "SKIPPED(judge)"
        return result

    persona = EVALS / "personas" / f"{md['persona']}.md"
    manifest = EVALS / "fixtures" / md["persona"] / "manifest.json"
    ws = job_dir / "workspace"
    env = {**os.environ,
           "REPO": str(REPO), "WS": str(ws),
           "ARTIFACTS": str(job_dir / "artifacts"),
           "REWARD_DIR": str(job_dir / "verifier"),
           "PERSONA": str(persona), "MANIFEST": str(manifest),
           "MONTH": md["month"]}
    for sub in ("workspace", "artifacts", "verifier"):
        (job_dir / sub).mkdir(parents=True, exist_ok=True)

    for phase, script in (("setup", task_dir / "environment" / "setup.sh"),
                          ("solve", task_dir / "solution" / "solve.sh"),
                          ("test", task_dir / "tests" / "test.sh")):
        rc = sh(script, env, job_dir / f"{phase}.log")
        if rc != 0 and phase != "test":
            result["status"] = f"INFRA_ERROR({phase})"
            return result

    reward_file = job_dir / "verifier" / "reward.txt"
    reward = float(reward_file.read_text().strip()) if reward_file.exists() else 0.0
    result["reward"] = reward
    result["status"] = "PASS" if reward >= result["threshold"] else "FAIL"

    if fixtures and result["status"] == "PASS":
        corrupt = task_dir / "tests" / "corrupt.py"
        if corrupt.exists():
            shutil.copytree(job_dir / "verifier", job_dir / "verifier_clean",
                            dirs_exist_ok=True)
            subprocess.run([sys.executable, str(corrupt), str(ws)],
                           check=True, capture_output=True)
            sh(task_dir / "tests" / "test.sh", env, job_dir / "test_corrupted.log")
            corrupted_reward = float(reward_file.read_text().strip())
            result["fixture_rule"] = "OK" if corrupted_reward == 0.0 \
                else "BROKEN(verifier passed a wrong result)"
        else:
            result["fixture_rule"] = "MISSING(corrupt.py)"
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", nargs="*")
    ap.add_argument("--fixtures", action="store_true")
    ap.add_argument("--judge", action="store_true",
                    help="run judge-task calibration fixtures (needs a judge "
                         "command, default `claude -p`; see evals/lib/judge.py)")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--exclude-anchor", action="store_true",
                    help="skip the frozen anchor sub-suite listed in evals/ANCHOR "
                         "(the PR-CI mode; the release workflow runs everything)")
    ap.add_argument("--job-name", default=time.strftime("%Y%m%d-%H%M%S"))
    args = ap.parse_args()

    tasks = discover()
    if args.exclude_anchor:
        anchor_file = EVALS / "ANCHOR"
        anchored = {l.strip() for l in anchor_file.read_text().splitlines()
                    if l.strip() and not l.startswith("#")} if anchor_file.exists() else set()
        tasks = [t for t in tasks if t.name not in anchored]
        print(f"anchor excluded: {', '.join(sorted(anchored)) or '(none)'}")
    if args.tasks:
        tasks = [t for t in tasks if t.name in args.tasks]
        missing = set(args.tasks) - {t.name for t in tasks}
        if missing:
            sys.exit(f"unknown task(s): {', '.join(sorted(missing))}")

    job_root = EVALS / "jobs" / args.job_name
    results = []
    for task_dir in tasks:
        print(f"== {task_dir.name}", flush=True)
        results.append(run_task(task_dir, job_root / task_dir.name,
                                args.fixtures, args.judge))

    print(f"\n{'task':<28} {'status':<22} {'reward':<7} fixture_rule")
    ok = True
    for r in results:
        if r["status"] == "FAIL" or r["status"].startswith("INFRA") \
                or r.get("fixture_rule", "OK").startswith("BROKEN"):
            ok = False
        print(f"{r['task']:<28} {r['status']:<22} "
              f"{r.get('reward', '-')!s:<7} {r.get('fixture_rule', '-')}")
    print(f"\nevidence: {job_root}")
    if not args.keep and ok:
        shutil.rmtree(job_root, ignore_errors=True)
        print("evidence removed (all green; use --keep to retain)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
