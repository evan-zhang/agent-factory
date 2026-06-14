#!/bin/bash
# bd-eval-cms 健康检测脚本
# 用法: bash bd-eval-cms-health-check.sh [--fix]

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FIX_MODE=false
[[ "${1:-}" == "--fix" ]] && FIX_MODE=true

PASS=0
FAIL=0
WARN=0

check() {
  local label="$1" ok="$2" fix_hint="${3:-}"
  # ok 是本脚本内部构造的测试表达式；必须用 eval 保留路径引号，避免带空格路径误判失败。
  if eval "$ok"; then
    echo "✅ $label"
    ((++PASS))
  else
    echo "❌ $label"
    ((++FAIL))
    if $FIX_MODE && [ -n "$fix_hint" ]; then
      echo "   💡 修复建议: $fix_hint"
    fi
  fi
}

warn() {
  local label="$1"
  echo "⚠️  $label"
  ((++WARN))
}

echo "════════════════════════════════════════"
echo "  bd-eval-cms 健康检测"
echo "════════════════════════════════════════"
echo ""

# 1. Skill 目录
echo "── Skill 安装 ──"
check "SKILL.md" "[ -f '$SKILL_DIR/SKILL.md' ]" "确认 bd-eval-cms Skill 目录完整"
check "SOP.md" "[ -f '$SKILL_DIR/references/SOP.md' ]" "确认 references/SOP.md 存在"
check "sub-agent-prompt-template" "[ -f '$SKILL_DIR/references/sub-agent-prompt-template.md' ]" "确认子Agent prompt模板存在"

# 2. 技能定义文件
echo ""
echo "── 22个技能定义文件 ──"
SKILL_FILES=(
  "00_CMS-投前评估技能体系总规则.md"
  "00_体系总规则增补条款_v1.1.md"
  "D-0_bd-evaluation-router.md"
  "D-1_pharma-bd-due-diligence.md"
  "D-2_pharma-market-landscape-report.md"
  "D-3_bd-project-one-pager.md"
  "A-0_bd-opportunity-intelligence.md"
  "A-1_bd-cn-overseas-unlisted.md"
  "A-2_bd-cn-agency-rights.md"
  "A-3_bd-cn-self-rd-pipeline.md"
  "A-4_bd-cn-biosimilar.md"
  "A-5_bd-cn-marketed-product-rights.md"
  "A-6_bd-cn-rx-to-otc.md"
  "A-7_bd-multi-target-screening.md"
  "A-8_bd-cn-generic-advanced.md"
  "B-1_medical-aesthetics-product-evaluator.md"
  "B-2_medical-aesthetics-portfolio-audit.md"
  "B-3_bd-cn-otc-consumer-health.md"
  "C-1_bd-intl-single-market.md"
  "C-2_bd-intl-multi-market.md"
  "C-3_bd-intl-portfolio-strategy.md"
  "E-1_bd-equity-biotech-due-diligence.md"
)

MISSING=0
for f in "${SKILL_FILES[@]}"; do
  if [ ! -f "$SKILL_DIR/references/$f" ]; then
    echo "❌ 缺失: $f"
    ((++MISSING))
    ((++FAIL))
  fi
done
if [ $MISSING -eq 0 ]; then
  echo "✅ 全部 $(echo "${SKILL_FILES[@]}" | wc -w | tr -d ' ') 个技能文件完整"
  ((++PASS))
fi

# 3. 依赖 Skill
# v0.9.4.2：bd-eval-cms 不再把 multi-search 作为硬依赖。
# Phase 1 搜索使用 OpenClaw 原生 web_search / web_fetch 工具；multi-search 若存在，仅可作为人工增强工具。
# v0.10.0：项目内置 scripts/search/ 子系统完全内化搜索能力
echo ""
echo "── 依赖 Skill ──"
echo "✅ 无硬依赖 Skill（multi-search 非必需）"
((++PASS))

# v0.10.0 新增：检查内置搜索子系统
echo ""
echo "── v0.10.0 内置搜索子系统 ──"
check "core_search.sh" "[ -x '$SKILL_DIR/scripts/search/core_search.sh' ]" "重新克隆 bd-eval-cms v0.10.0+"
check "source_ranker.sh" "[ -x '$SKILL_DIR/scripts/search/source_ranker.sh' ]" "重新克隆 bd-eval-cms v0.10.0+"
check "keyword_mapper.sh" "[ -x '$SKILL_DIR/scripts/search/keyword_mapper.sh' ]" "重新克隆 bd-eval-cms v0.10.0+"
check "field_extractor.sh" "[ -x '$SKILL_DIR/scripts/search/field_extractor.sh' ]" "重新克隆 bd-eval-cms v0.10.0+"
check "validate_gate_search.sh" "[ -x '$SKILL_DIR/scripts/search/validate_gate_search.sh' ]" "重新克隆 bd-eval-cms v0.10.0+"
check "source_priority.json" "[ -f '$SKILL_DIR/scripts/search/lib/source_priority.json' ]" "重新克隆 bd-eval-cms v0.10.0+"
check "quota.json" "[ -f '$SKILL_DIR/scripts/search/lib/quota.json' ]" "重新克隆 bd-eval-cms v0.10.0+"
check "extraction_prompts/" "[ -d '$SKILL_DIR/scripts/search/lib/extraction_prompts' ]" "重新克隆 bd-eval-cms v0.10.0+"
warn "multi-search：v0.10.0 不再使用 multi-search；如需人工增强可保留为辅助工具"

# 4. OpenClaw 工具
echo ""
echo "── OpenClaw 工具 ──"
check "curl" "[ -x '$(command -v curl 2>/dev/null || echo /dev/null)' ]" "安装 curl"
check "python3" "[ -x '$(command -v python3 2>/dev/null || echo /dev/null)' ]" "安装 python3"
check "~/.openclaw 目录" "[ -d '$HOME/.openclaw' ]" "确认 OpenClaw 已安装"

# 4b. 知识库同步配置（v0.10.2）
echo ""
echo "── 知识库同步配置 ──"
check "AppKey 环境变量" "[ -n \"${XG_BIZ_API_KEY:-${DOCVIEWER_KB_APPKEY:-}}\" ]" "配置 XG_BIZ_API_KEY（推荐）或 DOCVIEWER_KB_APPKEY 环境变量"
check "config.yaml knowledgeBase" "[ -f '$SKILL_DIR/config.yaml' ] && grep -q 'projectId' '$SKILL_DIR/config.yaml'" "确认 config.yaml 含 knowledgeBase.projectId"
check "sync-to-knowledge-base.sh" "[ -f '$SKILL_DIR/scripts/sync-to-knowledge-base.sh' ]" "确认知识库同步脚本存在"

# 5. 脚本
echo ""
echo "── 脚本 ──"
check "archive-links.sh" "[ -f '$SKILL_DIR/scripts/archive-links.sh' ]" "确认归档脚本存在"

# 汇总
echo ""
echo "════════════════════════════════════════"
echo "  ✅ $PASS  ⚠️  $WARN  ❌ $FAIL"
echo "════════════════════════════════════════"

if [ $FAIL -gt 0 ]; then
  echo ""
  if $FIX_MODE; then
    echo "运行 --fix 模式查看详细修复建议"
  else
    echo "💡 运行 bash $0 --fix 查看修复建议"
  fi
  exit 1
else
  echo "🎉 所有检查通过！bd-eval-cms Skill 就绪。"
  exit 0
fi
