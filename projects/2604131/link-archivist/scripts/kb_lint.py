#!/usr/bin/env python3
"""
KB Lint - Knowledge base index health checker for Link Archivist.

This script validates index integrity and reports issues.
"""
import json
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from kb_index.lint import lint_index


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


def main():
    import argparse

    parser = argparse.ArgumentParser(description="KB Lint - Link Archivist")
    parser.add_argument("--dir", help="Archive directory (overrides config)")
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

    # Execute lint
    try:
        result = lint_index(archive_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Exit with error code if issues found
        if result.get("issues"):
            return 1
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
