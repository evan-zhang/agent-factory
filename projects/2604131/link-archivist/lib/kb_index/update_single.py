#!/usr/bin/env python3
"""
Single-file incremental update with fcntl locking and atomic writes.

This module implements the core indexing logic:
- SHA256-based change detection
- fcntl flock for concurrent safety
- Atomic writes via temp files + os.replace
- Dirty marker + self-healing for derived indexes
"""
import fcntl
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .parse_frontmatter import parse_entry


class ConcurrentUpdateError(Exception):
    """Raised when another process is holding the write lock."""
    pass


def acquire_lock(lock_file: Path, timeout: float = 5.0) -> object:
    """Acquire exclusive lock with timeout.

    Args:
        lock_file: Path to lock file
        timeout: Seconds to wait before giving up

    Returns:
        File descriptor (must be kept alive to hold lock)

    Raises:
        ConcurrentUpdateError: If timeout expires
    """
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    fd = None
    try:
        fd = open(lock_file, "w")
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd  # Return fd to keep lock held
    except (IOError, OSError) as e:
        if fd:
            fd.close()
        # Wait and retry
        import time
        start = time.time()
        while time.time() - start < timeout:
            try:
                fd = open(lock_file, "w")
                fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return fd  # Return fd to keep lock held
            except (IOError, OSError):
                time.sleep(0.1)
                if fd:
                    fd.close()
                fd = None
        raise ConcurrentUpdateError(f"Could not acquire lock after {timeout}s")
    except Exception as e:
        if fd:
            fd.close()
        raise


