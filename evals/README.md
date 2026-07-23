# Belay evals — Harbor-format tasks + persona fixtures

The eval system follows the LangChain eval-engineering workflow (see the
`eval-engineer` skill in `.claude/skills/eval-engineer/`, incorporated from the
harness-engineering knowledge base): evals are authored interactively, one
capability per task, in the **Harbor task format**, and every verifier passes
its own fixture test before it is allowed to grade anything.

## Layout

```
evals/
├── personas/<id>.md        persona eval packages ("a persona IS a test case", D9)
├── fixtures/<id>/          generated: deterministic exports + ground-truth
│                           manifest.json (generate_fixtures.py; git-ignored)
├── lib/
│   ├── build_workspace.py  environment half: persona -> frozen post-onboarding
│   │                       workspace (accounts, categories, merchant rules)
│   └── ledger_verify.py    verifier half: pure-read independent recomputation
│                           of a month vs. the manifest ground truth
├── <task-id>/              one Harbor task per capability:
│   ├── task.toml           metadata incl. threshold + written justification
│   ├── instruction.md      the request shown to the agent (no answer leakage)
│   ├── environment/        setup.sh (local) + Dockerfile (containerized runs)
│   ├── solution/solve.sh   oracle: the deterministic pipeline the skills
│   │                       orchestrate — proves the task solvable
│   └── tests/              test.sh verifier -> reward.txt, corrupt.py = the
│                           verifier's plausible-but-wrong fixture
├── run_local.py            local runner (no Docker), Harbor phase semantics
└── jobs/                   run evidence (git-ignored)
```

## Tasks

| Task | Capability | Verifier |
|---|---|---|
| `reconcile-clean-month` | end-to-end ingest → match → categorize → exact June totals (p01) | deterministic: `validate_workspace` + `ledger_verify` vs manifest |
| `transfer-not-income` | one-legged own-account transfers never income/expense, under cp1250 + desc entropy (p02, blindspot #2) | deterministic, + own-account-internal clause |
| `reimport-dedup` | re-importing an overlapping export changes nothing (p01, blindspot #4) | deterministic, + harness-observed re-import artifact |
| `welcome-back-shame-free` | shame-free re-entry after an absence | LLM judge over `tests/rubric.md` (judge runner not wired yet — see below) |

## Running

```bash
uv run harness/scripts/generate_fixtures.py --all evals/personas evals/fixtures
python3 evals/run_local.py --fixtures --keep     # all tasks + verifier fixture tests
python3 evals/run_local.py reconcile-clean-month # one task
```

`--fixtures` enforces the fixture rule: after a passing oracle run, each task's
`tests/corrupt.py` mutates the workspace into a realistic wrong result and the
verifier must reject it. A verifier that passes a corrupted workspace is
reported `BROKEN` and fails the job.

Exit code 0 iff every executed task's reward meets its `metadata.threshold`.
Wire exactly this command into CI — evals that don't run on every change don't
exist.

## Statistical treatment

The three pipeline tasks are fully deterministic end to end (seeded fixtures,
Decimal arithmetic, rule categorization), so N=1 per change is sound — any
mismatch is a defect, and the thresholds are 1.0 by written justification in
each `task.toml`. Conversational tasks are distributions: when the judge runner
lands, run them N≥5 and track pass rate (pass^k for anything autonomous).

## Containerized runs (real Harbor)

Each deterministic task ships a self-contained `environment/Dockerfile`.
Stage the build contexts first, then run:

```bash
bash evals/prepare_containers.sh   # stages environment/ctx/ per task (git-ignored)
harbor run -p evals -i "*reconcile*" -i "*transfer*" -i "*reimport*" \
  -a oracle --env docker --jobs-dir evals/jobs
```

The `oracle` agent executes each task's `solution/solve.sh` in the container —
a full infrastructure check (build → agent → verifier → reward). Swap in a
real agent (e.g. `-a claude-code`) to evaluate the conversational layer.
Verified: all three tasks score 1.0 under Harbor 0.20 with the oracle agent.

### Full Harbor in Claude Code cloud containers

The Claude Code on the web container image ships `dockerd`/`containerd`/`runc`
but does not start the Docker daemon. The SessionStart hook
(`.claude/hooks/session-start.sh`, registered in `.claude/settings.json`)
starts the daemon and installs the Harbor CLI on session start, so full
containerized runs work out of the box. Two environment facts it accounts for:

- **TLS interception.** Outbound HTTPS from inside task containers is
  transparently intercepted by the session proxy; downloads fail certificate
  verification unless the proxy CA is trusted. `prepare_containers.sh` stages
  `/root/.ccr/ca-bundle.crt` into each build context and the Dockerfiles
  append it to the system trust store (never disable TLS verification).
  Keep verifiers network-free regardless — that's better eval hygiene anyway.
- **Degradation path.** If the daemon can't start (or locally without
  Docker), `evals/run_local.py` preserves Harbor's phase semantics
  (setup / solve / test, `reward.txt`, infrastructure-error vs reward-0)
  so the suite still gates changes.

## Known limitations / next evals

- The judge runner for `welcome-back-shame-free` is not wired; the rubric and
  its two judge-calibration fixtures are ready. Next: a small runner that sends
  reply + rubric to a pinned judge model and records verdict + reason.
- The oracle (`solution/solve.sh`) exercises the deterministic pipeline; the
  conversational layer above it (skills choosing when/how to run the scripts)
  is only covered by the judge-task family so far.
- Candidate next tasks (from the persona `expect` contracts): onboarding
  detection (`salary_days`, yearly items), budget balance
  (`reconcile.py --verify-budget`), mode recommendation, envelope-adoption
  journey.
