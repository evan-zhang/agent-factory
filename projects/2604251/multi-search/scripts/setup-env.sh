#!/bin/bash
# setup-env.sh — 多源搜索全量安装向导（交互式）
# 用途：配置 MiniMax web_search MCP + 选装所有可选搜索/抓取工具
# 项目：2604251 multi-search
#
# 交互式运行：bash scripts/setup-env.sh
# 带 Key：bash scripts/setup-env.sh --key sk-cp-j-xxx
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
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ok()    { echo "${GREEN}✅ $1${NC}"; }
warn()  { echo "${YELLOW}⚠️  $1${NC}"; }
fail()  { echo "${RED}❌ $1${NC}"; }
info()  { echo "${BLUE}ℹ️  $1${NC}"; }
step()  { echo ""; echo "${CYAN}━━━ Step $1 ━━━${NC}"; }

echo "============================================"
echo "  多源搜索全量安装向导"
echo "  项目 2604251 · multi-search"
echo "============================================"
echo ""
info "检测到运行时: $RUNTIME"
echo ""

# ============================================================
#  Step 1: 检查 uv/uvx（两个运行时都需要）
# ============================================================
step "1/10: 检查 uv/uvx"
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
#  Step 2: 运行时特定准备（mcporter / Hermes config）
# ============================================================
step "2/10: 运行时准备"

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
#  Step 3: 检查 MiniMax MCP 配置（必装）
# ============================================================
step "3/10: 检查 MiniMax MCP 配置"
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
step "4/10: 配置 MiniMax MCP"
if [ "$NEEDS_CONFIG" = true ]; then
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
    ok "MiniMax MCP 已就绪，跳过配置"
fi

# ============================================================
#  Step 5: 验证 MiniMax（必装）
# ============================================================
step "5/10: 验证 MiniMax"

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
    # Hermes: 检查 config.yaml 配置存在性
    if grep -q 'minimax' "$HERMES_CONFIG" 2>/dev/null; then
        VERIFY_OK=true
        ok "MiniMax MCP 已写入 Hermes config（运行时自动加载验证）"
    else
        warn "Hermes config.yaml 中未找到 minimax 配置"
        echo "  尝试: hermes chat -q '用 MiniMax 搜索 测试'"
    fi
fi

SEARCH_MINIMAX=$VERIFY_OK

# ============================================================
#  Step 6: Tavily Search（可选）
# ============================================================
step "6/10: Tavily Search（可选）"

SEARCH_TAVILY=false
# 先检测是否已配置
TAVILY_ALREADY=false
if [ -n "$TAVILY_API_KEY" ]; then
    TAVILY_ALREADY=true
    SEARCH_TAVILY=true
    ok "Tavily API Key 已配置（TAVILY_API_KEY 环境变量）"
elif [ "$RUNTIME" = "openclaw" ] && mcporter list 2>/dev/null | grep -q 'tavily'; then
    TAVILY_ALREADY=true
    SEARCH_TAVILY=true
    ok "Tavily MCP 已在 mcporter 中注册"
elif [ "$RUNTIME" = "hermes" ] && grep -q 'tavily' "$HERMES_CONFIG" 2>/dev/null; then
    TAVILY_ALREADY=true
    SEARCH_TAVILY=true
    ok "Tavily 已在 Hermes config 中配置"
fi

