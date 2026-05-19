#!/usr/bin/env python3
"""Migrate archive directories from flat YYYY-MM-DD to nested YYYY/MM/DD.

Usage (dry-run, default):
    python3 scripts/migrate_nested_dirs.py --local /path/to/archived

Usage (execute):
    python3 scripts/migrate_nested_dirs.py --local /path/to/archived --execute

This script handles:
1. Directories named YYYY-MM-DD → move to YYYY/MM/DD
2. Loose files named *-YYYY-MM-DD.md → extract date and move into nested path
"""
import argparse
import re
import shutil
import sys
from pathlib import Path


DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOOSE_FILE_RE = re.compile(r"-(\d{4}-\d{2}-\d{2})\.md$")


def migrate_flat_dirs(base_dir: Path, dry_run: bool = True) -> list[dict]:
    """Move YYYY-MM-DD directories to YYYY/MM/DD."""
    results = []
    for item in sorted(base_dir.iterdir()):
        if not item.is_dir():
            continue
        if not DATE_DIR_RE.match(item.name):
            continue

        parts = item.name.split("-")
        nested = base_dir / parts[0] / parts[1] / parts[2]

        action = {
            "type": "dir",
            "from": str(item),
            "to": str(nested),
            "files": len(list(item.iterdir())),
        }

        if dry_run:
            action["status"] = "dry_run"
        else:
            nested.mkdir(parents=True, exist_ok=True)
            # Move each file individually (target dir may already exist)
            for f in item.iterdir():
                dest = nested / f.name
                if dest.exists():
                    action["status"] = "conflict"
                    action.setdefault("conflicts", []).append(f.name)
                else:
                    shutil.move(str(f), str(dest))
            if "status" not in action:
                action["status"] = "ok"
            # Remove empty source dir
            try:
                item.rmdir()  # only works if empty
            except OSError:
                pass

        results.append(action)
    return results


def migrate_loose_files(base_dir: Path, dry_run: bool = True) -> list[dict]:
    """Move loose *-YYYY-MM-DD.md files into nested date directories."""
    results = []
    for item in sorted(base_dir.iterdir()):
        if not item.is_file() or not item.name.endswith(".md"):
            continue
        m = LOOSE_FILE_RE.search(item.name)
        if not m:
            continue

        date_str = m.group(1)
        parts = date_str.split("-")
        nested = base_dir / parts[0] / parts[1] / parts[2]

        action = {
            "type": "file",
            "from": str(item),
            "to": str(nested / item.name),
        }

        if dry_run:
            action["status"] = "dry_run"
        else:
            nested.mkdir(parents=True, exist_ok=True)
            dest = nested / item.name
            if dest.exists():
                action["status"] = "conflict"
            else:
                shutil.move(str(item), str(dest))
                action["status"] = "ok"

        results.append(action)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate flat date dirs to nested YYYY/MM/DD")
    parser.add_argument("--local", required=True, help="Local archive_dir path")
    parser.add_argument("--execute", action="store_true", help="Actually move files (default: dry-run)")
    args = parser.parse_args()

    mode = "EXECUTE" if args.execute else "DRY RUN"
    base = Path(args.local).expanduser()

    if not base.exists():
        print(f"Directory not found: {base}")
        return 1

    print(f"\n{'='*60}")
    print(f"[local] {mode}: {base}")
    print(f"{'='*60}")

    # 1. Migrate flat date directories
    dir_results = migrate_flat_dirs(base, dry_run=not args.execute)
    print(f"\nDate directories: {len(dir_results)}")
    for r in dir_results:
        flag = "✓" if r["status"] == "ok" else ("!" if r["status"] == "conflict" else "→")
        print(f"  {flag} {r['status']:8s} | {Path(r['from']).name} → {Path(r['to']).relative_to(base)} ({r.get('files', '?')} files)")

    # 2. Migrate loose files
    file_results = migrate_loose_files(base, dry_run=not args.execute)
    print(f"\nLoose files: {len(file_results)}")
    for r in file_results:
        flag = "✓" if r["status"] == "ok" else ("!" if r["status"] == "conflict" else "→")
        print(f"  {flag} {r['status']:8s} | {Path(r['from']).name} → {Path(r['to']).relative_to(base)}")

    if not args.execute:
        print(f"\n⚠️  DRY RUN — no files were moved. Add --execute to apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
