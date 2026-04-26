#!/usr/bin/env python3
"""
Init config for link-archivist.
Creates / updates / checks config file in platform-specific directory.

Usage:
  python3 init_config.py                          # 检查配置状态
  python3 init_config.py --set archive_dir=/path  # 设置单个配置项
  python3 init_config.py --setup                  # 交互式引导设置
"""
import json
import os
import sys
from pathlib import Path

CONFIG_FILENAME = "link-archivist-config.json"

# 所有可配置项及其说明
CONFIG_FIELDS = {
    "archive_dir": {
        "label": "本地归档主目录",
        "required": True,
        "hint": "报告存放的根目录，按日期自动分子目录",
        "example": "/path/to/knowledge-base",
    },
    "obsidian_dir": {
        "label": "Obsidian 同步目录",
        "required": False,
        "hint": "留空则跳过 Obsidian 同步",
        "example": "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/AI调研",
    },
    "xgjk_app_key": {
        "label": "玄关 appKey（AI 慧记转写）",
        "required": False,
        "hint": "用于音频转录，联系玄关管理员获取",
        "example": "your-app-key-here",
    },
    "tavily_api_key": {
        "label": "Tavily API key（Web Search 交叉验证）",
        "required": False,
        "hint": "用于 Web Search 交叉验证，获取：https://tavily.com",
        "example": "tvly-xxxxx",
    },
}


def get_config_dir() -> Path:
    """Detect platform and return appropriate config directory."""
    if os.getenv("OPENCLAW_ROOT"):
        return Path.home() / ".openclaw"
    elif os.getenv("HERMES_ROOT"):
        return Path.home() / ".hermes"
    else:
        return Path.home() / ".config"


def get_config_path() -> Path:
    return get_config_dir() / CONFIG_FILENAME


def load_config() -> dict:
    config_path = get_config_path()
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_config(config: dict) -> None:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / CONFIG_FILENAME
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def check_config(config: dict) -> dict:
    """检查配置状态，返回结构化结果。"""
    archive_ok = False
    if config.get("archive_dir"):
        archive = Path(config["archive_dir"]).expanduser()
        archive_ok = archive.is_dir()

    obsidian_ok = False
    if config.get("obsidian_dir"):
        obsidian = Path(config["obsidian_dir"]).expanduser()
        obsidian_ok = obsidian.is_dir()

    tavily_ok = bool(config.get("tavily_api_key")) or bool(os.getenv("TAVILY_API_KEY"))
    xgjk_ok = bool(config.get("xgjk_app_key"))

    hints = []
    if not archive_ok:
        hints.append("请设置 archive_dir（知识库主目录，必填）")
    if not obsidian_ok:
        hints.append("建议设置 obsidian_dir（Obsidian 同步目录，可选）")
    if not tavily_ok:
        hints.append("建议配置 tavily_api_key（Web Search 交叉验证，可选）")
    if not xgjk_ok:
        hints.append("建议配置 xgjk_app_key（AI 慧记音频转写，可选）")

    configured = archive_ok
    return {
        "ok": True,
        "configured": configured,
        "config_path": str(get_config_path()),
        "archive_dir": config.get("archive_dir"),
        "archive_ok": archive_ok,
        "obsidian_dir": config.get("obsidian_dir"),
        "obsidian_ok": obsidian_ok,
        "tavily_configured": tavily_ok,
        "xgjk_configured": xgjk_ok,
        "hints": hints if not configured else [],
    }


def print_current_config(config: dict) -> None:
    """显示当前配置。"""
    print("\n📋 当前配置：")
    print(f"   配置文件：{get_config_path()}")
    print()
    for key, meta in CONFIG_FIELDS.items():
        value = config.get(key, "")
        status = ""
        if meta["required"]:
            if value and Path(value).expanduser().is_dir() if "dir" in key else value:
                status = "✅"
            else:
                status = "❌ 必填"
        else:
            status = "✅" if value else "⚠️ 未设置（可选）"
        label = meta["label"]
        display = value if value else "（未设置）"
        # 对 key 类字段隐藏部分内容
        if "key" in key and value:
            display = value[:8] + "..." + value[-4:] if len(value) > 12 else value
        print(f"   {status} {label}")
        print(f"      {key} = {display}")
    print()


def main() -> int:
    args = sys.argv[1:]

    # 模式 1：--set key=value 修改单个配置
    if args and args[0] == "--set":
        if len(args) < 2 or "=" not in args[1]:
            print(json.dumps({
                "ok": False,
                "error": "用法：init_config.py --set key=value",
                "available_keys": list(CONFIG_FIELDS.keys()),
            }, ensure_ascii=False))
            return 1

        key, value = args[1].split("=", 1)
        if key not in CONFIG_FIELDS:
            print(json.dumps({
                "ok": False,
                "error": f"未知配置项：{key}",
                "available_keys": list(CONFIG_FIELDS.keys()),
            }, ensure_ascii=False))
            return 1

        config = load_config()
        config[key] = value
        save_config(config)

        print(json.dumps({
            "ok": True,
            "action": "updated",
            "key": key,
            "value": value,
            "config_path": str(get_config_path()),
        }, ensure_ascii=False))
        return 0

    # 模式 2：--setup 交互式引导
    if args and args[0] == "--setup":
        config = load_config()
        print("🔧 Link Archivist 配置向导")
        print(f"   配置文件：{get_config_path()}\n")

        for key, meta in CONFIG_FIELDS.items():
            current = config.get(key, "")
            required = "（必填）" if meta["required"] else "（可选，回车跳过）"
            print(f"   {meta['label']} {required}")
            print(f"   说明：{meta['hint']}")
            if current:
                display = current
                if "key" in key and len(current) > 12:
                    display = current[:8] + "..." + current[-4:]
                print(f"   当前值：{display}")
            print(f"   示例：{meta['example']}")
            value = input(f"   请输入 {key}：").strip()
            if value:
                config[key] = value
            elif meta["required"] and not current:
                print(f"   ⚠️ {key} 是必填项，稍后请设置")
            print()

        save_config(config)
        print("✅ 配置已保存")
        result = check_config(config)
        print(json.dumps(result, ensure_ascii=False))
        return 0

    # 模式 3：无参数 = 检查配置状态
    config = load_config()
    result = check_config(config)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
