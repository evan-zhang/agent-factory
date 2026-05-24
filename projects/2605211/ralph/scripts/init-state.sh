#!/usr/bin/env bash
# init-state.sh — 初始化 Ralph Loop state.json
# v3.1.0: 新增 guided 引导执行模式
set -euo pipefail

STATE_FILE=""
TASK=""
GOAL=""
MODE="executor"
VERIFY_FILE=""
CHECKLIST=()

usage() {
  cat <<'EOF'
用法: init-state.sh <state-file> [选项]

参数:
  <state-file>           state.json 输出路径

选项:
  --task <desc>          一句话任务描述
  --goal <conditions>    完成条件原文
  --mode <mode>          运行模式: executor（默认）| autonomous | guided
  --checklist <item>     检查项（可多次使用，执行者模式必填）
  --verify <file>        verify.sh 验证器路径（写入 meta.verify）

示例（引导执行模式 — 推荐）:
  init-state.sh /tmp/state.json \
    --task "建设 A05 物流流向库" \
    --goal "A05 数据完整且 golden test 通过" \
    --mode guided

示例（执行者模式）:
  init-state.sh /tmp/state.json \
    --task "建设 A05 物流流向库" \
    --goal "A05 数据完整且 golden test 通过" \
    --mode executor \
    --checklist "data/A05-物流流向库/ 目录存在" \
    --checklist "scripts/test_a05_golden.py exit 0"

示例（自主者模式）:
  init-state.sh /tmp/state.json \
    --task "完成全部本体库建设" \
    --goal "20 个本体库全部建设完成，golden test 通过" \
    --mode autonomous
EOF
  exit 1
}

# 第一个位置参数是 state file
[[ $# -lt 1 ]] && usage
[[ "$1" == "-h" || "$1" == "--help" ]] && usage
STATE_FILE="$1"
shift

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task)      TASK="$2"; shift 2 ;;
    --goal)      GOAL="$2"; shift 2 ;;
    --mode)      MODE="$2"; shift 2 ;;
    --checklist) CHECKLIST+=("$2"); shift 2 ;;
    --verify)    VERIFY_FILE="$2"; shift 2 ;;
    -h|--help)   usage ;;
    *) echo "未知参数: $1"; usage ;;
  esac
done

# 验证模式
if [[ "$MODE" != "executor" && "$MODE" != "autonomous" && "$MODE" != "guided" ]]; then
  echo "错误: --mode 必须是 executor、autonomous 或 guided"
  exit 1
fi

# guided 模式：不需要 checklist，初始化为空
if [[ "$MODE" == "guided" ]]; then
  python3 - "$STATE_FILE" "$TASK" "$GOAL" "$MODE" "$VERIFY_FILE" <<'PYEOF'
import json, sys

state_file = sys.argv[1]
task = sys.argv[2]
goal = sys.argv[3]
mode = sys.argv[4]
verify_file = sys.argv[5]

state = {
    "task": task,
    "goal": goal,
    "mode": "guided",
    "phase": "initialized",
    "iteration": 0,
    "checklist": {},
    "blockers": [],
    "decisions": [],
    "startedAt": "",
    "completedAt": "",
    "meta": {}
}
if verify_file:
    state["meta"]["verify"] = verify_file

with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print(f"已初始化: {state_file}")
print(f"模式: guided")
print(f"任务: {task}")
print(f"完成条件: {goal}")
print(f"AI 将自动生成 PROMPT.md + checklist + verify.sh，请确认后执行")
PYEOF
  exit 0
fi

# 用 Python 安全构建 JSON（处理所有特殊字符）
# 注意：CHECKLIST 仅 executor 模式需要，autonomous 模式不传避免空数组问题
if [[ "$MODE" == "executor" ]]; then
  python3 - "$STATE_FILE" "$TASK" "$GOAL" "$MODE" "$VERIFY_FILE" "${CHECKLIST[@]+"${CHECKLIST[@]}"}" <<'PYEOF'
import json, sys

state_file = sys.argv[1]
task = sys.argv[2]
goal = sys.argv[3]
mode = sys.argv[4]
verify_file = sys.argv[5]
checklist_items = sys.argv[6:]

state = {
    "task": task,
    "goal": goal,
    "mode": "executor",
    "phase": "initialized",
    "iteration": 0,
    "checklist": {item: False for item in checklist_items},
    "blockers": [],
    "decisions": [],
    "startedAt": "",
    "completedAt": "",
    "meta": {}
}
if verify_file:
    state["meta"]["verify"] = verify_file

with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print(f"已初始化: {state_file}")
print(f"模式: {mode}")
print(f"任务: {task}")
print(f"完成条件: {goal}")
print(f"检查项: {len(checklist_items)} 个")
if verify_file:
    print(f"验证器: {verify_file}")
PYEOF
else
  python3 - "$STATE_FILE" "$TASK" "$GOAL" "$MODE" "$VERIFY_FILE" <<'PYEOF'
import json, sys

state_file = sys.argv[1]
task = sys.argv[2]
goal = sys.argv[3]
mode = sys.argv[4]
verify_file = sys.argv[5]

state = {
    "task": task,
    "goal": goal,
    "mode": "autonomous",
    "phase": "initialized",
    "iteration": 0,
    "checklist": {},
    "route": [],
    "journal": [],
    "blockers": [],
    "decisions": [],
    "startedAt": "",
    "completedAt": "",
    "meta": {}
}
if verify_file:
    state["meta"]["verify"] = verify_file

with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print(f"已初始化: {state_file}")
print(f"模式: {mode}")
print(f"任务: {task}")
print(f"完成条件: {goal}")
if verify_file:
    print(f"验证器: {verify_file}")
PYEOF
fi
