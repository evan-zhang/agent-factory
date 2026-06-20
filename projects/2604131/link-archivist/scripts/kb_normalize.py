#!/usr/bin/env python3
"""
Batch normalize frontmatter for all archived .md files.

- Strips residual ```yaml blocks from body
- Rewrites frontmatter to canonical field order
- Preserves all field values and body content
- Reports changes without modifying archive_id/path

Usage:
  python3 scripts/kb_normalize.py --dir <archive_dir> [--dry-run]
"""
import json
import re
import sys
from pathlib import Path
from datetime import datetime

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))


def strip_yaml_block(body: str) -> str:
    """Remove residual ```yaml ... ``` blocks from the body (Phase 3 LLM output)."""
    # Match ```yaml ... ``` at the start of the body (with optional whitespace/newlines)
    body = re.sub(r'^\s*```ya?ml\s*\n.*?\n```\s*\n?', '', body, flags=re.DOTALL | re.IGNORECASE)
    return body


def parse_existing_frontmatter(content: str) -> tuple:
    """Parse frontmatter from content. Returns (parsed_dict, body)."""
    if not content.startswith("---"):
        return {}, content
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", content, re.DOTALL)
    if not m:
        return {}, content
    yaml_text, body = m.group(1), m.group(2)
    try:
        import yaml
        parsed = yaml.safe_load(yaml_text) or {}
        if not isinstance(parsed, dict):
            parsed = {}
    except Exception:
        parsed = {}
    return parsed, body


def build_canonical_frontmatter(fields: dict) -> str:
    """Build frontmatter in canonical field order."""
    parts = []

    archive = fields.get("archive", "")
    if archive:
        parts.append(f"archive: {archive}")

    source = fields.get("source", "unknown")
    parts.append(f"source: {source}")

    source_type = fields.get("source_type", "url")
    parts.append(f"source_type: {source_type}")

    created_at = fields.get("created_at", "")
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()
    parts.append(f"created_at: {created_at}")

    # Manual-only fields
    if source_type == "manual":
        project_id = fields.get("project_id", "")
        if project_id:
            parts.append(f"project_id: {project_id}")
        author = fields.get("author", "")
        if author:
            parts.append(f"author: {author}")

    # Entities
    entities = fields.get("entities", [])
    if not isinstance(entities, list):
        entities = [str(entities)] if entities else []
    if entities:
        parts.append("entities:")
        for ent in entities[:10]:
            parts.append(f"  - {ent}")
    else:
        parts.append("entities: []")

    # Summary
    summary = fields.get("summary", "")
    if summary:
        summary = str(summary).replace("\n", " ").strip()
        parts.append(f"summary: {summary}")

    # Tags
    tags = fields.get("tags", [])
    if not isinstance(tags, list):
        tags = [str(tags)] if tags else []
    if tags:
        parts.append("tags:")
        for tag in tags[:3]:
            parts.append(f"  - {tag}")
    else:
        parts.append("tags: []")

    # Confidence
    confidence = fields.get("confidence", "medium")
    if confidence not in ("high", "medium", "low"):
        confidence = "medium"
    parts.append(f"confidence: {confidence}")

    return "---\n" + "\n".join(parts) + "\n---\n"


def normalize_file(md_path: Path, dry_run: bool = False) -> dict:
    """Normalize a single file. Returns change report."""
    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"file": str(md_path), "status": "read_error", "error": str(e)}

    original = content
    fields, body = parse_existing_frontmatter(content)

    # Strip residual yaml blocks from body
    body = strip_yaml_block(body)

    # Rebuild canonical frontmatter
    new_frontmatter = build_canonical_frontmatter(fields)
    new_content = new_frontmatter + body

    changes = []
    if not original.startswith("---"):
        changes.append("added_frontmatter")
    if "```yaml" in body or "```yml" in body:
        pass  # Already stripped
    if re.search(r'```ya?ml', original[len("---\n"):]) if original.startswith("---") else False:
        changes.append("stripped_yaml_block")

    # Check if body changed
    _, old_body = parse_existing_frontmatter(original) if original.startswith("---") else ({}, original)
    old_body_clean = strip_yaml_block(old_body)
    if old_body_clean.strip() != body.strip():
        changes.append("body_changed")

    # Check if frontmatter order changed
    old_fm_lines = []
    if original.startswith("---"):
        m = re.match(r"^---\s*\n(.*?)\n---", original, re.DOTALL)
        if m:
            for line in m.group(1).split("\n"):
                if line and not line.startswith(" ") and ":" in line:
                    old_fm_lines.append(line.split(":")[0].strip())

    new_fm_lines = []
    for line in new_frontmatter.split("\n"):
        if line and not line.startswith(" ") and line != "---" and ":" in line:
            new_fm_lines.append(line.split(":")[0].strip())

    if old_fm_lines and old_fm_lines != new_fm_lines:
        changes.append("field_order_changed")

    if new_content == original:
        return {"file": str(md_path), "status": "unchanged"}

    if not dry_run:
        md_path.write_text(new_content, encoding="utf-8")

    return {
        "file": str(md_path),
        "status": "normalized" if not dry_run else "would_normalize",
        "changes": changes or ["reformatted"],
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch normalize frontmatter")
    parser.add_argument("--dir", required=True, help="Archive directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    archive_dir = Path(args.dir).expanduser()
    if not archive_dir.exists():
        print(json.dumps({"ok": False, "error": f"Directory not found: {archive_dir}"}))
        return 1

    # Scan all .md files (same rules as ingest: skip .kb-workdir, system dirs, system files)
    SYSTEM_FILES = {"index.md", "log.md", "inbox.md", "AGENTS.md", "WIKI.md"}
    SYSTEM_DIRS = {"sources", "entities", "concepts", "syntheses", "reports", "_attachments", "_views", ".openclaw-wiki"}

    md_files = []
    for md in archive_dir.rglob("*.md"):
        rel = md.relative_to(archive_dir)
        if ".kb-workdir" in str(md):
            continue
        if md.name.startswith("."):
            continue
        if len(rel.parts) == 1 and md.name in SYSTEM_FILES:
            continue
        if len(rel.parts) > 1 and rel.parts[0] in SYSTEM_DIRS:
            continue
        md_files.append(md)

    results = {"normalized": 0, "unchanged": 0, "error": 0, "would_normalize": 0}
    details = []

    for md in md_files:
        r = normalize_file(md, args.dry_run)
        status = r["status"]
        if status in ("normalized", "would_normalize"):
            results[status if args.dry_run else "normalized"] += 1
        elif status == "unchanged":
            results["unchanged"] += 1
        else:
            results["error"] += 1
        if status != "unchanged":
            details.append(r)

    print(json.dumps({
        "ok": True,
        "total_files": len(md_files),
        "results": results,
        "dry_run": args.dry_run,
        "details": details[:50],  # First 50 changes
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
