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
    "video_archive_dir": {
        "label": "视频归档目录",
        "required": False,
        "hint": "full 模式下载视频的保存目录，未配置则不保存视频",
        "example": "/path/to/video-archive",
    },
    "kb_index": {
        "label": "KB 索引配置",
        "required": False,
        "hint": "知识库索引设置（默认启用）",
        "example": '{"enabled": true, "query_mode": "keyword", "auto_update": true}',
        "type": "object",
    },
}


def get_config_dir() -> Path:
    """Detect platform and return appropriate config directory."""
    if os.getenv("OPENCLAW_ROOT"):
        return Path.home() / ".openclaw"
    elif os.getenv("HERMES_ROOT"):
        return Path.home() / ".hermes"
    else:
        # Default to ~/.openclaw for OpenClaw skill
        return Path.home() / ".openclaw"


def get_config_path() -> Path:
    return get_config_dir() / CONFIG_FILENAME


def load_config() -> dict:
    # Priority order for existing configs:
    # 1. ~/.openclaw/link-archivist-config.json
    # 2. ~/.hermes/link-archivist-config.json
    # 3. ~/.config/link-archivist-config.json
    for config_path in [
        Path.home() / ".openclaw" / CONFIG_FILENAME,
        Path.home() / ".hermes" / CONFIG_FILENAME,
        Path.home() / ".config" / CONFIG_FILENAME,
    ]:
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
    return {}


