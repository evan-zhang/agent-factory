#!/bin/bash
# verify-manifest.sh — 根据 lib/deliverable-manifest.json 校验零件完整性
#
# 用法：bash scripts/verify-manifest.sh <品种目录> [--strict] [--json]
#
# 功能：
#   1. 读取 lib/deliverable-manifest.json 单一权威清单
#   2. 逐项校验：文件存在 + 类型 + min_bytes/min_lines + state.json gateStatus 全 completed
#   3. recommended_lines 低于阈值只 WARN 不 FAIL
#   4. min_lines/min_bytes 低于阈值 → FAIL（exit 1）
#
# 参数：
#   --strict   WARN 也算 FAIL（严格模式）
#   --json     输出 JSON 格式（程序化用）
#
# 退出码：
#   0 - 全过
#   1 - 有 FAIL
#   2 - 参数错误
#
# 环境变量：
#   BD_EVAL_CMS_SKIP_MANIFEST=1  跳过检查（仅供测试/历史回放）

set -euo pipefail

# 允许跳过检查（测试/历史回放用）
if [ "${BD_EVAL_CMS_SKIP_MANIFEST:-}" = "1" ]; then
  echo "⚠️  跳过 manifest 检查（BD_EVAL_CMS_SKIP_MANIFEST=1，仅限测试/历史回放）"
  exit 0
fi

# 参数解析
CASE_DIR=""
STRICT_MODE=false
JSON_OUTPUT=false
CHECK_MODE="archive"  # render | archive | full（默认 archive，与归档一致；preflight 用 render 跳过 phase-5-5-html 自检）

while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict)
      STRICT_MODE=true
      shift
      ;;
    --json)
      JSON_OUTPUT=true
      shift
      ;;
    --mode)
      CHECK_MODE="$2"
      shift 2
      ;;
    -*)
      echo "❌ 未知参数: $1"
      exit 2
      ;;
    *)
      if [ -z "$CASE_DIR" ]; then
        CASE_DIR="$1"
      else
        echo "❌ 多个目录参数: $1"
        exit 2
      fi
      shift
      ;;
  esac
done

if [ -z "$CASE_DIR" ]; then
  echo "❌ verify-manifest 错误：必须提供品种目录路径"
  exit 2
fi

if [ ! -d "$CASE_DIR" ]; then
  echo "❌ verify-manifest 错误：品种目录不存在: $CASE_DIR"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST_FILE="$SKILL_DIR/lib/deliverable-manifest.json"

if [ ! -f "$MANIFEST_FILE" ]; then
  echo "❌ manifest 文件不存在: $MANIFEST_FILE"
  exit 1
fi

# 结果收集
FAIL_ITEMS=()
WARN_ITEMS=()
PASS_COUNT=0
TOTAL_COUNT=0

# JSON 输出缓冲区
JSON_RESULTS="[]"

