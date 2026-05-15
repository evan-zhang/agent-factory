#!/bin/bash
#
# bd-eval-health-check.sh
# 健康检测 + 自动配置脚本
# 用法: bash bd-eval-health-check.sh [--fix]
#
# 检测内容:
# 1. 核心 Skill 是否完整安装
# 2. 关键文件是否存在
# 3. OpenClaw 工具是否可用
# 4. 外部 API 是否可达
# 5. 环境变量配置
#
# --fix 参数会自动修复可修复的问题
#

set -e

FIX_MODE=false
if [ "$1" = "--fix" ]; then
  FIX_MODE=true
fi

SKILLS_DIR="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}"
AGENTS_DIR="${HOME}/.agents/skills"
RESULT=0

# ─── 颜色 ───────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

pass()  { echo -e "${GREEN}✅ $1${NC}"; }
fail()  { echo -e "${RED}❌ $1${NC}"; RESULT=1; }
warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
info()  { echo -e "${BLUE}ℹ️  $1${NC}"; }

# ─── 检测1: Skill 安装 ──────────────────
check_skills() {
  echo ""
  echo "═══════════════════════════════════════"
  echo "  1/5  Skill 安装检测"
  echo "═══════════════════════════════════════"

  local skills=(
    "bd-eval:主Skill"
    "doc-viewer:Phase5.5报告生成"
    "multi-search:搜索基础设施"
    "tpr-framework:Battle规范(可选)"
  )

  for entry in "${skills[@]}"; do
    IFS=':' read -r name desc <<< "$entry"
    if [ -f "$SKILLS_DIR/$name/SKILL.md" ] || [ -f "$AGENTS_DIR/$name/SKILL.md" ]; then
      pass "$name ($desc) 已安装"
    else
      fail "$name ($desc) 未安装"
      info "执行: bash install.sh --target $SKILLS_DIR"
    fi
  done
}

# ─── 检测2: 关键文件 ───────────────────
check_files() {
  echo ""
  echo "═══════════════════════════════════════"
  echo "  2/5 关键文件检测"
  echo "═══════════════════════════════════════"

  local files=(
    "$SKILLS_DIR/bd-eval/references/SOP.md:SOP规范"
    "$SKILLS_DIR/bd-eval/references/bd_report_templates_full.md:7套BD评估模板(139KB)"
    "$SKILLS_DIR/bd-eval/references/sub-agent-prompt-template.md:子Agent Prompt模板"
    "$AGENTS_DIR/doc-viewer/templates/style-03/reference-amber.html:琥珀金HTML模板"
    "$AGENTS_DIR/doc-viewer/templates/style-03/color-themes/amber.yml:琥珀金配色"
    "$SKILLS_DIR/bd-eval/scripts/archive-links.sh:归档脚本"
  )

  for entry in "${files[@]}"; do
    IFS=':' read -r filepath desc <<< "$entry"
    if [ -f "$filepath" ]; then
      local size=$(wc -c < "$filepath" 2>/dev/null || echo 0)
      pass "$desc ($(($size/1024))KB)"
    else
      # 尝试另一个路径
      local alt=""
      case "$filepath" in
        "$SKILLS_DIR"*) alt="${filepath#$SKILLS_DIR}"; alt="$AGENTS_DIR$alt" ;;  esac
      if [ -n "$alt" ] && [ -f "$alt" ]; then
        local size=$(wc -c < "$alt" 2>/dev/null || echo 0)
        pass "$desc ($(($size/1024))KB) ✓"
      else
        fail "$desc 不存在: $filepath"
      fi
    fi
  done
}

# ─── 检测3: OpenClaw 工具 ───────────────
check_tools() {
  echo ""
  echo "═══════════════════════════════════════"
  echo "  3/5 OpenClaw 工具检测"
  echo "═══════════════════════════════════════"

  # 检测可用工具（通过检查是否有对应命令）
  local tools=(
    "curl:CURL命令"
    "python3:Python3环境"
  )

  for entry in "${tools[@]}"; do
    IFS=':' read -r cmd desc <<< "$entry"
    if command -v $cmd &> /dev/null; then
      pass "$desc: $(which $cmd)"
    else
      fail "$desc: $cmd 未找到"
    fi
  done

  # 检测 OpenClaw 配置
  if [ -d "$HOME/.openclaw" ]; then
    pass "OpenClaw 配置目录存在: ~/.openclaw"
  else
    fail "OpenClaw 配置目录不存在: ~/.openclaw"
  fi
}

# ─── 检测4: 外部 API ────────────────────
check_api() {
  echo ""
  echo "═══════════════════════════════════════"
  echo "  4/5 外部 API 连通性检测"
  echo "═══════════════════════════════════════"

  local apis=(
    "https://doc.20100706.xyz:报告上传服务"
    "https://api.mediportal.com.cn:BP系统API(内网)"
  )

  for entry in "${apis[@]}"; do
    IFS=':' read -r url desc <<< "$entry"
    if curl -s --max-time 5 -o /dev/null -w "%{http_code}" "$url" | grep -qE "^(200|301|302|400|401|403|404|500)"; then
      pass "$desc: 可达"
    else
      warn "$desc: 无法访问（${url}）"
      info "如需使用上传功能，请确保网络畅通"
    fi
  done
}

