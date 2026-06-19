#!/usr/bin/env python3
"""
KB Rebuild - Knowledge base index rebuild for Link Archivist.

This script rebuilds the knowledge base index from archived files.
Supports full rebuild, incremental update, and force LLM recompile.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from kb_index.ingest import detect_changes, scan_markdown_files
from kb_index.parse_frontmatter import parse_entry, sha256
from kb_index.update_single import update_single, self_heal, ConcurrentUpdateError, save_json_atomic
from kb_index.build_graph import build_graph


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


def rebuild_full(archive_dir: Path, force_llm: bool = False) -> dict:
    """Full rebuild: scan all files and reindex.

    Args:
        archive_dir: Archive root directory
        force_llm: Force LLM recompile (ignores frontmatter)

    Returns:
        Result dict with stats
    """
    print(f"🔄 Starting full rebuild: {archive_dir}", file=sys.stderr)

    # Check for dirty marker and self-heal
    workdir = archive_dir / ".kb-workdir"
    dirty_marker = workdir / ".dirty"
    if dirty_marker.exists():
        print("⚠️  Detected dirty index, self-healing...", file=sys.stderr)
        if self_heal(workdir):
            print("✅ Self-heal complete", file=sys.stderr)
        else:
            print("⚠️  Self-heal failed, continuing with full rebuild", file=sys.stderr)

    # Scan all Markdown files
    md_files = scan_markdown_files(archive_dir)
    print(f"📂 Found {len(md_files)} Markdown files", file=sys.stderr)

    # Initialize entries
    entries = {}
    success_count = 0
    failed_count = 0
    skipped_count = 0

    for i, md in enumerate(md_files):
        if (i + 1) % 50 == 0:
            print(f"📝 Processing {i+1}/{len(md_files)}...", file=sys.stderr)

        try:
            if force_llm:
                # Force LLM recompile - try to use compile module
                try:
                    from kb_index.compile import compile_with_llm
                    result = compile_with_llm(md, archive_dir)
                    if isinstance(result, dict) and result.get("ok") is False:
                        raise ValueError(f"LLM compile failed: {result.get('error', 'Unknown error')}")
                    entry = result.get("entry", result) if isinstance(result, dict) else result
                    if not isinstance(entry, dict):
                        raise ValueError("LLM compile returned invalid entry")
                    entry["source_sha256"] = sha256(md)
                    entry["compiled_at"] = datetime.now().isoformat()
                    entry["compile_method"] = "llm_forced"
                    method = "llm_forced"
                except ImportError:
                    # LLM compile module not available
                    raise ValueError(
                        "force-llm not implemented: compile.py module not found. "
                        "Either implement the LLM compilation path or use frontmatter-only mode."
                    )
                except Exception as llm_error:
                    raise ValueError(f"LLM recompile failed: {llm_error}")
            else:
                # Parse from frontmatter
                entry = parse_entry(md)
                entry["source_sha256"] = sha256(md)
                entry["compiled_at"] = datetime.now().isoformat()
                entry["compile_method"] = "frontmatter"
                method = "frontmatter"

            rel_path = str(md.relative_to(archive_dir))
            # Fix: Set correct archive-relative path
            entry["path"] = rel_path
            entries[rel_path] = entry
            success_count += 1

        except Exception as e:
            failed_count += 1
            print(f"⚠️  Failed to process {md.name}: {e}", file=sys.stderr)

    # Save entries.json
    workdir.mkdir(parents=True, exist_ok=True)
    entries_path = workdir / "entries.json"

    try:
        if not save_json_atomic(entries_path, entries):
            return {
                "ok": False,
                "error": "Failed to write entries.json"
            }
    except Exception as e:
        return {
            "ok": False,
            "error": f"Failed to write entries.json: {e}"
        }

    # Build derived indexes
    print("🔨 Building derived indexes...", file=sys.stderr)

    try:
        # Build entities-registry
        from kb_index.update_single import update_entities_registry
        entities_registry = update_entities_registry(entries)
        registry_path = workdir / "entities-registry.json"
        save_json_atomic(registry_path, entities_registry)

        # Build graph-data
        graph_result = build_graph(archive_dir)
        graph_path = workdir / "graph-data.json"
        save_json_atomic(graph_path, graph_result)

        # Update build stats
        stats_path = workdir / "build_stats.json"
        stats = {
            "last_build": datetime.now().isoformat(),
            "total_entries": len(entries),
            "build_method": "full" if not force_llm else "full_llm",
        }
        save_json_atomic(stats_path, stats)

        # Clear dirty marker
        from kb_index.update_single import clear_dirty
        clear_dirty(workdir)

    except Exception as e:
        print(f"⚠️  Failed to build derived indexes: {e}", file=sys.stderr)

    print(f"✅ Rebuild complete: {success_count} indexed, {failed_count} failed, {skipped_count} skipped", file=sys.stderr)

    return {
        "ok": True,
        "stats": {
            "total_files": len(md_files),
            "indexed": success_count,
            "failed": failed_count,
            "skipped": skipped_count,
        },
        "build_method": "full" if not force_llm else "full_llm",
    }


def rebuild_incremental(archive_dir: Path) -> dict:
    """Incremental rebuild: only process changed files.

    Args:
        archive_dir: Archive root directory

    Returns:
        Result dict with stats
    """
    print(f"🔄 Starting incremental rebuild: {archive_dir}", file=sys.stderr)

    # Check for dirty marker and self-heal first
    workdir = archive_dir / ".kb-workdir"
    dirty_marker = workdir / ".dirty"
    if dirty_marker.exists():
        print("⚠️  Detected dirty index, self-healing...", file=sys.stderr)
        if self_heal(workdir):
            print("✅ Self-heal complete", file=sys.stderr)
        else:
            print("⚠️  Self-heal failed, continuing with incremental", file=sys.stderr)

    # Detect changes
    changes = detect_changes(archive_dir)

    new_files = changes.get("new_files", [])
    modified_files = changes.get("modified_files", [])
    deleted_files = changes.get("deleted_files", [])

    print(f"📊 Changes: {len(new_files)} new, {len(modified_files)} modified, {len(deleted_files)} deleted", file=sys.stderr)

    # Process new and modified files
    success_count = 0
    failed_count = 0

    all_changed = new_files + modified_files
    for i, rel_path in enumerate(all_changed):
        if (i + 1) % 10 == 0:
            print(f"📝 Processing {i+1}/{len(all_changed)}...", file=sys.stderr)

        md_path = archive_dir / rel_path
        try:
            result = update_single(md_path, archive_dir)
            if result.get("indexed"):
                success_count += 1
        except Exception as e:
            failed_count += 1
            print(f"⚠️  Failed to process {rel_path}: {e}", file=sys.stderr)

    # Handle deleted files
    if deleted_files:
        print(f"🗑️  Removing {len(deleted_files)} deleted files from index...", file=sys.stderr)
        entries_path = workdir / "entries.json"
        if entries_path.exists():
            entries = json.loads(entries_path.read_text(encoding="utf-8"))
            for deleted in deleted_files:
                entries.pop(deleted, None)
            save_json_atomic(entries_path, entries)

            # Rebuild derived indexes
            from kb_index.update_single import update_entities_registry, derive_graph_data
            entities_registry = update_entities_registry(entries)
            registry_path = workdir / "entities-registry.json"
            save_json_atomic(registry_path, entities_registry)

            graph_data = derive_graph_data(entries)
            graph_path = workdir / "graph-data.json"
            save_json_atomic(graph_path, graph_data)

    print(f"✅ Incremental rebuild complete: {success_count} indexed, {failed_count} failed", file=sys.stderr)

    return {
        "ok": True,
        "stats": {
            "new_files": len(new_files),
            "modified_files": len(modified_files),
            "deleted_files": len(deleted_files),
            "indexed": success_count,
            "failed": failed_count,
        },
        "build_method": "incremental",
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="KB Rebuild - Link Archivist")
    parser.add_argument("--dir", help="Archive directory (overrides config)")
    parser.add_argument("--incremental", action="store_true", help="Incremental update (SHA256-based)")
    parser.add_argument("--force-llm", action="store_true", help="Force LLM recompile (ignores frontmatter)")
    args = parser.parse_args()

    # Load config and determine archive directory
    config = load_config()
    archive_dir = Path(args.dir) if args.dir else Path(config.get("archive_dir", "."))

    if not archive_dir.exists():
        print(json.dumps({
            "ok": False,
            "error": f"Archive directory not found: {archive_dir}"
        }, ensure_ascii=False))
        return 1

    # Execute rebuild
    try:
        if args.incremental:
            result = rebuild_incremental(archive_dir)
        else:
            result = rebuild_full(archive_dir, args.force_llm)

        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except KeyboardInterrupt:
        print(json.dumps({"ok": False, "error": "Interrupted by user"}, ensure_ascii=False))
        return 130
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
