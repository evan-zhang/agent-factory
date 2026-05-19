#!/usr/bin/env python3
"""Archive report with auto-numbering. Single responsibility: write to archive_dir only."""
import json
from datetime import datetime
from pathlib import Path


def _date_to_nested_path(base_dir: Path, date_str: str) -> Path:
    """Convert YYYY-MM-DD to YYYY/MM nested path."""
    parts = date_str.split("-")  # [YYYY, MM, DD]
    return base_dir / parts[0] / parts[1]


def get_next_number(archive_dir: Path, date_str: str) -> int:
    """Scan existing files and return next sequence number."""
    date_dir = _date_to_nested_path(archive_dir, date_str)
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


def parse_args():
    """Parse command-line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description='Archive report with auto-numbering')
    parser.add_argument('content_file', nargs='?', help='Markdown report file path')
    parser.add_argument('archive_dir', nargs='?', help='Archive directory (optional, reads from config)')
    parser.add_argument('title', nargs='?', default='report', help='Report title for filename')
    parser.add_argument('--file', '-f', dest='file_arg', help='Markdown report file path (named)')
    parser.add_argument('--dir', '-d', dest='dir_arg', help='Archive directory (named)')
    parser.add_argument('--title', '-t', dest='title_arg', help='Report title (named)')
    args = parser.parse_args()

    content_file = args.file_arg or args.content_file
    archive_dir = args.dir_arg or args.archive_dir
    title = args.title_arg or args.title or 'report'

    return content_file, archive_dir, title


def load_config():
    """Load config from standard paths."""
    for config_file in [
        Path.home() / ".openclaw" / "link-archivist-config.json",
        Path.home() / ".hermes" / "link-archivist-config.json",
        Path.home() / ".config" / "link-archivist-config.json",
    ]:
        if config_file.exists():
            try:
                return json.loads(config_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
    return {}


def main() -> int:
    content_file_str, archive_dir_str, title = parse_args()

    if not content_file_str:
        print(json.dumps({
            "ok": False,
            "error": "usage: archive_report.py <content_file> <archive_dir> [title]\n"
                     "       or: archive_report.py --file <file> [--dir <dir>] [--title <title>]"
        }, ensure_ascii=False))
        return 1

    content_file = Path(content_file_str).expanduser()
    archive_dir = Path(archive_dir_str).expanduser() if archive_dir_str else Path(".")

    if not content_file.exists():
        print(json.dumps({"ok": False, "error": f"missing file: {content_file}"}, ensure_ascii=False))
        return 1

    # Load config
    config = load_config()
    if config:
        if not archive_dir_str:
            archive_dir = Path(config.get("archive_dir", archive_dir)).expanduser()

    # Resolve date strings
    today_display = datetime.now().strftime("%Y-%m-%d")  # YYYY-MM-DD for paths
    today_code = datetime.now().strftime("%y%m%d")       # YYMMDD for archive ID

    # --- Archive to local ---
    seq = get_next_number(archive_dir, today_display)
    archive_id = f"K-{today_code}-{seq:03d}"
    date_dir = _date_to_nested_path(archive_dir, today_display)
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

    print(json.dumps({
        "ok": True,
        "archive_id": archive_id,
        "archive_file": str(archive_file),
        "seq": seq
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
