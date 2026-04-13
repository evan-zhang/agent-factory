#!/usr/bin/env python3
"""Init config for link-archivist. Creates ~/.openclaw/link-archivist-config.json"""
import json
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".openclaw" / "link-archivist-config.json"


def load_config() -> dict | None:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    return None


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    config = load_config()
    if config and config.get("archive_dir"):
        archive = Path(config["archive_dir"]).expanduser()
        if archive.is_dir():
            print(json.dumps({"ok": True, "configured": True, "archive_dir": str(archive)}, ensure_ascii=False))
            return 0

    print(json.dumps({"ok": True, "configured": False, "hint": "请设置 archive_dir（知识库主目录）"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
