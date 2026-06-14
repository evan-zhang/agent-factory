#!/bin/bash
# test-merge-report.sh — 验证 Phase 5 纯合并行为

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

pass_count=0
fail_count=0

fail() {
  echo "❌ $1"
  fail_count=$((fail_count + 1))
}

pass() {
  echo "✅ $1"
  pass_count=$((pass_count + 1))
}

assert_contains() {
  local file="$1"
  local text="$2"
  local label="$3"
  if grep -Fq "$text" "$file"; then
    pass "$label"
  else
    fail "$label"
  fi
}

assert_not_contains() {
  local file="$1"
  local text="$2"
  local label="$3"
  if grep -Fq "$text" "$file"; then
    fail "$label"
  else
    pass "$label"
  fi
}

create_case_new_names() {
  local dir="$1"
  mkdir -p "$dir/02-gate-by-chapter" "$dir/battle" "$dir/references"
  cat > "$dir/state.json" <<'JSON'
{
  "caseCode": "TEST-MERGE-NEW",
  "displayName": "测试新命名",
  "businessEntity": "测试主体",
  "routedSkill": "A-1",
  "scheme": "B"
}
JSON
  cat > "$dir/01-discovery.md" <<'EOF'
# Discovery
DISCOVERY_UNIQUE_MARKER_001
EOF
  cat > "$dir/02-gate-by-chapter/One-pager.md" <<'EOF'
# One-pager
ONE_PAGER_UNIQUE_MARKER_001
EOF
  cat > "$dir/02-gate-by-chapter/Gate-0-premise.md" <<'EOF'
# Gate 0 新命名
GATE0_UNIQUE_MARKER_001
EOF
  cat > "$dir/02-gate-by-chapter/Gate-1-rights.md" <<'EOF'
# Gate 1 新命名
GATE1_UNIQUE_MARKER_001
这一段必须原样保留，不允许摘要或改写。
EOF
  cat > "$dir/02-gate-by-chapter/Gate-2-clinical-regulatory.md" <<'EOF'
# Gate 2 新命名
GATE2_UNIQUE_MARKER_001
EOF
  cat > "$dir/02-gate-by-chapter/Gate-3-market.md" <<'EOF'
# Gate 3 新命名
GATE3_UNIQUE_MARKER_001
EOF
  cat > "$dir/02-gate-by-chapter/Gate-4-commercial-finance.md" <<'EOF'
# Gate 4 新命名
GATE4_UNIQUE_MARKER_001
EOF
  cat > "$dir/02-gate-by-chapter/Gate-5-decision.md" <<'EOF'
# Gate 5 新命名
GATE5_UNIQUE_MARKER_001
EOF
  cat > "$dir/03-battle-summary.md" <<'EOF'
# Battle Summary
BATTLE_UNIQUE_MARKER_001
EOF
}

create_case_alias_priority() {
  local dir="$1"
  mkdir -p "$dir/02-gate-by-chapter"
  cat > "$dir/state.json" <<'JSON'
{
  "caseCode": "TEST-MERGE-ALIAS",
  "displayName": "测试别名优先",
  "businessEntity": "测试主体",
  "routedSkill": "A-1"
}
JSON
  cat > "$dir/02-gate-by-chapter/One-pager.md" <<'EOF'
# One-pager
ALIAS_ONE_PAGER
EOF
  cat > "$dir/02-gate-by-chapter/Gate-1-rights.md" <<'EOF'
# Gate 1 新命名优先
ALIAS_NEW_GATE1_INCLUDED
EOF
  cat > "$dir/02-gate-by-chapter/Gate-1-premise.md" <<'EOF'
# Gate 1 老命名不应重复合并
ALIAS_LEGACY_GATE1_SHOULD_NOT_APPEAR
EOF
}

run_merge() {
  local dir="$1"
  bash "$ROOT_DIR/scripts/merge-report.sh" "$dir" > "$dir/merge.log" 2>&1
}

echo "=== test-merge-report.sh ==="

# Test 1: v0.9.2 新命名全部合并，Gate 原文不改写
CASE1="$TMP_ROOT/case-new"
create_case_new_names "$CASE1"
run_merge "$CASE1"
REPORT1="$CASE1/04-final-report.md"

assert_contains "$REPORT1" "DISCOVERY_UNIQUE_MARKER_001" "Discovery 原文进入最终报告"
assert_contains "$REPORT1" "ONE_PAGER_UNIQUE_MARKER_001" "One-pager 原文进入最终报告"
assert_contains "$REPORT1" "GATE0_UNIQUE_MARKER_001" "Gate 0 新命名原文进入最终报告"
assert_contains "$REPORT1" "GATE1_UNIQUE_MARKER_001" "Gate 1 新命名原文进入最终报告"
assert_contains "$REPORT1" "这一段必须原样保留，不允许摘要或改写。" "Gate 1 长句原样保留"
assert_contains "$REPORT1" "GATE2_UNIQUE_MARKER_001" "Gate 2 新命名原文进入最终报告"
assert_contains "$REPORT1" "GATE3_UNIQUE_MARKER_001" "Gate 3 新命名原文进入最终报告"
assert_contains "$REPORT1" "GATE4_UNIQUE_MARKER_001" "Gate 4 新命名原文进入最终报告"
assert_contains "$REPORT1" "GATE5_UNIQUE_MARKER_001" "Gate 5 新命名原文进入最终报告"
assert_contains "$REPORT1" "BATTLE_UNIQUE_MARKER_001" "Battle 原文进入最终报告"
assert_contains "$CASE1/merge.log" "原文连续保留" "merge log 包含原文保真检查"
assert_contains "$CASE1/merge.log" "行数比通过" "merge log 行数比通过"

# Test 2: 新旧别名同时存在时，新命名优先且不重复合并旧别名
CASE2="$TMP_ROOT/case-alias"
create_case_alias_priority "$CASE2"
run_merge "$CASE2"
REPORT2="$CASE2/04-final-report.md"

assert_contains "$REPORT2" "ALIAS_NEW_GATE1_INCLUDED" "新 Gate-1-rights 优先合并"
assert_not_contains "$REPORT2" "ALIAS_LEGACY_GATE1_SHOULD_NOT_APPEAR" "旧 Gate-1-premise 不重复合并"

# Test 3: 真实 260613-SMQT 可以通过合并，不因短 Gate 文件被 200 行阈值阻断；不覆盖真实案例，用拷贝测试
CASE3="$TMP_ROOT/case-smqt-copy"
cp -R "$ROOT_DIR/260613-SMQT" "$CASE3"
run_merge "$CASE3"
REPORT3="$CASE3/04-final-report.md"
assert_contains "$REPORT3" "# Gate 1 权属与合作可能性" "真实 SMQT 拷贝：Gate 1 原始标题保留"
assert_contains "$REPORT3" "# Gate 3 市场与竞争格局" "真实 SMQT 拷贝：Gate 3 原始标题保留"
assert_contains "$REPORT3" "# Gate 5 综合决策与投委会建议" "真实 SMQT 拷贝：Gate 5 原始标题保留"
assert_contains "$CASE3/merge.log" "报告/源文件比" "真实 SMQT 拷贝：行数比已计算"

printf '\n=== 结果 ===\n'
echo "PASS: $pass_count"
echo "FAIL: $fail_count"

if [ "$fail_count" -ne 0 ]; then
  exit 1
fi

exit 0
