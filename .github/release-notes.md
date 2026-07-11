First public cut of **Belay** — a shame-free personal-finance companion for ADHD brains, built as a Claude Code harness. *You climb. It holds the rope.*

**Install** (Python 3.11+, uv, Claude Code):

```bash
uv run install.py /path/to/your-finance-repo --from-release
```

or clone this repo and run `uv run install.py <target>`.

**Contents:** 5 skills (onboarding, monthly-prep, reconcile-month, purchase-check, welcome-back), the finance-coach agent, the deterministic script core (10 scripts, Decimal-exact), 8 JSON schemas. Bank presets: Revolut/Wise/N26/Monzo CSV, OTP netbank XLSX, generic EU/HU shapes.

Licensed under MIT.
