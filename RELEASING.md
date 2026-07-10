# Releasing (maintainer note)

1. In the factory repo: bump `VERSION`, run the suite (0 FAIL), then
   `uv run package_release.py --export <this-checkout>` — the sanitization gate
   must pass; it refuses to package on any hit.
2. Commit the exported tree + `dist/` zips here; tag `v<version>`; push with tags.
3. On GitHub: Releases → "Draft a new release" → choose the tag → attach
   `dist/harness.zip` (stable asset name — `install.py --from-release` depends on
   it) and `dist/harness-v<version>.zip` → publish.

Note (2026-07-10): the automated session couldn't push tags through the git proxy
(branch pushes work; tag refs are rejected). Creating the tag is one click anyway:
in "Draft a new release", type `v0.1.0` as the tag targeting this branch's merge
commit and GitHub creates it on publish.
