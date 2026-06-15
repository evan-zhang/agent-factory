#!/bin/bash
# start-phase.sh — 执行某个具体阶段
# 用法：start-phase.sh <case-code> <gate-name> <mode>
# 这是 orchestrator-resume.sh 内部调用的子脚本
# 在真实生产环境，这里会调用对应的 sub-agent spawn 命令
# 当前实现：记录 + 输出占位（实际 sub-agent 由 orchestrator 调度）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# v0.10.0：跨平台 ISO 时间戳（macOS BSD date 老版本不支持 -Iseconds）
iso_now() {
  python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'))"
}
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"

CASE_CODE=$1
GATE=$2
MODE=${3:-auto}
PROJECT_DIR="$SKILL_ROOT/$CASE_CODE"
STATE_FILE="$PROJECT_DIR/state.json"

# 标记 in_progress
NOW=$(iso_now)
TMP=$(mktemp)
jq --arg g "$GATE" --arg ts "$NOW" \
  '.gateStatus[$g] = "in_progress" | .lastHeartbeat = $ts | .inProgressGate = $g' \
  "$STATE_FILE" > "$TMP" && mv "$TMP" "$STATE_FILE"

echo "▶️  启动阶段：$GATE (项目：$CASE_CODE, 模式：$MODE)"

# 这里在真实环境应该调用对应的 sub-agent
# 例如：
#   case "$GATE" in
#     phase-1)  spawn sub-agent discovery-agent "$CASE_CODE" ;;
#     gate-0)   spawn sub-agent gate-0-agent "$CASE_CODE" ;;
#     ...
#   esac
#
# 当前实现：占位输出，让 orchestrator 知道要执行什么

# ========== Phase 5.5 提示（实际执行由 AI 调 render_report.sh + sync） ==========
if [ "$GATE" = "phase-5-5-html" ]; then
  echo "📋 任务：执行 Phase 5.5 HTML 生成 + 知识库同步"
  echo ""
  echo "📌 执行步骤（AI 按顺序调用）："
  echo "   1. bash scripts/render_report.sh \"$PROJECT_DIR\"   # 生成 REPORT.html（内部调 preflight）"
  echo "   2. bash scripts/sync-to-knowledge-base.sh \"$PROJECT_DIR\"   # 上传到知识库"
  echo ""
  echo "⚠️  本脚本仅为占位提示，不执行实际渲染或上传。"
  echo "    AI 应按 SKILL.md / SOP Phase 5.5 指令自行调用上述脚本。"
fi

case "$GATE" in
  phase-1)        echo "📋 任务：执行 Phase 1 DISCOVERY（5次联网搜索 + 6篇参考文献）" ;;
  phase-2)        echo "📋 任务：执行 Phase 2 路由 Battle（确认技能编号如 A-1）" ;;
  one-pager)      echo "📋 任务：生成 One-pager（终局五问 + 结论卡）" ;;
  gate-0)         echo "📋 任务：执行 Gate 0 准入门（五必填 + 硬排除）" ;;
  gate-1)         echo "📋 任务：执行 Gate 1 前提门（海外注册 + III期数据）" ;;
  gate-2)         echo "📋 任务：执行 Gate 2 定调门（MoA + 临床证据）" ;;
  gate-3)         echo "📋 任务：执行 Gate 3 商业门（市场规模 + 竞争格局）" ;;
  gate-4)         echo "📋 任务：执行 Gate 4 支付门（财务回报测算）" ;;
  gate-5)         echo "📋 任务：执行 Gate 5 成本门（交易结构 + 供应协议）" ;;
  phase-4-battle) echo "📋 任务：执行 Phase 4 Battle 对抗审查" ;;
  phase-5-merge)  echo "📋 任务：执行 Phase 5 报告合并（生成 04-final-report.md）" ;;
  *)              echo "📋 任务：执行 $GATE" ;;
esac

echo ""
echo "💡 当前为占位实现。在生产环境，orchestrator 应："
echo "   1. spawn 对应 sub-agent"
echo "   2. 注入 state.json + EXT/ 资料 + 前缀"
echo "   3. sub-agent 完成后调用 mark-completed.sh $CASE_CODE $GATE"
