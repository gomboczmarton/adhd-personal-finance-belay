<p align="center">
  <img src="assets/logo.svg" width="170" alt="Belay logo — a carabiner holding a rope">
</p>

<h1 align="center">Belay</h1>

<p align="center"><b>You climb. It holds the rope.</b><br>
A shame-free personal-finance companion for ADHD brains, built as a Claude Code harness.</p>

---

In climbing, the *belayer* is the partner who holds your rope — mostly invisible,
always attentive, and the reason a slip is an event, not a fall. Belay does that for
your money: it ingests your real bank exports, learns what your transactions mean,
and then carries the executive function of a monthly money rhythm — planning,
reconciliation, and behavioral coaching — so you don't have to hold it all in your
head.

**Philosophy: awareness over budgeting, structure as optional equipment.** Belay
starts by making money *visible* without judgment. Where visibility alone isn't
enough, it *proposes* small reversible steps — one envelope, one category, with a
review date. Envelope budgeting is a destination some users converge to, never a
prerequisite. And the make-or-break scenario is designed in: coming back after a
missed month (or three) is a five-minute, zero-shame catch-up — never a wall of
overdue tasks. **The win is that you came back.**

## Install

Into any git repo you want to keep your finances in (a fresh empty one is fine):

```bash
# from this repo
git clone https://github.com/gomboczmarton/adhd-personal-finance-belay
uv run adhd-personal-finance-belay/install.py /path/to/your-finance-repo

# or straight from the latest release
uv run install.py /path/to/your-finance-repo --from-release

cd /path/to/your-finance-repo && claude
> /onboarding
```

Requirements: Python 3.11+, [uv](https://docs.astral.sh/uv/),
[Claude Code](https://claude.com/claude-code).

## What you get

| Skill / agent | When |
|---|---|
| `/onboarding` | Once: drop 12–24 months of bank exports (CSV/XLSX — known banks are auto-detected, a mapping wizard adapts to any other), answer a handful of evidence-backed questions, get your workspace and first budget. Resumable at every stage. |
| `/monthly-prep` | Start of month: a drafted budget from your history, yearly items due this month pre-filled and highlighted, transfer checklist for your banking app. |
| `/reconcile-month` | End of month: exports in → deduped, transfers matched, categorized, plan-vs-actual story + Excel view. Overspend is information, not failure. |
| `/purchase-check` | "Should I buy this?" — a 30-second factual impact picture. You decide; Belay is the mirror, not the parent. |
| `/welcome-back` | Been away? The whole gap summarized in five lines and a fresh start. |
| `finance-coach` agent | The journey layer: pattern reflections, small reversible experiments, goal check-ins. |

Bank formats with built-in auto-detection: Revolut, Wise, N26, Monzo CSV; OTP
netbank XLSX; generic EU / Hungarian CSV shapes. Anything else goes through the
interactive mapping wizard once and is remembered.

## See it before you run it

- [`examples/sample-monthly-report.html`](examples/sample-monthly-report.html) — a
  closed month as Belay presents it: a coach's letter first (one win leads), energy
  meters where numbers need shape, the full statement table one layer down.
- [`examples/demo-workspace/`](examples/demo-workspace/) — a complete synthetic
  workspace six months into the journey: readable markdown state, an append-only
  ledger, budgets with a yellow-flagged yearly item, and one freshly adopted
  envelope experiment. Every file is what your own `finance/` folder would look
  like. (All data is synthetic by construction — no real person's finances appear
  anywhere in this repository.)

## Why you can trust the numbers

- **The model never does arithmetic.** All money math — parsing, dedup, transfer
  matching, reconciliation, budget verification — runs in deterministic Python
  scripts (`harness/scripts/`), exact to the cent in `Decimal`.
- **Internal transfers are never income.** Credit-card refills and own-account
  sweeps are matched and excluded — the classic failure of finance apps on
  envelope-style banking.
- **Re-importing is always safe.** Content-hash dedup means overlapping exports add
  zero duplicates, ever.
- **Tested like software, and like a conversation.** The engine ships with a
  deterministic eval suite (five synthetic personas, ground-truth manifests,
  40 checks green), and the conversational behavior is evaluated with persona-bot
  sessions judged against a shame-free rubric before any skill changes ship.

## Your data stays yours

Everything lives in *your* repo: readable markdown plus an append-only ledger under
`finance/`. Nothing is uploaded anywhere except through the Claude API calls that
power the conversation itself. Delete the folder and it's gone.

## Version

v0.1.0 — first public cut. Built in a private factory repo where the eval suite,
personas, and design history live; releases here carry the packaged harness
(`dist/harness.zip`, also attached to GitHub Releases).
