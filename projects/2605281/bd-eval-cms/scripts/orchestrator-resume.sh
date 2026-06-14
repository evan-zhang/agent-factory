#!/bin/bash
# orchestrator-resume.sh — 智能续跑器
# 用法：
#   orchestrator-resume.sh --case-code=260611-EPIO [--mode=auto] [--rerun=Gate-3]
#   orchestrator-resume.sh --case-code=260611-EPIO --rerun=all
#   orchestrator-resume.sh --case-code=260611-EPIO --status  # 只看状态
#
# 设计：基于 state.json.gateStatus 字段 + lastHeartbeat 字段自动判断续跑起点
# 模式：auto = 全静默（商机池场景），semi = 每完成一阶段 push 确认

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"

# v0.10.0：跨平台 ISO 时间戳（macOS BSD date 老版本不支持 -Iseconds）
iso_now() {
  python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'))"
}

# 解析参数
CASE_CODE=""
MODE="auto"
RERUN_GATE=""
SHOW_STATUS=false
PROJECTS_ROOT="${SKILL_ROOT}"

for arg in "$@"; do
  case $arg in
    --case-code=*)  CASE_CODE="${arg#--case-code=}" ;;
    --mode=*)       MODE="${arg#--mode=}" ;;
    --rerun=*)      RERUN_GATE="${arg#--rerun=}" ;;
    --status)       SHOW_STATUS=true ;;
    --projects-root=*) PROJECTS_ROOT="${arg#--projects-root=}" ;;
    *) echo "❌ 未知参数：$arg" >&2; exit 1 ;;
  esac
done

if [ -z "$CASE_CODE" ]; then
  echo "❌ 必须提供 --case-code"
  echo "用法：orchestrator-resume.sh --case-code=260611-EPIO [--mode=auto] [--rerun=Gate-3]"
  exit 1
fi

PROJECT_DIR="$PROJECTS_ROOT/$CASE_CODE"
STATE_FILE="$PROJECT_DIR/state.json"

