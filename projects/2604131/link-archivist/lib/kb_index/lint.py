#!/usr/bin/env python3
"""
Index health checks: orphan files, dangling refs, coverage stats.

This module validates the index integrity and reports issues.
"""
import json
from pathlib import Path
from typing import Dict, Any, List


def load_entries(root: Path) -> Dict[str, Any]:
    """Load entries from .kb-workdir/entries.json."""
    entries_path = Path(root) / ".kb-workdir" / "entries.json"
    if not entries_path.exists():
        return {}
    try:
        return json.loads(entries_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def detect_orphan_files(archive_dir: Path) -> List[str]:
    """Detect Markdown files not in entries.json.

    Args:
        archive_dir: Archive root directory

    Returns:
        List of orphan file paths
    """
    entries = load_entries(archive_dir)
    if not entries:
        return []

    indexed = set(entries.keys())
    for entry in entries.values():
        path = entry.get("path", "")
        if path:
            indexed.add(str(path))

    orphans = []
    for md in archive_dir.rglob("*.md"):
        if md.name.startswith(".") or ".kb-workdir" in str(md):
            continue
        rel = str(md.relative_to(archive_dir))
        if rel not in indexed:
            orphans.append(rel)

    return orphans


def detect_dangling_refs(archive_dir: Path) -> List[Dict[str, str]]:
    """Detect relationship targets that don't exist.

    Args:
        archive_dir: Archive root directory

    Returns:
        List of dangling references with file and target
    """
    entries = load_entries(archive_dir)
    if not entries:
        return []

    dangling = []
    indexed_paths = set(entries.keys())

    for rel_path, entry in entries.items():
        relationships = entry.get("relationships", [])
        if not isinstance(relationships, list):
            continue
        for rel in relationships:
            if not isinstance(rel, dict):
                continue
            target = rel.get("target", "")
            if not target:
                continue

            # Check if target exists in indexed paths
            target_found = False
            for indexed_path in indexed_paths:
                if target.lower() in indexed_path.lower():
                    target_found = True
                    break

            if not target_found:
                dangling.append({
                    "file": rel_path,
                    "target": target,
                    "description": rel.get("description", ""),
                })

    return dangling


def compute_coverage_stats(archive_dir: Path) -> Dict[str, Any]:
    """Compute entity/tag coverage and confidence distribution.

    Args:
        archive_dir: Archive root directory

    Returns:
        Statistics dict
    """
    entries = load_entries(archive_dir)
    if not entries:
        return {}

    total = len(entries)
    empty_entities = sum(1 for e in entries.values() if not e.get("entities"))
    empty_tags = sum(1 for e in entries.values() if not e.get("tags"))

    confidence_dist = {"high": 0, "medium": 0, "low": 0}
    for entry in entries.values():
        conf = entry.get("confidence", "medium")
        if conf in confidence_dist:
            confidence_dist[conf] += 1

    return {
        "total_entries": total,
        "empty_entities": empty_entities,
        "empty_tags": empty_tags,
        "entity_coverage": round((total - empty_entities) / total * 100, 1) if total > 0 else 0,
        "tag_coverage": round((total - empty_tags) / total * 100, 1) if total > 0 else 0,
        "confidence_distribution": confidence_dist,
    }


def lint_index(archive_dir: Path) -> Dict[str, Any]:
    """Run full lint check on index.

    Args:
        archive_dir: Archive root directory

    Returns:
        Lint result with issues and stats
    """
    issues = []
    warnings = []

    # Check for orphan files
    try:
        orphans = detect_orphan_files(archive_dir)
        if orphans:
            issues.append({
                "type": "orphan",
                "severity": "warning",
                "count": len(orphans),
                "files": orphans[:10],  # First 10
            })
    except Exception as e:
        warnings.append(f"Orphan detection failed: {e}")

    # Check for dangling refs
    try:
        dangling = detect_dangling_refs(archive_dir)
        if dangling:
            issues.append({
                "type": "dangling-ref",
                "severity": "warning",
                "count": len(dangling),
                "refs": dangling[:10],
            })
    except Exception as e:
        warnings.append(f"Dangling ref detection failed: {e}")

    # Compute coverage stats
    try:
        stats = compute_coverage_stats(archive_dir)
        if stats.get("entity_coverage", 100) < 80:
            issues.append({
                "type": "low-entity-coverage",
                "severity": "info",
                "coverage": stats["entity_coverage"],
            })
    except Exception as e:
        warnings.append(f"Coverage stats failed: {e}")

    return {
        "ok": True,
        "issues": issues,
        "warnings": warnings,
        "stats": stats if 'stats' in locals() else {},
    }


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="KB Index lint")
    parser.add_argument("--dir", required=True, help="Archive directory")
    args = parser.parse_args()

    try:
        result = lint_index(Path(args.dir))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
