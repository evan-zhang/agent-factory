#!/usr/bin/env python3
"""Archive report with auto-numbering. Single responsibility: write to archive_dir only."""
import json
from datetime import datetime
from pathlib import Path


def _date_to_nested_path(base_dir: Path, date_str: str) -> Path:
    """Convert YYYY-MM-DD to YYYY/MM nested path."""
    parts = date_str.split("-")  # [YYYY, MM, DD]
    return base_dir / parts[0] / parts[1]


def get_next_number(archive_dir: Path, date_str: str, prefix: str = "K") -> int:
    """Scan existing files and return next sequence number."""
    date_dir = _date_to_nested_path(archive_dir, date_str)
    if not date_dir.exists():
        return 1
    max_num = 0
    for f in date_dir.glob(f"{prefix}-*.md"):
        try:
            # {PREFIX}-YYMMDD-NNN-*.md
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
    parser.add_argument('--entities', help='JSON array of entities, e.g. \'["AI","OpenClaw"]\'')
    parser.add_argument('--tags', help='JSON array of tags, e.g. \'["AI","架构"]\'')
    parser.add_argument('--summary', help='One-line summary of the report')
    parser.add_argument('--confidence', default='medium', choices=['high', 'medium', 'low'], help='Extraction confidence')
    parser.add_argument('--source-type', dest='source_type', default='url', choices=['url', 'manual'], help='Source type: url (external) or manual (handwritten)')
    parser.add_argument('--source-url', dest='source_url', help='Original source URL (for external links)')
    parser.add_argument('--project-id', dest='project_id', help='Project ID for manual documents (required for source-type=manual)')
    parser.add_argument('--author', help='Author for manual documents')
    args = parser.parse_args()

    content_file = args.file_arg or args.content_file
    archive_dir = args.dir_arg or args.archive_dir
    title = args.title_arg or args.title or 'report'

    # Parse entities/tags JSON
    entities = []
    if args.entities:
        try:
            entities = json.loads(args.entities)
        except json.JSONDecodeError:
            entities = [e.strip() for e in args.entities.split(",")]

    tags = []
    if args.tags:
        try:
            tags = json.loads(args.tags)
        except json.JSONDecodeError:
            tags = [t.strip() for t in args.tags.split(",")]

    return content_file, archive_dir, title, entities, tags, args.summary, args.confidence, args.source_type, args.source_url, args.project_id, args.author


def _trigger_kb_index(archive_file: Path, archive_dir: Path, result: dict):
    """Best-effort: trigger KB index update on the newly archived file.

    Non-blocking: if indexing fails, just log a warning.
    The result dict is updated with index_status if available.
    """
    try:
        # Import internal KB index module
        import sys
        lib_path = Path(__file__).parent.parent / "lib"
        if str(lib_path) not in sys.path:
            sys.path.insert(0, str(lib_path))

        from kb_index.update_single import update_single, ConcurrentUpdateError

        # Incremental index update
        index_result = update_single(archive_file, archive_dir)

        if index_result.get("ok"):
            result["index_status"] = "indexed"
            result["compile_method"] = index_result.get("compile_method", "frontmatter")
        else:
            result["index_status"] = "failed"

    except ConcurrentUpdateError:
        result["index_status"] = "concurrent_skip"
    except Exception as e:
        # Non-blocking: don't fail the archive if index fails
        result["index_status"] = f"error: {str(e)[:100]}"


