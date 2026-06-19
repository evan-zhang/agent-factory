#!/usr/bin/env python3
"""
KB Query - Knowledge base query interface for Link Archivist.

This script provides query capabilities over archived knowledge.
Default mode: keyword (no external dependencies).
"""
import json
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from kb_index.query_engine import query


def load_config():
    """Load archive_dir from config."""
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


def main():
    import argparse

    parser = argparse.ArgumentParser(description="KB Query - Link Archivist")
    parser.add_argument("query", nargs="?", help="Query string")
    parser.add_argument("--dir", help="Archive directory (overrides config)")
    parser.add_argument(
        "--mode",
        default="keyword",
        choices=["keyword", "semantic", "hybrid"],
        help="Query mode (default: keyword)"
    )
    args = parser.parse_args()

    # Handle special "status" command
    if args.query == "status":
        config = load_config()
        archive_dir = Path(args.dir) if args.dir else Path(config.get("archive_dir", "."))

        if not archive_dir.exists():
            print(json.dumps({
                "ok": False,
                "error": f"Archive directory not found: {archive_dir}"
            }, ensure_ascii=False))
            return 1

        # Load and show stats
        entries_path = archive_dir / ".kb-workdir" / "entries.json"
        if entries_path.exists():
            entries = json.loads(entries_path.read_text(encoding="utf-8"))
            print(json.dumps({
                "ok": True,
                "status": "ready",
                "archive_dir": str(archive_dir),
                "total_entries": len(entries),
                "workdir": str(archive_dir / ".kb-workdir"),
            }, indent=2, ensure_ascii=False))
        else:
            print(json.dumps({
                "ok": True,
                "status": "no_index",
                "archive_dir": str(archive_dir),
                "message": "No index found. Run kb_rebuild.py to create index.",
            }, indent=2, ensure_ascii=False))
        return 0

    if not args.query:
        parser.print_help()
        return 1

    # Determine archive directory
    config = load_config()
    archive_dir = Path(args.dir) if args.dir else Path(config.get("archive_dir", "."))

    if not archive_dir.exists():
        print(json.dumps({
            "ok": False,
            "error": f"Archive directory not found: {archive_dir}"
        }, ensure_ascii=False))
        return 1

    # Execute query
    try:
        result = query(args.query, archive_dir, args.mode)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": str(e)
        }, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
