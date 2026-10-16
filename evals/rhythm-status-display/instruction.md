Your finance workspace is the directory given by `$WS`. June 2026 is
reconciled and budgets exist for June and July.

Belay's terminal displays (the band above the prompt, the status line, the
`/belay` month view) draw from one view-model. Produce it for three days, so I
can check what each display would show:

- 2026-07-10 — mid-July, everything in rhythm;
- 2026-08-02 — early August, July not closed yet;
- 2026-11-20 — back after a long break.

For each day write `$WS/.display/status_<day>.json` (the view-model JSON) and
`$WS/.display/line_<day>.txt` (the status-line text).

House rules: numbers come only from the harness scripts (`harness/scripts/`).
The status line never shows an amount, and after a long break nothing on
screen counts or lists what was missed.
