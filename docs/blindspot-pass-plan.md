# Blindspot Pass — docs/plan.md

Date: 2026-07-09 · Phase 1 (Unhubble) of the Fable Flow · Input: `docs/plan.md`

Findings are ordered by architectural impact — the top ones change the shape of the
system, the bottom ones change scope or polish. Each ends with the decision it forces.

---

## 1. The deterministic-core vs LLM-shell split is THE architecture decision

`plan.md` says "the harness will do the reconciliation" and "it will allocate money
automatically." If *the model* does arithmetic — summing envelopes, pairing budget items
with actuals, computing carry-over — results will be non-reproducible and occasionally
silently wrong. Financial software has a zero-tolerance property most agent projects
don't: a single wrong number destroys trust in every number.

The proven shape: **scripts do all money math and matching (deterministic, testable);
the agent converses, classifies, explains, and asks.** The LLM never adds two numbers;
it decides *what a transaction means*, a script decides *what the totals are*.

**Decision forced:** adopt script-core / agent-shell as a founding constraint, or
consciously reject it.

## 2. Internal-transfer matching is a core algorithm, not a prompt

You flagged your own case (envelope refills look like fake income/expense pairs), but the
general solution is unspecified. Every envelope-strategy user generates this noise
constantly: minus on sub-account A, plus on account B, same amount, 0–2 days apart.
This needs a real matching engine — amount-equality within a date window across accounts,
confidence scoring, and an "unmatched leftovers" queue where the agent asks the user.
If this is done by vibes-classification per month, reconciliation reports will
double-count income and the product is dead on arrival.

**Decision forced:** transfer-matching becomes a named, tested component with its own evals.

## 3. The harness's memory needs a schema and a versioning story

The plan names several knowledge stores implicitly: the yearly spending bank, the
recipient/meaning map, category rules, persona/life-situation config, monthly budget
templates. Unstated: where they live, in what format, and how they survive upgrades.
"Elastic for future changes" *means* versioned schemas + migrations — otherwise every
harness update breaks existing users' data, which is fatal for a sold product.
Also: files must be the single source of truth; nothing load-bearing may live only in
conversation memory.

**Decision forced:** define the data files (names, formats, schema-version field) before
writing any skill that reads or writes them.

## 4. Bank CSV chaos is worse than plan.md assumes

Real-world blindspots in "the agent extracts the column structure":

- **Encodings**: Hungarian banks commonly export ISO-8859-2 / Windows-1250, not UTF-8.
- **Decimal commas** and thousand separators (`1 234,56`), dates as `2026.07.09.`
- **No stable transaction IDs** → deduplication across overlapping exports (you download
  2 years at onboarding, then re-download monthly with overlap) is a hard requirement.
- **Silent format changes**: banks change export columns without notice → parser contract
  tests that fail loudly, not scripts that mis-parse quietly.
- Some banks only export XLSX or PDF; is CSV-only a hard v1 assumption?

Also a product trap: "the agent writes a reusable parser per bank" is a support treadmill
across thousands of banks. Safer: one generic **column-mapping wizard** (agent-assisted at
onboarding, persisted as config) + contract tests, instead of promising known-bank parsers.

**Decision forced:** CSV-only v1? Generic mapping wizard vs per-bank parsers?

## 5. Evaluating an interactive onboarding requires a simulated user

The eval vision in plan.md (personas → scenarios → iterate to convergence) is right, but
one mechanism is missing: onboarding is *conversational*, so evals need a **persona-bot**
(an LLM playing the user, seeded with a life situation + synthetic bank data) driving the
harness, plus assertions. And because LLM output is non-deterministic, assertions must
target **artifacts and invariants**, not wording:

- envelope allocations sum to income;
- reconciliation balances to zero (every transaction categorized exactly once);
- no transaction double-counted across overlapping CSV exports;
- yearly-bank items surface in the correct month's plan.

