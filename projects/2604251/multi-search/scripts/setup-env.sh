#!/bin/bash
# setup-env.sh — 多源搜索环境初始化 + 能力探测（兼容 OpenClaw / Hermes）
# 用途：配置 MiniMax web_search MCP + 探测采集工具链能力
# 项目：2604251 multi-search
#
# 支持运行时：
#   OpenClaw — 通过 mcporter CLI 管理 MCP
#   Hermes   — 通过 ~/.hermes/config.yaml 原生 MCP
#
# 参数：
#   --key <API Key>    MiniMax Token Plan API Key（优先级最高）
#   --host <API Host>  API 地址（默认国内版 api.minimax.chat）
#
# 环境变量：
#   MINIMAX_API_KEY    MiniMax API Key（--key 优先）
#   MINIMAX_API_HOST   API 地址（--host 优先）

set -e

# === 参数解析 ===
MINIMAX_KEY="${MINIMAX_API_KEY:-}"
MINIMAX_HOST="${MINIMAX_API_HOST:-}"
while [ $# -gt 0 ]; do
    case "$1" in
        --key)
            if [ -n "$2" ]; then MINIMAX_KEY="$2"; shift 2; else shift; fi
            ;;
        --host)
            if [ -n "$2" ]; then MINIMAX_HOST="$2"; shift 2; else shift; fi
            ;;
        *)
            shift
            ;;
    esac
done

# 自动判断 API Host
if [ -z "$MINIMAX_HOST" ]; then
    MINIMAX_HOST="https://api.minimax.chat"
    if echo "$MINIMAX_KEY" | grep -q '^sk-cp-i-'; then
        MINIMAX_HOST="https://api.minimax.io"
    fi
fi

# === 运行时检测 ===
RUNTIME="unknown"
if [ -d "$HOME/.hermes" ] && [ -f "$HOME/.hermes/config.yaml" ]; then
    RUNTIME="hermes"
elif which mcporter >/dev/null 2>&1 || [ -f "$HOME/.mcporter/mcporter.json" ]; then
    RUNTIME="openclaw"
fi

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()   { echo "${GREEN}✅ $1${NC}"; }
warn() { echo "${YELLOW}⚠️  $1${NC}"; }
fail() { echo "${RED}❌ $1${NC}"; }
info() { echo "${BLUE}ℹ️  $1${NC}"; }

echo "========================================"
echo "  MiniMax Web Search 环境初始化"
echo "  项目 2604251 · multi-search"
echo "========================================"
echo ""
info "检测到运行时: $RUNTIME"
echo ""

# ============================================================
#  Step 1: 检查 uv/uvx（两个运行时都需要）
# ============================================================
echo "--- Step 1/5: 检查 uv/uvx ---"
UVX_PATH=$(which uvx 2>/dev/null || true)
if [ -z "$UVX_PATH" ]; then
    warn "uvx 未安装，正在安装 uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    UVX_PATH=$(which uvx 2>/dev/null || true)
    if [ -z "$UVX_PATH" ]; then
        fail "uvx 安装失败，请手动安装: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
fi
ok "uvx 已就绪: $UVX_PATH"

# ============================================================
#  Step 2: 运行时特定准备
# ============================================================
echo ""
echo "--- Step 2/5: 运行时准备 ---"

if [ "$RUNTIME" = "openclaw" ]; then
    # OpenClaw: 检查 mcporter
    MCPORTER_PATH=$(which mcporter 2>/dev/null || true)
    if [ -z "$MCPORTER_PATH" ]; then
        warn "mcporter 未安装，正在安装..."
        npm install -g mcporter 2>/dev/null || sudo npm install -g mcporter
        MCPORTER_PATH=$(which mcporter 2>/dev/null || true)
        if [ -z "$MCPORTER_PATH" ]; then
            fail "mcporter 安装失败，请手动安装: npm install -g mcporter"
            exit 1
        fi
    fi
    ok "OpenClaw: mcporter 已就绪: $MCPORTER_PATH"
    MCP_CONFIG="$HOME/.mcporter/mcporter.json"

