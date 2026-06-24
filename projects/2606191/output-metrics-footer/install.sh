#!/bin/bash
# output-metrics-footer 一键安装脚本
# 用法：
#   curl -fsSL https://raw.githubusercontent.com/evan-zhang/agent-factory/main/projects/2606191/output-metrics-footer/install.sh | bash
#
# 选项（可叠加）：
#   --apply-recommended    非交互模式：自动应用推荐的压缩配置
#   --keep-current         非交互模式：保留当前压缩配置，不提示
#   （都不传 = 交互模式，会提示用户三选一）
#
# 功能：
#   1. sparse-checkout 取项目文件
#   2. 复制插件到 ~/.openclaw/extensions/output-metrics-footer/
#   3. 自动 patch openclaw.json（allow + entries + load.paths）
#   4. 检测压缩配置，提示用户是否应用推荐参数（详见 docs/compaction-config.md）
#   5. 提示重启 gateway

set -e

REPO="https://github.com/evan-zhang/agent-factory"
PROJECT_PATH="projects/2606191/output-metrics-footer"
EXT_DIR="$HOME/.openclaw/extensions/output-metrics-footer"

# 解析参数
APPLY_MODE="ask"  # ask | apply | keep
for arg in "$@"; do
    case "$arg" in
        --apply-recommended) APPLY_MODE="apply" ;;
        --keep-current) APPLY_MODE="keep" ;;
    esac
done

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
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
# 把文档也复制过去，方便用户随时查看
mkdir -p "$EXT_DIR/docs"
cp "$PROJECT_PATH/docs/"*.md "$EXT_DIR/docs/" 2>/dev/null || true
echo -e "${GREEN}✓ 插件文件已就位${NC}"

# --- 3. patch openclaw.json（插件本身的部分）---
echo -e "${CYAN}⚙ 修改 openclaw.json（注册插件）...${NC}"

python3 << PYEOF
import json, shutil
from datetime import datetime

config_path = "$OPENCLAW_JSON"
ext_dir = "$EXT_DIR"
plugin_id = "openclaw-output-metrics-footer"

backup = config_path + ".bak-footer-install-" + datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(config_path, backup)
print(f"  备份：{backup}")

with open(config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

plugins = cfg.setdefault("plugins", {})
allow = plugins.setdefault("allow", [])
entries = plugins.setdefault("entries", {})
load = plugins.setdefault("load", {})
paths = load.setdefault("paths", [])

changed = False
if plugin_id not in allow:
    allow.append(plugin_id); changed = True
    print(f"  ✓ 添加到 plugins.allow")

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
    if not entries[plugin_id].get("enabled", False):
        entries[plugin_id]["enabled"] = True; changed = True
        print(f"  ✓ 启用插件")
    else:
        print(f"  · entries 已存在且已启用，跳过")

if ext_dir not in paths:
    paths.append(ext_dir); changed = True
    print(f"  ✓ 添加到 plugins.load.paths")

if changed:
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"  ✓ 配置已写入")
else:
    print(f"  · 配置无需修改")
PYEOF

# --- 4. 检测压缩配置并按 APPLY_MODE 处理 ---
echo ""
echo -e "${CYAN}🔍 检测当前压缩配置...${NC}"

# 推荐配置（与 docs/compaction-config.md 保持一致）
RECOMMENDED=$(cat <<'EOF'
{
  "contextTokens": 256000,
  "compaction": {
    "mode": "safeguard",
    "reserveTokensFloor": 40000,
    "reserveTokens": 32768,
    "keepRecentTokens": 50000,
    "maxHistoryShare": 0.65,
    "memoryFlush": {
      "enabled": true,
      "softThresholdTokens": 30000
    },
    "midTurnPrecheck": {"enabled": true},
    "recentTurnsPreserve": 4,
    "notifyUser": false,
    "truncateAfterCompaction": true,
    "maxActiveTranscriptBytes": "30mb",
    "timeoutSeconds": 120,
    "postIndexSync": "async"
  }
}
EOF
)

