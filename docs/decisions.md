# Decisions Log

Running record of architecture-shaping decisions, resolved through the Fable Flow
interview phase (see `docs/blindspot-pass-plan.md` for the questions' origins).
Newest at the bottom. Each entry: decision, consequences, date.

---

## D1 — Local-first, pure Claude Code harness; monetization out of scope

**Date:** 2026-07-09 · **Answers blindspot:** #10, interview Q1

The harness is entirely local and file-based: the user's git repo is the database,
everything runs inside the user's own Claude Code. No hosted component, no accounts,
no licensing infrastructure.

Monetization is explicitly **out of scope** — the near-term goal is a project worth
showing to a stakeholder (demo-readiness over product packaging).

**Consequences:**
- Files + versioned schemas are the entire persistence layer (raises priority of
  blindspot #3).
- Installer = git clone + onboarding slash command; no update server.
- License/disclaimer/data-flow-disclosure items (#10) are deprioritized, not deleted —
  revisit if the project later goes public.
- "Sellable" quality bar is replaced by "stakeholder-demo" quality bar: an end-to-end,
  polished happy path matters more than breadth of bank/persona coverage.

## D2 — Two modes, chosen at onboarding: awareness ↔ envelope-control

**Date:** 2026-07-09 · **Answers blindspot:** #13

The harness supports both philosophies as configurable modes selected during onboarding:
*awareness* (shame-free visibility, drift reports, impact checks — what the reference repo
does today) and *envelope control* (strict allocation + monthly reconciliation — plan.md's
family scenario). Onboarding asks where the user sits on the awareness↔control spectrum
and wires the matching skills.

**Consequences:**
- Skill set is layered: shared core (ingestion, categorization, transfer matching,
  reports) + mode-specific skills (allocation/reconciliation vs drift/impact).
- Personas and evals must cover both modes; mode is a dimension of the eval matrix.
- Onboarding gains a mode-selection step; config schema gets a `mode` field.

### D2a — Amendment (2026-07-09): ADHD coaching is the foundation; mode is a journey, not a switch

Marci's historical note: the project *started* as an ADHD facilitator. He later learned
personal finance, discovered envelope budgeting, and found it to be his personal missing
piece — his harness **converged** to the envelope structure over time, guided by the
awareness the coaching layer had built. That convergence story is itself the product's
core promise: the harness facilitates each user in finding the setup that fits *their*
life, rather than imposing a structure.

Refinements to D2:
- **The ADHD coaching skill system is the moat and the primary extraction target.**
  Do NOT extract/generalize the envelope solution strictly as the harness's spine.
- Envelope budgeting is **one strategy module** (well-proven by the reference
  implementation), not the mandatory destination. The architecture must leave room for
  other structures a user might converge to.
- The onboarding `mode` is a **starting point, not a lifetime setting**: the coaching
  layer may propose transitions ("your patterns suggest envelope allocation might help
  with X — want to try it for groceries only?") and the config schema must support
  gradual/partial adoption and later change without data loss.
- Evals gain a **journey scenario**: a persona that starts awareness-only and migrates
  to (partial) envelopes over simulated months — the reference user's own arc.

## D8 — Data architecture: Notebook state + transaction Ledger (hybrid)

**Date:** 2026-07-09 · **Answers blindspot:** #3 · **Chosen from:** `docs/design/schema-directions.md`

Human-edited state (strategy, accounts, knowledge, monthly budgets) lives in readable
markdown documents whose YAML frontmatter is the machine-parsed part — one file is both
the human view and the machine state. Transactions and categorizations live in an
append-only event log (`ledger/events.jsonl`) where dedup and audit matter most.
Reports (reconciliation, snapshots, XLSX) are always generated, never edited.

**Consequences:**
- One owner per fact: frontmatter for slow-changing state, ledger for money facts,
  `reports/` strictly generated (kills the reference repo's sync-drift problem).
- Needs a frontmatter-validating script/hook, since prose edits can break machine state.
- Scripts read state through a frontmatter-parsing layer; events are plain JSONL.
- The D2a journey is representable on both sides: `strategy.md` tells the story,
  `strategy.adopted` events record the transitions.

## D9 — Persona = eval package (profile + fixtures + expected outcomes in one file)

**Date:** 2026-07-09 · **Answers blindspot:** #5 · **Chosen from:** Step 2 branching moment

A persona is a single markdown file whose frontmatter carries the persona-bot profile,
the fixture-generation parameters, AND the `expect:` block — what the harness must
detect and produce for this persona. The body is the first-person story (bot voice).
Personas literally are the test cases: plan.md's TDD-for-harness made concrete.

**Consequences:**
- Adding a scenario = adding one persona file; the eval matrix grows by files, not code.
- The fixture generator validates personas against `persona.schema.json` before
  generating; fixtures ship with a `manifest.json` ground truth for assertions.
- Fixture generation is deterministic (seed from persona id) so eval runs are
  reproducible and fixture diffs reviewable.

## D10 — Two-tier evals: deterministic scripts always, persona-bot at milestones

**Date:** 2026-07-09 · **Answers blindspot:** #5, plan.md item 4 · **Chosen from:** Step 3 branching moment

Tier 1: pure-script invariant checks against fixture manifests and produced workspaces —
run on every change, no LLM, exit-code driven (the gnuplot convergence loop). Tier 2:
an LLM persona-bot drives real onboarding/coaching conversations in a fixture-seeded
sandbox; judged artifacts-first (mechanical Layer 1) with an LLM rubric only for tone
and proposal quality (Layer 2), run at milestones.

**Consequences:**
- Component-gated checks SKIP until the component exists, then FAIL until implemented —
  Step 4's definition of done is "Tier 1 fully green".
- Assertions never depend on LLM wording; transcripts + workspaces are archived per run.
- Dynamic Workflows (plan.md item 4): used to fan out Tier 2 persona × flow sessions in
  parallel; never a dependency of the user-facing harness.

## D11 — Install = copy script (plugin packaging deferred)

**Date:** 2026-07-09 · **Answers blindspot:** #10 distribution · **Chosen from:** Step 5 branching moment

`uv run install.py <target-repo>` copies `harness/skills/*` → target `.claude/skills/`,
`harness/agents/*` → `.claude/agents/`, and `harness/{scripts,schemas}` → target
`harness/`. Creates `finance/inbox/`. Harness-owned files are overwritten on reinstall
(that's the upgrade path); user state under `finance/` is never touched.

**Consequences:**
- Works in vanilla Claude Code, zero packaging infrastructure, auditable by reading.
- The install path is exercised by the `lifecycle_end_to_end` eval on every run.
- Claude Code plugin packaging remains possible later without changing the layout.

## D12 — Onboarding is data-first with staged, evidence-backed confirmation

**Date:** 2026-07-09 · **Answers blindspot:** #6 of plan.md scenarios · **Chosen from:** Step 5 branching moment

The user drops exports into `finance/inbox/`; scripts analyze (mapping, income days,
recurring monthlies, yearly candidates, transfer pairs); then a short staged review
where every question carries its evidence. Progress checkpointed in
`finance/onboarding-state.md` — fully resumable (the abandoned-onboarding case is a
welcome-back scenario, not a restart).

**Consequences:**
- Question economy is a hard rule: nothing the data can answer is asked.
- Only user-confirmed facts become workspace state; detection output is evidence.
- `detect_patterns.py` is the analysis engine; its findings are asserted against
  persona ground truth inside the lifecycle eval.

## D13 — Monthly report design: coach's-letter shell + energy meters, table one layer down

**Date:** 2026-07-09 · **Chosen from:** Step 5 visual branching moment
(4 directions, artifact `report-design-directions`, four philosophies on identical
synthetic data)

The report opens as a short letter (one win first, numbers inside sentences, exactly
one decision asked), with energy-meter capacity bars embedded where numbers need shape
(outline = plan, fill = actual, warm fill = over), and the sober status-chip table
available one scroll/click below for power users. Rejected as primary surfaces:
pure meter (weak on tone), pure table (no emotional lift), mission-control density
(overwhelms the core user; may return as an optional stakeholder-demo view).

**Consequences:**
- The HTML monthly report generator (demo polish, next step) renders letter → meters
  → table in that order; Tier 2's judge rubric ("one win first", "one decision max")
  now has a designed surface to match.
- Chart colors/marks follow the validated dataviz palette used in the prototypes.
- "Full = bad" meter semantics apply only to envelopes; awareness targets render as
  reference ticks, not capacity limits (D2a tone rule).

## D14 — Product name: **Belay**; factory/product distribution split

**Date:** 2026-07-10 · **Chosen from:** the step 7 naming branching moment
(4 directions, artifact `naming-directions`: Belay / Squirrel Money / Steady /
Money Mirror — name + logo + pitch each)

The public product is named **Belay** — the climbing partner who holds your rope.
Tagline direction: *"You climb. It holds the rope."* Chosen because it makes the
harness metaphor warm instead of clinical: structure as optional *equipment* becomes
literal, and `/welcome-back` is being caught after a slip — the zero-shame philosophy
in one image. Runner-up qualities (Squirrel's memorability, Mirror's philosophy line)
may inform README voice but not the name.

Distribution split (roadmap C9): THIS factory repo stays private; a public product
repo under the chosen name carries the marketing README, logo (SVG), install
instructions, screenshots/sample report, and GitHub Releases with the packaged
artifact (`harness-vX.Y.zip` = `harness/` + `install.py` + README). Factory → product
publishing is a scripted, sanitization-checked export (iron rule #2 enforced by a
script, not by care). `install.py` gains `--from-release`. Versioning: tag factory,
release product.

**Consequences:**
- Namespace due diligence (2026-07-10): no finance/budgeting project named Belay
  found; the notable collision is `BrianPugh/belay` (a MicroPython dev tool) and
  BELAY Solutions (a US staffing company) — different domains, no blocker for a
  free OSS repo. Recommended slug `belay-money` (distinguishes in search); bare
  `belay` acceptable under the owner's namespace. PyPI publishing is NOT planned
  (zip release), so the PyPI `belay` package collision is moot.
- Marci creates the empty public repo and adds it to a session via `add_repo`;
  Fable fills it (README, logo, packaging script, first release `harness-v0.1.zip`).
  Created 2026-07-10 as `gomboczmarton/adhd-personal-finance-belay` — Marci chose a
  descriptive slug over the recommended `belay-money`; product NAME stays Belay.
- Executed 2026-07-10 (branch `claude/session-context-emyydi` in the product repo):
  marketing README with the one-sentence belay explanation, carabiner+rope SVG logo,
  vendored sanitization-checked export (5 skills, coach agent, 10 scripts,
  8 schemas, install.py), synthetic examples (demo workspace + sample D13 report),
  `dist/harness.zip` + versioned zip, RELEASING.md. Factory side:
  `package_release.py` (whitelist + forbidden-pattern gate; negative-tested),
  `VERSION` 0.1.0, `install.py --from-release/--from-zip` (zip path tested
  end-to-end). DONE 2026-07-11: GitHub Release v0.1.0 PUBLISHED via a release workflow
  (`.github/workflows/release.yml`, idempotent on VERSION) with both zips
  attached; the workflow created the tag. License: MIT (Marci's choice),
  LICENSE committed. Remaining: flip the repo to PUBLIC when ready to launch
  (it is private today), and merge the session branches (done same day).
- README hero must explain the belay metaphor in one sentence for non-climbers.
- Status: name decided; repo creation + fill pending (next-steps.md step 7.2–7.4).

## D3 — Ingestion via a generic column-mapping wizard (CSV + XLSX)

**Date:** 2026-07-09 · **Answers blindspot:** #4

One ingestion engine, bank-agnostic. At onboarding the agent inspects the user's real
export file, proposes a column mapping (dates, amounts, description, balance, encoding,
decimal format), the user confirms, and the mapping is persisted as per-account config
protected by contract tests. No per-bank parser library is shipped or promised.

**Consequences:**
- Handles encodings (Windows-1250 etc.), decimal commas, and XLSX from day one.
- Dedup across overlapping exports is part of the engine (content-hash transaction
  identity), not per-bank code.
- An Erste mapping will exist as *the user's own config*, not as shipped harness code —
  keeps the confidentiality boundary clean (semantics cross, data never).
- Contract tests fail loudly when a bank silently changes its export format.

## D4 — Script stack: Python 3.11+ with uv, dependency-lean

**Date:** 2026-07-09 · **Answers blindspot:** #1 (confirms script-core/agent-shell), #9

The deterministic core (money math, matching, dedup, ingestion, Excel generation) is
Python, run via uv with inline script metadata; openpyxl for XLSX. The agent never does
arithmetic — scripts compute, the agent converses, classifies, and explains.

**Consequences:**
- Matches the reference repo's existing Python logic → extraction stays close to source.
- Harness prerequisite: Python 3.11+ and uv (checked by the installer/onboarding).
- Every core component ships with tests; the eval system invokes the same scripts.

## D5 — Excel is write-only: human-facing view, never machine state

**Date:** 2026-07-09 · **Answers blindspot:** #9

The harness *generates* XLSX budget templates and reports for humans to read. Machine
state lives exclusively in harness-owned CSV/JSON files. User input comes through chat
(or files the harness itself owns) — user-edited XLSX is never parsed back.

**Consequences:**
- Kills the fragile round-trip failure mode (moved rows, merged cells) entirely.
- Monthly inputs like the savings-account balance are asked in chat, not read from sheets.
- If round-trip is ever wanted, it becomes a new decision with its own eval coverage.

## D6 — English core, user language as onboarding config

**Date:** 2026-07-09 · **Answers blindspot:** #12

All harness code, skills, schemas, and docs are English. The user's language (chosen at
onboarding) governs dialogue, category display names, and generated reports — rendered
naturally by the agent, no i18n string files. Marci's own instance runs in Hungarian.

**Consequences:**
- Extraction from the reference repo includes translation to English as part of the work.
- Category taxonomy stores canonical English keys + per-user display names.
- Evals run in English; at least one persona exercises a non-English configuration.

## D7 — Stakeholder demo = full lifecycle on a synthetic persona

**Date:** 2026-07-09 · **Answers blindspot:** #5, #6 (reinforces), demo scope

The demo shows the whole promise end-to-end on synthetic data: onboarding from fake bank
exports → configuration + first monthly budget → a simulated month of transactions →
reconciliation report → next-month plan. Safe to show anyone; exercises every core
component.

**Consequences:**
- The synthetic fixture generator (fake bank exports per persona) is on the critical
  path for BOTH the demo and the eval system — build it first.
- Every core component must actually work for at least the demo persona — nothing in the
  happy path can be stubbed.
- No real personal data is ever needed for the demo (confidentiality by construction).

## D15 — Partner outreach begins: demo videos for monetization conversations

**Date:** 2026-07-11 · **Amends:** D1's "monetization out of scope"

Marci opened the monetization track: partner-facing demo videos of the harness's
onboarding and monthly use. D1's local-first architecture is unchanged — what
changes is the audience (potential partners, not just stakeholders). Choices
(Marci, 2026-07-11): English; a 90s teaser AND a ~3min walkthrough; silent with
captions; mixed visuals (stylized chat UI for conversations, terminal look for
commands/evals).

**Consequences:**
- `demo/video/` carries a deterministic render pipeline (seek(t) frame renderer —
  no screen recording, byte-stable re-renders, surgical edits).
- All conversational content in the videos is quoted/condensed from archived
  judged Tier 2 transcripts; terminal content is real script output (rule #2:
  synthetic only, enforced by sourcing).
- The videos themselves are not committed (gitignored); they are delivered
  directly and can be re-rendered from source at any time.
- Future monetization decisions (pricing, packaging, hosted offering) remain
  OPEN — this decision covers outreach material only.

## D16 — Consolidation: one public repo + private instances; factory archived

**Date:** 2026-07-23 · **Amends:** D14 (factory/product split) · **Decision record:** harness-engineering store, `research/2026-07-23-factory-product-topology.md` + `docs/19`–`docs/25`

The factory/product two-repo split collapses into ONE public repo (this one).
Rationale, in the order the reasons fell: privacy is synthetic-by-construction
(iron rule #2), so the only privacy event is a one-time history boundary — this
repo's history starts at the public cut; holdout secrecy is replaced by
structural defenses (seeded fixture regeneration at release time, frozen anchor
sub-suite outside PR CI, case rotation); and the engineering machinery is
product runtime, because Belay self-extends (users request new flows; the meta
plane builds them WITH their evals).

**Consequences:**
- All five factory personas join the public suite (p03–p07), each with a Harbor
  task and a verifier fixture (`corrupt.py`). Persona-bot/judge material lives
  on as rubric sources (`evals/lib/rubrics/`).
- Three activation planes, mechanically separated: domain flows trigger on user
  intent; guardrails are WIRED into flow steps (never description-triggered);
  meta capabilities run on explicit invocation or schedule only. Plane isolation
  is itself eval-tested (`evals/trigger-isolation/`).
- Releases are git tags: the release workflow runs the frozen anchor + a
  fresh-seed regeneration gate + the sanitization scan, then packages
  `dist/harness.zip` (`tools/package_release.py`, ex-factory, `--export` removed).
- Instances are private template copies (NEVER GitHub forks — they cannot be
  made private). Reinstalling upgrades harness-owned paths only (D11 install
  contract = the two-namespace rule). Contributions from instances pass an
  anonymization gate at the PR edge.
- Iron rules D1–D15 carry over unchanged except D14's split, which this
  decision supersedes. Iron rule #1 ("no skill without evaluation") now also
  binds RUNTIME self-extension: a flow built by `/extend` ships with its evals.
- The factory repo (`adhd-personal-finance-harness`) is archived as the
  pre-consolidation history; its `evals/runs/` archive stays there. The
  `2026-07-09-private-data-simulation` run summary is NOT migrated pending
  owner review (open item).

## D17 — Terminal surfaces: rhythm is ambient, numbers are pulled

**Date:** 2026-10-16 · **Decision record:** harness-engineering store, `docs/43` (presentation surfaces)

Belay gets a visual terminal layer in two tiers, and neither does math:
`harness/scripts/status.py` is the one view-model every display reads (the
numbers come from reconcile.py's report and the budget, compared in Decimal).

- **Stable tier** (`harness/settings.json`, merged add-only by `install.py`):
  status line, climbing spinner verbs, tips. Works in every Claude Code once
  the folder is trusted; a key the user already set is never overwritten.
- **Mod tier** (`harness/skills/belay-ui/`, a Claude Code mod): the rhythm band
  above the prompt, the `/belay` month view (meters; an SVG in the desktop
  app), a quiet receipt after the scripts run, and a markdown fallback where no
  pane can be drawn. Mods are early access behind a remote switch: optional
  equipment, never the rope.
- **Ambient vs pull.** The always-visible surfaces (band, status line) carry
  rhythm and the next small step, never an amount: the envelope experiment is
  designed with no mid-month alerts, and a live meter would feed the checking
  loop it exists to stop. Figures live on pull surfaces (`/belay`, the HTML
  report). After a break, the ambient surfaces say "good to see you" and
  nothing that counts or lists (welcome-back iron rules).
- **Meter semantics carry over from D13/D2a**: warm only for an envelope over
  its plan; an awareness category past its reference keeps the calm colour.
- Covered by `evals/rhythm-status-display` (deterministic + fixture rule) and
  the mod's own `claude plugin test` suite.
