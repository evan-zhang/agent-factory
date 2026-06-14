#!/bin/bash
# preflight-phase.sh — Phase 5.5 HTML 生成前的 readiness 检查
#
# 用法：bash preflight-phase.sh <品种目录>
#
# 检查项：
#   1. state.json 存在且 JSON 有效
#   2. 04-final-report.md 存在且非空
#   3. 关键上游产物存在：01-discovery.md、One-pager、Gate 0~5、Battle 产物
#   4. state.json.gateStatus 存在，且 Phase 5.5 前置 gate 全部为 completed
#
# 环境变量：
#   BD_EVAL_CMS_SKIP_PREFLIGHT=1  跳过检查（仅限测试/历史回放）
#
# 退出码：
#   0 - 所有检查通过
#   1 - 检查失败，列出缺失项

set -euo pipefail

# 允许跳过检查（测试/历史回放用）
if [ "${BD_EVAL_CMS_SKIP_PREFLIGHT:-}" = "1" ]; then
  echo "⚠️  跳过 preflight 检查（BD_EVAL_CMS_SKIP_PREFLIGHT=1，仅限测试/历史回放）"
  exit 0
fi

CASE_DIR="${1:-}"

if [ -z "$CASE_DIR" ]; then
  echo "❌ preflight 错误：必须提供品种目录路径"
  exit 1
fi

if [ ! -d "$CASE_DIR" ]; then
  echo "❌ preflight 错误：品种目录不存在: $CASE_DIR"
  exit 1
fi

echo "=== Phase 5.5 Readiness Preflight ==="
echo "检查目录: $CASE_DIR"
echo ""

MISSING_ITEMS=()
JSON_VALID=true

# 1. 检查 state.json 存在且 JSON 有效
STATE_FILE="$CASE_DIR/state.json"
if [ ! -f "$STATE_FILE" ]; then
  MISSING_ITEMS+=("state.json（文件不存在）")
  JSON_VALID=false
else
  if ! jq empty "$STATE_FILE" 2>/dev/null; then
    MISSING_ITEMS+=("state.json（JSON 无效）")
    JSON_VALID=false
  else
    echo "✅ state.json 存在且 JSON 有效"
  fi
fi

# 2. 检查 04-final-report.md 存在且非空
FINAL_REPORT="$CASE_DIR/04-final-report.md"
if [ ! -f "$FINAL_REPORT" ]; then
  MISSING_ITEMS+=("04-final-report.md（文件不存在）")
else
  CONTENT_SIZE=$(wc -c < "$FINAL_REPORT" 2>/dev/null || echo 0)
  if [ "$CONTENT_SIZE" -lt 100 ]; then
    MISSING_ITEMS+=("04-final-report.md（文件内容过小: ${CONTENT_SIZE} 字符）")
  else
    echo "✅ 04-final-report.md 存在且非空 (${CONTENT_SIZE} 字符)"
  fi
fi

# 3. 检查关键上游产物
DISCOVERY="$CASE_DIR/01-discovery.md"
if [ ! -f "$DISCOVERY" ]; then
  MISSING_ITEMS+=("01-discovery.md（Phase 1 DISCOVERY 输出）")
else
  echo "✅ 01-discovery.md 存在"
fi

ONE_PAGER="$CASE_DIR/02-gate-by-chapter/One-pager.md"
if [ ! -f "$ONE_PAGER" ]; then
  MISSING_ITEMS+=("02-gate-by-chapter/One-pager.md（终局 One-pager）")
else
  echo "✅ 02-gate-by-chapter/One-pager.md 存在"
fi

GATE_DIR="$CASE_DIR/02-gate-by-chapter"
if [ ! -d "$GATE_DIR" ]; then
  MISSING_ITEMS+=("02-gate-by-chapter/（目录不存在）")