# 检查单个文件
check_file() {
  local item_label="$1"
  local path_path="$2"
  local path_glob="$3"
  local type="$4"
  local min_bytes="$5"
  local min_lines="$6"
  local recommended_lines="$7"
  local description="$8"

  TOTAL_COUNT=$((TOTAL_COUNT + 1))

  # 支持路径 glob 匹配
  local matched_files=()
  if [ -n "$path_glob" ]; then
    # 使用 glob 匹配
    for f in "$CASE_DIR"/$path_glob; do
      if [ -f "$f" ]; then
        matched_files+=("$f")
      fi
    done
  else
    # 精确路径
    if [ -f "$CASE_DIR/$path_path" ]; then
      matched_files+=("$CASE_DIR/$path_path")
    fi
  fi

  if [ ${#matched_files[@]} -eq 0 ]; then
    local result="❌ FAIL: $item_label - 文件不存在"
    FAIL_ITEMS+=("$result")

    if [ "$JSON_OUTPUT" = true ]; then
      JSON_RESULTS=$(echo "$JSON_RESULTS" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({
    'path': '$item_label',
    'status': 'FAIL',
    'reason': '文件不存在',
    'description': '$description'
})
print(json.dumps(results, ensure_ascii=False))
")
    fi
    return
  fi

  # 检查每个匹配的文件
  local file_has_fail=false
  local file_has_warn=false

  for matched_file in "${matched_files[@]}"; do
    local filename=$(basename "$matched_file")
    local file_reasons=()

    # 检查类型
    if [ "$type" = "json" ]; then
      if ! jq empty "$matched_file" 2>/dev/null; then
        file_reasons+=("JSON 无效")
        file_has_fail=true
      fi
    fi

    # 检查 min_bytes
    if [ -n "$min_bytes" ] && [ "$min_bytes" -gt 0 ]; then
      local file_size=$(stat -f%z "$matched_file" 2>/dev/null || stat -c%s "$matched_file" 2>/dev/null || echo 0)
      if [ "$file_size" -lt "$min_bytes" ]; then
        file_reasons+=("大小 ${file_size} 字节 < ${min_bytes} 字节底线")
        file_has_fail=true
      fi
    fi

    # 检查 min_lines
    if [ -n "$min_lines" ] && [ "$min_lines" -gt 0 ]; then
      local file_lines=$(wc -l < "$matched_file" 2>/dev/null || echo 0)
      if [ "$file_lines" -lt "$min_lines" ]; then
        file_reasons+=("行数 ${file_lines} < ${min_lines} 行底线")
        file_has_fail=true
      elif [ -n "$recommended_lines" ] && [ "$recommended_lines" -gt 0 ] && [ "$file_lines" -lt "$recommended_lines" ]; then
        file_reasons+=("行数 ${file_lines} < ${recommended_lines} 行推荐值（WARN）")
        file_has_warn=true
      fi
    fi

    # 汇总结果
    if [ "$file_has_fail" = true ]; then
      local result="❌ FAIL: $filename - ${file_reasons[*]}"
      FAIL_ITEMS+=("$result")

      if [ "$JSON_OUTPUT" = true ]; then
        JSON_RESULTS=$(echo "$JSON_RESULTS" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({
    'path': '${filename}',
    'status': 'FAIL',
    'reason': '${file_reasons[*]}',
    'description': '$description'
})
print(json.dumps(results, ensure_ascii=False))
")
      fi
    elif [ "$file_has_warn" = true ]; then
      local result="⚠️  WARN: $filename - ${file_reasons[*]}"
      WARN_ITEMS+=("$result")

      if [ "$JSON_OUTPUT" = true ]; then
        JSON_RESULTS=$(echo "$JSON_RESULTS" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({
    'path': '${filename}',
    'status': 'WARN',
    'reason': '${file_reasons[*]}',
    'description': '$description'
})
print(json.dumps(results, ensure_ascii=False))
")
      fi
    else
      PASS_COUNT=$((PASS_COUNT + 1))

      if [ "$JSON_OUTPUT" = true ]; then
        JSON_RESULTS=$(echo "$JSON_RESULTS" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({
    'path': '${filename}',
    'status': 'PASS',
    'reason': '通过校验',
    'description': '$description'
})
print(json.dumps(results, ensure_ascii=False))
")
      fi
    fi
  done
}

# 读取 manifest 并校验
STATE_FILE="$CASE_DIR/state.json"
JSON_VALID=false
GATE_STATUS_CHECK=true

# 先检查 state.json 是否存在且有效
if [ ! -f "$STATE_FILE" ]; then
  FAIL_ITEMS+=("❌ state.json（文件不存在）")
  JSON_RESULTS=$(echo "$JSON_RESULTS" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({
    'path': 'state.json',
    'status': 'FAIL',
    'reason': '文件不存在',
    'description': '项目状态文件'
})
print(json.dumps(results, ensure_ascii=False))
")
  GATE_STATUS_CHECK=false
else
  if ! jq empty "$STATE_FILE" 2>/dev/null; then
    FAIL_ITEMS+=("❌ state.json（JSON 无效）")
    JSON_RESULTS=$(echo "$JSON_RESULTS" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({
    'path': 'state.json',
    'status': 'FAIL',
    'reason': 'JSON 无效',
    'description': '项目状态文件'
})
print(json.dumps(results, ensure_ascii=False))
")
    GATE_STATUS_CHECK=false
  else
    JSON_VALID=true
    JSON_RESULTS=$(echo "$JSON_RESULTS" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({
    'path': 'state.json',
    'status': 'PASS',
    'reason': 'JSON 有效',
    'description': '项目状态文件'
})
print(json.dumps(results, ensure_ascii=False))
")
    PASS_COUNT=$((PASS_COUNT + 1))
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
  fi
fi

# 逐个检查 required_files
# 使用 Python 处理 JSON，避免 jq 的引号转义问题
MANIFEST_ITEMS=$(python3 -c "
import json
with open('$MANIFEST_FILE') as f:
    data = json.load(f)
for item in data['required_files']:
    path = item.get('path', '')
    path_glob = item.get('path_glob', '')
    item_type = item.get('type', 'md')
    min_bytes = item.get('min_bytes', 0)
    min_lines = item.get('min_lines', 0)
    recommended_lines = item.get('recommended_lines', 0)
    description = item.get('description', '')
    print(f'{path}|{path_glob}|{item_type}|{min_bytes}|{min_lines}|{recommended_lines}|{description}')
")

while IFS='|' read -r path path_glob type min_bytes min_lines recommended_lines description; do

  # 如果是 state.json，已经检查过了，跳过
  if [ "$path" = "state.json" ]; then
    continue
  fi

  # 使用 path 或 path_glob 作为标签
  label="${path:-$path_glob}"
  check_file "$label" "$path" "$path_glob" "$type" "$min_bytes" "$min_lines" "$recommended_lines" "$description"
done <<< "$(echo "$MANIFEST_ITEMS")"

# 检查 gateStatus
if [ "$JSON_VALID" = true ] && [ "$GATE_STATUS_CHECK" = true ]; then
  TOTAL_COUNT=$((TOTAL_COUNT + 1))
  HAS_GATE_STATUS=$(jq -r 'has("gateStatus")' "$STATE_FILE" 2>/dev/null)

  if [ "$HAS_GATE_STATUS" != "true" ]; then
    FAIL_ITEMS+=("❌ state.json.gateStatus（缺失）")
    JSON_RESULTS=$(echo "$JSON_RESULTS" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({
    'path': 'state.json.gateStatus',
    'status': 'FAIL',
    'reason': 'gateStatus 字段缺失',
    'description': 'Gate 状态检查'
})
print(json.dumps(results, ensure_ascii=False))
")
  else
    # 根据 mode 选择 gate 列表（向后兼容 state_gates_must_be_completed）
    case "$CHECK_MODE" in
      render)
        REQUIRED_GATES=$(jq -r '.state_gates_required_for_render[]? // empty' "$MANIFEST_FILE" 2>/dev/null)
        ;;
      archive|full)
        REQUIRED_GATES=$(jq -r '.state_gates_required_for_archive[]? // empty' "$MANIFEST_FILE" 2>/dev/null)
        ;;
      *)
        echo "❌ 未知 --mode: $CHECK_MODE（允许 render | archive | full）" >&2
        exit 2
        ;;
    esac
    # 向后兼容旧字段名
    if [ -z "$REQUIRED_GATES" ]; then
      REQUIRED_GATES=$(jq -r '.state_gates_must_be_completed[]? // empty' "$MANIFEST_FILE" 2>/dev/null)
    fi
    INCOMPLETE_GATES=()

    for gate in $REQUIRED_GATES; do
      STATUS=$(jq -r ".gateStatus.\"$gate\" // \"__missing__\"" "$STATE_FILE" 2>/dev/null)
      if [ "$STATUS" != "completed" ]; then
        INCOMPLETE_GATES+=("$gate: $STATUS")
      fi
    done

    if [ ${#INCOMPLETE_GATES[@]} -gt 0 ]; then
      result="❌ state.json.gateStatus（未完成）: ${INCOMPLETE_GATES[*]}"
      FAIL_ITEMS+=("$result")
      JSON_RESULTS=$(echo "$JSON_RESULTS" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({
    'path': 'state.json.gateStatus',
    'status': 'FAIL',
    'reason': '未完成的 gate: ${INCOMPLETE_GATES[*]}',
    'description': 'Gate 状态检查'
})
print(json.dumps(results, ensure_ascii=False))
")
    else
      PASS_COUNT=$((PASS_COUNT + 1))
      JSON_RESULTS=$(echo "$JSON_RESULTS" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({
    'path': 'state.json.gateStatus',
    'status': 'PASS',
    'reason': '所有前置 gate 均为 completed',
    'description': 'Gate 状态检查'
})
print(json.dumps(results, ensure_ascii=False))
")
    fi
  fi
fi

# 输出结果
if [ "$JSON_OUTPUT" = true ]; then
  # JSON 输出
  python3 -c "
import sys, json
exit_code = 0 if ${#FAIL_ITEMS[@]} == 0 and (${#WARN_ITEMS[@]} == 0 or '$STRICT_MODE' != 'true') else 1
print(json.dumps({
    'success': exit_code == 0,
    'exit_code': exit_code,
    'total': $TOTAL_COUNT,
    'pass': $PASS_COUNT,
    'warn': ${#WARN_ITEMS[@]},
    'fail': ${#FAIL_ITEMS[@]},
    'strict': '$STRICT_MODE' == 'true',
    'results': $JSON_RESULTS
}, ensure_ascii=False, indent=2))
"
else
  # 文本输出
  echo "=== 零件清单 Manifest 校验 ==="
  echo "目录: $CASE_DIR"
  echo "Manifest: $MANIFEST_FILE"
  echo ""

  echo "通过: $PASS_COUNT / $TOTAL_COUNT"
  if [ ${#WARN_ITEMS[@]} -gt 0 ]; then
    echo "警告: ${#WARN_ITEMS[@]}"
  fi
  if [ ${#FAIL_ITEMS[@]} -gt 0 ]; then
    echo "失败: ${#FAIL_ITEMS[@]}"
  fi
  echo ""

  # 显示 WARN
  if [ ${#WARN_ITEMS[@]} -gt 0 ]; then
    echo "⚠️  WARN 项（不阻断）："
    for warn in "${WARN_ITEMS[@]}"; do
      echo "  $warn"
    done
    echo ""
  fi

  # 显示 FAIL
  if [ ${#FAIL_ITEMS[@]} -gt 0 ]; then
    echo "❌ FAIL 项（阻断）："
    for fail in "${FAIL_ITEMS[@]}"; do
      echo "  $fail"
    done
    echo ""
  fi

  # 决定退出码
  if [ ${#FAIL_ITEMS[@]} -gt 0 ]; then
    echo "❌ Manifest 校验失败：存在 ${#FAIL_ITEMS[@]} 个 FAIL 项"
    exit 1
  elif [ ${#WARN_ITEMS[@]} -gt 0 ] && [ "$STRICT_MODE" = true ]; then
    echo "❌ Manifest 校验失败（--strict 模式）：存在 ${#WARN_ITEMS[@]} 个 WARN 项"
    exit 1
  else
    echo "✅ Manifest 校验通过"
    if [ ${#WARN_ITEMS[@]} -gt 0 ]; then
      echo "   （存在 ${#WARN_ITEMS[@]} 个 WARN 项，不阻断）"
    fi
    exit 0
  fi
fi