# ─── 检测5: 环境变量 ───────────────────
check_env() {
  echo ""
  echo "═══════════════════════════════════════"
  echo "  5/5 环境变量检测"
  echo "═══════════════════════════════════════"

  # BD 评估流程实际依赖的 Key
  local keys=(
    "MINIMAX_API_KEY:MiniMax模型（OpenClaw web_search 默认模型）"
    "TAVILY_API_KEY:Tavily搜索（multi-search fallback 降级链）"
    "EXA_API_KEY:Exa搜索（multi-search fallback 降级链）"
  )

  for entry in "${keys[@]}"; do
    IFS=':' read -r key desc <<< "$entry"
    if [ -n "$(eval echo \$$key)" ]; then
      pass "$key 已配置"
    else
      warn "$key 未配置（$desc）"
      info "建议：至少配置 MINIMAX_API_KEY，其他为可选降级"
    fi
  done
}

# ─── 自动修复 ───────────────────────────
auto_fix() {
  if [ "$FIX_MODE" = false ]; then
    return
  fi

  echo ""
  echo "═══════════════════════════════════════"
  echo "  自动修复指引"
  echo "═══════════════════════════════════════"

  # 1. Skill 安装缺失
  for name in bd-eval doc-viewer multi-search tpr-framework; do
    if [ ! -f "$SKILLS_DIR/$name/SKILL.md" ] && [ ! -f "$AGENTS_DIR/$name/SKILL.md" ]; then
      echo ""
      warn "缺少 Skill: $name"
      echo "  → cd <解压目录> && bash install.sh --target $SKILLS_DIR --force"
    fi
  done

  # 2. API Key 配置指引
  if [ -z "$MINIMAX_API_KEY" ]; then
    echo ""
    warn "MINIMAX_API_KEY 未配置（必须）"
    echo "  → OpenClaw 配置文件中设置，或联系管理员"
    echo "  → 配置路径: ~/.openclaw/config.json 或环境变量"
  fi

  if [ -z "$TAVILY_API_KEY" ]; then
    echo ""
    warn "TAVILY_API_KEY 未配置（搜索降级用）"
    echo "  → 申请: https://tavily.com → 免费账号 → 获取 API Key"
    echo "  → 写入 ~/.bashrc 或 ~/.zshrc:"
    echo "    export TAVILY_API_KEY='你的Key'"
  fi

  if [ -z "$EXA_API_KEY" ]; then
    echo ""
    warn "EXA_API_KEY 未配置（搜索降级用）"
    echo "  → 申请: https://exa.ai → 免费账号 → 获取 API Key"
    echo "  → 写入 ~/.bashrc 或 ~/.zshrc:"
    echo "    export EXA_API_KEY='你的Key'"
  fi

  # 3. 网络问题
  if ! curl -s --max-time 3 -o /dev/null https://doc.20100706.xyz 2>/dev/null; then
    echo ""
    warn "doc.20100706.xyz 无法访问"
    echo "  → 检查网络/代理设置，确保能访问外部网络"
  fi

  echo ""
  info "运行以下命令使环境变量生效:"
  echo "  source ~/.bashrc"
  echo "  source ~/.zshrc"
}

# ─── 汇总报告 ───────────────────────────
summary() {
  echo ""
  echo "═══════════════════════════════════════"
  echo "  检测结果汇总"
  echo "═══════════════════════════════════════"
  if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}🎉 所有检测通过！Skill 已就绪。${NC}"
    echo ""
    echo "使用方式:"
    echo '  用户: "BD评估：CG-0255、RHOFADE、门冬氨酸钙片"'
    echo ""
    echo "详细文档: $SKILLS_DIR/bd-eval/SKILL.md"
  else
    echo -e "${RED}⚠️  有检测项未通过，请修复后使用。${NC}"
    echo ""
    echo "运行以下命令查看修复指引:"
    echo ""
    echo "  bash $0 --fix"
    echo ""
    echo "常见问题:"
    echo "  • Skill 未安装    → bash install.sh --target ~/.openclaw/skills"
    echo "  • Key 未配置     → source ~/.bashrc 后重新检测"
    echo "  • 网络不通       → 检查代理设置"
    echo ""
    echo "检测详情请往上滚动查看 ⬆️"
  fi
}

# ─── 主流程 ─────────────────────────────
echo "╔═══════════════════════════════════════╗"
echo "║   BD 品种评估 Skill 健康检测        ║"
echo "║   检测时间: $(date '+%Y-%m-%d %H:%M')        ║"
echo "╚═══════════════════════════════════════╝"

check_skills
check_files
check_tools
check_api
check_env
auto_fix
summary

exit $RESULT
