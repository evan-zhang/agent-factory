#!/usr/bin/env python3
"""KB Graph 配置初始化脚本"""
import json
import os
from pathlib import Path

CONFIG_PATH = Path.home() / ".openclaw/kb-graph-config.json"

DEFAULT_CONFIG = {
    "watch_dirs": [],
    "llm_provider": "anthropic",
    "model": "claude-sonnet-4-20250514",
    "schema_file": ".kb-schema.md",
    "index_file": ".kb-index.md",
    "cache_dir": ".kb-workdir",
    "auto_update": True,
    "lint_schedule": "daily"
}

def main():
    if CONFIG_PATH.exists():
        print(json.dumps({"ok": True, "status": "exists", "path": str(CONFIG_PATH)}, indent=2))
        return

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)

    print(json.dumps({"ok": True, "status": "created", "path": str(CONFIG_PATH)}, indent=2))

if __name__ == "__main__":
    main()