if [ "$TAVILY_ALREADY" = false ]; then
    echo ""
    echo "Tavily Search 是可选搜索引擎，用于 MiniMax 搜索的回退。"
    echo "获取 API Key：https://app.tavily.com/home"
    echo ""
    echo -n "是否安装配置 Tavily Search？(y/N): "
    read -r INSTALL_TAVILY
    if [ "$INSTALL_TAVILY" = "y" ] || [ "$INSTALL_TAVILY" = "Y" ]; then
        echo -n "请输入 Tavily API Key: "
        read -r TAVILY_KEY
        if [ -n "$TAVILY_KEY" ]; then
            # 写入环境变量或 mcporter
            if [ "$RUNTIME" = "openclaw" ]; then
                echo ""
                info "Tavily 配置方式："
                echo "  方式 A（推荐）：将以下行添加到 shell profile (~/.zshrc / ~/.bashrc)"
                echo "    export TAVILY_API_KEY=\"$TAVILY_KEY\""
                echo ""
                echo "  方式 B：写入 mcporter.json（需 mcporter 支持自定义 MCP）"
                echo ""
                echo -n "使用方式 A（写入 profile）？(Y/n): "
                read -r USE_PROFILE
                if [ "$USE_PROFILE" != "n" ] && [ "$USE_PROFILE" != "N" ]; then
                    SHELL_PROFILE="$HOME/.zshrc"
                    if [ ! -f "$SHELL_PROFILE" ]; then
                        SHELL_PROFILE="$HOME/.bashrc"
                    fi
                    echo "export TAVILY_API_KEY=\"$TAVILY_KEY\"" >> "$SHELL_PROFILE"
                    ok "TAVILY_API_KEY 已写入 $SHELL_PROFILE"
                    export TAVILY_API_KEY="$TAVILY_KEY"
                    SEARCH_TAVILY=true
                else
                    warn "未写入配置，Tavily 未生效。请手动设置 TAVILY_API_KEY 环境变量。"
                fi
            else
                # Hermes: 写入 config.yaml
                export TAVILY_API_KEY="$TAVILY_KEY"
                SEARCH_TAVILY=true
                ok "TAVILY_API_KEY 已设置（当前会话生效）"
            fi
        else
            warn "未输入 API Key，Tavily 跳过"
        fi
    else
        info "Tavily Search 跳过"
    fi
fi

# ============================================================
#  Step 7: Exa AI（可选）
# ============================================================
step "7/10: Exa AI（可选）"

SEARCH_EXA=false
# 先检测是否已安装配置
EXA_ALREADY=false
if [ "$RUNTIME" = "openclaw" ] && mcporter list 2>/dev/null | grep -q 'exa'; then
    EXA_ALREADY=true
    SEARCH_EXA=true
    ok "Exa MCP 已在 mcporter 中注册"
elif [ "$RUNTIME" = "hermes" ] && grep -q 'exa' "$HERMES_CONFIG" 2>/dev/null; then
    EXA_ALREADY=true
    SEARCH_EXA=true
    ok "Exa 已在 Hermes config 中配置"
fi

if [ "$EXA_ALREADY" = false ]; then
    echo ""
    echo "Exa AI 是可选搜索增强引擎，支持 includeDomains 定向搜索。"
    echo "获取 API Key：https://dashboard.exa.ai/api-keys"
    echo ""
    echo -n "是否安装配置 Exa MCP？(y/N): "
    read -r INSTALL_EXA
    if [ "$INSTALL_EXA" = "y" ] || [ "$INSTALL_EXA" = "Y" ]; then
        echo -n "请输入 Exa API Key: "
        read -r EXA_KEY
        if [ -n "$EXA_KEY" ]; then
            if [ "$RUNTIME" = "openclaw" ]; then
                # 尝试用 mcporter 安装
                MCP_ADD_OK=false
                if command -v mcporter >/dev/null 2>&1; then
                    MCP_RESULT=$(mcporter add exa --key "$EXA_KEY" 2>&1 || true)
                    if echo "$MCP_RESULT" | grep -qi "success\|added\|ok\|done"; then
                        MCP_ADD_OK=true
                        SEARCH_EXA=true
                        ok "Exa MCP 已通过 mcporter 安装并注册"
                    fi
                fi
                if [ "$MCP_ADD_OK" = false ]; then
                    # 手动写入 mcporter.json
                    if [ -f "$MCP_CONFIG" ]; then
                        python3 -c "
import json
with open('$MCP_CONFIG') as f:
    d = json.load(f)
if 'mcpServers' not in d:
    d['mcpServers'] = {}
