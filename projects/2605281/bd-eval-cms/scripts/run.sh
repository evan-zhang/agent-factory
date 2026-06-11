#!/bin/bash
# run.sh — 入口脚本
# 用法：
#   run.sh <case-code>                          # 默认 auto 模式，自动判断续跑点
#   run.sh <case-code> --mode=semi              # 半自动（每完成一阶段 push 确认）
#   run.sh <case-code> --rerun=Gate-3           # 重跑指定 gate
#   run.sh <case-code> --rerun=all              # 强制全量重跑
#   run.sh <case-code> --status                 # 查看项目状态
#   run.sh --list                               # 列出商机池所有项目
#
# 设计原则：
#   - 入口 = caseCode（不是项目名）
#   - 默认模式 = auto（全静默，商机池场景）
#   - 找不到 caseCode → 明确报错，不会"猜"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"

# 解析参数
LIST=false
for arg in "$@"; do
  case $arg in
    --list) LIST=true ;;
  esac
done

# --list：列出所有项目
if $LIST; then
  echo "📋 商机池项目（$SKILL_ROOT/）："
  for d in "$SKILL_ROOT"/*/; do
    if [ -d "$d" ]; then
      name=$(basename "$d")
      # 跳过非项目目录
      case "$name" in
        scripts|templates|references|references_v1.4.bak|__pycache__|__init__|node_modules|.git) continue ;;
      esac
      if [ -f "$d/state.json" ]; then
        phase=$(jq -r '.phase // "unknown"' "$d/state.json" 2>/dev/null)
        heartbeat=$(jq -r '.lastHeartbeat // "无"' "$d/state.json" 2>/dev/null)
        echo "  ✅ $name (phase: $phase, heartbeat: $heartbeat)"
      else
        echo "  🆕 $name (state.json 不存在 → 全量启动)"
      fi
    fi
  done
  exit 0
fi

# 其他命令需要 case-code
CASE_CODE=$1
if [ -z "$CASE_CODE" ]; then
  echo "❌ 必须提供 case-code"
  echo ""
  echo "用法："
  echo "  run.sh <case-code>                        # 续跑或启动"
  echo "  run.sh <case-code> --rerun=Gate-3         # 重跑指定 gate"
  echo "  run.sh <case-code> --rerun=all            # 强制全量重跑"
  echo "  run.sh <case-code> --status               # 查看项目状态"
  echo "  run.sh --list                             # 列出商机池所有项目"
  echo ""
  echo "示例："
  echo "  run.sh 260611-EPIO"
  echo "  run.sh 260611-EPIO --rerun=Gate-3"
  echo "  run.sh 260611-EPIO --status"
  exit 1
fi

# 透传给 orchestrator-resume.sh
# 支持两种输入：caseCode（如 260611-EPIO）或项目名（如 Epioxa）
# 如果输入是项目名，自动查找 caseCode

# 扫描所有项目的 state.json，建立 名称→caseCode 映射
resolve_case_code() {
  local input=$1
  # 1. 如果直接以 caseCode 形式存在（YYMMDD-XXXX）
  if [ -d "$SKILL_ROOT/$input" ]; then
    echo "$input"
    return 0
  fi
  # 2. 扫描所有 state.json：name、displayName、目录名、caseCode 任一匹配
  for d in "$SKILL_ROOT"/*/; do
    [ -d "$d" ] || continue
    local dirname=$(basename "$d")
    if [ "$dirname" = "$input" ]; then
      # 目录名匹配：返回 state.json 里的 caseCode（如果有）
      if [ -f "$d/state.json" ]; then
        local code=$(jq -r '.caseCode // empty' "$d/state.json" 2>/dev/null)
        if [ -n "$code" ]; then
          echo "$code"
          return 0
        fi
      fi
      # state.json 没有 caseCode，使用目录名
      echo "$dirname"
      return 0
    fi
    if [ -f "$d/state.json" ]; then
      local code=$(jq -r '.caseCode // empty' "$d/state.json" 2>/dev/null)
      local name=$(jq -r '.name // empty' "$d/state.json" 2>/dev/null)
      local display=$(jq -r '.displayName // empty' "$d/state.json" 2>/dev/null)
      if [ "$code" = "$input" ] || [ "$name" = "$input" ] || [ "$display" = "$input" ]; then
        if [ -n "$code" ]; then
          echo "$code"
          return 0
        fi
        echo "$dirname"
        return 0
      fi
    fi
  done
  # 3. 找不到，返回原值（让后续逻辑报错）
  echo "$input"
}

REAL_CASE_CODE=$(resolve_case_code "$CASE_CODE")
if [ "$REAL_CASE_CODE" != "$CASE_CODE" ]; then
  echo "🔍 解析项目名 '$CASE_CODE' → caseCode '$REAL_CASE_CODE'"
fi

exec "$SCRIPT_DIR/orchestrator-resume.sh" --case-code="$REAL_CASE_CODE" --projects-root="$SKILL_ROOT" "${@:2}"
