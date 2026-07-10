# Releasing (maintainer note)

1. In the factory repo: bump `VERSION`, run the suite (0 FAIL), then
   `uv run package_release.py --export <this-checkout>` — the sanitization gate
   must pass; it refuses to package on any hit.
2. Commit the exported tree + `dist/` zips here; tag `v<version>`; push with tags.
3. On GitHub: Releases → "Draft a new release" → choose the tag → attach
   `dist/harness.zip` (stable asset name — `install.py --from-release` depends on
   it) and `dist/harness-v<version>.zip` → publish.
