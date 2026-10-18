#!/usr/bin/env python3
"""Install the game and inline animated preview into a local najla23/najla23 clone.

Usage: python3 /path/to/unpacked/package/install_ion_game.py /path/to/najla23
This edits local files only. It does not commit, push, or change Pages settings.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
from html import escape
from html.parser import HTMLParser
import re
import shutil
import subprocess

START = "<!-- NH_ION_GAME_START -->"
END = "<!-- NH_ION_GAME_END -->"


def preserve_play_alert(current, replacement):
    """Keep a previously configured recipient when the update has none."""
    class Endpoint(HTMLParser):
        value = ""
        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            if tag == "meta" and values.get("name") == "nh-play-alert-endpoint":
                self.value = values.get("content", "")
    old, new = Endpoint(), Endpoint()
    old.feed(current)
    new.feed(replacement)
    if old.value and not new.value:
        replacement = re.sub(
            r'<meta name="nh-play-alert-endpoint" content="">',
            lambda _: '<meta name="nh-play-alert-endpoint" content="'
            + escape(old.value, quote=True) + '">',
            replacement, count=1,
        )
    return replacement


def updated_readme(current, block):
    if START in current or END in current:
        if current.count(START) != 1 or current.count(END) != 1:
            raise ValueError("README has inconsistent game markers; no files changed.")
        start, end = current.index(START), current.index(END) + len(END)
        if start >= end:
            raise ValueError("README game markers are reversed; no files changed.")
        return current[:start] + block + current[end:]
    # Only the new generated section is added. Existing writing is preserved.
    return block + "\n\n" + current


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, stderr=subprocess.PIPE
    ).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", nargs="?", default=".")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    try:
        root = Path(git(Path(args.repository).resolve(), "rev-parse", "--show-toplevel"))
        origin = git(root, "remote", "get-url", "origin").rstrip("/")
    except subprocess.CalledProcessError:
        raise SystemExit("Run this inside your local najla23/najla23 Git clone.")
    clean = origin.removesuffix(".git")
    if not clean.endswith(("/najla23/najla23", ":najla23/najla23")):
        raise SystemExit("This installer is for najla23/najla23; origin does not match.")
    if git(root, "branch", "--show-current") != "main":
        raise SystemExit("Switch this clone to main first: git switch main")
    block = (source / "README_GAME.md").read_text(encoding="utf-8").strip()
    readme = root / "README.md"
    current = readme.read_text(encoding="utf-8") if readme.exists() else ""
    new_readme = updated_readme(current, block)
    copies = {
        "docs/index.html": source / "docs/index.html",
        "nh/ion-rescue.gif": source / "nh/ion-rescue.gif",
    }
    for path in copies.values():
        if not path.is_file():
            raise SystemExit("Extract the whole package first; missing " + str(path.name))
    old_html = root / "docs/index.html"
    new_html = preserve_play_alert(
        old_html.read_text(encoding="utf-8") if old_html.exists() else "",
        copies["docs/index.html"].read_text(encoding="utf-8"),
    )
    backup_base = Path(git(root, "rev-parse", "--git-path", "nh-game-backups"))
    if not backup_base.is_absolute():
        backup_base = root / backup_base
    backup = backup_base / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    for relative in ["README.md", *copies]:
        path = root / relative
        if path.exists():
            destination = backup / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    for relative, path in copies.items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if relative == "docs/index.html":
            destination.write_text(new_html, encoding="utf-8")
        elif destination.resolve() != path.resolve():
            shutil.copy2(path, destination)
    (root / "docs/.nojekyll").touch(exist_ok=True)
    readme.write_text(new_readme, encoding="utf-8")
    print("Installed Ion Rescue, its animated preview, and the README section.")
    print("Existing files were backed up inside .git/nh-game-backups.")
    print("Review and publish:")
    print("git diff --stat")
    print("git add README.md docs/index.html docs/.nojekyll nh/ion-rescue.gif")
    print('git commit -m "Add five Ion Rescue worlds and selectable hydrated ions"')
    print("git push origin main")


if __name__ == "__main__":
    main()
