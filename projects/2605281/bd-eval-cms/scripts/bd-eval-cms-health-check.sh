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

# 3. 依赖 Skill（v0.7.0 起不再依赖 doc-viewer）
echo ""
echo "── 依赖 Skill ──"
for dep in multi-search; do
  if [ -f "$HOME/.openclaw/skills/$dep/SKILL.md" ] || [ -f "$HOME/.agents/skills/$dep/SKILL.md" ]; then
    check "$dep" "true"
  else
    check "$dep" "false" "安装 $dep Skill: 参考 bd-eval-cms SKILL.md 配置与授权章节"
  fi
done

# 4. OpenClaw 工具
echo ""
echo "── OpenClaw 工具 ──"
check "curl" "[ -x '$(command -v curl 2>/dev/null || echo /dev/null)' ]" "安装 curl"
check "python3" "[ -x '$(command -v python3 2>/dev/null || echo /dev/null)' ]" "安装 python3"
check "~/.openclaw 目录" "[ -d '$HOME/.openclaw' ]" "确认 OpenClaw 已安装"

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