d['mcpServers']['exa'] = {
    'command': 'uvx',
    'args': ['mcp-exa', '-y'],
    'env': {
        'EXA_API_KEY': '$EXA_KEY'
    }
}
with open('$MCP_CONFIG', 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
print('ok')
" 2>/dev/null && {
                            SEARCH_EXA=true
                            ok "Exa MCP 配置已手动写入 mcporter.json"
                        }
                    fi
                fi
            elif [ "$RUNTIME" = "hermes" ]; then
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
d['mcp_servers']['exa'] = {
    'command': 'uvx',
    'args': ['mcp-exa', '-y'],
    'env': {
        'EXA_API_KEY': '$EXA_KEY'
    }
}
with open(config_path, 'w') as f:
    yaml.dump(d, f, default_flow_style=False, allow_unicode=True)
print('ok')
" 2>/dev/null && {
                    SEARCH_EXA=true
                    ok "Exa MCP 配置已写入 Hermes config.yaml"
                }
            fi
        else
            warn "未输入 API Key，Exa 跳过"
        fi
    else
        info "Exa AI 跳过"
    fi
fi

# ============================================================
#  Step 8: Jina Reader 探测（零安装，仅检测连通性）
# ============================================================
step "8/10: Jina Reader 探测（零安装）"

FETCH_JINA=false
JINA_TEST=$(curl -sL --max-time 10 "https://r.jina.ai/https://example.com" -o /dev/null -w '%{http_code}' 2>/dev/null || true)
if [ "$JINA_TEST" = "200" ]; then
    FETCH_JINA=true
    ok "Jina Reader 可用（远程 JS 渲染，零安装）"
else
    info "Jina Reader 不可用（网络不通或被墙）"
fi

# 同时探测 Hermes 内置 web 工具
SEARCH_HERMES_WEB=false
if [ "$RUNTIME" = "hermes" ]; then
    if grep -q 'web_search\|web_extract' "$HERMES_CONFIG" 2>/dev/null || \
       grep -qi 'toolsets.*web' "$HERMES_CONFIG" 2>/dev/null; then
        SEARCH_HERMES_WEB=true
        ok "Hermes web 工具集可用"
    fi
fi

# ============================================================
#  Step 9: Crawl4AI（可选）
# ============================================================
step "9/10: Crawl4AI（可选）"

FETCH_CRAWL4AI=false
# 先检测是否已安装
if which crwl >/dev/null 2>&1 || python3 -c "import crawl4ai" 2>/dev/null; then
    FETCH_CRAWL4AI=true
    ok "Crawl4AI 已安装"
else
    echo ""
    echo "Crawl4AI 是本地 JS 渲染引擎，可用 Python 命令按需抓取。"
    echo "需要 Python 3.9+ 环境。"
    echo ""
    echo -n "是否安装 Crawl4AI？(y/N): "
    read -r INSTALL_CRAWL4AI
    if [ "$INSTALL_CRAWL4AI" = "y" ] || [ "$INSTALL_CRAWL4AI" = "Y" ]; then
        echo ""
        info "正在安装 Crawl4AI（pip install -U crawl4ai）..."
        PIP_RESULT=$(pip install -U crawl4ai 2>&1 || true)
        if echo "$PIP_RESULT" | grep -qi "successfully installed\|Requirement already satisfied"; then
            echo ""
            info "正在运行 crawl4ai-setup..."
            SETUP_RESULT=$(crawl4ai-setup 2>&1 || true)
            if echo "$SETUP_RESULT" | grep -qi "success\|done\|already\|OK"; then
                FETCH_CRAWL4AI=true
                ok "Crawl4AI 安装完成"
            else
                warn "crawl4ai-setup 可能未完全成功"
                echo "$SETUP_RESULT"
                # 即使 setup 不完全成功，crawl4ai 的 Python 包可能仍可用
                if python3 -c "import crawl4ai" 2>/dev/null; then
                    FETCH_CRAWL4AI=true
                    ok "Crawl4AI Python 模块可用"
                fi
            fi
        else
            fail "Crawl4AI 安装失败"
            echo "$PIP_RESULT"
        fi
    else
        info "Crawl4AI 跳过"
    fi
fi

# ============================================================
#  Step 10: Scrapling（可选）
# ============================================================
step "10/10: Scrapling（可选）"