def _trigger_xgkb_sync(archive_file: Path, archive_dir: Path, result: dict):
    """Best-effort: sync to XGKB (玄关知识库) if configured.

    Non-blocking: if sync fails or xgkb-sync-helper is not installed, just log.
    The result dict is updated with xgkb_status if available.
    """
    try:
        # Check if .xgkb.json exists in archive_dir (opt-in)
        xgkb_config = archive_dir / ".xgkb.json"
        if not xgkb_config.exists():
            return  # Not configured, skip silently

        # Find xgkb_push.py in standard skills directory
        import shutil
        candidates = [
            Path.home() / ".openclaw" / "skills" / "xgkb-sync-helper" / "scripts" / "xgkb_push.py",
            Path.home() / ".openclaw" / "skills" / "xgkb-sync-helper" / "scripts" / "xgkb_push.py",
        ]
        xgkb_push = next((p for p in candidates if p.exists()), None)

        if not xgkb_push:
            result["xgkb_status"] = "not_installed"  # xgkb-sync-helper not found
            return

        # Call xgkb_push.py, non-blocking
        import subprocess
        proc = subprocess.run(
            ["python3", str(xgkb_push), str(archive_file)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if proc.returncode == 0:
            result["xgkb_status"] = "synced"
        else:
            result["xgkb_status"] = "failed"
            result["xgkb_error"] = proc.stderr[:200] if proc.stderr else "unknown"

    except Exception as e:
        # Non-blocking: don't fail the archive if sync fails
        result["xgkb_status"] = f"error: {str(e)[:100]}"


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
    content_file_str, archive_dir_str, title, entities, tags, summary, confidence, source_type, source_url, project_id, author = parse_args()

    if not content_file_str:
        print(json.dumps({
            "ok": False,
            "error": "usage: archive_report.py <content_file> <archive_dir> [title]\n"
                     "       or: archive_report.py --file <file> [--dir <dir>] [--title <title>]\n"
                     "            [--entities '<json>'] [--tags '<json>'] [--summary '<text>'] [--confidence high]\n"
                     "            [--source-type url|manual] [--source-url <url>] [--project-id <id>] [--author <name>]"
        }, ensure_ascii=False))
        return 1

    content_file = Path(content_file_str).expanduser()
    archive_dir = Path(archive_dir_str).expanduser() if archive_dir_str else Path(".")

    if not content_file.exists():
        print(json.dumps({"ok": False, "error": f"missing file: {content_file}"}))
        return 1

    # Load config
    config = load_config()
    if config:
        if not archive_dir_str:
            archive_dir = Path(config.get("archive_dir", archive_dir)).expanduser()

    # Determine prefix: K for external (url), M for manual
    if source_type == "manual":
        prefix = "M"
        if not project_id:
            print(json.dumps({
                "ok": False,
                "error": "--project-id is required for --source-type manual",
                "hint": "Ask the user: 这篇文档来自哪个项目？"
            }, ensure_ascii=False))
            return 1
    else:
        prefix = "K"

    # Resolve date strings
    today_display = datetime.now().strftime("%Y-%m-%d")  # YYYY-MM-DD for paths
    today_code = datetime.now().strftime("%y%m%d")       # YYMMDD for archive ID

    # --- Archive to local ---
    seq = get_next_number(archive_dir, today_display, prefix)
    archive_id = f"{prefix}-{today_code}-{seq:03d}"
    date_dir = _date_to_nested_path(archive_dir, today_display)
    date_dir.mkdir(parents=True, exist_ok=True)

    content = content_file.read_text(encoding="utf-8")

    # Add YAML header if not present
    if not content.startswith("---"):
        header_parts = [
            f"archive: {archive_id}",
            f"source: {source_url or source_type}",
            f"source_type: {source_type}",
            f"created_at: {datetime.now().isoformat()}",
        ]
        if source_type == "manual":
            if project_id:
                header_parts.append(f"project_id: {project_id}")
            if author:
                header_parts.append(f"author: {author}")
        if entities:
            header_parts.append("entities:")
            for ent in entities[:10]:
                header_parts.append(f"  - {ent}")
        else:
            header_parts.append("entities: []")
        if summary:
            header_parts.append(f"summary: {summary}")
        if tags:
            header_parts.append("tags:")
            for tag in tags[:3]:
                header_parts.append(f"  - {tag}")
        else:
            header_parts.append("tags: []")
        if confidence:
            header_parts.append(f"confidence: {confidence}")
        header = "---\n" + "\n".join(header_parts) + "\n---\n"
        content = header + content

    safe_title = title.replace(" ", "-").replace("/", "-")[:50]
    archive_file = date_dir / f"{archive_id}-{safe_title}.md"
    archive_file.write_text(content, encoding="utf-8")

    result = {
        "ok": True,
        "archive_id": archive_id,
        "archive_file": str(archive_file),
        "seq": seq,
    }

    # Auto-trigger KB index incremental update (non-blocking, best-effort)
    _trigger_kb_index(archive_file, archive_dir, result)

    # Auto-sync to XGKB (玄关知识库) if configured, non-blocking
    _trigger_xgkb_sync(archive_file, archive_dir, result)

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