def load_json(path: Path) -> Any:
    """Load JSON file with error handling."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_json_atomic(path: Path, data: Any) -> bool:
    """Atomically save JSON via temp file + os.replace.

    Returns:
        True if successful

    Raises:
        ValueError: If data is not JSON-serializable
    """
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        # Validate JSON by serializing first
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        # Write temp file
        temp_path.write_text(json_str, encoding="utf-8")

        # Atomic replace
        temp_path.replace(path)

        return True
    except (json.JSONDecodeError, OSError) as e:
        # Cleanup temp file on failure
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        return False


def update_entities_registry(entries: Dict[str, Any]) -> Dict[str, list]:
    """Build entity -> files reverse index from entries."""
    registry = {}
    for rel_path, entry in entries.items():
        for entity in entry.get("entities", []):
            if entity not in registry:
                registry[entity] = []
            registry[entity].append(rel_path)
    return registry


def derive_graph_data(entries: Dict[str, Any]) -> Dict[str, Any]:
    """Derive graph nodes and edges from entries.

    This is the self-healing logic: if derived files are corrupted,
    we can rebuild from entries.json alone.
    """
    nodes = []
    edges = []

    # Build nodes
    for rel_path, entry in entries.items():
        nodes.append({
            "id": rel_path,
            "title": entry.get("title", rel_path),
            "tags": entry.get("tags", []),
            "entities": entry.get("entities", []),
        })

    # Build edges from shared entities
    entity_map = {}
    for rel_path, entry in entries.items():
        for ent in entry.get("entities", []):
            if ent not in entity_map:
                entity_map[ent] = []
            entity_map[ent].append(rel_path)

    for entity, paths in entity_map.items():
        if len(paths) < 2:
            continue
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                edges.append({
                    "from": paths[i],
                    "to": paths[j],
                    "type": "entity",
                    "label": entity,
                    "weight": 1.0
                })

    # Build edges from shared tags
    tag_map = {}
    for rel_path, entry in entries.items():
        for tag in entry.get("tags", []):
            if tag not in tag_map:
                tag_map[tag] = []
            tag_map[tag].append(rel_path)

    for tag, paths in tag_map.items():
        if len(paths) < 2:
            continue
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                edges.append({
                    "from": paths[i],
                    "to": paths[j],
                    "type": "tag",
                    "label": tag,
                    "weight": 0.3
                })

    return {"nodes": nodes, "edges": edges}


def mark_dirty(workdir: Path) -> None:
    """Mark workdir as dirty (needs self-healing)."""
    dirty_marker = workdir / ".dirty"
    dirty_marker.write_text(f"dirty_since: {datetime.now().isoformat()}\n")


def clear_dirty(workdir: Path) -> None:
    """Clear dirty marker."""
    dirty_marker = workdir / ".dirty"
    if dirty_marker.exists():
        dirty_marker.unlink()


def update_single(
    md_path: Path,
    archive_dir: Path,
    *,
    force_recompile: bool = False
) -> Dict[str, Any]:
    """Incrementally update single file index.

    Args:
        md_path: Absolute path to archived Markdown file
        archive_dir: Archive root directory (contains .kb-workdir/)
        force_recompile: Force LLM recompile (ignores frontmatter)

    Returns:
        {"ok": True, "entry_path": "...", "compile_method": "frontmatter"}

    Raises:
        FileNotFoundError: If md_path doesn't exist
        ValueError: If frontmatter invalid and not force_recompile
        ConcurrentUpdateError: If lock timeout expires
    """
    md_path = Path(md_path).resolve()
    archive_dir = Path(archive_dir).resolve()
    workdir = archive_dir / ".kb-workdir"
    lock_file = workdir / ".lock"

    if not md_path.exists():
        raise FileNotFoundError(f"File not found: {md_path}")

    # Acquire lock and keep fd to hold it
    lock_fd = acquire_lock(lock_file)

    try:
        # Initialize workdir
        workdir.mkdir(parents=True, exist_ok=True)

        # Load existing cache
        cache_path = workdir / "kb_cache.json"
        cache = load_json(cache_path) or {}
        entries_path = workdir / "entries.json"
        entries = load_json(entries_path) or {}

        # Calculate SHA256
        from .parse_frontmatter import sha256
        current_sha256 = sha256(md_path)
        rel_path = str(md_path.relative_to(archive_dir))

        # Check if unchanged
        if not force_recompile:
            old_entry = entries.get(rel_path, {})
            old_sha256 = old_entry.get("source_sha256", "")
            if old_sha256 == current_sha256 and old_entry:
                # Already indexed, no-op
                return {
                    "ok": True,
                    "entry_path": rel_path,
                    "compile_method": old_entry.get("compile_method", "legacy"),
                    "indexed": False,  # No change
                }

        # Parse entry (from frontmatter or LLM)
        if not force_recompile:
            try:
                entry = parse_entry(md_path)
                # Fix: Set correct archive-relative path
                entry["path"] = rel_path
                entry["source_sha256"] = current_sha256
                entry["compiled_at"] = datetime.now().isoformat()
                compile_method = "frontmatter"
            except ValueError as e:
                # Frontmatter invalid - mark as failed in cache
                cache[rel_path] = {
                    "status": "failed",
                    "error": str(e),
                    "sha256": current_sha256,
                    "last_attempt": datetime.now().isoformat(),
                }
                save_json_atomic(cache_path, cache)
                raise ValueError(f"Frontmatter parsing failed: {e}")
        else:
            # Force LLM recompile - check if compile.py is available
            try:
                from .compile import compile_with_llm
                result = compile_with_llm(md_path, archive_dir)
                if isinstance(result, dict) and result.get("ok") is False:
                    raise ValueError(f"LLM compile failed: {result.get('error', 'Unknown error')}")
                entry = result.get("entry", result) if isinstance(result, dict) else result
                if not isinstance(entry, dict):
                    raise ValueError("LLM compile returned invalid entry")
                # Fix: Set correct archive-relative path
                entry["path"] = rel_path
                entry["source_sha256"] = current_sha256
                entry["compiled_at"] = datetime.now().isoformat()
                entry["compile_method"] = "llm_forced"
                compile_method = "llm_forced"
            except ImportError:
                # LLM compile module not available, return clear error
                raise ValueError(
                    "force-llm not implemented: compile.py module not found. "
                    "Either implement the LLM compilation path or use frontmatter-only mode."
                )
            except Exception as e:
                raise ValueError(f"LLM recompile failed: {e}")

        # Update entries.json (atomic)
        entries[rel_path] = entry
        if not save_json_atomic(entries_path, entries):
            mark_dirty(workdir)
            raise RuntimeError("Failed to write entries.json")

        # Update derived indexes (atomic, with dirty fallback)
        try:
            # Update entities-registry.json
            entities_registry = update_entities_registry(entries)
            registry_path = workdir / "entities-registry.json"
            if not save_json_atomic(registry_path, entities_registry):
                mark_dirty(workdir)
        except Exception:
            mark_dirty(workdir)

        try:
            # Update graph-data.json
            graph_data = derive_graph_data(entries)
            graph_path = workdir / "graph-data.json"
            if not save_json_atomic(graph_path, graph_data):
                mark_dirty(workdir)
        except Exception:
            mark_dirty(workdir)

        # Update cache
        cache[rel_path] = {
            "status": "ok",
            "sha256": current_sha256,
            "indexed_at": datetime.now().isoformat(),
        }
        save_json_atomic(cache_path, cache)

        # Update build_stats.json
        stats_path = workdir / "build_stats.json"
        stats = {
            "last_build": datetime.now().isoformat(),
            "total_entries": len(entries),
            "last_entry_path": rel_path,
        }
        save_json_atomic(stats_path, stats)

        # Clear dirty marker if all succeeded
        clear_dirty(workdir)

        return {
            "ok": True,
            "entry_path": rel_path,
            "compile_method": compile_method,
            "indexed": True,
        }

    finally:
        # Release lock by closing file descriptor
        if lock_fd:
            lock_fd.close()


def self_heal(workdir: Path) -> bool:
    """Self-healing: rebuild derived indexes from entries.json.

    Returns:
        True if healing successful

    This is called when .dirty marker exists.
    """
    entries_path = workdir / "entries.json"
    entries = load_json(entries_path)
    if not entries:
        return False

    try:
        # Rebuild entities-registry.json
        entities_registry = update_entities_registry(entries)
        registry_path = workdir / "entities-registry.json"
        save_json_atomic(registry_path, entities_registry)

        # Rebuild graph-data.json
        graph_data = derive_graph_data(entries)
        graph_path = workdir / "graph-data.json"
        save_json_atomic(graph_path, graph_data)

        # Clear dirty marker
        clear_dirty(workdir)

        return True
    except Exception:
        return False


def main():
    """CLI interface for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Incrementally update single file index")
    parser.add_argument("file", help="Markdown file path")
    parser.add_argument("--dir", required=True, help="Archive directory")
    parser.add_argument("--force-llm", action="store_true", help="Force LLM recompile")
    args = parser.parse_args()

    try:
        result = update_single(
            Path(args.file),
            Path(args.dir),
            force_recompile=args.force_llm
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
