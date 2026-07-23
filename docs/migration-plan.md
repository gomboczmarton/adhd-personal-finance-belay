# Migration plan — factory → belay consolidation

Decided 2026-07-23 (decision record: harness-engineering
`research/2026-07-23-factory-product-topology.md`, `docs/19`–`docs/25`; final
architecture: `docs/architecture.md` here). Belay becomes the single public
repo — product + machinery + full suite; the factory repo
(`adhd-personal-finance-harness`, last commit `2e56934` "D15") migrates in and
is archived. Every phase ends with a gate; no phase starts before the previous
gate is green. Record the whole consolidation as **D16** in the migrated
`docs/decisions.md` (phase B) — the first decision recorded in belay.

## Phase A — Prepare belay's structure (no factory content yet)

1. Define the **two namespaces** and write them into README + CONTRIBUTING:
   - *Template-owned* (upgrades may overwrite): `harness/`, `evals/`,
     `.claude/skills/` (shipped skills), `.claude/hooks/`, `.github/`,
     `install.py`, `docs/` (project docs).
   - *Instance-local* (upgrades never touch): `finance/` (user data),
     `harness-local/`, `.claude/skills-local/`, `evals-local/`.
   - `install.py` gains an `--upgrade` mode that touches only template paths.
2. Flip the GitHub **template repository** flag; add the README warning:
   instances via *Use this template* or clone+push to a **private** repo —
   never a GitHub fork (forks of public repos cannot be made private).
3. Add `CONTRIBUTING.md`: contributor flow, the anonymization gate for
   instance-born content, PR CI expectations, plane rules (see gate list).
   **Gate A:** existing suite green (`run_local.py --fixtures`); README/CONTRIBUTING
   reviewed by owner.

## Phase B — Migrate factory content (source paths verified 2026-07-23)

| # | From (factory) | To (belay) | Note |
|---|---|---|---|
| 1 | `evals/personas/{alex-hybrid-journey, eva-real-shape, kovacs-family, noor-multibank, sam-freelancer}.md` | `evals/personas/p03..p07-*.md` | Renumber into the p0x scheme (p01/p02 exist). Fixtures NOT copied — regenerated: `uv run harness/scripts/generate_fixtures.py --all` (seeded ⇒ reproducible). |
| 2 | `evals/bot/persona-bot.md`, `evals/bot/judge.md` | `evals/lib/rubrics/` + new judge tasks | Persona-bot material becomes rubric sources for judge-type Harbor tasks (welcome-back-shame-free is the pattern). |
| 3 | `evals/run_evals.py` | `evals/legacy/run_evals.py` | Kept until parity gate (Phase C), then deleted. |
| 4 | `docs/decisions.md` (D1–D15), `docs/fable.md` + images, `docs/design/*`, `docs/research/bank-formats.md`, `docs/implementation-notes.md` | `docs/` | Design history becomes public project history. Append **D16** (this consolidation). |
| 5 | `evals/runs/` (9 archived runs) | summaries → `evals/experiments.md`; raw runs stay in archived factory | Import one-paragraph summaries per run; raw archives remain reachable in the archived repo. The `2026-07-09-private-data-simulation` run: summary only after owner reviews it for real-data adjacency. |
| 6 | `package_release.py` | `.github/workflows/release.yml` + `tools/package_release.py` | Reworked: tag-push triggers packaging — sanitization scan (unchanged rules: cards, IBANs, emails, home paths ⇒ abort) → `dist/harness-v<ver>.zip` → GitHub Release. The `--export` mode is deleted (no downstream repo anymore). |
| 7 | `demo/` (talk track, video pipeline) | owner's call: `docs/demo/` or stays archived | Not load-bearing; decide during review. |

   **Gate B:** full suite green including regenerated fixtures for all 7
   personas; sanitization scan green over the whole migrated tree; D16 recorded.

## Phase C — Converge the eval systems

1. Author Harbor tasks for the migrated personas' capabilities (eval-engineer
   skill, one capability at a time), reusing their `expect:` blocks.
2. Parity check: legacy `run_evals.py` and `run_local.py` both green on the
   same personas for one full cycle → delete `evals/legacy/`.
3. Designate the **frozen anchor sub-suite** (owner picks ~2 personas' tasks),
   fingerprint it, exclude it from PR CI.
   **Gate C:** parity proven; anchor fingerprint committed.

## Phase D — Activation-plane build (the "superb separation")

1. Meta-entry: `/extend` command routing to the flow builder; builder creates
   flow + wired guardrail calls + component evals + trigger evals together
   (runtime iron rule #1).
2. Harden meta-skill descriptions ("only when the user explicitly asks to
   create/modify flows or evals"); schedule (don't trigger) skill-optimizer.
3. Author the **trigger-isolation eval cases** with skill-creator's method:
   ~20 realistic finance queries asserting NO meta skill fires; ~10 meta
   queries asserting no finance flow launches; add to PR CI.
   **Gate D:** isolation cases green at N≥3 runs; suite green.

## Phase E — Release train

1. PR CI = deterministic suite + trigger isolation (fast, every PR).
2. Release workflow (tag-triggered) = frozen anchor + **fresh-seed
   regeneration gate** (regenerate all fixtures with a new seed; suite must
   stay green) + sanitization scan + package + GitHub Release.
   **Gate E:** one dry-run release end-to-end (v0.2.0 candidate).

## Phase F — Archive the factory

1. Final factory commit: README pointer "migrated to belay @ <tag>, this repo
   is the historical archive"; GitHub *Archive repository* setting.
2. harness-engineering store: record completion in the topology research doc.
   **Gate F:** owner confirms nothing left behind (checklist = Phase B table).

## Standing rules after migration

- All development happens in belay; instances never push upstream;
  contributions pass the anonymization gate (see `docs/architecture.md`).
- Store→belay skill refreshes are deliberate, pinned, and logged in
  `evals/experiments.md`.
- Every phase of this plan is an `experiments.md` entry with its gate result.

## Open items for the owner

1. Phase B #5: review the private-data-simulation run before its summary
   migrates. 2. Phase B #7: demo pipeline in or out. 3. Phase C #3: which
   personas anchor. 4. Naming: keep repo name `adhd-personal-finance-belay`
   or rename to `belay` at consolidation.
