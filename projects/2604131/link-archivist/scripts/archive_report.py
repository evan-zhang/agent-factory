#!/usr/bin/env python3
"""Archive report with auto-numbering and optional Obsidian sync."""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


def get_next_number(archive_dir: Path, date_str: str) -> int:
    """Scan existing files and return next sequence number."""
    date_dir = archive_dir / date_str
    if not date_dir.exists():
        return 1
    max_num = 0
    for f in date_dir.glob("K-*.md"):
        try:
            # K-YYMMDD-NNN-*.md
            parts = f.stem.split("-")
            if len(parts) >= 3:
                num = int(parts[2])
                max_num = max(max_num, num)
        except (ValueError, IndexError):
            continue
    return max_num + 1


def get_next_obsidian_number(obsidian_dir: Path, date_str: str) -> int:
    """Scan existing Obsidian files and return next sequence number."""
    date_dir = obsidian_dir / date_str
    if not date_dir.exists():
        return 1
    max_num = 0
    for f in date_dir.glob("*-{}.md".format(date_str)):
        try:
            # {title}-YYYY-MM-DD.md - extract sequence from name
            parts = f.stem.split("-")
            for p in parts[:-1]:  # skip the date part
                if p.isdigit() and len(p) == 6:  # YYMMDD
                    seq = int(f.stem.split("-")[-2]) if len(f.stem.split("-")) > 1 else 0
                    max_num = max(max_num, seq)
        except (ValueError, IndexError):
            continue
    return max_num + 1


def parse_args():
    """Parse both positional and named arguments."""
    import argparse
    parser = argparse.ArgumentParser(description='Archive report with auto-numbering')
    parser.add_argument('content_file', nargs='?', help='Markdown report file path')
    parser.add_argument('archive_dir', nargs='?', help='Archive directory (optional, reads from config)')
    parser.add_argument('title', nargs='?', default='report', help='Report title for filename')
    parser.add_argument('--file', '-f', dest='file_arg', help='Markdown report file path (named)')
    parser.add_argument('--dir', '-d', dest='dir_arg', help='Archive directory (named)')
    parser.add_argument('--title', '-t', dest='title_arg', help='Report title (named)')
    parser.add_argument('--obsidian', '-o', dest='obsidian_dir', help='Obsidian sync directory')
    parser.add_argument('--no-obsidian', action='store_true', help='Skip Obsidian sync')
    args = parser.parse_args()

    content_file = args.file_arg or args.content_file
    archive_dir = args.dir_arg or args.archive_dir
    title = args.title_arg or args.title or 'report'
    obsidian_dir = args.obsidian_dir
    skip_obsidian = args.no_obsidian

    return content_file, archive_dir, title, obsidian_dir, skip_obsidian


def load_config():
    """Load config from standard paths."""
    config_file = Path.home() / ".config" / "link-archivist-config.json"
    alt_paths = [
        Path.home() / ".openclaw" / "link-archivist-config.json",
        Path.home() / ".hermes" / "link-archivist-config.json",
    ]
    for p in alt_paths:
        if p.exists():
            config_file = p
            break

    if config_file.exists():
        try:
            return json.loads(config_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def sync_to_obsidian(content_file: Path, obsidian_dir: Path, title: str, date_str: str) -> dict:
    """Sync report to Obsidian directory.
    
    Obsidian structure: {obsidian_dir}/YYYY-MM-DD/{title}-YYYY-MM-DD.md
    """
    if not obsidian_dir:
        return {"ok": False, "reason": "no obsidian_dir configured"}

    obsidian_dir = Path(obsidian_dir).expanduser()
    if not obsidian_dir.exists():
        return {"ok": False, "reason": f"obsidian dir not found: {obsidian_dir}"}

    date_path = obsidian_dir / date_str
    date_path.mkdir(parents=True, exist_ok=True)

    safe_title = title.replace(" ", "-").replace("/", "-")[:50]
    obsidian_file = date_path / f"{safe_title}-{date_str}.md"

    # Avoid overwriting - add sequence if file exists
    counter = 1
    original_path = obsidian_file
    while obsidian_file.exists():
        obsidian_file = date_path / f"{safe_title}-{date_str}-{counter}.md"
        counter += 1

    shutil.copy2(content_file, obsidian_file)
    return {"ok": True, "file": str(obsidian_file)}


def main() -> int:
    content_file_str, archive_dir_str, title, obsidian_dir_arg, skip_obsidian = parse_args()

    if not content_file_str:
        print(json.dumps({
            "ok": False,
            "error": "usage: archive_report.py <content_file> <archive_dir> [title]\n"
                      "       or: archive_report.py --file <file> [--dir <dir>] [--title <title>] [--obsidian <path>] [--no-obsidian]"
        }, ensure_ascii=False))
        return 1

    content_file = Path(content_file_str).expanduser()
    archive_dir = Path(archive_dir_str).expanduser() if archive_dir_str else Path(".")
    obsidian_dir = obsidian_dir_arg

    if not content_file.exists():
        print(json.dumps({"ok": False, "error": f"missing file: {content_file}"}, ensure_ascii=False))
        return 1

    # Load config
    config = load_config()
    if config:
        if not archive_dir_str:
            archive_dir = Path(config.get("archive_dir", archive_dir)).expanduser()
        if not obsidian_dir:
            obsidian_dir = config.get("obsidian_dir")

    # Resolve date strings
    today_display = datetime.now().strftime("%Y-%m-%d")  # YYYY-MM-DD for paths
    today_code = datetime.now().strftime("%y%m%d")       # YYMMDD for archive ID

    # --- Archive to local ---
    seq = get_next_number(archive_dir, today_display)
    archive_id = f"K-{today_code}-{seq:03d}"
    date_dir = archive_dir / today_display
    date_dir.mkdir(parents=True, exist_ok=True)

    content = content_file.read_text(encoding="utf-8")

    # Add YAML header if not present
    if not content.startswith("---"):
        header = f"""---
archive: {archive_id}
source: unknown
created_at: {datetime.now().isoformat()}
tags: []
---
"""
        content = header + content

    safe_title = title.replace(" ", "-").replace("/", "-")[:50]
    archive_file = date_dir / f"{archive_id}-{safe_title}.md"
    archive_file.write_text(content, encoding="utf-8")

    # --- Sync to Obsidian ---
    obsidian_result = {"ok": False}
    if not skip_obsidian and obsidian_dir:
        obsidian_result = sync_to_obsidian(archive_file, Path(obsidian_dir), safe_title, today_display)

    print(json.dumps({
        "ok": True,
        "archive_id": archive_id,
        "archive_file": str(archive_file),
        "seq": seq,
        "obsidian": obsidian_result
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