def save_config(config: dict) -> None:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / CONFIG_FILENAME
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def migrate_kb_graph_config(config: dict, archive_dir: str = None) -> dict:
    """迁移 KB Graph 配置到 Link Archivist 配置（备份而非删除）。

    根据MERGE_PLAN_v2.md §7.3的设计：
    - case A: watch_dirs[0] == archive_dir → 合并配置，备份为 .bak
    - case B: watch_dirs[0] != archive_dir → 不合并，不修改旧文件，提示用户
    - case C: archive_dir 不存在 → 引导用户先配置

    Args:
        config: 当前 link-archivist 配置
        archive_dir: 可选的 archive_dir 覆盖值

    Returns:
        更新后的配置，包含迁移信息
    """
    # Look for kb-graph-config.json in the same priority order
    kb_config_path = None
    for candidate in [
        Path.home() / ".openclaw" / "kb-graph-config.json",
        Path.home() / ".hermes" / "kb-graph-config.json",
        Path.home() / ".config" / "kb-graph-config.json",
    ]:
        if candidate.exists():
            kb_config_path = candidate
            break

    if not kb_config_path:
        return config

    try:
        kb_config = json.loads(kb_config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # 旧配置文件损坏，不处理
        return config

    watch_dirs = kb_config.get("watch_dirs", [])
    if not watch_dirs:
        return config

    kb_watch_dir = watch_dirs[0]
    current_archive_dir = archive_dir or config.get("archive_dir", "")

    if not current_archive_dir:
        # case C: archive_dir 未配置，不合并
        return config

    if kb_watch_dir == current_archive_dir:
        # case A: 目录一致，合并配置
        if "kb_index" not in config:
            config["kb_index"] = {
                "enabled": True,
                "query_mode": kb_config.get("query_mode", "keyword"),
                "auto_update": kb_config.get("auto_update", True),
                "embeddings_enabled": kb_config.get("embeddings_enabled", False),
            }

        # 备份旧配置文件为 .bak（不删除）
        try:
            backup_path = kb_config_path.with_suffix(".json.bak")
            if not backup_path.exists():
                kb_config_path.rename(backup_path)
                config["_migration_note"] = f"KB Graph 配置已合并并备份为 {backup_path.name}"
        except OSError:
            config["_migration_note"] = "KB Graph 配置已合并，但备份失败（权限问题）"

    else:
        # case B: 目录不一致，不合并，提示用户
        config["_migration_warning"] = (
            f"检测到 KB Graph 配置的 watch_dirs ({kb_watch_dir}) "
            f"与 archive_dir ({current_archive_dir}) 不一致。"
            "请手动决定：(1) 修改 archive_dir 指向 watch_dirs[0]；"
            "(2) 移动 watch_dirs[0] 的内容到 archive_dir；"
            "(3) 忽略旧配置（KB Graph v0.3.2 仍可独立运行）"
        )

    return config


def check_config(config: dict) -> dict:
    """检查配置状态，返回结构化结果。"""
    archive_ok = False
    if config.get("archive_dir"):
        archive = Path(config["archive_dir"]).expanduser()
        archive_ok = archive.is_dir()

    tavily_ok = bool(config.get("tavily_api_key")) or bool(os.getenv("TAVILY_API_KEY"))
    xgjk_ok = bool(config.get("xgjk_app_key"))

    video_archive_ok = False
    if config.get("video_archive_dir"):
        video_archive_ok = Path(config["video_archive_dir"]).expanduser().is_dir()

    # KB 索引状态检查
    kb_index_ok = False
    kb_index_config = config.get("kb_index", {})
    if isinstance(kb_index_config, dict):
        kb_index_ok = kb_index_config.get("enabled", True)

    hints = []
    if not archive_ok:
        hints.append("请设置 archive_dir（知识库主目录，必填）")
    if not tavily_ok:
        hints.append("建议配置 tavily_api_key（Web Search 交叉验证，可选）")
    if not xgjk_ok:
        hints.append("建议配置 xgjk_app_key（AI 慧记音频转写，可选）")
    if not video_archive_ok and config.get("video_archive_dir"):
        hints.append("video_archive_dir 目录不存在，视频归档将不可用")

    configured = archive_ok
    return {
        "ok": True,
        "configured": configured,
        "config_path": str(get_config_path()),
        "archive_dir": config.get("archive_dir"),
        "archive_ok": archive_ok,
        "tavily_configured": tavily_ok,
        "xgjk_configured": xgjk_ok,
        "video_archive_dir": config.get("video_archive_dir"),
        "video_archive_ok": video_archive_ok,
        "kb_index_enabled": kb_index_ok,
        "hints": hints if not configured else [],
        "_migration_note": config.get("_migration_note"),
        "_migration_warning": config.get("_migration_warning"),
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

        # 处理 kb_index 特殊字段（JSON 对象）
        if key == "kb_index":
            try:
                kb_config = json.loads(value)
                config[key] = kb_config
            except json.JSONDecodeError:
                print(json.dumps({
                    "ok": False,
                    "error": "kb_index 必须是 JSON 对象格式，例如: '{\"enabled\": true}'",
                }, ensure_ascii=False))
                return 1
        else:
            config[key] = value

        save_config(config)

        print(json.dumps({
            "ok": True,
            "action": "updated",
            "key": key,
            "value": config[key],
            "config_path": str(get_config_path()),
        }, ensure_ascii=False))
        return 0

    # 模式 2：--setup 交互式引导
    if args and args[0] == "--setup":
        config = load_config()

        # 首先尝试迁移 KB Graph 配置
        config = migrate_kb_graph_config(config)

        print("🔧 Link Archivist 配置向导")
        print(f"   配置文件：{get_config_path()}\n")

        # 显示迁移信息（如果有）
        if config.get("_migration_note"):
            print(f"ℹ️  {config['_migration_note']}\n")
        if config.get("_migration_warning"):
            print(f"⚠️  {config['_migration_warning']}\n")

        for key, meta in CONFIG_FIELDS.items():
            # 跳过复杂的 kb_index 配置
            if key == "kb_index":
                continue

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

        # 设置默认的 kb_index 配置
        if "kb_index" not in config:
            config["kb_index"] = {
                "enabled": True,
                "query_mode": "keyword",
                "auto_update": True,
                "embeddings_enabled": False,
            }

        save_config(config)
        print("✅ 配置已保存")
        result = check_config(config)
        print(json.dumps(result, ensure_ascii=False))
        return 0

    # 模式 3：无参数 = 检查配置状态
    config = load_config()

    # 自动迁移（静默，不影响正常流程）
    config = migrate_kb_graph_config(config)

    result = check_config(config)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
