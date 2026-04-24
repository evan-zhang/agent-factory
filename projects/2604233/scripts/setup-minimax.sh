#!/bin/bash
# setup-minimax.sh — MiniMax Web Search MCP 一键初始化
# 用途：检查并配置 MiniMax web_search 所需的 mcporter 环境
# 项目：2604233 七大政策采集 Skill Pack

set -e

# === 参数解析 ===
# 优先级：--key 参数 > MINIMAX_API_KEY 环境变量 > 交互式 read
# 优先级：--host 参数 > MINIMAX_API_HOST 环境变量 > 自动判断（国内版默认）
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

# 自动判断 API Host（国内版 vs 国际版）
# 国内版：https://api.minimax.chat（大多数中国用户）
# 国际版：https://api.minimax.io
if [ -z "$MINIMAX_HOST" ]; then
    MINIMAX_HOST="https://api.minimax.chat"
    # 如果 Key 以 sk-cp-i- 开头，使用国际版
    if echo "$MINIMAX_KEY" | grep -q '^sk-cp-i-'; then
        MINIMAX_HOST="https://api.minimax.io"
    fi
fi

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo "${GREEN}✅ $1${NC}"; }
warn() { echo "${YELLOW}⚠️  $1${NC}"; }
fail() { echo "${RED}❌ $1${NC}"; }

MCPORTER_CONFIG="$HOME/.mcporter/mcporter.json"

echo "========================================"
echo "  MiniMax Web Search 环境初始化"
echo "  项目 2604233 · 七大政策采集"
echo "========================================"
echo ""

# === Step 1: 检查 uv/uvx ===
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

# === Step 2: 检查 mcporter ===
echo ""
echo "--- Step 2/5: 检查 mcporter ---"
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
ok "mcporter 已就绪: $MCPORTER_PATH"

# === Step 3: 检查 mcporter 配置 ===
echo ""
echo "--- Step 3/5: 检查 mcporter 配置 ---"
NEEDS_CONFIG=false
# 注意：不在此处重置 MINIMAX_KEY，保留脚本头部 --key / 环境变量传入的值

if [ -f "$MCPORTER_CONFIG" ]; then
    # 检查是否已有 minimax 配置
    if grep -q '"minimax"' "$MCPORTER_CONFIG" 2>/dev/null; then
        # 检查 key 是否有效（非空且以 sk-cp- 开头）
        EXISTING_KEY=$(python3 -c "
import json, sys
try:
    with open('$MCPORTER_CONFIG') as f:
        d = json.load(f)
    env = d.get('mcpServers', {}).get('minimax', {}).get('env', {})
    print(env.get('MINIMAX_API_KEY', ''))
except: print('')
" 2>/dev/null || echo "")
        if echo "$EXISTING_KEY" | grep -q '^sk-cp-'; then
            ok "MiniMax MCP 已配置 (Key: ${EXISTING_KEY:0:12}...)"
        else
            warn "MiniMax MCP 已配置但 Key 格式不正确（需要 sk-cp- 开头的 Token Plan Key）"
            NEEDS_CONFIG=true
        fi
    else
        warn "mcporter 配置中未找到 minimax server"
        NEEDS_CONFIG=true
    fi
else
    warn "mcporter 配置文件不存在: $MCPORTER_CONFIG"
    NEEDS_CONFIG=true
fi

# === Step 4: 配置 MiniMax（如需要）===
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
    # 如果已有 key（来自 --key 参数或环境变量），跳过交互输入
    if [ -z "$MINIMAX_KEY" ]; then
        echo -n "请输入 MiniMax Token Plan API Key: "
        read -r MINIMAX_KEY
    fi
    
    if [ -z "$MINIMAX_KEY" ]; then
        fail "未输入 API Key，初始化中止。"
        echo "请重新运行此脚本并提供有效的 API Key。"
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
    
    # 写入或更新 mcporter 配置
    mkdir -p "$(dirname "$MCPORTER_CONFIG")"
    
    if [ -f "$MCPORTER_CONFIG" ]; then
        # 更新现有配置
        python3 -c "
import json
with open('$MCPORTER_CONFIG') as f:
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
with open('$MCPORTER_CONFIG', 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
print('ok')
"
    else
        # 创建新配置
        cat > "$MCPORTER_CONFIG" << EOF
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
    ok "MiniMax MCP 配置已写入: $MCPORTER_CONFIG"
else
    echo ""
    echo "--- Step 4/5: MiniMax MCP 配置 — 已就绪，跳过 ---"
fi

# === Step 5: 验证 ===
echo ""
echo "--- Step 5/5: 验证 MiniMax web_search ---"
VERIFY_RESULT=$(mcporter call minimax.web_search query="测试搜索" 2>&1 || true)
if echo "$VERIFY_RESULT" | grep -qi "error\|fail\|timeout\|not found\|login fail"; then
    # 二次确认：检查是否包含有效搜索结果（避免误判 error_code:0 等）
    if echo "$VERIFY_RESULT" | grep -q '"query_id"\|"search_results"\|"title"'; then
        ok "MiniMax web_search 调用成功（响应含已知错误关键词但结果有效）"
    else
        fail "MiniMax web_search 调用失败"
        echo "错误信息: $VERIFY_RESULT"
        echo ""
        echo "常见问题排查："
        echo "  1. Key 不是 Token Plan Key（需 sk-cp- 开头）"
        echo "  2. uvx 路径不正确（运行 which uvx 确认）"
        echo "  3. 网络问题（确认能访问 $MINIMAX_HOST）"
        exit 1
    fi
else
    ok "MiniMax web_search 调用成功"
fi

echo ""
echo "========================================"
ok "初始化完成！环境已就绪。"
echo "========================================"
echo ""
echo "现在可以使用执行提示词模板启动政策采集："
echo "  替换 {目标城市} 和 {年份/时间范围} 后发送给 Agent"
