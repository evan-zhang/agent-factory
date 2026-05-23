#!/usr/bin/env bash
# ralph-loop.sh — Ralph Loop 核心循环引擎
# v3.0.0: 新增 verify.sh 支持、只读文件 hash 保护、results.tsv 追踪
set -euo pipefail

# ── 默认配置 ──
MAX_ITERATIONS=20
COOLDOWN_SECONDS=3
ITERATION_TIMEOUT=600  # 秒（默认 10 分钟）
STATE_FILE=""
PROMPT_FILE=""
PROJECT_ROOT=""
EXECUTOR="claude"
VERIFY_FILE=""

# ── macOS 兼容：检测 timeout 命令 ──
TIMEOUT_CMD=""
if command -v timeout &>/dev/null; then
  TIMEOUT_CMD="timeout"
elif command -v gtimeout &>/dev/null; then
  TIMEOUT_CMD="gtimeout"
fi
# 如果都没有，运行时不加超时（风险自担）

# ── 参数解析 ──
usage() {
  cat <<'EOF'
用法: ralph-loop.sh --prompt <file> --state <file> [选项]

必选:
  --prompt <file>        PROMPT.md 任务描述文件
  --state <file>         state.json 状态文件路径

可选:
  --max-iterations <n>   最大迭代次数 (默认: 20)
  --cooldown <seconds>   迭代间冷却秒数 (默认: 3)
  --timeout <seconds>    单次迭代超时秒数 (默认: 600)
  --project-root <dir>   项目根目录 (默认: 当前目录)
  --executor <command>   执行器 (默认: claude)
                         可选: claude | codex | 任意可执行命令
  --verify <file>        verify.sh 验证器路径（可选）

模式由 state.json 中的 "mode" 字段决定:
  executor    — 执行者模式：按 checklist 逐条执行
  autonomous  — 自主者模式：AI 自主规划、执行、记录

退出码:
  0 — 任务完成
  1 — 执行错误
  2 — 达到最大迭代次数
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt)      PROMPT_FILE="$2"; shift 2 ;;
    --state)       STATE_FILE="$2"; shift 2 ;;
    --max-iterations) MAX_ITERATIONS="$2"; shift 2 ;;
    --cooldown)    COOLDOWN_SECONDS="$2"; shift 2 ;;
    --timeout)     ITERATION_TIMEOUT="$2"; shift 2 ;;
    --project-root) PROJECT_ROOT="$2"; shift 2 ;;
    --executor)    EXECUTOR="$2"; shift 2 ;;
    --verify)      VERIFY_FILE="$2"; shift 2 ;;
    -h|--help)     usage ;;
    *) echo "未知参数: $1"; usage ;;
  esac
done

[[ -z "$PROMPT_FILE" ]] && { echo "错误: 缺少 --prompt 参数"; usage; }
[[ -z "$STATE_FILE" ]]  && { echo "错误: 缺少 --state 参数"; usage; }
[[ ! -f "$PROMPT_FILE" ]] && { echo "错误: PROMPT 文件不存在: $PROMPT_FILE"; exit 1; }
[[ -n "$VERIFY_FILE" && ! -f "$VERIFY_FILE" ]] && { echo "错误: verify 文件不存在: $VERIFY_FILE"; exit 1; }

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
LOG_DIR="${PROJECT_ROOT}/.ralph-logs"
BACKUP_DIR="${LOG_DIR}/state-backups"
RESULTS_FILE="${PROJECT_ROOT}/results.tsv"
mkdir -p "$LOG_DIR" "$BACKUP_DIR"

# 初始化 results.tsv header（仅首次）
if [[ -n "$VERIFY_FILE" && ! -f "$RESULTS_FILE" ]]; then
  printf 'iteration\tscore_before\tscore_after\tstatus\tdiff_stat\treason\n' > "$RESULTS_FILE"
fi

# ── 初始化 state.json（如果不存在）──
if [[ ! -f "$STATE_FILE" ]]; then
  cat > "$STATE_FILE" <<'STATEJSON'
{
  "task": "",
  "goal": "",
  "mode": "executor",
  "phase": "initialized",
  "iteration": 0,
  "checklist": {},
  "blockers": [],
  "decisions": [],
  "startedAt": "",
  "completedAt": "",
  "meta": {}
}
STATEJSON
  echo "已初始化 state.json: $STATE_FILE"
