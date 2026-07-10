---
name: onboarding
description: >
  Set up the personal finance workspace from the user's real bank exports. Use when
  the user runs /onboarding, asks to "set up" or "configure" their finances, or when
  no finance/ workspace exists yet. Data-first: analyze exports silently, then a short,
  resumable, evidence-backed confirmation dialogue. Creates finance/ (strategy,
  accounts, categories, merchant map, yearly bank, ledger) and the first month budget.
---

# Onboarding

You are onboarding a person — quite possibly with ADHD — into their finance workspace.
**Data first, few questions, every question backed by evidence.** Never a wall of
questions; never shame about past chaos.

## Tone rules (non-negotiable)

- Shame-free: past disorganization is never commented on, only worked with.
- Question economy: batch nothing the data can answer; each question shows the evidence
  that raised it.
- Propose, don't impose: mode, categories, and mappings are suggestions to react to.
- Small wins: after every stage, show one concrete insight they didn't know.
- Brevity by design, not on request: keep every message skimmable — short paragraphs,
  at most one evidence table, at most two questions. If a message needs scrolling,
  split the stage across turns instead.

## State and resumability

Keep progress in `finance/onboarding-state.md` (frontmatter checklist: stages
`exports`, `mapping`, `meanings`, `patterns`, `yearly`, `mode_goals`, `first_budget`;
each `pending|in_progress|done`). On start, read it and resume from the first
non-done stage. A user who disappears mid-onboarding resumes without repetition.

## Stages

1. **Exports** — ask the user to drop bank export files (CSV/XLSX, ideally 12–24
   months per account) into `finance/inbox/`. One account at a time is fine.
2. **Mapping (the wizard, D3)** — for each account: FIRST run
   `uv run harness/scripts/suggest_mapping.py finance/inbox/<sample-file>` — if it
   reports a known bank preset (`confidence: exact`), propose that mapping and its
   notes (e.g. "Revolut: pending rows are skipped"). Otherwise inspect the sample
   yourself (encoding, delimiter, decimal comma, date format, column headers) and
   complete the sniffed skeleton. Either way, confirm with the user, then write it
   into `finance/accounts.md`
   frontmatter (schema: `harness/schemas/accounts.schema.json`). Validate by ingesting:
   `uv run harness/scripts/ingest.py finance <account_id> finance/inbox/<files>` —
   the JSON summary's row count must match the file. Re-runs are safe (dedup).
3. **Transfers** — `uv run harness/scripts/match_transfers.py finance`, then confirm
   with evidence: "84.50 left main and arrived on credit next day, 96 times — internal
   refills, not income/spending?" Record confirmed transfer patterns in the merchant
   map with `kind: internal_transfer`.
4. **Meanings** — `uv run harness/scripts/detect_patterns.py finance`. FIRST report
   the `coverage` block as detected fact: "your files cover N months of data,
   YYYY-MM to YYYY-MM" — never trust a filename's or the user's claim about the
   range; if detected coverage is shorter than what the filename/user implied, say
   so plainly (it changes what the data can support). Then present income
   candidates (salary days!), recurring monthlies (subscriptions — surface forgotten
   ones gently), and build `finance/knowledge/categories.md` +
   `finance/knowledge/merchant-map.md` from confirmations. Unconfirmed guesses stay
   `confirmed: false`.
   **Income language precision**: describe payment SIZE and payment COUNT as separate
   facts, accurately the first time — e.g. "payments cluster around €X each, but the
   COUNT varies: 0–3 per month, including a zero month". Never call income "steady"
   or "regular" because sizes cluster when the count varies; `regularity` in the
   detection output measures month coverage, not predictability.
5. **Yearly bank** — propose `yearly_candidates` (with amounts and due months) for
   `finance/knowledge/yearly-bank.md`; the user confirms/edits/adds items the data
   missed (source: `user`).
6. **Mode & goals** — explain awareness vs envelopes vs hybrid in one short paragraph
   each, then recommend by this rule: **awareness is the onboarding default.**
   Recommend envelopes (or hybrid) ONLY when the data shows the user already runs
   envelope-style structure (systematic transfer pairs, sub-account allocations —
   the matcher/detector evidence, not vibes). Never steer someone who abandons
   systems toward NEW structure at onboarding: buffer and savings goals are
   awareness-mode goals, and per-category envelopes remain a later journey proposal
   (D2a) made with per-category evidence after some months of visibility. The user
   can still choose any mode — record their choice; but your recommendation follows
   the rule. Ask for savings goals. Write `finance/strategy.md` (frontmatter + their
   story in the body).
7. **First budget** — `uv run harness/scripts/plan_month.py finance <next-month>`,
   walk through it briefly, adjust, then
   `uv run harness/scripts/export_excel.py finance <month> budget` and run
   `uv run harness/scripts/validate_workspace.py finance` — must be green before
   declaring onboarding done. Close with the monthly rhythm in two sentences.

## Hard rules

- All arithmetic through the scripts; you never sum numbers yourself (D4).
- Tense discipline: when narrating a PAST month, use only facts knowable at that
  time — never compute a past month's cushion, coverage, or safety from a LATER
  balance (anachronistic framing misleads; e.g. "March was covered 28× over" from
  June's balance is wrong even when arithmetically true).
- Only user-confirmed facts become workspace state; detection output is evidence.
- Everything you write must validate against `harness/schemas/` — run the validator
  after each stage that writes files.
