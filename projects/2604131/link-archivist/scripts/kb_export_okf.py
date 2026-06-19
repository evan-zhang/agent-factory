#!/usr/bin/env python3
"""
KB Export OKF - OKF-style knowledge bundle exporter for Link Archivist.

This script exports archived knowledge to an OKF-style bundle structure:
- index.md: Knowledge bundle navigation index
- log.md: Change log generated from build_stats + cache
- archive/: OKF-style concept documents (copies of original .md files)

Output location: .kb-workdir/okf-export/ (to avoid duplicate indexing)
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from kb_index.ingest import load_entries, load_cache


def load_build_stats(root: Path) -> Dict[str, Any]:
    """Load build stats from .kb-workdir/build_stats.json."""
    stats_path = Path(root) / ".kb-workdir" / "build_stats.json"
    if not stats_path.exists():
        return {}
    try:
        return json.loads(stats_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def calculate_tag_stats(entries: Dict[str, Any]) -> Dict[str, int]:
    """Calculate tag statistics from entries."""
    tag_counts: Dict[str, int] = {}
    for entry in entries.values():
        for tag in entry.get("tags", []):
            if isinstance(tag, dict):
                tag = tag.get("name", tag.get("value", str(tag)))
            elif not isinstance(tag, str):
                tag = str(tag)
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return tag_counts


def calculate_entity_stats(entries: Dict[str, Any]) -> Dict[str, int]:
    """Calculate entity statistics from entries."""
    entity_counts: Dict[str, int] = {}
    for entry in entries.values():
        for entity in entry.get("entities", []):
            if isinstance(entity, dict):
                entity = entity.get("name", entity.get("value", str(entity)))
            elif not isinstance(entity, str):
                entity = str(entity)
            entity_counts[entity] = entity_counts.get(entity, 0) + 1
    return entity_counts


def generate_index_md(
    entries: Dict[str, Any],
    export_dir: Path,
    build_stats: Dict[str, Any]
) -> bool:
    """Generate index.md with navigation structure.

    Args:
        entries: All entries from entries.json
        export_dir: Export directory path
        build_stats: Build statistics

    Returns:
        True if successful
    """
    timestamp = datetime.now().isoformat()
    total_concepts = len(entries)

    # Sort entries by created_at (most recent first)
    sorted_entries = sorted(
        entries.items(),
        key=lambda x: x[1].get("created_at", ""),
        reverse=True
    )

    # Calculate tag and entity stats
    tag_stats = calculate_tag_stats(entries)
    entity_stats = calculate_entity_stats(entries)

    # Generate recent updates (top 20)
    recent_updates = []
    for rel_path, entry in sorted_entries[:20]:
        created_at = entry.get("created_at", "")
        archive_id = entry.get("archive_id", rel_path)
        title = entry.get("title", rel_path)
        recent_updates.append(f"- {created_at} — {archive_id} — {title}")

    # Generate tags section
    tags_section = []
    sorted_tags = sorted(tag_stats.items(), key=lambda x: x[1], reverse=True)
    for tag, count in sorted_tags:
        tags_section.append(f"- **{tag}** ({count} concepts)")

    # Generate key entities section (top 20)
    entities_section = []
    sorted_entities = sorted(entity_stats.items(), key=lambda x: x[1], reverse=True)[:20]
    for entity, count in sorted_entities:
        entities_section.append(f"- **{entity}** ({count} concepts)")

    # Generate all concepts section
    all_concepts = []
    for rel_path, entry in sorted_entries:
        title = entry.get("title", rel_path)
        summary = entry.get("summary", "").strip()
        # Create relative path from index.md to archive file
        archive_rel_path = Path("archive") / rel_path
        all_concepts.append(f"- [{title}]({archive_rel_path}) — {summary}")

    # Build index.md content
    content = f"""# Knowledge Bundle Index

> Generated from Link Archivist v2.1.0 index
> Last updated: {timestamp}
> Total concepts: {total_concepts}

## Recent Updates

{chr(10).join(recent_updates)}

## Tags

{chr(10).join(tags_section)}

## Key Entities

{chr(10).join(entities_section)}

## All Concepts

{chr(10).join(all_concepts)}
"""

    try:
        index_path = export_dir / "index.md"
        index_path.write_text(content, encoding="utf-8")
        return True
    except OSError:
        return False


def generate_log_md(
    cache: Dict[str, Any],
    build_stats: Dict[str, Any],
    export_dir: Path
) -> bool:
    """Generate log.md with change history.

    Args:
        cache: KB cache with indexed_at timestamps
        build_stats: Build statistics
        export_dir: Export directory path

    Returns:
        True if successful
    """
    timestamp = datetime.now().isoformat()

    # Collect index updates from cache
    index_updates = []
    for rel_path, entry in cache.items():
        if entry.get("status") == "ok":
            indexed_at = entry.get("indexed_at", "")
            status = entry.get("status", "unknown")
            index_updates.append((indexed_at, rel_path, status))

    # Sort by indexed_at (most recent first)
    index_updates.sort(key=lambda x: x[0], reverse=True)

    # Take top 50
    recent_updates = []
    for indexed_at, rel_path, status in index_updates[:50]:
        recent_updates.append(f"- {indexed_at} — {rel_path} — {status}")

    # Build log.md content
    content = f"""# Knowledge Bundle Change Log

