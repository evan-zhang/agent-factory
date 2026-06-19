#!/usr/bin/env python3
"""
Parse frontmatter from archived Markdown files.

This module extracts structured entry data from YAML frontmatter without LLM calls.
It's designed for the main indexing path where Phase 3 LLM already generated the metadata.
"""
import hashlib
import re
from pathlib import Path
from typing import Dict, Any


def sha256(path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_yaml_frontmatter(content: str) -> Dict[str, Any]:
    """Parse YAML frontmatter from Markdown content.

    Args:
        content: Markdown file content

    Returns:
        Parsed frontmatter as dict

    Raises:
        ValueError: If frontmatter format is invalid
    """
    if not content.startswith("---"):
        raise ValueError("No YAML frontmatter found")

    # Extract content between --- markers
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        raise ValueError("Invalid YAML frontmatter format")

    yaml_text = match.group(1)

    # Prefer PyYAML when available: relationships are list-of-dict and
    # hand-rolled parsing is too fragile for nested YAML.
    try:
        import yaml
        parsed = yaml.safe_load(yaml_text) or {}
        if not isinstance(parsed, dict):
            raise ValueError("YAML frontmatter must be a mapping")
        return parsed
    except ImportError:
        pass
    except Exception as e:
        raise ValueError(f"YAML parse failed: {e}")

    # Fallback simple YAML parser (limited subset; nested structures unsupported).
    frontmatter = {}
    lines = yaml_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not line or line.strip().startswith("#"):
            i += 1
            continue

        # Handle key-value pairs
        if ":" in line and not line.strip().startswith("-"):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Check if it's an empty list, inline list, or list start
            if value.strip() == "[]":
                # Empty list
                frontmatter[key] = []
                i += 1
            elif value.strip().startswith("[") and value.strip().endswith("]"):
                # Inline list like [Python, Programming]
                list_content = value.strip()[1:-1].strip()
                if not list_content:
                    frontmatter[key] = []
                else:
                    # Split by comma and clean each item
                    items = [item.strip().strip('"\'') for item in list_content.split(",")]
                    frontmatter[key] = items
                i += 1
            elif i + 1 < len(lines) and lines[i + 1].strip().startswith("-"):
                # It's a multi-line list
                frontmatter[key] = []
                i += 1
                # Collect list items
                while i < len(lines):
                    list_line = lines[i].rstrip()
                    if not list_line.strip() or not list_line.strip().startswith("-"):
                        break
                    # Extract item after "- "
                    item_match = re.match(r'\s*-\s*(.+)', list_line)
                    if item_match:
                        item = item_match.group(1).strip()
                        # Remove quotes if present
                        if item.startswith('"') and item.endswith('"'):
                            item = item[1:-1]
                        elif item.startswith("'") and item.endswith("'"):
                            item = item[1:-1]
                        frontmatter[key].append(item)
                    i += 1
            else:
                # Simple value
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                frontmatter[key] = value
                i += 1
        else:
            i += 1

    return frontmatter


def parse_entry(md_path: Path) -> Dict[str, Any]:
    """Parse entry from Markdown file's YAML frontmatter.

    Args:
        md_path: Path to Markdown file

    Returns:
        Entry dict with all required fields

    Raises:
        ValueError: If required fields are missing or invalid
    """
    if not md_path.exists():
        raise FileNotFoundError(f"File not found: {md_path}")

    content = md_path.read_text(encoding="utf-8")

    # Parse frontmatter
    try:
        frontmatter = parse_yaml_frontmatter(content)
    except ValueError as e:
        raise ValueError(f"Invalid frontmatter: {e}")

    # Extract required fields
    archive = frontmatter.get("archive")
    source = str(frontmatter.get("source", ""))
    source_type = str(frontmatter.get("source_type", "unknown"))
    created_at = frontmatter.get("created_at", "")
    created_at = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
    summary = str(frontmatter.get("summary", "")).strip()
    entities = frontmatter.get("entities", [])
    tags = frontmatter.get("tags", [])
    confidence = frontmatter.get("confidence", "medium")
    relationships = frontmatter.get("relationships", [])

    # Validation
    if not summary:
        raise ValueError("Missing required field: summary")

    if len(summary) > 200:
        raise ValueError(f"summary too long: {len(summary)} > 200 characters")

    if not isinstance(entities, list):
        raise ValueError("entities must be a list")

    if len(entities) > 10:
        entities = entities[:10]  # Truncate with warning

    if not isinstance(tags, list):
        raise ValueError("tags must be a list")

    if len(tags) > 3:
        tags = tags[:3]  # Truncate with warning

    if confidence not in ("high", "medium", "low"):
        raise ValueError(f"Invalid confidence: {confidence}")

    if relationships is None:
        relationships = []
    if not isinstance(relationships, list):
        relationships = []
    else:
        cleaned_relationships = []
        for rel in relationships:
            if not isinstance(rel, dict):
                continue
            cleaned_relationships.append({
                "type": str(rel.get("type", "unknown")),
                "target": str(rel.get("target", "")),
                "description": str(rel.get("description", "")),
            })
        relationships = cleaned_relationships[:20]

    # Extract title from content (first heading)
    title = ""
    for line in content.split("\n"):
        match = re.match(r"^#+\s+(.+)", line)
        if match:
            title = match.group(1).strip()
            break

    if not title:
        title = md_path.stem

    # Build entry (path will be set by caller to ensure archive-relative path)
    entry = {
        "title": title,
        "summary": summary,
        "entities": entities,
        "tags": tags,
        "relationships": relationships,
        "confidence": confidence,
        "source_sha256": sha256(md_path),
        "archive_id": archive,
        "source": source,
        "source_type": source_type,
        "created_at": created_at,
        "compiled_at": None,  # Will be set by update_single
        "compile_method": "frontmatter",
        "provider": "phase3_llm",
    }

    return entry


def main():
    """CLI interface for testing."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Parse frontmatter from Markdown file")
    parser.add_argument("file", help="Markdown file path")
    args = parser.parse_args()

    try:
        entry = parse_entry(Path(args.file))
        print(json.dumps({"ok": True, "entry": entry}, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
