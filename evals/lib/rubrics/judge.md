# Judge — Tier 2 verdicts (spec)

Judging is **artifacts-first, wording-never**: LLM output varies run to run, so no
assertion may depend on phrasing. The judge produces a structured verdict per session.

## Layer 1 — mechanical (scripts, not LLM)

Run before any LLM judging; a failure here fails the session outright:

1. `validate_workspace.py` on the produced workspace → must be green.
2. `expect.onboarding_detects` resolution — each token maps to a machine check against
   the produced workspace + the fixture `manifest.json`, e.g.:
   - `salary_day_1` → strategy/accounts capture income day 1
   - `refills_not_income` → no REFILL-pair transaction categorized as income
   - `car_insurance_due_july` → yearly-bank item with due_months [7] exists
   - `seven_subscriptions` → ≥7 distinct monthly merchants in merchant-map
3. `expect.mode_suggestion` → strategy.md mode matches.
4. Tier 1 invariants re-run on the produced workspace.

## Layer 2 — rubric (LLM judge, transcript)

Only for what scripts cannot measure, scored 1–5 with cited transcript evidence:

- **Shame-free tone**: zero guilt framing, even when the persona confesses failures or
  disappears (the missed-month recovery scenario is scored here).
- **Proposal quality**: changes (e.g. envelope adoption) are *proposed with evidence,
  never imposed*; timing respects the persona's journey (`expect.journey.by_month`).
- **Question economy**: onboarding asks few, high-impact questions; no walls of text
  (ADHD-hostile).
- **Robustness**: handles the bot's quirk-driven friction (vague answers, denial,
  disappearance) without breaking flow or badgering.

Judge prompt rule: the judge sees `expect:` and the rubric, NEVER the persona-bot's
system prompt; it must quote transcript lines as evidence for every score.

## Verdict

`evals/runs/<run>/verdict.json`: layer-1 booleans, layer-2 scores + evidence, overall
pass = all layer-1 true AND no layer-2 score < 3.
