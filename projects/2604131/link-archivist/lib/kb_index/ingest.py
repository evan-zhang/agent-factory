#!/usr/bin/env python3
"""
Ingest layer: directory scanning and change detection.

This module scans directories and identifies files needing indexing.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Set


def load_cache(root: Path) -> Dict[str, Any]:
    """Load SHA256 cache from .kb-workdir/kb_cache.json."""
    cache_path = Path(root) / ".kb-workdir" / "kb_cache.json"
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def load_entries(root: Path) -> Dict[str, Any]:
    """Load entries from .kb-workdir/entries.json."""
    entries_path = Path(root) / ".kb-workdir" / "entries.json"
    if not entries_path.exists():
        return {}
    try:
        return json.loads(entries_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def scan_markdown_files(archive_dir: Path) -> List[Path]:
    """Scan directory for Markdown files.

    Args:
        archive_dir: Archive root directory

    Returns:
        List of Markdown file paths
    """
    if not archive_dir.exists():
        return []

    # Files at root level that are system-generated, not archives
    SYSTEM_FILES = {"index.md", "log.md"}

    md_files = []
    for md in archive_dir.rglob("*.md"):
        # Skip .kb-workdir, hidden files, and system docs
        rel = md.relative_to(archive_dir)
        if ".kb-workdir" in str(md):
            continue
        if md.name.startswith("."):
            continue
        # Skip root-level system files (index.md, log.md)
        if len(rel.parts) == 1 and md.name in SYSTEM_FILES:
            continue
        md_files.append(md)

    return md_files


def detect_changes(archive_dir: Path) -> Dict[str, Any]:
    """Detect files that need indexing.

    Args:
        archive_dir: Archive root directory

    Returns:
        Change detection result with new, modified, deleted files
    """
    cache = load_cache(archive_dir)
    entries = load_entries(archive_dir)

    # Scan current files
    current_files = scan_markdown_files(archive_dir)

    # Calculate SHA256 for current files
    from .parse_frontmatter import sha256
    current_hashes = {}
    for md in current_files:
        try:
            current_hashes[str(md)] = sha256(md)
        except (OSError, IOError):
            pass

    # Detect new and modified files
    indexed_paths = set(entries.keys())
    current_paths = set(str(md.relative_to(archive_dir)) for md in current_files)

    new_files = []
    modified_files = []
    unchanged_files = []
    deleted_files = []

    for md in current_files:
        rel_path = str(md.relative_to(archive_dir))
        current_hash = current_hashes.get(str(md), "")

        if rel_path not in indexed_paths:
            # New file
            new_files.append(rel_path)
        else:
            # Check if modified
            old_entry = entries.get(rel_path, {})
            old_hash = old_entry.get("source_sha256", "")

            if old_hash != current_hash:
                modified_files.append(rel_path)
            else:
                unchanged_files.append(rel_path)

    # Detect deleted files
    for indexed_path in indexed_paths:
        if indexed_path not in current_paths:
            deleted_files.append(indexed_path)

    return {
        "ok": True,
        "new_files": new_files,
        "modified_files": modified_files,
        "unchanged_files": unchanged_files,
        "deleted_files": deleted_files,
        "stats": {
            "total_current": len(current_files),
            "total_indexed": len(indexed_paths),
            "new_count": len(new_files),
            "modified_count": len(modified_files),
            "deleted_count": len(deleted_files),
        }
    }


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="KB Index ingest")
    parser.add_argument("--dir", required=True, help="Archive directory")
    args = parser.parse_args()

    try:
        result = detect_changes(Path(args.dir))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
