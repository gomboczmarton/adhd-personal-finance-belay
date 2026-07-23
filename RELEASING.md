# Releasing (maintainer note)

Since D16 (2026-07-23, consolidation) this repo is the single source: there is
no factory export step. **Tags are releases** — the release workflow does the
rest.

1. Bump `VERSION` on `main` (PR like any change; PR CI must be green).
2. Create the tag `v<version>` (GitHub "Draft a new release" with a new tag
   works and creates the tag on publish — handy because the session git proxy
   rejects tag pushes; see note below).
3. `.github/workflows/release.yml` then runs, in order:
   - baseline fixtures + the FULL deterministic suite (frozen anchor included);
   - the **fresh-seed regeneration gate** (`tools/fresh_seed_gate.py`) — the
     whole suite must stay green on brand-new ground truth;
   - the **sanitization scan + packaging** (`tools/package_release.py`) — any
     forbidden pattern aborts the release;
   - publishes the GitHub release with `dist/harness.zip` (stable asset name —
     `install.py --from-release` depends on it) and `dist/harness-v<version>.zip`.
4. If the workflow goes red, fix on `main` and re-tag; never publish assets by
   hand around a red gate.

Manual pre-flight (optional but recommended, mirrors the workflow):

```bash
uv run harness/scripts/generate_fixtures.py --all evals/personas evals/fixtures
python3 evals/run_local.py --fixtures          # full suite incl. anchor
python3 tools/fresh_seed_gate.py               # fresh-seed check
uv run tools/package_release.py                # sanitize + package locally
```

The committed `dist/` zips are the historical v0.1.0 assets (pre-D16 flow);
from v0.2.0 on, assets are built by the workflow at tag time and the committed
copies are no longer inputs to anything.

Note (2026-07-10, still true): automated sessions can't push tag refs through
the git proxy — branch pushes work. Creating the tag via "Draft a new release"
is one click and triggers the workflow on publish.
