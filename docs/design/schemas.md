# Workspace Schemas (Step 1) — Spec

Data architecture per **D8** (Notebook state + transaction Ledger). The machine-readable
truth is in `harness/schemas/*.schema.json` (JSON Schema 2020-12); this page is the
human map. Validator: `uv run harness/scripts/validate_workspace.py <workspace>` —
checks frontmatter against schemas, every ledger line, and cross-file references the
schemas can't express. Reference instance: `examples/alex-workspace/finance/` (synthetic
persona, no real data).

## File inventory — one owner per fact

| File | Owner / editor | Machine part | Content |
|---|---|---|---|
| `strategy.md` | user + agent (dialogue) | frontmatter | mode (awareness/envelopes/hybrid), per-category envelope adoption, next review, language |
| `accounts.md` | wizard at onboarding | frontmatter | accounts, cards, envelopes, per-account ingestion mapping (D3) |
| `knowledge/categories.md` | agent, user confirms | frontmatter | canonical English keys + display names in user language (D6), need/want/goal lens |
| `knowledge/yearly-bank.md` | agent, user confirms | frontmatter | annual/quarterly items with due months and typical amounts |
| `knowledge/merchant-map.md` | agent learns, user confirms | frontmatter | description patterns → merchant, category, kind (incl. internal_transfer) |
| `months/YYYY-MM/budget.md` | planning dialogue | frontmatter | income, envelope allocations and/or awareness targets, overlay items (yearly-bank hits land here highlighted), savings target |
| `ledger/events.jsonl` | scripts ONLY, append-only | every line | money facts: txn.imported / txn.categorized / txn.matched / strategy.adopted / decision.logged |
| `months/YYYY-MM/reports/*` | generated ONLY | — | reconciliation, snapshots, XLSX (D5 write-only) |

Markdown bodies below the frontmatter are free-form — the user's story, agent
explanations. Never parsed, never load-bearing.

## Design points

- **Transaction identity** = 16-hex content hash (account + date + amount + description)
  → overlapping re-imports dedup naturally; `txn.matched` pairs internal-transfer legs so
  envelope refills are never counted as income/expense (blindspot #2).
- **Journey (D2a)** lives twice, consistently: `strategy.md` frontmatter is the *current*
  state; `strategy.adopted` events are the *history*. Mode `hybrid` + `envelope_adoption`
  entries = gradual adoption in progress.
- **Ledger is append-only**: corrections are compensating events, never edits.
- **Arithmetic invariants** (allocations vs income, reconciliation balance) are enforced
  by scripts at Step 3/4 — deliberately NOT in the schemas.
- **schema_version: 1** pinned as a const in every schema; a version bump ships with a
  migration script.

## Validator guarantees (tested)

Positive: the Alex workspace validates clean. Negative (all caught in test): missing
frontmatter, unknown transaction hash, unknown category key in events, budget
month ≠ folder name, unknown envelope id in allocations, duplicate import hashes,
malformed YAML/JSON, schema violations with path-precise messages.
