# Demo sessions — one user's first month with Belay, recorded

Six real, recorded Claude Code sessions in one continuous workspace, played as
persona **p03 Alex** (24 months of synthetic exports, 2 accounts). Together they
model how the harness is meant to be used: onboard once, then live the monthly
rhythm. Each folder has `session.gif` (wait-time compressed), `session.cast`
(same, for `asciinema play`), and `session-full.cast` (raw timing).

Recorded 2026-07-24 → 2026-07-26 in a disposable cloud container; the finance
workspace itself was discarded with the container, as intended. Sessions ran
through Claude Code print mode behind a thin chat frontend (see
`01-onboarding/README.md` for the mechanics and why).

| # | Session | What it demonstrates |
|---|---|---|
| 01 | [`/onboarding`](01-onboarding/) | Fresh repo → workspace: dialect detection, 96/96 transfer pairs, forgotten subscription surfaced, awareness mode recommended by rule, first budget. Wrote the `CLAUDE.md` memory profile on request. |
| 02 | [`/welcome-back`](02-welcome-back/) | The make-or-break re-entry: warm first sentence, gap stated as fact ("July is just… not in the system"), the small door, and an exit that's genuinely okay to take — Alex leaves without doing anything, and that's treated as fine. |
| 03 | [`/reconcile-month`](03-reconcile-month/) | July closed in one turn: 18 transactions auto-categorized, the €420 yearly insurance recognized (flagged since onboarding), accidental overlapping re-downloads deduped (427 duplicate rows skipped, zero double-counting), letter + HTML report + Excel written. |
| 04 | [`/monthly-prep`](04-monthly-prep/) | August drafted from fresh history — and the rolling average *protected* from July's insurance spike (kept car at €72.56 instead of the naive €214.12). One open question ("anything unusual?") adds a €200 trip as a user-sourced overlay that won't skew future baselines. |
| 05 | [`/purchase-check`](05-purchase-check/) | €340 espresso machine: four factual lines (July surplus, August draft, buffer-goal effect), options not verdicts. Alex chooses to wait and the choice is logged as a `decision.logged` win. |
| 06 | [`finance-coach`](06-coach-checkin/) | First journey check-in: one theme, evidence not adjectives, the logged espresso win reflected back, Cloudtunes gently resurfaced, and — correctly — *nothing proposed* after a single month of data. |

## Findings the demo surfaced

- `plan_month.py`'s 3-month lookback counts the current, not-yet-exported month
  as zero when run mid-month (caught and worked around in session 01, recorded
  in the workspace `CLAUDE.md`).
- Session 05's `decision.logged` event was written with a `note` field instead
  of the schema-required `text` — caught by `validate_workspace.py` after the
  session (fixed in the workspace by hand). The purchase-check skill's flow
  doesn't end with a validator run the way the other writing skills do; adding
  that step (or an evals task for decision logging) would close the gap.
- `install.py` ships no `CLAUDE.md`; the memory profile in session 01 was
  written only because the user asked. Worth considering as an install-time
  artifact.
