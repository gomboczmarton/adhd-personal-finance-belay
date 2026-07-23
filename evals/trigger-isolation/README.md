# Trigger-isolation cases (activation-plane gate)

Proves the plane contract (`docs/architecture.md`): finance queries never fire
the meta plane; meta queries fire it and never launch finance flows. A harness
that fails these misbehaves exactly the way the consolidation was designed to
prevent — engineering skills waking up during a user's money conversation.

## Running

Use the built-in **skill-creator** skill's trigger-eval mechanism (it plants
each skill description and runs real `claude -p` queries, detecting whether
the skill actually loads — behavioral, not judged):

1. In a Claude Code session in this repo: ask skill-creator to run a trigger
   eval using `evals/trigger-isolation/cases.json` for each skill in
   `planes.meta_skills`, 3 runs per query.
2. Pass rule is in `cases.json`. Record the run in `evals/experiments.md`.

Notes: needs an authenticated `claude` CLI able to spawn subprocesses (works
locally and in interactive sessions; cloud permission classifiers may block
it). Cases 7–11 are deliberate near-misses — the valuable negatives. When
`/extend` creates a new flow, it must append that flow's should/should-not
cases here (see the extend skill, step 3).
