#!/bin/bash
# output-metrics-footer 卸载脚本
# 从 openclaw.json 移除插件注册 + 删除插件文件

set -e

EXT_DIR="$HOME/.openclaw/extensions/output-metrics-footer"
PLUGIN_ID="openclaw-output-metrics-footer"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🗑 卸载 output-metrics-footer...${NC}"
echo ""

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
    echo -e "${YELLOW}⚠ 找不到 openclaw.json，跳过配置清理${NC}"
else
    # --- patch openclaw.json ---
    python3 << PYEOF
import json
import shutil
from datetime import datetime

config_path = "$OPENCLAW_JSON"
plugin_id = "$PLUGIN_ID"
ext_dir = "$EXT_DIR"

# 备份
backup = config_path + ".bak-footer-uninstall-" + datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(config_path, backup)

with open(config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

plugins = cfg.get("plugins", {})
changed = False

# allow
allow = plugins.get("allow", [])
if plugin_id in allow:
    allow.remove(plugin_id)
    changed = True
    print("  ✓ 从 plugins.allow 移除")

# entries
entries = plugins.get("entries", {})
if plugin_id in entries:
    del entries[plugin_id]
    changed = True
    print("  ✓ 从 plugins.entries 移除")

# load.paths
load = plugins.get("load", {})
paths = load.get("paths", [])
if ext_dir in paths:
    paths.remove(ext_dir)
    changed = True
    print("  ✓ 从 plugins.load.paths 移除")

if changed:
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print("  ✓ 配置已写入")
else:
    print("  · 配置无需修改")

PYEOF
fi

# --- 删除插件文件 ---
if [ -d "$EXT_DIR" ]; then
    rm -rf "$EXT_DIR"
    echo -e "${GREEN}✓ 插件文件已删除${NC}"
else
    echo -e "${YELLOW}· 插件目录不存在，跳过${NC}"
fi

echo ""
echo -e "${GREEN}✅ 卸载完成${NC}"
echo -e "${YELLOW}请重启 gateway：${NC}"
echo -e "  openclaw gateway restart"
