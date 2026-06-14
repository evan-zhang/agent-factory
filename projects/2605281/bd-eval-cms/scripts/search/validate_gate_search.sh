#!/usr/bin/env bash
# validate_gate_search.sh — Gate 搜索证据校验（v0.10.0 加固版）
#
# 职责：
#   1. 校验 case/references/{prefix}/ 目录文件数 ≥ 最低门槛
#   2. 校验本 Gate 章节文件**存在**（不是可选）
#   3. 校验章节含至少 1 个引用 [{PREFIX}-XXX]
#   4. 校验每个引用的编号对应到 references/ 真实文件
#   5. 校验每个 reference 文件含必要结构字段（URL/抓取时间/关键数据点）
#
# 不做什么：
#   - 不做搜索本身
#   - 不做章节内容质量审查
#   - 不写文件

# Gate 列表（"gate prefix min_files chapter_rel_path"）
# 注意：chapter_rel 是相对 case_dir 的路径
# 路径修正（v0.10.0 FAIL 修复）：one-pager 在 02-gate-by-chapter/ 下
gate_config() {
  case "$1" in
    gate-1)   echo "G1 2 02-gate-by-chapter/Gate-1-premise.md" ;;
    gate-2)   echo "G2 3 02-gate-by-chapter/Gate-2-positioning.md" ;;
    gate-3)   echo "G3 3 02-gate-by-chapter/Gate-3-evidence.md" ;;
    gate-4)   echo "G4 2 02-gate-by-chapter/Gate-4-payment.md" ;;
    gate-5)   echo "G5 2 02-gate-by-chapter/Gate-5-cost.md" ;;
    phase-1)  echo "P1 2 01-discovery.md" ;;
    phase-2)  echo "P2 2 02-discovery/01-background.md" ;;
    one-pager) echo "OP 1 02-gate-by-chapter/One-pager.md" ;;
    *)        return 1 ;;
  esac
}

list_gates() {
  echo "gate-1 gate-2 gate-3 gate-4 gate-5 phase-1 phase-2 one-pager"
}