This also forces a **synthetic fixture generator** (fake banks, fake CSVs per persona) —
you cannot ship or test with real data (see #6). The fixture generator is a bigger
workstream than it sounds and should be built first, since everything tests against it.

**Decision forced:** eval stack = fixture generator + persona-bot + invariant checks;
built on day zero, as plan.md already demands.

## 6. Confidentiality must be a process, not an intention

plan.md says "keep my personal data confidential" — but the plan is to *extract* the
harness from the private repo into a public one. Leak vectors: sub-account names, salary
amounts, recipient maps, bank names in examples, real CSV fragments pasted into fixtures
or evals — and **git history is forever** (a later deletion doesn't unpublish it).

Rule worth writing down: **semantics may cross the boundary, data never.** Concretely:
only schemas, flows, and logic are extracted; every example, fixture, and eval input is
synthetic; extraction commits get a sanitization check before push.

**Decision forced:** adopt the "semantics cross, data never" gate as a standing rule in
CLAUDE.md / the flow.

## 7. The ADHD layer is the differentiator — and it's unspecified

The repo is named *adhd*-personal-finance-harness and plan.md mentions "facilitating my
habit changes," but no ADHD-specific feature is specified. Meanwhile envelope budgeting
itself is a solved, crowded market (YNAB, Actual Budget — the latter open-source). The
sellable moat is the **agent + behavioral layer**: e.g.

- **recovery from a missed month** (the make-or-break ADHD scenario — shame-free
  catch-up flow, not a wall of overdue tasks);
- low-friction capture (one command, no forms);
- small-win feedback loops at reconciliation;
- the agent carrying the executive function (it remembers, it initiates via schedules).

**Decision forced:** specify 3–5 concrete ADHD behaviors as first-class scenarios in the
eval set, or accept building a generic envelope tool in a market that has free ones.

## 8. Time doesn't align: statement cycles, cash, and screenshots

- **Credit card statement period ≠ calendar month.** Reconciliation "for the previous
  month" must define which boundary wins, or numbers never tie out.
- **Cash is a black hole**: ATM withdrawal is visible, what the cash bought is not.
  Needs an explicit stance (treat withdrawal as the spend? envelope for cash?).
- **Portfolio screenshots as input** (plan.md §17) are a fragile OCR dependency —
  conservative alternative: ask the user to type one number monthly.

**Decision forced:** pick conservative defaults for all three and log them.

## 9. Excel round-trip is much harder than Excel export

"Excel templates and scripts to fill them" — writing XLSX is easy; **reading back a
user-edited XLSX** (merged cells, moved rows, manual formatting) is where these tools
break. Decide early: Excel as *write-only human view* with CSV/markdown as the machine
interface, or commit to full round-trip and pay for it in the eval suite. This also sets
the installer's dependency baseline (Python + openpyxl, or Node + exceljs).

**Decision forced:** write-only Excel vs round-trip; pick the runtime stack.

## 10. Monetization has non-code blindspots

- **License before code**: "open-sourcable or sellable" → open-core needs a license
  chosen *before* the repo is public (MIT/Apache = anyone resells; AGPL/BSL protect).
- **Disclaimer**: budgeting tool, "not financial advice" — cheap to add, costly to forget.
- **Data-flow honesty**: users' bank transactions go through the Claude API; the README
  must say so — for an ADHD/privacy-sensitive audience this is a trust make-or-break.
- **Distribution**: Claude Code plugin/marketplace vs git-clone installer — affects how
  onboarding, updates, and schedules are wired.

**Decision forced:** license choice + distribution channel.

## 11. plan.md's open question: Dynamic Workflows — answer

Yes, but narrowly: Dynamic Workflows shine for the **eval loop** (fan out persona ×
scenario simulations in parallel, verify invariants, iterate to convergence — exactly
your gnuplot-loop analogy). The *user-facing* monthly flow should NOT depend on them —
it must run as plain skills/commands so it works in any user's vanilla Claude Code.

---

# Improved prompt (the meta half of the pass)

`plan.md` is strong on vision and scenarios but leaves the constraints above implicit.
Kickoff prompt that would get the best out of Fable for the next phase:

> "Design the personal finance harness from docs/plan.md with these constraints:
> (1) script-core / agent-shell — the model never does arithmetic; all math and matching
> in tested scripts. (2) All harness knowledge in versioned schema files — define them
> first. (3) Semantics cross from my private repo, data never — all fixtures synthetic.
> (4) Build the eval stack first: synthetic fixture generator, persona-bot, invariant
> checks (envelopes sum to income, reconciliation balances to zero, no double-counting).
> (5) v1 scope: CSV-only, write-only Excel, generic column-mapping wizard, single
> currency; log everything else as future work. (6) The ADHD behavioral layer is a
> first-class requirement — including the missed-month recovery scenario.
> Keep docs/implementation-notes.md with a Deviations section. Interview me before
> designing anything the constraints don't settle."

Suggested additions to `plan.md` itself: a **Decisions** section (each blindspot's
resolution), a **Non-goals for v1** list, and the **invariants** list evals will enforce.

---

# Addendum: validated against the reference repo (structure only, no personal data)

After the pass above was written, the private `adhd-personal-finances` repo was cloned
(read-only) and surveyed at the structural level. Results:

**Confirmed:**
- **#4 (bank format chaos)**: real inputs are Erste Bank exports in *both* CSV and XLSX —
  the "CSV-only v1" assumption is already violated by the reference user's own data.
  A dedicated Erste-specific processing script exists, confirming the per-bank-parser
  pattern (and its treadmill risk).
- **#7 (ADHD layer)**: the reference repo has explicit behavioral-finance components
  (shame-free awareness, ADHD-optimized visualization, purchase-impact checks) — the
  differentiator exists in practice and must be extracted, not invented.
- **Phase 4 anchor is strong**: the reference repo already contains ~8 skills
  (monthly-prep, verify-budget, monthly allocation, drift reports, purchase-impact-check,
  financial-wisdom-check…), 5 subagent groups, an ETL spec, a knowledge folder, and
  architecture specs. The harness is an *extraction and generalization* job far more than
  a green-field design — which raises the priority of #6 (sanitization gate).

**New blindspots found:**

12. **Language and localization.** The reference repo is substantially Hungarian
    (docs, category names, reports). A sellable/open-source harness must be
    English-first with the user's language as configuration — affecting category
    taxonomies, report templates, onboarding dialogue, and evals. Translation is
    part of extraction, not a polish step.

13. **Philosophy tension: "awareness over budgeting" vs envelope budgeting.**
    The reference repo's stated principle is *awareness over budgeting* (mindfulness,
    shame-free, no restriction), while plan.md's scenarios describe strict envelope
    allocation and reconciliation. These attract different users and imply different
    defaults. The harness likely needs both as configurable *modes* (or a spectrum
    chosen at onboarding) — an architecture-level decision for the interview.

---

*Next: Phase 2 (Interview) — resolve the forced decisions above, one question at a time,
architecture-first.*
