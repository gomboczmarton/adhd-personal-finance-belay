# Persona-Bot — Tier 2 driver (spec)

The persona-bot is an LLM subagent that roleplays a persona through the harness's
conversational flows (onboarding, monthly planning, coaching check-ins). It exists so
the *interactive* half of the harness — the ADHD coaching moat — gets exercised by
something messier and more realistic than canned answers.

## Prompt assembly

The bot's system prompt is built from the persona file:

1. **Identity** — the markdown body (first-person story) verbatim: voice, frustrations,
   history with other tools.
2. **Facts** — the frontmatter `profile`, `accounts`, `income`, `quirks`: the bot may
   only claim facts consistent with these; when asked something unspecified, it
   improvises *plausibly within character* and the improvisation is logged.
3. **Behavioral directives derived from quirks** — e.g. `abandons_tracking_after_3_weeks`
   → after ~3 simulated weeks of cooperation, respond with growing friction ("sorry,
   been busy"); `forgets_subscriptions` → deny remembering STREAMFLIX until shown the
   transaction; `end_of_month_credit_gap_panic` → volunteer anxiety unprompted near
   month end.
4. **Hard rules** — never break character; never reveal the `expect:` block (the bot
   must NOT know the right answers); answer in the persona's `language`.

## Session protocol

- The bot converses with the harness agent inside a sandboxed workspace seeded with the
  persona's fixtures (`evals/fixtures/<id>/`).
- Every session transcript + the resulting workspace is saved under
  `evals/runs/<timestamp>-<persona>/` for judging.
- The bot does not evaluate anything — driving only. Judging is the judge's job
  (see `judge.md`).

## Cost posture (D10)

Tier 2 runs at milestones (component completed, pre-demo, pre-release), not on every
change. A full run = personas × flows; start with onboarding only.