else
  # Phase 5.5 生产护栏：Gate 0~5 必须有物理产物。
  # 文件名允许 Gate-0-premise.md / Gate-0-precondition.md 等变体。
  for gate_num in 0 1 2 3 4 5; do
    if compgen -G "$GATE_DIR/Gate-${gate_num}-*.md" > /dev/null || [ -f "$GATE_DIR/Gate-${gate_num}.md" ]; then
      echo "✅ Gate-${gate_num} 产物存在"
    else
      MISSING_ITEMS+=("02-gate-by-chapter/Gate-${gate_num}-*.md（Gate ${gate_num} 产物缺失）")
    fi
  done
fi

# 检查 Battle 产物（03-battle-summary.md 或 battle/ROUTE-SELECTION-AUDITOR.md）
BATTLE_SUMMARY="$CASE_DIR/03-battle-summary.md"
ROUTE_AUDITOR="$CASE_DIR/battle/ROUTE-SELECTION-AUDITOR.md"
if [ ! -f "$BATTLE_SUMMARY" ] && [ ! -f "$ROUTE_AUDITOR" ]; then
  MISSING_ITEMS+=("Battle 产物（03-battle-summary.md 或 battle/ROUTE-SELECTION-AUDITOR.md 至少需要其一）")
else
  if [ -f "$BATTLE_SUMMARY" ]; then
    echo "✅ 03-battle-summary.md 存在"
  fi
  if [ -f "$ROUTE_AUDITOR" ]; then
    echo "✅ battle/ROUTE-SELECTION-AUDITOR.md 存在"
  fi
fi

# 4. gateStatus 必须存在，且前置 gate 全部为 completed
if [ "$JSON_VALID" = true ]; then
  HAS_GATE_STATUS=$(jq -r 'has("gateStatus")' "$STATE_FILE" 2>/dev/null)

  if [ "$HAS_GATE_STATUS" != "true" ]; then
    MISSING_ITEMS+=("state.json.gateStatus（缺失；生产渲染必须证明前置 gate 状态）")
  else
    echo "✅ state.json 包含 gateStatus 字段，进行前置 gate 状态检查"

    PRE_PHASE_GATES=("phase-1" "phase-2" "one-pager" "gate-0" "gate-1" "gate-2" "gate-3" "gate-4" "gate-5" "phase-4-battle" "phase-5-merge")
    INCOMPLETE_GATES=()

    for gate in "${PRE_PHASE_GATES[@]}"; do
      STATUS=$(jq -r ".gateStatus.\"$gate\" // \"__missing__\"" "$STATE_FILE" 2>/dev/null)
      if [ "$STATUS" != "completed" ]; then
        INCOMPLETE_GATES+=("$gate: $STATUS")
      fi
    done

    if [ ${#INCOMPLETE_GATES[@]} -gt 0 ]; then
      echo "❌ 发现未完成或缺失的前置 gate："
      for gate_status in "${INCOMPLETE_GATES[@]}"; do
        echo "   - $gate_status"
      done
      MISSING_ITEMS+=("前置 gate 状态检查：${INCOMPLETE_GATES[*]}")
    else
      echo "✅ 所有前置 gate 状态均为 completed"
    fi
  fi
fi

# 汇总结果
echo ""
if [ ${#MISSING_ITEMS[@]} -eq 0 ]; then
  echo "✅ Preflight 检查通过：所有关键产物齐全，可以进行 Phase 5.5 HTML 生成"
  exit 0
else
  echo "❌ Preflight 检查失败：发现 ${#MISSING_ITEMS[@]} 个缺失项，无法进行 Phase 5.5 HTML 生成"
  echo ""
  echo "缺失项清单："
  for item in "${MISSING_ITEMS[@]}"; do
    echo "  - $item"
  done
  echo ""
  echo "建议："
  echo "  1. 补全缺失的上游产物"
  echo "  2. 确保 state.json.gateStatus 中所有 Phase 5.5 前置 gate 均为 completed"
  echo "  3. 如为测试/历史回放，可设置 BD_EVAL_CMS_SKIP_PREFLIGHT=1 跳过检查"
  exit 1
fi
