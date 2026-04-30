#!/usr/bin/env python3
"""
vault-writer init_config.py
配置初始化、检测、路径验证。

用法：
  python3 scripts/init_config.py                  # 检查配置状态
  python3 scripts/init_config.py --init           # 交互式初始化（列出已有 vault 供选择）
  python3 scripts/init_config.py --verify-path <path>  # 验证目标路径安全性
"""

import argparse
import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path


def get_config_path() -> Path:
    """按环境自动选择配置文件路径。"""
    env = os.environ.get("OPENCLAW_ENV") or os.environ.get("HERMES_ENV")
    if env:
        return Path.home() / ".config" / "vault-writer-config.json"

    # OpenClaw 环境：检查 ~/.openclaw 是否存在
    openclaw_dir = Path.home() / ".openclaw"
    if openclaw_dir.exists():
        return openclaw_dir / "vault-writer-config.json"

    return Path.home() / ".config" / "vault-writer-config.json"


def load_config() -> dict | None:
    """加载已有配置，不存在返回 None。"""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_config(config: dict) -> None:
    """保存配置到文件。"""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(json.dumps({"ok": True, "config_path": str(config_path)}, ensure_ascii=False))


def discover_obsidian_vaults() -> list[dict]:
    """
    从 Obsidian 的 obsidian.json 发现已注册的 vault。
    仅 macOS 有效。返回 [{name, path}] 列表。
    """
    vaults = []

    if platform.system() != "Darwin":
        return vaults

    obsidian_config = (
        Path.home()
        / "Library"
        / "Application Support"
        / "obsidian"
        / "obsidian.json"
    )

    if not obsidian_config.exists():
        return vaults

    try:
        with open(obsidian_config, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return vaults

    raw_vaults = data.get("vaults", {})
    for _vault_id, vault_info in raw_vaults.items():
        vault_path = vault_info.get("path", "")
        if vault_path and Path(vault_path).is_dir():
            vault_name = Path(vault_path).name
            vaults.append({"name": vault_name, "path": vault_path})

    return vaults


def check_config() -> None:
    """检查当前配置状态，输出 JSON。"""
    config = load_config()
    if config is None:
        print(json.dumps({
            "ok": False,
            "error": "配置不存在，请运行 --init 初始化",
            "config_path": str(get_config_path()),
        }))
        return

    vault_path = config.get("vault_path", "")
    vault_dir = Path(vault_path) if vault_path else None

    if not vault_path:
        print(json.dumps({"ok": False, "error": "vault_path 未配置"}))
        return

    if not vault_dir.exists():
        print(json.dumps({
            "ok": False,
            "error": f"vault_path 指向的目录不存在：{vault_path}。请重新配置已有 vault。",
        }))
        return

    writable = os.access(vault_path, os.W_OK)
    print(json.dumps({
        "ok": True,
        "vault_path": vault_path,
        "writable": writable,
        "config": config,
    }, ensure_ascii=False))


def verify_path(target_path: str) -> None:
    """验证目标路径在 vault 内且安全。"""
    config = load_config()
    if config is None:
        print(json.dumps({"ok": False, "error": "配置不存在"}))
        return

    vault_path = Path(config["vault_path"]).resolve()
    resolved = Path(target_path).resolve()

    # 目录穿越检查：目标路径必须在 vault 内
    try:
        resolved.relative_to(vault_path)
    except ValueError:
        print(json.dumps({
            "ok": False,
            "error": f"目标路径不在 vault 内：{resolved}（vault: {vault_path}）",
        }))
        return

    print(json.dumps({
        "ok": True,
        "resolved": str(resolved),
        "vault_relative": str(resolved.relative_to(vault_path)),
    }))


def interactive_init() -> None:
    """
    交互式初始化配置。
    - 列出已有 Obsidian vault 供选择
    - 用户也可手动输入已有目录路径
    - 不创建新 vault
    """
    print("📋 正在发现已有的 Obsidian vault...")

    vaults = discover_obsidian_vaults()

    if vaults:
        print(f"\n发现 {len(vaults)} 个已有的 Obsidian vault：\n")
        for i, v in enumerate(vaults, 1):
            exists = "✅" if Path(v["path"]).exists() else "⚠️ (路径不存在)"
            print(f"  {i}. {v['name']}")
            print(f"     {v['path']}  {exists}")
        print(f"\n  0. 手动输入已有目录路径")
        print()
    else:
        print("\n未发现已注册的 Obsidian vault（非 macOS 或未安装 Obsidian）。")
        print("请手动输入已有的 vault 目录路径。\n")

    # 读取用户选择（通过 stdin，Agent 会传入选择）
    # 交互模式：从 stdin 读取
    if not sys.stdin.isatty():
        # 被管道/Agent 调用，读取 JSON 输入
        try:
            inp = json.load(sys.stdin)
            choice = inp.get("choice", "")
            manual_path = inp.get("path", "")
        except (json.JSONDecodeError, EOFError):
            print(json.dumps({"ok": False, "error": "无输入"}))
            return
    else:
        # 终端交互
        choice = input("\n请输入编号选择 vault（或输入 0 手动指定路径）：").strip()
        manual_path = ""

    # 解析选择
    selected_path = ""

    if choice == "0" or (not vaults and not choice):
        if manual_path:
            selected_path = manual_path
        else:
            prompt = "请输入已有 vault 目录的绝对路径："
            selected_path = input(prompt).strip() if sys.stdin.isatty() else manual_path
    elif choice.isdigit() and 1 <= int(choice) <= len(vaults):
        selected_path = vaults[int(choice) - 1]["path"]
    else:
        print(json.dumps({"ok": False, "error": f"无效选择：{choice}"}))
        return

    # 验证目录
    if not selected_path:
        print(json.dumps({"ok": False, "error": "未提供 vault 路径"}))
        return

    vault_dir = Path(selected_path).expanduser().resolve()

    if not vault_dir.exists():
        print(json.dumps({
            "ok": False,
            "error": f"目录不存在：{vault_dir}。vault-writer 不会创建新 vault，请在 Obsidian app 中先创建。",
        }))
        return

    if not vault_dir.is_dir():
        print(json.dumps({"ok": False, "error": f"路径不是目录：{vault_dir}"}))
        return

    if not os.access(str(vault_dir), os.W_OK):
        print(json.dumps({"ok": False, "error": f"目录不可写：{vault_dir}"}))
        return

    # 检查是否像 Obsidian vault（含 .obsidian 目录）
    has_obsidian_dir = (vault_dir / ".obsidian").is_dir()
    warning = ""
    if not has_obsidian_dir:
        warning = "该目录未检测到 .obsidian 文件夹，可能不是有效的 Obsidian vault，但仍可使用。"

    # 保存配置
    config = {
        "vault_path": str(vault_dir),
        "default_folder": "",
        "default_tags": ["agent-output"],
        "initialized_at": datetime.now().isoformat(),
    }

    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    result = {
        "ok": True,
        "vault_path": str(vault_dir),
        "config_path": str(config_path),
        "vault_detected": has_obsidian_dir,
    }
    if warning:
        result["warning"] = warning

    print(json.dumps(result, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="vault-writer 配置管理")
    parser.add_argument("--init", action="store_true", help="交互式初始化配置")
    parser.add_argument("--verify-path", type=str, help="验证目标路径安全性")
    args = parser.parse_args()

    if args.init:
        interactive_init()
    elif args.verify_path:
        verify_path(args.verify_path)
    else:
        check_config()


if __name__ == "__main__":
    main()
