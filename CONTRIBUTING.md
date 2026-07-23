# Contributing to Belay

Belay is one public repo serving two audiences: **users** install tagged
releases and live in private instances; **contributors** (who are usually
users too) work here on `main`. Architecture: `docs/architecture.md`.
Decision history: `docs/decisions.md`.

## The rules that gate every PR

1. **No flow without evaluation** (iron rule #1). A new or changed skill ships
   in the same PR with its eval coverage: a Harbor task (or extension of one),
   a verifier fixture (`tests/corrupt.py` that the verifier must reject), and
   — for new skills — trigger-isolation cases.
2. **Flows trigger, guardrails wire, meta invokes.** Domain skills may trigger
   on user intent; verifiers are invoked by flow steps (never left to skill
   triggering); meta capabilities (flow building, eval authoring, optimizers)
   activate only on explicit request. PRs that blur planes are rejected.
3. **Scripts do the math** (D4). The model never does arithmetic; money logic
   lives in `harness/scripts/` with eval coverage.
4. **Anonymization gate.** Content sourced from your own instance (flows,
   fixtures, bug reproductions) must be synthetic before it enters a PR:
   no real merchants tied to you, no real amounts/dates from your ledger, no
   personal data of any kind. Personas are the pattern — encode the *shape*,
   not your data. `tools/package_release.py`'s forbidden-pattern scan runs in
   CI and will reject the obvious cases; the judgment call is yours.
5. **One capability per eval task**; deterministic verifiers assert against
   generated `manifest.json` ground truth, never re-derive it.

## Workflow

- Run the suite before pushing: `uv run harness/scripts/generate_fixtures.py
  --all evals/personas evals/fixtures && python3 evals/run_local.py --fixtures`.
- PR CI runs the deterministic suite minus the frozen anchor sub-suite
  (`evals/ANCHOR`); the anchor + fresh-seed regeneration run only in the
  release workflow — don't tune against them.
- Record notable experiments in `evals/experiments.md` (change, hypothesis,
  before/after, decision).
- User-suggested workflows land as issues; generalizing one into a shipped
  flow means building it the same way `/extend` does: flow + wired guardrails
  + evals together.

## What NOT to send

- Personal data in any form (see rule 4) — including in fixtures and examples.
- Direct edits to generated content (`evals/fixtures/` is git-ignored and
  regenerated; edit personas instead).
- Skills whose description could fire during finance flows but whose job is
  engineering (plane violation).
