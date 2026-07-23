# SkillOpt-Sleep — installation and operating reference

Source: https://github.com/microsoft/SkillOpt (MIT). Examined at commit
`61735e3922efc2b90c6d6cab561e62e98452ca90` (2026-07-23, post-v0.2.0 `main`).
Full annotated summary: the store's
`research/references/2026-07-23-microsoft-skillopt.md`.

## Install options (in order of preference)

**A. Source checkout + Claude Code marketplace plugin (recommended — gets
handoff mode and `--preferences`, which PyPI 0.2.0 lacks):**

```bash
git clone https://github.com/microsoft/SkillOpt.git ~/SkillOpt
cd ~/SkillOpt && git checkout 61735e3922efc2b90c6d6cab561e62e98452ca90  # pin; drop for latest
# inside Claude Code:
/plugin marketplace add ./plugins/claude-code
/plugin install skillopt-sleep@skillopt-sleep
/skillopt-sleep status        # verify
```

A source checkout needs **no pip install** — the plugin's bundled runner
(`scripts/sleep.sh`) auto-selects a Python ≥ 3.10 interpreter and imports the
`skillopt_sleep` package from the checkout. The engine has zero dependency on the
research half (`skillopt/`).

**B. PyPI (base CLI only; no handoff, no `--preferences` until the next release):**

```bash
pip install skillopt        # or: uv tool install skillopt
python -m skillopt_sleep --help
```

Field note (2026-07-23, Claude cloud container): `pip install skillopt` into a
venv worked; running the engine from a raw source checkout via `PYTHONPATH`, and
spawning `claude -p` subprocesses (`--backend claude`), were both blocked by the
session permission classifier. In cloud sessions prefer the pip-installed CLI
with `mock`, and the plugin's `/skillopt-sleep-handoff` command for real
optimization; run `--backend claude` nights on a local machine.

## CLI surface (v0.2.0)

Actions: `run`, `dry-run`, `status`, `adopt`, `harvest`, `schedule`, `unschedule`.

| Flag | Default | Meaning |
|---|---|---|
| `--project PATH` | cwd | project to evolve (targets, state, staging live here) |
| `--scope invoked\|all` | invoked | which `~/.claude/projects/*` transcripts to harvest |
| `--backend mock\|claude\|codex\|cursor\|copilot\|handoff\|azure_openai` | mock | who performs model calls |
| `--source claude\|codex\|cursor\|auto` | claude | transcript source |
| `--lookback-hours N` | 72 | harvest window |
| `--max-sessions / --max-tasks` | 3×tasks / 40 | work bounds (NOT token budgets) |
| `--edit-budget N` | 4 | max bounded edits per night |
| `--target-skill-path PATH` | managed skill | explicit SKILL.md to evolve |
| `--tasks-file PATH` | — | replay a reviewed task file instead of harvesting |
| `--preferences "…"` | empty | house rules injected into reflection (main only) |
| `--auto-adopt` | off | adopt accepted proposal without a separate command |
| `--progress` / `--json` | off | stderr progress / machine-readable output |

Do NOT pass experiment-harness flags (`--gate`, `--rollouts-k`,
`--optimizer-model`, `--budget-tokens`…) to the nightly CLI — unsupported.

## Config keys (`~/.skillopt-sleep/config.json`)

`gate_mode` (`on` default / `off` greedy — keep ON; their own gate-off run
collapsed −52.8 pts), `gate_metric` (`hard|soft|mixed`), `dream_rollouts` (>1 =
contrastive multi-rollout reflection; experiments used 5), `recall_k` (>0 recalls
similar past tasks; experiments used 10–20), `dream_factor` (synthetic variants),
`evolve_memory` / `evolve_skill` (toggle CLAUDE.md vs SKILL.md consolidation),
`preferences`. Shipping defaults are conservative (`dream_rollouts=1`,
`recall_k=0`) — safe, not spectacular; opt into replay knobs once tasks recur
with a checkable signal.

## One night, mechanically

```
harvest ~/.claude (read-only) → mine recurring TaskRecords (train/val split)
  → replay under current skill+memory → consolidate: reflect → bounded edits
  → held-out gate → stage .skillopt-sleep/staging/<ts>/{report.md,proposed_*,…}
  → (human) adopt → backup + apply
```

Handoff mode specifics: engine exits code 3 with
`.skillopt-sleep-handoff/PROMPTS.md` + `pending.json`; each prompt is answered
verbatim by an isolated fresh-context subagent into `answers/<id>.md`; re-run the
same command to resume; typically 3–6 rounds. Mined tasks are pinned to
`tasks.json` on round one so answering sessions cannot shift the task set.

## Repo hygiene in the target harness

- Add `.skillopt-sleep/` and `.skillopt-sleep-handoff/` to `.gitignore` — staging
  and handoff dirs are run artifacts; the lab-notebook record goes in
  `experiments.md`, adopted skill edits arrive via normal commits.
- Treat `evidence.jsonl` and handoff batches as sensitive local data (truncated,
  redacted-but-not-guaranteed transcript excerpts).

## Key-freeness map (why this tool answers the API-key pain)

| Need | Key-free path |
|---|---|
| Prove mechanism / gate | `experiments.run_experiment` (deterministic) |
| Plumbing on real transcripts | `--backend mock` |
| Real optimization, cloud session | `/skillopt-sleep-handoff` (session budget, isolated subagents) |
| Real optimization, local machine | `--backend claude` (authenticated CLI subscription) |
| Only path that truly needs a raw key | direct-API backends (`azure_openai`, OpenAI-compatible) — avoid unless a spend-capped eval key already exists |
