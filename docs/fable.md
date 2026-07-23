# Work with Fable — the Playbook

This document is the working protocol between Marci (the human) and Fable (the model)
in this repository. It was originally distilled from the slide deck in
`docs/fable-images/` (Thariq Shihipar's "Field Guide to Fable") as a six-phase
pipeline, and later aligned with the canonical **menu-based** version maintained in the
separate fable-flow repo. The portable skill is `.claude/skills/fable-playbook/SKILL.md`
— kept identical to that canon; this page adds only how the playbook is wired into
*this* project.

## The single organizing principle

> **The most important part of working with Fable is staying in the loop.**

Fable-class models can go a long way autonomously. The value comes from the *cycle*
between Marci and Fable — not from long unattended runs on decisions Marci would want
to weigh in on. Every technique below is a **crossroads to involve the human**:
suggest the move, run it together, let the response steer what comes next.

Fable helps in two ways at once, on every task:

1. **Meta guidance** — help Marci instruct Fable better (surface unknowns, sharpen
   prompts).
2. **Project guidance** — drive the actual work while Marci stays in the loop for
   every decision that matters.

## A menu, not a pipeline

Seven techniques, selected by situation — never a fixed sequence. The numbering only
preserves the order of the original talk.

| # | Technique | Group | Reach for it when… |
|---|---|---|---|
| 1 | **Unknown Matrix** — known knowns / known unknowns / unknown knowns / unknown unknowns, mapped with the user | Discovery | a task is vague, novel, or under-specified |
| 2 | **Blindspot pass** — explore the domain first, report the relevant unknown unknowns, propose a sharper prompt | Discovery | Marci enters unfamiliar territory |
| 3 | **Interview** — one question at a time, architecture-changing answers first; stop when remaining unknowns don't change the shape | Discovery | ambiguity survived the first two moves |
| 4 | **Brainstorms & prototypes** — several *wildly different* directions to react to; contrast over polish | Generative | the shape of the solution is unknown |
| 5 | **References** — find an exemplar and reimplement the same semantics, rather than inventing from description | Generative | something existing already behaves right |
| 6 | **Implementation notes** — running log; on edge cases pick the conservative option, record it under Deviations, keep going | Execution | any build is underway |
| 7 | **Report + quiz** — context, intuition, what was done — ending in a quiz the user must pass | Verification | a meaningful chunk of work is done |

When to reach for what: new project → usually open with a discovery move; stuck on
"what should this even look like?" → generative; mid-build ambiguity → interview or
blindspot pass; after any substantial change → report + quiz; at every crossroads →
surface the option instead of pressing on alone.

## How the playbook is wired into this repository

- **Interview outcomes become decisions**: architecture-shaping answers are recorded
  in `docs/decisions.md` (D1…), each with its consequences. CLAUDE.md rule #5.
- **Technique 6 lives in `docs/implementation-notes.md`**: status, progress, and the
  Deviations audit trail Marci reviews at sync points.
- **Technique 4 is generalized here by Marci's standing note**: whenever a single-shot
  answer would silently pick among meaningfully different directions — schemas,
  architecture, report design, dialogue style, naming, eval strategy — Fable
  proactively generates the alternatives in whatever form makes reacting easiest
  (side-by-side HTML for visuals, comparison tables for schemas, samples for tone).
- **Worked examples from this project**: `docs/blindspot-pass-plan.md` (technique 2 on
  plan.md), `docs/design/schema-directions.md` and the report-design artifact
  (technique 4), the reference-repo extraction rules (technique 5, bounded by
  "semantics cross, data never"), the retro-quiz artifact (technique 7).

## Portable version

Copy `.claude/skills/fable-playbook/` into any repository to reuse the playbook; it is
self-contained. The canonical copy is maintained in the dedicated fable-flow repo —
when the canon changes, re-sync the skill here and re-align this page.
