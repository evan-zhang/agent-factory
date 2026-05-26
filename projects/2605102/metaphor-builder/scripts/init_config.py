#!/usr/bin/env python3
"""
metaphor-builder 配置初始化脚本

用法：
  python3 scripts/init_config.py --init    # 交互式配置 vault_path

配置文件：config.json（与 SKILL.md 同目录）
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(SKILL_DIR, "config.json")


def load_config():
    """加载现有配置，不存在则返回默认值"""
    defaults = {"vault_path": "", "html_style": "style-11"}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            defaults.update(data)
        except (json.JSONDecodeError, IOError):
            pass
    return defaults


def save_config(config):
    """保存配置到 config.json"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"✅ 配置已保存到 {CONFIG_PATH}")


def interactive_init():
    """交互式配置流程"""
    config = load_config()

    print("=" * 40)
    print("Metaphor Builder 配置初始化")
    print("=" * 40)
    print()

    # vault_path
    current_vault = config.get("vault_path", "")
    if current_vault:
        print(f"当前 vault_path: {current_vault}")
        print("直接回车保留当前值")
    else:
        print("vault_path: Obsessions 笔记所在的 Obsidian vault 路径")
        print("例如: /Users/you/ObsidianVault/Notes/Obsessions")
        print("留空则使用 Agent 上下文推荐模式（方式 B）")

    vault_input = input("\nvault_path: ").strip()
    if vault_input:
        # 展开用户目录
        vault_input = os.path.expanduser(vault_input)
        if not os.path.isdir(vault_input):
            print(f"⚠️  警告: {vault_input} 不存在或不是目录，仍会保存")
        config["vault_path"] = vault_input
    elif not vault_input and not current_vault:
        config["vault_path"] = ""

    # html_style
    print()
    current_style = config.get("html_style", "style-11")
    print(f"当前 html_style: {current_style}")
    print("直接回车保留当前值，或输入新值")

    style_input = input("html_style: ").strip()
    if style_input:
        config["html_style"] = style_input

    save_config(config)
    print()
    print("配置完成！")
    print(f"  vault_path: {config['vault_path'] or '(未设置，使用方式 B)'}")
    print(f"  html_style: {config['html_style']}")


def main():
    if "--init" in sys.argv:
        interactive_init()
    else:
        print("用法: python3 scripts/init_config.py --init")
        sys.exit(1)


if __name__ == "__main__":
    main()