# 校验 reference 文件结构
# 用法：validate_ref_file <file_path>
# 必要字段：**URL** / **抓取时间** / **关键数据点**
validate_ref_file() {
  local file="$1"
  local missing=()
  
  if [ ! -s "$file" ]; then
    echo "EMPTY"
    return 1
  fi
  
  # 校验 URL
  if ! grep -qE 'URL.*https?://' "$file"; then
    missing+=("URL")
  fi
  # 校验抓取时间
  if ! grep -qE '抓取时间' "$file"; then
    missing+=("抓取时间")
  fi
  # 校验关键数据点
  if ! grep -qE '关键数据点' "$file"; then
    missing+=("关键数据点")
  fi
  
  if [ ${#missing[@]} -gt 0 ]; then
    echo "MISSING:${missing[*]}"
    return 1
  fi
  echo "OK"
  return 0
}

# 主函数
# 用法：validate_gate_search.sh <case-dir> <gate-name>
validate() {
  local case_dir="$1"
  local gate="$2"
  local ERRORS=()
  
  local cfg prefix min_files chapter_rel
  cfg=$(gate_config "$gate") || {
    echo "❌ 未知 Gate: $gate（已知：$(list_gates)）" >&2
    return 1
  }
  prefix=$(echo "$cfg" | awk '{print $1}')
  min_files=$(echo "$cfg" | awk '{print $2}')
  chapter_rel=$(echo "$cfg" | awk '{print $3}')
  local prefix_upper
  prefix_upper=$(echo "$prefix" | tr '[:lower:]' '[:upper:]')
  
  # 1. 校验 references 目录文件数
  local ref_dir="$case_dir/references/$prefix"
  local actual_files
  actual_files=$(find "$ref_dir" -name "*.md" 2>/dev/null | sort)
  local actual_count
  # 用 wc -l + tr 去末尾空白/换行，避免空变量时 echo 拼接多出“0\n0”
  actual_count=$(printf '%s\n' "$actual_files" | grep -c '\.md$' 2>/dev/null | tr -d ' \n' || true)
  [ -z "$actual_count" ] && actual_count=0
  if [ "$actual_count" -lt "$min_files" ]; then
    ERRORS+=("references/$prefix/ 有 $actual_count 个文件，期望 ≥$min_files")
  fi
  
  # 2. 章节文件**必须存在**（不是可选）
  local chapter="$case_dir/$chapter_rel"
  if [ ! -f "$chapter" ]; then
    ERRORS+=("章节文件不存在：$chapter_rel（必须存在）")
  fi
  
  # 3. 章节含至少 1 个引用 [{PREFIX}-XXX]（仅当章节存在时）
  local chapter_refs=""
  if [ -f "$chapter" ]; then
    local ref_pattern="\\[${prefix_upper}-[0-9]+\\]"
    chapter_refs=$(grep -oE "$ref_pattern" "$chapter" | sort -u || true)
    if [ -z "$chapter_refs" ]; then
      ERRORS+=("章节缺引用 $ref_pattern（$chapter_rel）")
    fi
  fi
  
  # 4. 每个引用的编号必须对应 references/ 真实文件
  if [ -n "$chapter_refs" ]; then
    local missing_files=()
    while IFS= read -r ref_token; do
      # 提取编号：[G1-001] → G1-001
      local ref_id
      ref_id=$(echo "$ref_token" | sed -E 's/\[([^]]+)\]/\1/')
      if [ ! -f "$ref_dir/$ref_id.md" ]; then
        missing_files+=("$ref_id")
      fi
    done <<< "$chapter_refs"
    if [ ${#missing_files[@]} -gt 0 ]; then
      ERRORS+=("引用对应文件不存在：${missing_files[*]}")
    fi
  fi
  
  # 5. 校验每个 reference 文件结构
  if [ -n "$actual_files" ]; then
    local bad_files=()
    while IFS= read -r f; do
      [ -z "$f" ] && continue
      local status
      status=$(validate_ref_file "$f")
      if [ "$status" != "OK" ]; then
        bad_files+=("$(basename "$f"):$status")
      fi
    done <<< "$actual_files"
    if [ ${#bad_files[@]} -gt 0 ]; then
      ERRORS+=("reference 文件结构不完整：${bad_files[*]}")
    fi
  fi
  
  # 汇总
  if [ ${#ERRORS[@]} -gt 0 ]; then
    echo "❌ Gate $gate 搜索证据校验失败：" >&2
    for e in "${ERRORS[@]}"; do
      echo "   - $e" >&2
    done
    return 1
  fi
  
  echo "✅ Gate $gate 搜索证据 OK：$actual_count 个文件 + 引用对应 + 文件结构"
  return 0
}

# 单元测试
if [ "${1:-}" = "--test" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  TEST_DIR=$(mktemp -d)
  trap "rm -rf $TEST_DIR" EXIT
  
  echo "=== T1: 全过（gate-1 满足） ==="
  mkdir -p "$TEST_DIR/case1/references/G1"
  cat > "$TEST_DIR/case1/references/G1/G1-001.md" <<'EOF'
# [G1-001] Test
- **URL**: https://example.com
- **抓取时间**: 2026-06-14
- **来源类型**: 官方

## 原文内容
text

## 关键数据点
- point 1
EOF
  cat > "$TEST_DIR/case1/references/G1/G1-002.md" <<'EOF'
# [G1-002] Test2
- **URL**: https://example.com/2
- **抓取时间**: 2026-06-14
- **来源类型**: 官方

## 关键数据点
- p
EOF
  mkdir -p "$TEST_DIR/case1/02-gate-by-chapter"
  echo "看 [G1-001] [G1-002]" > "$TEST_DIR/case1/02-gate-by-chapter/Gate-1-premise.md"
  if validate "$TEST_DIR/case1" "gate-1"; then
    echo "✅ T1 通过"
  else
    echo "❌ T1 预期通过却失败"; exit 1
  fi
  
  echo "=== T2: 引用对应文件不存在（预期失败） ==="
  echo "看 [G1-001] [G1-999]" > "$TEST_DIR/case1/02-gate-by-chapter/Gate-1-premise.md"
  if validate "$TEST_DIR/case1" "gate-1"; then
    echo "❌ T2 预期失败却通过"; exit 1
  else
    echo "✅ T2 按预期失败"
  fi
  
  echo "=== T3: reference 文件结构不完整（预期失败） ==="
  cat > "$TEST_DIR/case1/references/G1/G1-001.md" <<'EOF'
# [G1-001] Test
- **URL**: https://example.com
- **抓取时间**: 2026-06-14
## 原文内容
text
EOF
  echo "看 [G1-001]" > "$TEST_DIR/case1/02-gate-by-chapter/Gate-1-premise.md"
  if validate "$TEST_DIR/case1" "gate-1"; then
    echo "❌ T3 预期失败却通过"; exit 1
  else
    echo "✅ T3 按预期失败"
  fi
  
  echo "=== T4: 章节文件不存在（预期失败） ==="
  rm -rf "$TEST_DIR/case1/02-gate-by-chapter"
  if validate "$TEST_DIR/case1" "gate-1"; then
    echo "❌ T4 预期失败却通过"; exit 1
  else
    echo "✅ T4 按预期失败"
  fi
  
  echo "=== T5: 文件数不足（预期失败） ==="
  rm -rf "$TEST_DIR/case1/references/G1"
  mkdir -p "$TEST_DIR/case1/references/G1"
  echo "x" > "$TEST_DIR/case1/references/G1/G1-001.md"
  mkdir -p "$TEST_DIR/case1/02-gate-by-chapter"
  echo "看 [G1-001]" > "$TEST_DIR/case1/02-gate-by-chapter/Gate-1-premise.md"
  if validate "$TEST_DIR/case1" "gate-1"; then
    echo "❌ T5 预期失败却通过"; exit 1
  else
    echo "✅ T5 按预期失败"
  fi
  
  echo ""
  echo "=== 全部 T1-T5 测试通过 ==="
  exit 0
fi

# CLI
[ $# -ge 2 ] || { echo "用法: validate_gate_search.sh <case-dir> <gate-name> | --test" >&2; exit 1; }
validate "$1" "$2"
