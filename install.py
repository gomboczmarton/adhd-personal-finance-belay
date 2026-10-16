#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Install the ADHD Personal Finance Harness into a finance repository (D11).

Usage:
    uv run install.py <target-repo-dir>                    # from this checkout
    uv run install.py <target-repo-dir> --from-release     # fetch latest release
    uv run install.py <target-repo-dir> --from-zip <path>  # from a packaged zip

Copies into <target>:
    .claude/skills/<skill>/   from harness/skills/   (conversational layer; also
                              belay-ui, the terminal mod, which loads once
                              the folder is trusted)
    .claude/agents/<agent>.md from harness/agents/   (subagents)
    .claude/settings.json     keys of harness/settings.json (status line,
                              spinner verbs, tips), ADDED only where absent:
                              a key the user already set is never overwritten
    harness/scripts/*.py      the deterministic core (harness-owned, overwritten
    harness/schemas/*.json    on reinstall/upgrade)
    finance/inbox/            drop zone for bank exports (created empty)

--from-release downloads the `harness.zip` asset from the latest GitHub release
of the product repo (default gomboczmarton/adhd-personal-finance-belay; override
with --repo owner/name). --from-zip installs from a local packaged zip instead.

Never touches finance/ state beyond creating inbox/. Reinstalling upgrades the
harness-owned files and leaves user data alone. After installing: open the repo
in Claude Code and run /onboarding.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

SRC = Path(__file__).resolve().parent
DEFAULT_REPO = "gomboczmarton/adhd-personal-finance-belay"
ASSET = "harness.zip"


def source_from_zip(zip_path: Path, workdir: Path) -> Path:
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.startswith("/") or ".." in Path(name).parts:
                sys.exit(f"error: unsafe path in zip: {name}")
        zf.extractall(workdir)
    candidates = [workdir] + [p for p in workdir.iterdir() if p.is_dir()]
    for c in candidates:
        if (c / "harness" / "scripts").is_dir():
            return c
    sys.exit(f"error: {zip_path} does not contain a harness/ tree")


def merge_settings(fragment: Path, dest: Path) -> list[str]:
    """Add the display layer's settings keys the user has not set.

    Add-only: an existing key (the user's own status line, say) wins and
    nothing else in their settings is touched. Returns the keys added.
    """
    if not fragment.is_file():
        return []
    ours = json.loads(fragment.read_text(encoding="utf-8"))
    theirs = json.loads(dest.read_text(encoding="utf-8")) if dest.is_file() else {}
    added = [k for k in ours if k not in theirs]
    if added:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps({**theirs, **{k: ours[k] for k in added}},
                                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return added


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print(__doc__, file=sys.stderr)
        return 2
    target = Path(args[0]).resolve()
    src = SRC
    tmp: tempfile.TemporaryDirectory | None = None

    if "--from-zip" in args or "--from-release" in args:
        tmp = tempfile.TemporaryDirectory(prefix="harness-install-")
        workdir = Path(tmp.name)
        if "--from-zip" in args:
            zip_path = Path(args[args.index("--from-zip") + 1]).resolve()
        else:
            repo = args[args.index("--repo") + 1] if "--repo" in args else DEFAULT_REPO
            url = f"https://github.com/{repo}/releases/latest/download/{ASSET}"
            zip_path = workdir / ASSET
            print(f"fetching {url}", file=sys.stderr)
            urllib.request.urlretrieve(url, zip_path)  # noqa: S310 — fixed https URL
        src = source_from_zip(zip_path, workdir / "src")

    if target == src or target == SRC:
        sys.exit("error: install into your own finance repo, not the harness repo")
    target.mkdir(parents=True, exist_ok=True)

    installed: dict[str, list[str]] = {"skills": [], "agents": [], "scripts": [], "schemas": []}

    for skill_dir in sorted((src / "harness" / "skills").iterdir()):
        if not skill_dir.is_dir():
            continue
        dest = target / ".claude" / "skills" / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        installed["skills"].append(skill_dir.name)

    agents_src = src / "harness" / "agents"
    if agents_src.is_dir():
        (target / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
        for agent in sorted(agents_src.glob("*.md")):
            shutil.copy2(agent, target / ".claude" / "agents" / agent.name)
            installed["agents"].append(agent.stem)

    for sub, key in (("scripts", "scripts"), ("schemas", "schemas")):
        dest = target / "harness" / sub
        dest.mkdir(parents=True, exist_ok=True)
        for f in sorted((src / "harness" / sub).iterdir()):
            if f.is_file():
                shutil.copy2(f, dest / f.name)
                installed[key].append(f.name)

    installed["settings"] = merge_settings(src / "harness" / "settings.json",
                                           target / ".claude" / "settings.json")

    (target / "finance" / "inbox").mkdir(parents=True, exist_ok=True)

    print(json.dumps({"target": str(target), "installed": installed}, indent=2))
    print("\nNext: open the repo in Claude Code and run /onboarding", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
