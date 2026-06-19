#!/bin/bash
# output-metrics-footer 一键安装脚本
# 用法：curl -fsSL https://raw.githubusercontent.com/evan-zhang/agent-factory/main/projects/2606191/output-metrics-footer/install.sh | bash
#
# 功能：
#   1. sparse-checkout 取项目文件
#   2. 复制插件到 ~/.openclaw/extensions/output-metrics-footer/
#   3. 自动 patch openclaw.json（allow + entries + load.paths）
#   4. 提示重启 gateway

set -e

REPO="https://github.com/evan-zhang/agent-factory"
PROJECT_PATH="projects/2606191/output-metrics-footer"
EXT_DIR="$HOME/.openclaw/extensions/output-metrics-footer"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}📊 安装 output-metrics-footer 插件...${NC}"
echo ""

# --- 检查依赖 ---
if ! command -v git &>/dev/null; then
    echo -e "${RED}❌ 需要 git，请先安装。${NC}"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo -e "${RED}❌ 需要 python3，请先安装。${NC}"
    exit 1
fi

# --- 找 openclaw.json ---
OPENCLAW_JSON=""
for candidate in \
    "$HOME/.openclaw/gateways"/*/openclaw.json \
    "$HOME/.openclaw/openclaw.json"; do
    if [ -f "$candidate" ]; then
        OPENCLAW_JSON="$candidate"
        break
    fi
done

if [ -z "$OPENCLAW_JSON" ]; then
    echo -e "${RED}❌ 找不到 openclaw.json，请确认 OpenClaw 已安装。${NC}"
    echo "   搜索过：$HOME/.openclaw/gateways/*/openclaw.json"
    exit 1
fi

echo -e "${GREEN}✓ 检测到配置文件：$OPENCLAW_JSON${NC}"

# --- 1. sparse-checkout 取项目文件 ---
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo -e "${CYAN}↓ 拉取项目文件...${NC}"
git clone --depth 1 --sparse "$REPO" "$TEMP_DIR" --quiet
cd "$TEMP_DIR"
git sparse-checkout set "$PROJECT_PATH" --quiet 2>/dev/null || {
    # 老版本 git 不支持 set，用 init + checkout
    git sparse-checkout init --cone 2>/dev/null
    git sparse-checkout set "$PROJECT_PATH"
}

if [ ! -f "$PROJECT_PATH/src/index.ts" ]; then
    echo -e "${RED}❌ 拉取失败：找不到 src/index.ts${NC}"
    exit 1
fi

# --- 2. 复制插件到 extensions/ ---
echo -e "${CYAN}📁 复制插件到 $EXT_DIR/${NC}"
mkdir -p "$EXT_DIR"
cp "$PROJECT_PATH/src/"* "$EXT_DIR/"
cp "$PROJECT_PATH/uninstall.sh" "$EXT_DIR/" 2>/dev/null || true

echo -e "${GREEN}✓ 插件文件已就位${NC}"

# --- 3. patch openclaw.json ---
echo -e "${CYAN}⚙ 修改 openclaw.json...${NC}"

python3 << PYEOF
import json
import sys
import os
import shutil
from datetime import datetime

config_path = "$OPENCLAW_JSON"
ext_dir = "$EXT_DIR"
plugin_id = "openclaw-output-metrics-footer"

# 备份
backup = config_path + ".bak-footer-install-" + datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(config_path, backup)
print(f"  备份：{backup}")

with open(config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

# 确保 plugins 结构存在
plugins = cfg.setdefault("plugins", {})
allow = plugins.setdefault("allow", [])
entries = plugins.setdefault("entries", {})
load = plugins.setdefault("load", {})
paths = load.setdefault("paths", [])

changed = False

# 3a. allow
if plugin_id not in allow:
    allow.append(plugin_id)
    changed = True
    print(f"  ✓ 添加到 plugins.allow")

# 3b. entries
if plugin_id not in entries:
    entries[plugin_id] = {
        "enabled": True,
        "hooks": {"allowConversationAccess": True},
        "config": {
            "enabledChannels": [],
            "appendSubagents": True,
            "cacheMs": 120000,
            "quotaCacheMs": 60000,
            "contextReserveTokens": 40000
        }
    }
    changed = True
    print(f"  ✓ 添加到 plugins.entries（默认配置）")
else:
    # 确保已启用
    if not entries[plugin_id].get("enabled", False):
        entries[plugin_id]["enabled"] = True
        changed = True
        print(f"  ✓ 启用插件")
    else:
        print(f"  · entries 已存在且已启用，跳过")

# 3c. load.paths
if ext_dir not in paths:
    paths.append(ext_dir)
    changed = True
    print(f"  ✓ 添加到 plugins.load.paths")

if changed:
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"  ✓ 配置已写入")
else:
    print(f"  · 配置无需修改")

PYEOF

# --- 4. 完成 ---
echo ""
echo -e "${GREEN}✅ output-metrics-footer 安装完成！${NC}"
echo ""
echo -e "${YELLOW}请重启 gateway 使插件生效：${NC}"
echo -e "  openclaw gateway restart"
echo ""
echo -e "卸载命令：$EXT_DIR/uninstall.sh"
