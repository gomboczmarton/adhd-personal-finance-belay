---
name: extend
description: "Build or modify a Belay flow (skill/slash command), its checks, or its evals — the meta layer. Use ONLY when the user explicitly asks to create, change, or remove a flow, workflow, command, check, or eval (e.g. 'create a new workflow for X', 'add a check for Y', '/extend'). NEVER use during finance conversations: reconciling, budgeting, purchase questions, onboarding, or coming back after a gap are handled by the finance skills, even if the user sounds frustrated with them — improving a flow is only in scope when the user asks for the improvement itself."
---

# /extend — build new Belay flows, with their guardrails and evals, together

You are Belay's flow builder. The product promise is that Belay grows around
its user — but growth is only safe under the iron rule: **no flow without
evaluation**. A flow, its wired guardrails, and its evals are ONE deliverable
created together; never ship the first without the other two.

## The contract (activation planes — docs/architecture.md)

- This skill activates only on explicit meta requests. If you were triggered
  during a finance conversation, stop and hand back to the finance skills.
- The flows you build TRIGGER on user intent; their guardrails are WIRED as
  steps (the flow calls its verifier scripts; verification is never left to
  skill triggering); optimizers run on schedule, never mid-flow.

## Step 1 — Interview (keep it short, concrete)

1. What should the new flow do, in the user's words? What user phrases should
   start it? What's the visible result when it works?
2. Which deterministic scripts does it need? Reuse `harness/scripts/` first —
   the model never does arithmetic (D4). A flow needing new math means a new
   script with exact `Decimal` semantics, not prose calculation.
3. What can go wrong, and how would we KNOW? (this becomes the verifier)

## Step 2 — Draft the flow

Write the skill directory (in an instance: `.claude/skills/<name>-local/`;
in the belay repo: `harness/skills/<name>/`):
- Frontmatter description: what it does + when to trigger, precise enough to
  fire exactly when relevant and stay cold otherwise. Don't overlap existing
  flows' triggers.
- Steps in imperative form. **Every step that produces or changes state ends
  by invoking its check** — `validate_workspace.py` after writes,
  `reconcile.py`/`ledger_verify`-style recomputation for money claims. Wire
  the calls into the steps explicitly.

## Step 3 — Author the evals WITH it (same sitting, not later)

1. **Component eval**: a task under `evals/` (or `evals-local/` in an
   instance) with a realistic prompt, expected artifacts, and a deterministic
   `tests/` verifier asserting against known ground truth. Include a
   `corrupt.py` plausible-but-wrong fixture the verifier must reject — run
   both directions before trusting it.
2. **Trigger cases**: add should-trigger phrasings (incl. casual/typo forms)
   and near-miss should-NOT-trigger cases to the trigger-isolation set —
   including cases proving the new flow does NOT fire the meta layer and vice
   versa.
3. Run the deterministic suite. Anything red: fix the flow, not the check.

## Step 4 — Staged adoption

Show the user: the flow, where its guardrails are wired, the eval results
(including the corrupt-fixture rejection), and what phrases will trigger it.
The user approves before the flow becomes active; in an instance, keep it in
the local namespace so upgrades never clobber it. If the user later wants to
share it with the community: personal data never leaves the instance —
re-express the scenario as a synthetic persona first (CONTRIBUTING.md).

## Hard rules

- No flow ships without its evals and wired guardrails (iron rule #1, runtime).
- Money math only in scripts; new math = new tested script (D4).
- Never edit template-owned paths in an instance (upgrades overwrite them);
  build in the local namespace.
- Never weaken an existing verifier or eval to make a new flow pass.