FETCH_SCRAPLING=false
# 先检测是否已安装
if python3 -c "import scrapling" 2>/dev/null; then
    FETCH_SCRAPLING=true
    ok "Scrapling 已安装"
else
    echo ""
    echo "Scrapling 是反爬抓取引擎，可绕过 Cloudflare 等防护。"
    echo "需要 Python 3.9+ 环境。"
    echo ""
    echo -n "是否安装 Scrapling？(y/N): "
    read -r INSTALL_SCRAPLING
    if [ "$INSTALL_SCRAPLING" = "y" ] || [ "$INSTALL_SCRAPLING" = "Y" ]; then
        echo ""
        info "正在安装 Scrapling（pip install scrapling）..."
        PIP_RESULT=$(pip install scrapling 2>&1 || true)
        if echo "$PIP_RESULT" | grep -qi "successfully installed\|Requirement already satisfied"; then
            FETCH_SCRAPLING=true
            ok "Scrapling 安装完成"
        else
            fail "Scrapling 安装失败"
            echo "$PIP_RESULT"
        fi
    else
        info "Scrapling 跳过"
    fi
fi

# ============================================================
#  内置工具能力判定
# ============================================================
FETCH_TOOL="未知"
FETCH_JS=false

if [ "$RUNTIME" = "openclaw" ]; then
    FETCH_TOOL="web_fetch（OpenClaw 内置）"
    FETCH_JS=false
elif [ "$RUNTIME" = "hermes" ]; then
    FETCH_TOOL="browser（Hermes 内置）"
    if grep -q 'browser' "$HERMES_CONFIG" 2>/dev/null || \
       grep -qi 'toolsets.*browser' "$HERMES_CONFIG" 2>/dev/null; then
        FETCH_JS=true
    fi
fi

# ============================================================
#  输出汇总
# ============================================================
echo ""
echo "============================================"
echo "  📋 组件状态汇总"
echo "============================================"
echo ""

echo "【搜索引擎】"
echo "  MiniMax web_search:  $([ "$SEARCH_MINIMAX" = true ] && echo "${GREEN}已配置${NC}" || echo "${RED}未配置${NC}")"
echo "  Tavily Search:       $([ "$SEARCH_TAVILY" = true ] && echo "${GREEN}已配置${NC}" || echo "${YELLOW}未配置（跳过）${NC}")"
echo "  Exa AI:              $([ "$SEARCH_EXA" = true ] && echo "${GREEN}已配置${NC}" || echo "${YELLOW}未配置（跳过）${NC}")"

if [ "$SEARCH_HERMES_WEB" = true ]; then
    echo "  Hermes web 工具集:   ${GREEN}可用${NC}"
fi

echo ""
echo "【抓取工具】"
echo "  内置:                $FETCH_TOOL $([ "$FETCH_JS" = true ] && echo '（支持JS渲染）' || echo '（不支持JS渲染）')"
echo "  Jina Reader:         $([ "$FETCH_JINA" = true ] && echo "${GREEN}可用${NC}" || echo "${YELLOW}不可用${NC}")（远程渲染，零安装）"
echo "  Crawl4AI:            $([ "$FETCH_CRAWL4AI" = true ] && echo "${GREEN}已安装${NC}" || echo "${YELLOW}未安装（跳过）${NC}")"
echo "  Scrapling:           $([ "$FETCH_SCRAPLING" = true ] && echo "${GREEN}已安装${NC}" || echo "${YELLOW}未安装（跳过）${NC}")"
echo "  curl:                兜底（始终可用）"

echo ""
echo "============================================"
if [ "$SEARCH_MINIMAX" = true ]; then
    ok "配置完成！核心搜索已就绪。"
else
    warn "配置未完成。请检查上述标记的未配置项。"
fi
echo "============================================"
echo ""
echo "降级链执行顺序："
echo "  搜索：MiniMax → Tavily → Exa → 停止"
echo "  抓取：内置工具 → Jina Reader → Crawl4AI/Scrapling → curl → 标注缺口"
echo ""
echo "如需重新运行：bash scripts/setup-env.sh"
