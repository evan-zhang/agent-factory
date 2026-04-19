#!/usr/bin/env python3
"""Init config for link-archivist. Creates config file in platform-specific directory."""
import json
import os
import sys
from pathlib import Path


def get_config_dir() -> Path:
    """Detect platform and return appropriate config directory."""
    if os.getenv("OPENCLAW_ROOT"):
        return Path.home() / ".openclaw"
    elif os.getenv("HERMES_ROOT"):
        return Path.home() / ".hermes"
    else:
        return Path.home() / ".config"


def load_config() -> dict | None:
    config_path = get_config_dir() / "link-archivist-config.json"
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    return None


def save_config(config: dict) -> None:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "link-archivist-config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    config = load_config()

    archive_ok = False
    if config and config.get("archive_dir"):
        archive = Path(config["archive_dir"]).expanduser()
        archive_ok = archive.is_dir()

    obsidian_ok = False
    if config and config.get("obsidian_dir"):
        obsidian = Path(config["obsidian_dir"]).expanduser()
        obsidian_ok = obsidian.is_dir()

    tavily_ok = bool(config.get("tavily_api_key")) or bool(os.getenv("TAVILY_API_KEY"))

    hints = []
    if not archive_ok:
        hints.append("请设置 archive_dir（知识库主目录）")
    if not obsidian_ok:
        hints.append("建议设置 obsidian_dir（Obsidian 同步目录，可选）")
    if not tavily_ok:
        hints.append("建议配置 tavily_api_key（用于 Web Search 交叉验证，可提升报告质量）")

    if archive_ok:
        print(json.dumps({
            "ok": True,
            "configured": True,
            "archive_dir": str(Path(config["archive_dir"]).expanduser()),
            "obsidian_dir": config.get("obsidian_dir"),
            "obsidian_configured": obsidian_ok,
            "tavily_configured": tavily_ok,
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "ok": True,
            "configured": False,
            "archive_dir": config.get("archive_dir") if config else None,
            "obsidian_dir": config.get("obsidian_dir"),
            "obsidian_configured": obsidian_ok,
            "tavily_configured": tavily_ok,
            "hints": hints,
        }, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