fi

# ── 信号处理：Ctrl+C 优雅退出 ──
cleanup() {
  echo ""
  echo "⚠️  收到中断信号，正在保存状态..."
  # 不修改 phase，保留当前状态供恢复
  echo "状态已保留: $STATE_FILE"
  echo "可用 --state $STATE_FILE 恢复执行"
  exit 130
}
trap cleanup SIGINT SIGTERM

# ── 安全读取 state.json 字段（统一用 Python argv）──
state_get() {
  local key="$1"
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get(sys.argv[2],''))" "$STATE_FILE" "$key" 2>/dev/null || echo ""
}

state_get_phase() {
  state_get "phase"
}

state_get_mode() {
  state_get "mode"
}

file_hash() {
  if command -v sha256sum &>/dev/null; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

capture_readonly_hashes() {
  local checksum_file="$1"
  : > "$checksum_file"

  if [[ -n "$VERIFY_FILE" ]]; then
    printf '%s\t%s\n' "$VERIFY_FILE" "$(file_hash "$VERIFY_FILE")" >> "$checksum_file"
  fi

  printf '%s\t%s\n' "$PROMPT_FILE" "$(file_hash "$PROMPT_FILE")" >> "$checksum_file"

  local protocol_file="${PROJECT_ROOT}/PROTOCOL.md"
  if [[ -f "$protocol_file" ]]; then
    printf '%s\t%s\n' "$protocol_file" "$(file_hash "$protocol_file")" >> "$checksum_file"
  fi
}

readonly_files_tampered() {
  local checksum_file="$1"
  local path expected_hash actual_hash
  local tampered=0

  while IFS=$'\t' read -r path expected_hash; do
    [[ -z "$path" ]] && continue
    actual_hash=$(file_hash "$path" 2>/dev/null || echo "__missing__")
    if [[ "$actual_hash" != "$expected_hash" ]]; then
      echo "⚠️  只读文件被篡改: $path"
      tampered=1
    fi
  done < "$checksum_file"

  return "$tampered"
}

verify_last_json() {
  local output_file="$1"
  tail -n 1 "$output_file" 2>/dev/null || true
}

verify_parse_field() {
  local json_line="$1"
  local field="$2"
  python3 - "$json_line" "$field" <<'PYEOF'
import json, sys
try:
    data = json.loads(sys.argv[1])
    value = data.get(sys.argv[2], "")
    print(value)
except Exception:
    sys.exit(1)
PYEOF
}

run_verify() {
  local output_file verify_exit json_line status score details
  output_file=$(mktemp /tmp/ralph-verify-XXXXXX.log)

  set +e
  (cd "$PROJECT_ROOT" && bash "$VERIFY_FILE") > "$output_file" 2>&1
  verify_exit=$?
  set -e

  json_line=$(verify_last_json "$output_file")
  if ! status=$(verify_parse_field "$json_line" "status" 2>/dev/null); then
    status="crash"
  fi
  if ! score=$(verify_parse_field "$json_line" "score" 2>/dev/null); then
    score="1"
  fi
  if ! details=$(verify_parse_field "$json_line" "details" 2>/dev/null); then
    details="verify.sh 输出格式错误"
  fi

  # 退出码优先：exit 1 = FAIL, exit 0 = PASS
  if [[ "$verify_exit" -ne 0 ]]; then
    status="FAIL"
    [[ "$score" == "0" ]] && score="1"
  fi

  rm -f "$output_file"
  printf '%s\t%s\t%s\n' "$status" "$score" "$details"
}

verify_score() {
  local result_line="$1"
  printf '%s' "$result_line" | awk -F '\t' '{print $2}'
}

diff_stat_summary() {
  local stat
  stat=$(git -C "$PROJECT_ROOT" diff --shortstat 2>/dev/null || true)
  [[ -n "$stat" ]] && printf '%s' "$stat" || printf '0'
}

# ── state.json 校验 + 备份 ──
validate_state() {
  python3 - "$STATE_FILE" <<'PYEOF'
import json, sys
try:
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        json.load(f)
except (json.JSONDecodeError, FileNotFoundError) as e:
    print(f"STATE_INVALID:{e}")
    sys.exit(1)
PYEOF
}

backup_state() {
  local ts
  ts=$(date +%Y%m%d-%H%M%S)
  cp "$STATE_FILE" "${BACKUP_DIR}/state-iteration-${1:-unknown}-${ts}.json" 2>/dev/null || true
}

restore_last_backup() {
  local latest
  latest=$(ls -t "${BACKUP_DIR}"/state-iteration-*.json 2>/dev/null | head -1)
  if [[ -n "$latest" ]]; then
    cp "$latest" "$STATE_FILE"
    echo "⚠️  已从备份恢复 state.json: $(basename "$latest")"
  else
    echo "❌ 无可用备份，state.json 可能已损坏"
  fi
}

# ── 构建动态 prompt ──
build_prompt_executor() {
  local state_content
  state_content=$(cat "$STATE_FILE")

  cat <<PROMPT
# Ralph Loop 迭代任务（执行者模式）

## 当前状态 (state.json)

$state_content

## 任务描述

$(cat "$PROMPT_FILE")

## 执行规则

1. 先读取 state.json 的 checklist，只做未完成（false）的部分
2. 条件通过 = 对应验证命令 exit 0。通过后标记为 true，绝不回退
3. 全部 true 后将 phase 设为 "done"
4. 每次改动后必须运行验证命令（backpressure）
5. 遇到技术选择记录到 decisions（含理由）
6. 遇到阻塞记录到 blockers
7. 改动范围不超过本次迭代目标（无发散）
8. 更新 iteration +1
9. **更新 state.json 时必须保留所有已有字段（特别是 checklist、blockers、decisions），只修改本次迭代需要变更的字段。不要只输出部分字段导致覆盖丢失。**

## 质量门禁

- [ ] 产出可验证
- [ ] 相关检查通过
- [ ] 改动范围 ≤ 本次迭代目标
- [ ] state.json 已如实更新

PROMPT
}

build_prompt_autonomous() {
  local state_content
  state_content=$(cat "$STATE_FILE")

  cat <<PROMPT
# Ralph Loop 迭代任务（自主者模式）

## 当前状态 (state.json)

$state_content

## 目标描述

$(cat "$PROMPT_FILE")

## 自主执行规则

1. 理解最终目标，从 route 数组中取下一个未完成的步骤执行
2. 如果是第一次迭代（iteration=0 或 route 为空）：
   - 规划执行路径，写入 route 数组
   - 将目标拆解为可验证的 checklist 条目
   - 将 phase 设为 "planning"
   - **重要：完成规划后，将 phase 设为 "awaiting_approval"，等待人类审阅 route 和 checklist 后再继续**
3. 每次迭代：
   - 从 route 中取下一个可行步骤
   - 执行一个明确的步骤
   - 验证结果（附上可复验的证据）
   - 将过程记录写入 journal
4. 如果 checklist 中有条目通过，标记为 true
5. 全部 checklist 为 true 后 phase 设为 "done"
6. 遇到技术选择记录到 decisions（含理由）
7. 遇到阻塞记录到 blockers
8. **避免重复走错路**：每次行动前检查 journal 历史，不在同一个坑里跌倒两次
9. 更新 iteration +1
10. **更新 state.json 时必须保留所有已有字段（特别是 journal、route、checklist、blockers、decisions），只修改本次迭代需要变更的字段。不要只输出部分字段导致覆盖丢失。**

## Journal 写入格式

每次迭代必须在 journal 数组末尾追加一条（保留所有历史条目）：
{
  "iteration": <当前迭代号>,
  "timestamp": "<ISO 8601>",
  "action": "做了什么（一句话）",
  "reason": "为什么这么做",
  "evidence": "可复验的证据（命令输出、文件 diff、URL 等）",
  "result": "结果（success/partial/fail）",
  "learned": "学到了什么",
  "nextFocus": "下一次迭代聚焦什么"
}

## 质量门禁

- [ ] 本次迭代聚焦一个目标
- [ ] 产出有可验证的证据
- [ ] journal 已如实记录
- [ ] state.json 已如实更新（保留所有已有字段）
- [ ] 无重复走错路

PROMPT
}

# ── 执行器调度 ──
run_executor() {
  local prompt_content="$1"

  case "$EXECUTOR" in
    claude)
      if command -v claude &>/dev/null; then
        if [[ -n "$TIMEOUT_CMD" ]]; then
          $TIMEOUT_CMD "$ITERATION_TIMEOUT" claude --print "$prompt_content" 2>&1
        else
          claude --print "$prompt_content" 2>&1
        fi
      else
        echo "错误: claude CLI 未找到，请确保已安装 Claude Code"
        return 1
      fi
      ;;
    codex)
      local codex_bin=""
      if command -v codex &>/dev/null; then
        codex_bin="codex"
      elif [[ -x "$HOME/.npm-global/bin/codex" ]]; then
        codex_bin="$HOME/.npm-global/bin/codex"
      else
        echo "错误: codex CLI 未找到"
        return 1
      fi
      if [[ -n "$TIMEOUT_CMD" ]]; then
        $TIMEOUT_CMD "$ITERATION_TIMEOUT" "$codex_bin" exec "$prompt_content" 2>&1
      else
        "$codex_bin" exec "$prompt_content" 2>&1
      fi
      ;;
    *)
      # 自定义执行器：将 prompt 写入临时文件
      local temp_prompt
      temp_prompt=$(mktemp /tmp/ralph-prompt-XXXXXX.md)
      echo "$prompt_content" > "$temp_prompt"
      if [[ -n "$TIMEOUT_CMD" ]]; then
        $TIMEOUT_CMD "$ITERATION_TIMEOUT" "$EXECUTOR" "$temp_prompt" 2>&1
      else
        "$EXECUTOR" "$temp_prompt" 2>&1
      fi
      rm -f "$temp_prompt"
      ;;
  esac
}