# 第一步：检测差异
DIFF_REPORT=$(python3 <<PYEOF
import json
config_path = "$OPENCLAW_JSON"
rec = json.loads('''$RECOMMENDED''')

with open(config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

defaults = cfg.get("agents", {}).get("defaults", {})
cur_ctx = defaults.get("contextTokens")
cur_comp = defaults.get("compaction", {})

diffs = []

def cmp(path, cur, expected):
    if cur != expected:
        diffs.append((path, cur, expected))

cmp("agents.defaults.contextTokens", cur_ctx, rec["contextTokens"])
for k, v in rec["compaction"].items():
    if isinstance(v, dict):
        cur_sub = cur_comp.get(k, {})
        for kk, vv in v.items():
            cmp(f"agents.defaults.compaction.{k}.{kk}", cur_sub.get(kk), vv)
    else:
        cmp(f"agents.defaults.compaction.{k}", cur_comp.get(k), v)

if not diffs:
    print("MATCH")
else:
    for path, cur, exp in diffs:
        print(f"  · {path}: {cur} → {exp}")
PYEOF
)

if [ "$DIFF_REPORT" == "MATCH" ]; then
    echo -e "${GREEN}✓ 当前配置已与推荐配置完全一致，无需调整。${NC}"
    APPLY_MODE="skip"
else
    echo ""
    echo -e "${YELLOW}${BOLD}当前压缩配置与推荐配置存在差异：${NC}"
    echo -e "${DIFF_REPORT}"
    echo ""
    echo -e "${CYAN}💡 推荐配置的设计理念：${NC}"
    echo "  · 把 1M 标称模型钳制在 256k 实际甜蜜点，让模型更聪明、响应更快"
    echo "  · 配合 footer 显示真实使用率，而不是按 1M 算出的虚假"很轻松""
    echo "  · 详见 $EXT_DIR/docs/compaction-config.md"
    echo ""

    if [ "$APPLY_MODE" == "ask" ]; then
        # 检查是否是交互式终端
        if [ -t 0 ]; then
            echo -e "${BOLD}是否应用推荐配置？${NC}"
            echo "  [A] 应用推荐配置（自动备份当前配置）"
            echo "  [K] 保留当前配置，不修改"
            echo "  [D] 打开文档查看更多说明（不修改配置）"
            echo ""
            read -p "请选择 [A/K/D]: " choice
            case "$choice" in
                [Aa]*) APPLY_MODE="apply" ;;
                [Kk]*) APPLY_MODE="keep" ;;
                [Dd]*)
                    echo ""
                    echo -e "${CYAN}文档路径：${NC}$EXT_DIR/docs/compaction-config.md"
                    echo "查看后可通过以下命令重新应用："
                    echo "  bash $EXT_DIR/install.sh --apply-recommended"
                    APPLY_MODE="keep"
                    ;;
                *)
                    echo -e "${YELLOW}未识别选项，默认保留当前配置${NC}"
                    APPLY_MODE="keep"
                    ;;
            esac
        else
            echo -e "${YELLOW}⚠ 非交互模式（通过管道执行），默认保留当前配置${NC}"
            echo "  如需应用推荐配置，请直接运行："
            echo "    bash <(curl -fsSL https://raw.githubusercontent.com/evan-zhang/agent-factory/main/projects/2606191/output-metrics-footer/install.sh) --apply-recommended"
            APPLY_MODE="keep"
        fi
    fi
fi

# --- 5. 按选择应用 ---
if [ "$APPLY_MODE" == "apply" ]; then
    echo ""
    echo -e "${CYAN}⚙ 应用推荐压缩配置...${NC}"
    python3 <<PYEOF
import json, shutil
from datetime import datetime

config_path = "$OPENCLAW_JSON"
rec = json.loads('''$RECOMMENDED''')

backup = config_path + ".bak-compaction-" + datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(config_path, backup)
print(f"  备份：{backup}")

with open(config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

agents = cfg.setdefault("agents", {})
defaults = agents.setdefault("defaults", {})
defaults["contextTokens"] = rec["contextTokens"]
print(f"  ✓ contextTokens = {rec['contextTokens']}")

compaction = defaults.setdefault("compaction", {})
for k, v in rec["compaction"].items():
    if isinstance(v, dict):
        sub = compaction.setdefault(k, {})
        for kk, vv in v.items():
            sub[kk] = vv
    else:
        compaction[k] = v
print(f"  ✓ compaction 参数已更新（共 {len(rec['compaction'])} 项）")

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
print(f"  ✓ 配置已写入")
PYEOF
    echo -e "${GREEN}✓ 推荐配置已应用${NC}"
elif [ "$APPLY_MODE" == "keep" ]; then
    echo ""
    echo -e "${YELLOW}保留当前压缩配置不变。${NC}"
    echo "如改主意，随时执行："
    echo "  bash $EXT_DIR/install.sh --apply-recommended"
fi

# --- 6. 完成 ---
echo ""
echo -e "${GREEN}✅ output-metrics-footer 安装完成！${NC}"
echo ""
echo -e "${YELLOW}请重启 gateway 使插件生效：${NC}"
echo -e "  openclaw gateway restart"
echo ""
echo -e "文档：$EXT_DIR/docs/compaction-config.md"
echo -e "卸载：$EXT_DIR/uninstall.sh"