elif [ "$RUNTIME" = "hermes" ]; then
    # Hermes: 检查 config.yaml
    HERMES_CONFIG="$HOME/.hermes/config.yaml"
    ok "Hermes: 配置文件 $HERMES_CONFIG"
    MCP_CONFIG="$HERMES_CONFIG"

else
    warn "未检测到 OpenClaw 或 Hermes 环境"
    echo "请安装其一后再运行："
    echo "  OpenClaw: https://github.com/openclaw/openclaw"
    echo "  Hermes:   https://github.com/NousResearch/hermes-agent"
    exit 1
fi

# ============================================================
#  Step 3: 检查 MiniMax MCP 配置
# ============================================================
echo ""
echo "--- Step 3/5: 检查 MiniMax MCP 配置 ---"
NEEDS_CONFIG=false

if [ "$RUNTIME" = "openclaw" ]; then
    # OpenClaw: 检查 mcporter.json
    if [ -f "$MCP_CONFIG" ]; then
        if grep -q '"minimax"' "$MCP_CONFIG" 2>/dev/null; then
            EXISTING_KEY=$(python3 -c "
import json, sys
try:
    with open('$MCP_CONFIG') as f:
        d = json.load(f)
    env = d.get('mcpServers', {}).get('minimax', {}).get('env', {})
    print(env.get('MINIMAX_API_KEY', ''))
except: print('')
" 2>/dev/null || echo "")
            if echo "$EXISTING_KEY" | grep -q '^sk-cp-'; then
                ok "MiniMax MCP 已配置 (Key: ${EXISTING_KEY:0:12}...)"
            else
                warn "MiniMax MCP 已配置但 Key 格式不正确"
                NEEDS_CONFIG=true
            fi
        else
            warn "mcporter 配置中未找到 minimax server"
            NEEDS_CONFIG=true
        fi
    else
        warn "mcporter 配置文件不存在: $MCP_CONFIG"
        NEEDS_CONFIG=true
    fi

elif [ "$RUNTIME" = "hermes" ]; then
    # Hermes: 检查 config.yaml 中的 minimax
    if grep -q 'minimax' "$MCP_CONFIG" 2>/dev/null; then
        ok "Hermes config.yaml 中已有 minimax 配置"
    else
        warn "Hermes config.yaml 中未找到 minimax"
        NEEDS_CONFIG=true
    fi
fi

# ============================================================
#  Step 4: 配置 MiniMax（如需要）
# ============================================================
if [ "$NEEDS_CONFIG" = true ]; then
    echo ""
    echo "--- Step 4/5: 配置 MiniMax MCP ---"
    echo ""
    echo "请提供 MiniMax Token Plan API Key。"
    echo "获取方式："
    echo "  1. 访问 https://platform.minimax.io/subscribe/token-plan"
    echo "  2. 订阅 Token Plan（Coding Plan）"
    echo "  3. 在控制台获取 API Key（格式：sk-cp-j-xxxx...）"
    echo ""

    if [ -z "$MINIMAX_KEY" ]; then
        echo -n "请输入 MiniMax Token Plan API Key: "
        read -r MINIMAX_KEY
    fi

    if [ -z "$MINIMAX_KEY" ]; then
        fail "未输入 API Key，初始化中止。"
        exit 1
    fi

    if ! echo "$MINIMAX_KEY" | grep -q '^sk-cp-'; then
        warn "Key 不是以 sk-cp- 开头。普通 MiniMax Key 不支持 web_search。"
        echo -n "确认要使用这个 Key 吗？(y/N): "
        read -r CONFIRM
        if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
            fail "初始化中止。"
            exit 1
        fi
    fi

    # 按运行时写入配置
    if [ "$RUNTIME" = "openclaw" ]; then
        mkdir -p "$(dirname "$MCP_CONFIG")"
        if [ -f "$MCP_CONFIG" ]; then
            python3 -c "
import json
with open('$MCP_CONFIG') as f:
    d = json.load(f)
if 'mcpServers' not in d:
    d['mcpServers'] = {}
d['mcpServers']['minimax'] = {
    'command': '$UVX_PATH',
    'args': ['minimax-coding-plan-mcp', '-y'],
    'env': {
        'MINIMAX_API_KEY': '$MINIMAX_KEY',
        'MINIMAX_API_HOST': '$MINIMAX_HOST'
    }
}
with open('$MCP_CONFIG', 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
print('ok')
"
        else
            cat > "$MCP_CONFIG" << EOF
{
  "mcpServers": {
    "minimax": {
      "command": "$UVX_PATH",
      "args": ["minimax-coding-plan-mcp", "-y"],
      "env": {
        "MINIMAX_API_KEY": "$MINIMAX_KEY",
        "MINIMAX_API_HOST": "$MINIMAX_HOST"
      }
    }
  }
}
EOF
        fi
        ok "MiniMax MCP 配置已写入: $MCP_CONFIG"

    elif [ "$RUNTIME" = "hermes" ]; then
        # Hermes: 写入 config.yaml
        python3 -c "
import yaml, os

config_path = '$MCP_CONFIG'
if os.path.exists(config_path):
    with open(config_path) as f:
        d = yaml.safe_load(f) or {}
else:
    d = {}

if 'mcp_servers' not in d:
    d['mcp_servers'] = {}

d['mcp_servers']['minimax'] = {
    'command': '$UVX_PATH',
    'args': ['minimax-coding-plan-mcp', '-y'],
    'env': {
        'MINIMAX_API_KEY': '$MINIMAX_KEY',
        'MINIMAX_API_HOST': '$MINIMAX_HOST'
    }
}

with open(config_path, 'w') as f:
    yaml.dump(d, f, default_flow_style=False, allow_unicode=True)
print('ok')
"
        ok "MiniMax MCP 配置已写入 Hermes config.yaml"
    fi
else
    echo ""
    echo "--- Step 4/5: MiniMax MCP 配置 — 已就绪，跳过 ---"
fi

# ============================================================
#  Step 5: 验证 MiniMax
# ============================================================
echo ""
echo "--- Step 5/5: 验证 MiniMax ---"

VERIFY_OK=false

if [ "$RUNTIME" = "openclaw" ]; then
    # OpenClaw: 用 mcporter 实际调用验证
    VERIFY_RESULT=$(mcporter call minimax.web_search query="测试搜索" 2>&1 || true)
    if echo "$VERIFY_RESULT" | grep -qi "error\|fail\|timeout\|not found\|login fail"; then
        if echo "$VERIFY_RESULT" | grep -q '"query_id"\|"search_results"\|"title"'; then
            VERIFY_OK=true
        fi
    else
        if [ -n "$VERIFY_RESULT" ]; then
            VERIFY_OK=true
        fi
    fi
    if [ "$VERIFY_OK" = true ]; then
        ok "MiniMax web_search 验证通过"
    else
        warn "MiniMax web_search 验证未通过（可能 Key 未生效或网络问题）"
        echo "  尝试: mcporter call minimax.web_search query='测试'"
    fi

elif [ "$RUNTIME" = "hermes" ]; then
    # Hermes: 检查 config.yaml 配置存在性（实际调用由运行时负责）
    if grep -q 'minimax' "$HERMES_CONFIG" 2>/dev/null; then
        VERIFY_OK=true
        ok "MiniMax MCP 已写入 Hermes config（运行时自动加载验证）"
    else
        warn "Hermes config.yaml 中未找到 minimax 配置"
        echo "  尝试: hermes chat -q '用 MiniMax 搜索 测试'"
    fi
fi

# ============================================================
#  Step 6: 环境能力探测
# ============================================================
echo ""
echo "--- Step 6/6: 环境能力探测 ---"
echo ""

SEARCH_MINIMAX=$VERIFY_OK
SEARCH_TAVILY=false
SEARCH_EXA=false
SEARCH_HERMES_WEB=false

# 搜索能力探测
if [ "$VERIFY_OK" = true ]; then
    ok "搜索：MiniMax web_search 已就绪"
fi

if [ -n "$TAVILY_API_KEY" ] || which openclaw-tavily-search >/dev/null 2>&1; then
    SEARCH_TAVILY=true
    ok "搜索回退：Tavily search 可用"
else
    echo "搜索回退：Tavily search 未配置（可选）"
fi

if [ "$RUNTIME" = "openclaw" ] && mcporter list 2>/dev/null | grep -q 'exa'; then
    SEARCH_EXA=true
    ok "搜索增强：Exa AI 可用"
elif [ "$RUNTIME" = "hermes" ] && grep -q 'exa' "$HERMES_CONFIG" 2>/dev/null; then
    SEARCH_EXA=true
    ok "搜索增强：Exa AI 可用"
else
    echo "搜索增强：Exa AI 未配置（可选）"
fi

# Hermes 内置搜索
if [ "$RUNTIME" = "hermes" ]; then
    if grep -q 'web_search\|web_extract' "$HERMES_CONFIG" 2>/dev/null || \
       grep -qi 'toolsets.*web' "$HERMES_CONFIG" 2>/dev/null; then
        SEARCH_HERMES_WEB=true
        ok "搜索内置：Hermes web 工具集可用"
    fi
fi

# 页面抓取能力探测
FETCH_TOOL="未知"
FETCH_JS=false

if [ "$RUNTIME" = "openclaw" ]; then
    # OpenClaw 的 web_fetch 不支持 JS 渲染，强制标记
    FETCH_TOOL="web_fetch（OpenClaw 内置）"
    FETCH_JS=false
    warn "抓取：$FETCH_TOOL 不支持 JS 渲染（静态页面可用，SPA/动态页面会失败）"
elif [ "$RUNTIME" = "hermes" ]; then
    FETCH_TOOL="web_extract / browser（Hermes 内置）"
    # 只有 Hermes 的 browser 工具才支持 JS 渲染
    if grep -q 'browser' "$HERMES_CONFIG" 2>/dev/null || \
       grep -qi 'toolsets.*browser' "$HERMES_CONFIG" 2>/dev/null; then
        FETCH_JS=true
        ok "抓取：Hermes 浏览器工具可用（支持 JS 渲染）"
    else
        FETCH_JS=false
        warn "抓取：Hermes 未检测到 browser 工具（JS 渲染不可用）"
    fi
fi

# ============================================================
#  输出汇总
# ============================================================
echo ""
echo "========================================"
ok "初始化完成！环境已就绪。"
echo "========================================"
echo ""
echo "运行时：$RUNTIME"
echo ""
echo "本次采集可用工具："
echo "  搜索：MiniMax web_search [$([ "$SEARCH_MINIMAX" = true ] && echo '已就绪' || echo '不可用')]"
if [ "$SEARCH_HERMES_WEB" = true ]; then
    echo "  搜索内置：Hermes web_search/web_extract [可用]"
fi
echo "  搜索回退：Tavily search [$([ "$SEARCH_TAVILY" = true ] && echo '可用' || echo '未配置')]"
echo "  搜索增强：Exa AI [$([ "$SEARCH_EXA" = true ] && echo '可用' || echo '未配置')]"
echo "  页面抓取：$FETCH_TOOL [$([ "$FETCH_JS" = true ] && echo '支持JS渲染' || echo '不支持JS渲染')]"
if [ "$FETCH_JS" = false ]; then
    echo "  已知限制：当前抓取工具不支持 JS 渲染，gov.cn 等动态页面可能抓取失败"
fi
echo ""
echo "工具选择策略："
echo "  搜索：优先 MiniMax → Tavily → Exa → 内置搜索 → 都不可用则停止"
echo "  抓取：使用运行时抓取工具 → 拿到空壳时在缺口表标注「JS渲染失败」"
if [ "$RUNTIME" = "hermes" ] && [ "$FETCH_JS" = true ]; then
    echo "  浏览器：Hermes 浏览器工具可处理 JS 渲染页面（优先用于 gov.cn）"
fi
echo ""
echo "现在可以使用执行提示词模板启动政策采集："
echo "  直接开始使用搜索能力"