# ── 主循环 ──
MODE=$(state_get_mode)

echo "=========================================="
echo " Ralph Loop 启动"
echo " 模式:    $MODE"
echo " 执行器:  $EXECUTOR"
echo " Prompt:  $PROMPT_FILE"
echo " State:   $STATE_FILE"
[[ -n "$VERIFY_FILE" ]] && echo " Verify:  $VERIFY_FILE"
echo " 上限:    $MAX_ITERATIONS 次迭代"
echo " 冷却:    ${COOLDOWN_SECONDS}s"
[[ -n "$TIMEOUT_CMD" ]] && echo " 超时:    ${ITERATION_TIMEOUT}s (via $TIMEOUT_CMD)" || echo " 超时:    未启用（未检测到 timeout/gtimeout）"
echo "=========================================="

consecutive_fails=0
iteration=0

while [[ $iteration -lt $MAX_ITERATIONS ]]; do
  iteration=$((iteration + 1))
  timestamp=$(date +%Y%m%d-%H%M%S)
  log_file="${LOG_DIR}/iteration-${iteration}-${timestamp}.log"

  # 检查是否已完成
  current_phase=$(state_get_phase)

  # 自主者模式：检查是否在等待人审阅
  if [[ "$MODE" == "autonomous" && "$current_phase" == "awaiting_approval" ]]; then
    echo ""
    echo "=========================================="
    echo " ⏸️  自主者模式：等待人类审阅"
    echo " AI 已完成初始规划，请查看 state.json"
    echo " 审阅 route 和 checklist 后："
    echo "   确认 → 将 phase 改为 'working'"
    echo "   修改 → 修改 route/checklist 后将 phase 改为 'working'"
    echo "   取消 → 将 phase 改为 'done'"
    echo "=========================================="
    echo ""
    echo "等待中...（每 10 秒检查一次）"
    while true; do
      sleep 10
      new_phase=$(state_get_phase)
      if [[ "$new_phase" != "awaiting_approval" ]]; then
        current_phase="$new_phase"
        echo "检测到 phase 变更为 '$new_phase'，继续执行"
        break
      fi
    done
  fi

  if [[ "$current_phase" == "done" ]]; then
    echo ""
    echo "=========================================="
    echo " ✅ Ralph Loop 完成！"
    echo " 模式:    $MODE"
    echo " 总迭代:  $iteration"
    echo " 状态文件: $STATE_FILE"
    echo "=========================================="
    exit 0
  fi

  echo ""
  echo "--- 迭代 ${iteration}/${MAX_ITERATIONS} ($(date +%H:%M:%S)) ---"

  # 备份当前 state.json
  backup_state "$iteration"

  score_before=""
  if [[ -n "$VERIFY_FILE" ]]; then
    verify_before=$(run_verify)
    score_before=$(verify_score "$verify_before")
  fi

  CHECKSUM_FILE=""
  if [[ -n "$VERIFY_FILE" ]]; then
    CHECKSUM_FILE=$(mktemp /tmp/ralph-checksums-XXXXXX)
    capture_readonly_hashes "$CHECKSUM_FILE"
  fi

  # 根据模式构建 prompt
  local_prompt=""
  if [[ "$MODE" == "autonomous" ]]; then
    local_prompt=$(build_prompt_autonomous)
  else
    local_prompt=$(build_prompt_executor)
  fi

  # 执行
  set +e
  run_executor "$local_prompt" 2>&1 | tee "$log_file"
  exit_code=${PIPESTATUS[0]}
  set -e

  if [[ -n "$VERIFY_FILE" ]]; then
    if ! readonly_files_tampered "$CHECKSUM_FILE"; then
      rm -f "$CHECKSUM_FILE"
      git -C "$PROJECT_ROOT" reset --hard HEAD
      git -C "$PROJECT_ROOT" clean -fd
      printf '%s\t%s\t%s\t%s\t%s\t%s\n' "${iteration}" "${score_before}" "${score_before}" "crash" "0" "只读文件被篡改，全部回滚" >> "$RESULTS_FILE"
      continue
    fi
    rm -f "$CHECKSUM_FILE"
  fi

  # 校验 state.json 完整性
  if ! validate_state; then
    echo "⚠️  state.json 损坏，正在从备份恢复..."
    restore_last_backup
  fi

  if [[ -n "$VERIFY_FILE" ]]; then
    verify_after=$(run_verify)
    verify_status=$(printf '%s' "$verify_after" | awk -F '\t' '{print $1}')
    score_after=$(printf '%s' "$verify_after" | awk -F '\t' '{print $2}')
    verify_details=$(printf '%s' "$verify_after" | awk -F '\t' '{print $3}')

    # score 比较：越小越好，决定 keep/discard
    action="keep"
    reason="$verify_details"
    if [[ "$verify_status" == "FAIL" || "$verify_status" == "crash" ]]; then
      action="discard"
      reason="验证失败: $verify_details"
      # 撤回本轮改动
      git -C "$PROJECT_ROOT" reset --hard HEAD
      git -C "$PROJECT_ROOT" clean -fd
    elif [[ -n "$score_before" ]]; then
      # score 越小越好；score_after >= score_before 表示没有改善
      if awk "BEGIN{exit !($score_after >= $score_before)}" 2>/dev/null; then
        action="discard"
        reason="score 未改善: $score_before -> $score_after"
        git -C "$PROJECT_ROOT" reset --hard HEAD
        git -C "$PROJECT_ROOT" clean -fd
      else
        # score 改善，提交
        git -C "$PROJECT_ROOT" add -A
        git -C "$PROJECT_ROOT" commit -m "ralph iter ${iteration}: score ${score_before} -> ${score_after}" --allow-empty 2>/dev/null || true
        reason="score 改善: $score_before -> $score_after; $verify_details"
      fi
    else
      # 第一轮没有 score_before，PASS 就保留
      git -C "$PROJECT_ROOT" add -A
      git -C "$PROJECT_ROOT" commit -m "ralph iter ${iteration}: initial score ${score_after}" --allow-empty 2>/dev/null || true
    fi

    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "${iteration}" "${score_before}" "${score_after}" "${action}" "$(diff_stat_summary)" "${reason}" >> "$RESULTS_FILE"
  fi

  # 检查迭代结果
  if [[ $exit_code -ne 0 ]]; then
    consecutive_fails=$((consecutive_fails + 1))
    echo "⚠️  迭代 ${iteration} 失败 (exit code: ${exit_code})"

    if [[ $consecutive_fails -ge 3 ]]; then
      echo "⚠️  连续 ${consecutive_fails} 次失败，暂停 30 秒..."
      sleep 30
      echo "   继续尝试..."
    fi
  else
    consecutive_fails=0
  fi

  # 冷却
  if [[ $COOLDOWN_SECONDS -gt 0 ]]; then
    sleep "$COOLDOWN_SECONDS"
  fi
done

echo ""
echo "=========================================="
echo " ⚠️  达到最大迭代次数 ($MAX_ITERATIONS)"
echo " 模式:    $MODE"
echo " 任务可能未完成，请检查 state.json"
echo "=========================================="
exit 2