> Generated from `.kb-workdir/build_stats.json` and `kb_cache.json`
> Last updated: {timestamp}
> Note: Historical changes before indexed_at are not recoverable.

## Build Statistics

- Last build: {build_stats.get("last_build", "N/A")}
- Total entries: {build_stats.get("total_entries", 0)}
- Last entry: {build_stats.get("last_entry_path", "N/A")}

## Recent Index Updates

{chr(10).join(recent_updates) if recent_updates else "No index updates recorded yet."}
"""

    try:
        log_path = export_dir / "log.md"
        log_path.write_text(content, encoding="utf-8")
        return True
    except OSError:
        return False


def copy_archives(
    entries: Dict[str, Any],
    archive_dir: Path,
    export_archive_dir: Path
) -> int:
    """Copy archive files to export directory.

    Args:
        entries: All entries from entries.json
        archive_dir: Source archive directory
        export_archive_dir: Destination archive directory

    Returns:
        Number of successfully copied files
    """
    success_count = 0
    for rel_path in entries.keys():
        src_path = archive_dir / rel_path
        dst_path = export_archive_dir / rel_path

        if not src_path.exists():
            print(f"⚠️  Warning: Source file not found: {src_path}", file=sys.stderr)
            continue

        try:
            # Create parent directories
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file (not symlink - more portable)
            shutil.copy2(src_path, dst_path)
            success_count += 1
        except OSError as e:
            print(f"⚠️  Warning: Failed to copy {rel_path}: {e}", file=sys.stderr)

    return success_count


def export_okf(
    archive_dir: Path,
    output_dir: Path = None,
    force: bool = False
) -> Dict[str, Any]:
    """Export knowledge base to OKF-style bundle.

    Args:
        archive_dir: Archive root directory
        output_dir: Custom output directory (must be inside .kb-workdir)
        force: Force rebuild (delete existing export first)

    Returns:
        Result dict with stats
    """
    # Validate archive directory
    if not archive_dir.exists():
        return {
            "ok": False,
            "error": f"Archive directory not found: {archive_dir}"
        }

    # Set output directory
    if output_dir:
        export_dir = output_dir
    else:
        export_dir = archive_dir / ".kb-workdir" / "okf-export"

    # Verify export is inside .kb-workdir
    workdir = archive_dir / ".kb-workdir"
    try:
        export_dir.relative_to(workdir)
    except ValueError:
        return {
            "ok": False,
            "error": f"Output directory must be inside .kb-workdir: {export_dir}"
        }

    # Check for entries.json
    entries_path = workdir / "entries.json"
    if not entries_path.exists():
        return {
            "ok": False,
            "error": "entries.json not found. Run kb_rebuild.py first to create index.",
            "hint": f"Expected: {entries_path}"
        }

    # Load data
    entries = load_entries(archive_dir)
    cache = load_cache(archive_dir)
    build_stats = load_build_stats(archive_dir)

    if not entries:
        # Generate graceful empty index
        export_dir.mkdir(parents=True, exist_ok=True)
        empty_content = f"""# Knowledge Bundle Index

> Generated from Link Archivist v2.1.0 index
> Last updated: {datetime.now().isoformat()}
> Total concepts: 0

No concepts indexed yet. Run kb_rebuild.py to create index.
"""
        (export_dir / "index.md").write_text(empty_content, encoding="utf-8")
        return {
            "ok": True,
            "export_dir": str(export_dir),
            "concepts_exported": 0,
            "index_generated": True,
            "note": "No concepts to export"
        }

    # Force rebuild: delete existing export
    if force and export_dir.exists():
        try:
            shutil.rmtree(export_dir)
        except OSError as e:
            return {
                "ok": False,
                "error": f"Failed to delete existing export: {e}"
            }

    # Create export directory
    export_dir.mkdir(parents=True, exist_ok=True)

    # Copy archives
    archive_export_dir = export_dir / "archive"
    copied_count = copy_archives(entries, archive_dir, archive_export_dir)

    # Generate index.md
    index_ok = generate_index_md(entries, export_dir, build_stats)

    # Generate log.md
    log_ok = generate_log_md(cache, build_stats, export_dir)

    return {
        "ok": True,
        "export_dir": str(export_dir),
        "concepts_exported": copied_count,
        "index_generated": index_ok,
        "log_generated": log_ok,
        "timestamp": datetime.now().isoformat()
    }


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="KB Export OKF - Link Archivist v2.1.0"
    )
    parser.add_argument("--dir", required=True, help="Archive directory")
    parser.add_argument(
        "--out",
        help="Custom output directory (must be inside .kb-workdir)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild (delete existing export first)"
    )
    args = parser.parse_args()

    try:
        result = export_okf(
            Path(args.dir),
            Path(args.out) if args.out else None,
            args.force
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": str(e)
        }, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