if [ ! -d "$PROJECT_DIR" ]; then
  # 目录名不等于 caseCode，扫描 state.json 查找 caseCode 对应的目录
  for d in "$PROJECTS_ROOT"/*/; do
    [ -d "$d" ] || continue
    if [ -f "$d/state.json" ]; then
      _code=$(jq -r '.caseCode // empty' "$d/state.json" 2>/dev/null)
      if [ "$_code" = "$CASE_CODE" ]; then
        PROJECT_DIR="$d"
        STATE_FILE="$d/state.json"
        break
      fi
    fi
  done
fi

if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ 项目不存在：$CASE_CODE"
  echo "💡 请先在商机池创建项目目录：$PROJECTS_ROOT/<项目名>/"
  echo "   或在现有项目的 state.json 中设置 caseCode=\"$CASE_CODE\""
  exit 1
fi

if [ ! -f "$STATE_FILE" ]; then
  STATE_FILE="$PROJECT_DIR/state.json"
fi

# 更新 heartbeat（任何时刻访问都更新）
update_heartbeat() {
  if [ -f "$STATE_FILE" ]; then
    local NOW=$(iso_now)
    local TMP=$(mktemp)
    jq --arg ts "$NOW" '.lastHeartbeat = $ts' "$STATE_FILE" > "$TMP" && mv "$TMP" "$STATE_FILE"
  fi
}

# 标记 gate 状态
mark_gate() {
  local gate=$1
  local status=$2
  # v0.10.0：状态为 completed 时，强制验证搜索证据
  if [ "$status" = "completed" ]; then
    if ! verify_search_evidence "$gate"; then
      echo "❌ mark_gate $gate=completed 被拒绝：搜索证据校验失败" >&2
      return 1
    fi
  fi
  local TMP=$(mktemp)
  jq --arg g "$gate" --arg s "$status" '.gateStatus[$g] = $s' "$STATE_FILE" > "$TMP" && mv "$TMP" "$STATE_FILE"
}

# v0.10.0 新增：标记 completed 前先校验搜索证据
# 返回 0 = 通过 / 1 = 证据不足
# 用法：verify_search_evidence <gate>
verify_search_evidence() {
  local gate=$1
  # 适用 Gate 列表：gate-1 ~ gate-5 + phase-1/2/one-pager
  case "$gate" in
    gate-1|gate-2|gate-3|gate-4|gate-5|phase-1|phase-2|one-pager) ;;
    *) return 0 ;;  # 其他 Gate 不检查
  esac

  # case_dir = STATE_FILE 所在目录（作为唯一 case 目录源）
  local case_dir
  case_dir=$(dirname "$STATE_FILE")

  if [ ! -d "$case_dir" ]; then
    echo "❌ 搜索证据校验失败：case 目录不存在 $case_dir" >&2
    return 1
  fi

  local validator="$SCRIPT_DIR/search/validate_gate_search.sh"
  if [ ! -x "$validator" ]; then
    echo "❌ 搜索证据校验失败：验证脚本不存在或不可执行 $validator" >&2
    return 1
  fi

  "$validator" "$case_dir" "$gate"
}

# 标记 gate in_progress + 更新心跳
mark_in_progress() {
  local gate=$1
  local TMP=$(mktemp)
  local NOW=$(iso_now)
  jq --arg g "$gate" --arg ts "$NOW" \
    '.gateStatus[$g] = "in_progress" | .lastHeartbeat = $ts | .inProgressGate = $g' \
    "$STATE_FILE" > "$TMP" && mv "$TMP" "$STATE_FILE"
}

# 找第一个非 completed 的 gate
find_resume_point() {
  local order=(
    "phase-1"
    "phase-2"
    "one-pager"
    "gate-0"
    "gate-1"
    "gate-2"
    "gate-3"
    "gate-4"
    "gate-5"
    "phase-4-battle"
    "phase-5-merge"
    "phase-5-5-html"
  )
  for g in "${order[@]}"; do
    local s=$(jq -r ".gateStatus.\"$g\"" "$STATE_FILE" 2>/dev/null)
    if [ "$s" != "completed" ]; then
      echo "$g"
      return
    fi
  done
}

# 报告当前状态
if $SHOW_STATUS; then
  if [ ! -f "$STATE_FILE" ]; then
    echo "📋 项目：$CASE_CODE（state.json 不存在 → 全量启动）"
    exit 0
  fi
  echo "📋 项目：$CASE_CODE"
  echo "  Phase：$(jq -r '.phase' $STATE_FILE)"
  echo "  当前进度："
  jq -r '.gateStatus | to_entries[] | "    \(if .key == .key then .key else .key end): \(.value)"' "$STATE_FILE" | sort
  echo "  Heartbeat：$(jq -r '.lastHeartbeat' $STATE_FILE)"
  echo "  报告链接：$(jq -r '.reportHtmlUrl // "（未生成）"' $STATE_FILE)"
  exit 0
fi

# 模式 0：--rerun=all 强制全量重跑
if [ "$RERUN_GATE" = "all" ]; then
  echo "🔄 全量重跑：$CASE_CODE"
  rm -f "$STATE_FILE"
  RERUN_GATE=""
fi

# 模式 1：state.json 不存在 → 全量启动
if [ ! -f "$STATE_FILE" ]; then
  echo "🆕 新项目，全量启动：$CASE_CODE"
  exec "$SCRIPT_DIR/start-phase.sh" "$CASE_CODE" "phase-1" "$MODE"
fi

# 模式 2：--rerun=Gate-X 显式重跑
if [ -n "$RERUN_GATE" ]; then
  # 规范化 gate 名：小写、kebab-case
  RERUN_GATE=$(echo "$RERUN_GATE" | tr '[:upper:]' '[:lower:]' | sed 's/_/-/g')
  echo "🔄 显式重跑：$RERUN_GATE"
  mark_gate "$RERUN_GATE" "pending"
  # 重跑该 Gate 之后的下游也置 pending（强制重新跑完整链路）
  case "$RERUN_GATE" in
    phase-1)   for g in phase-2 one-pager gate-0 gate-1 gate-2 gate-3 gate-4 gate-5 phase-4-battle phase-5-merge phase-5-5-html; do mark_gate "$g" "pending"; done ;;
    phase-2)   for g in one-pager gate-0 gate-1 gate-2 gate-3 gate-4 gate-5 phase-4-battle phase-5-merge phase-5-5-html; do mark_gate "$g" "pending"; done ;;
    gate-0|gate-1|gate-2) for g in gate-3 gate-4 gate-5 phase-4-battle phase-5-merge phase-5-5-html; do mark_gate "$g" "pending"; done ;;
    gate-3)    for g in gate-4 gate-5 phase-4-battle phase-5-merge phase-5-5-html; do mark_gate "$g" "pending"; done ;;
    gate-4)    for g in gate-5 phase-4-battle phase-5-merge phase-5-5-html; do mark_gate "$g" "pending"; done ;;
    gate-5)    for g in phase-4-battle phase-5-merge phase-5-5-html; do mark_gate "$g" "pending"; done ;;
  esac
  exec "$SCRIPT_DIR/start-phase.sh" "$CASE_CODE" "$RERUN_GATE" "$MODE"
fi

# 模式 3：检查 in_progress 是否僵尸
IN_PROGRESS=$(jq -r '.gateStatus | to_entries[] | select(.value == "in_progress") | .key' "$STATE_FILE" | head -1)
if [ -n "$IN_PROGRESS" ]; then
  HEARTBEAT=$(jq -r '.lastHeartbeat' "$STATE_FILE")
  # 用 python 统一解析 ISO 时间戳（跨平台）
  HEARTBEAT_TS=$(python3 -c "
from datetime import datetime
import sys
try:
    ts = sys.argv[1].replace('Z', '+00:00')
    dt = datetime.fromisoformat(ts)
    print(int(dt.timestamp()))
except Exception:
    print(0)
" "$HEARTBEAT" 2>/dev/null)
  NOW=$(date +%s)
  DIFF=$((NOW - HEARTBEAT_TS))
  
  if [ $DIFF -gt 1800 ]; then
    echo "⚠️ 检测到僵尸：$IN_PROGRESS (heartbeat ${DIFF}s ago > 30min)"
    mark_gate "$IN_PROGRESS" "failed"
    IN_PROGRESS=""
  else
    echo "🔄 续跑：$IN_PROGRESS (heartbeat ${DIFF}s ago)"
    exec "$SCRIPT_DIR/start-phase.sh" "$CASE_CODE" "$IN_PROGRESS" "$MODE"
  fi
fi

# 模式 4：全部 completed → 报告已完成
RESUME=$(find_resume_point)
if [ -z "$RESUME" ]; then
  echo "✅ 报告已完成：$CASE_CODE"
  if [ "$MODE" = "semi" ]; then
    echo "📄 报告链接：$(jq -r '.reportHtmlUrl // "（未生成）"' $STATE_FILE)"
  fi
  exit 0
fi

# 模式 5：找第一个 pending → 续跑
echo "🔄 续跑：$RESUME"
exec "$SCRIPT_DIR/start-phase.sh" "$CASE_CODE" "$RESUME" "$MODE"
