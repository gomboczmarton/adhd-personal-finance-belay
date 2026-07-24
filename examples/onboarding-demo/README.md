# Onboarding demo — recorded session (persona: Alex, p03)

A real, end-to-end `/onboarding` run of the Belay harness, recorded as a terminal
screencast on 2026-07-24 in a disposable cloud container.

- [`session.gif`](session.gif) — the screencast (88 s; model wait-time compressed,
  everything else real time).
- [`session.cast`](session.cast) — the same, playable with
  `asciinema play session.cast`.
- [`session-full.cast`](session-full.cast) — the uncompressed recording
  (~13 min wall time, real model latency included).
- [`resulting-CLAUDE.md`](resulting-CLAUDE.md) — the memory file the session wrote
  into the finance repo at the user's request, alongside the harness's own state
  (`finance/strategy.md`, `finance/knowledge/`, `finance/accounts.md`).

## How it was made

1. A fresh git repo was created and the harness installed into it with
   `uv run install.py <repo>`.
2. Synthetic bank exports for persona **p03 Alex** (24 months, 2 accounts,
   48 files) were generated with `harness/scripts/generate_fixtures.py` and
   dropped into `finance/inbox/` — the ground-truth `manifest.json` was withheld.
3. `/onboarding` was driven turn by turn playing Alex: confirming the account
   mapping, the 96 refill transfer pairs, categories (including the forgotten
   CLOUDTUNES subscription), the July car insurance, a user-added yearly item,
   awareness mode, and a 3-month buffer goal computed from the data.
4. The session ran through Claude Code print mode (`claude -p` /
   `claude --continue -p`) behind a thin chat frontend, because the interactive
   TUI requires an OAuth login that isn't available inside a cloud session
   container. The skills, scripts, file writes, and conversation are all real.
5. Recorded with asciinema; spinner wait-stretches compressed to ≤2.5 s each
   before rendering the gif with agg.

## What the run verified

- Auto-detection of both dialects (eu_csv preset match; xlsx sniffed by hand).
- 427 transactions ingested, 96/96 transfer pairs matched and excluded from
  income/spending.
- Detected coverage reported as fact (24 months, 2024-07 → 2026-06).
- Salary, both subscriptions, fuel, groceries, dining patterns surfaced with
  evidence; awareness mode recommended per the onboarding rule (no envelope
  structure in the data).
- `plan_month.py` mid-month lookback pitfall caught and worked around in-session
  (July had no export yet and would have deflated the August draft).
- `validate_workspace.py` green at the end: 6 documents, 854 ledger events.
