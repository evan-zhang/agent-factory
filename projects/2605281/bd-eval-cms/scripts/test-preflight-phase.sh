#!/bin/bash
# test-preflight-phase.sh — Phase 5.5 readiness preflight 测试
#
# 用法：bash test-preflight-phase.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"
PREFLIGHT_SCRIPT="$SCRIPT_DIR/preflight-phase.sh"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Phase 5.5 Readiness Preflight 测试 ==="
echo ""

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
  local test_name="$1"
  local test_dir="$2"
  local expected_result="$3"

  TOTAL_TESTS=$((TOTAL_TESTS + 1))

  echo "测试 $TOTAL_TESTS: $test_name"
  echo "测试目录: $test_dir"
  echo "预期结果: $expected_result"

  if [ ! -d "$test_dir" ]; then
    echo -e "${RED}❌ 测试失败：测试目录不存在${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo ""
    return
  fi

  if bash "$PREFLIGHT_SCRIPT" "$test_dir" 2>&1; then
    if [ "$expected_result" = "pass" ]; then
      echo -e "${GREEN}✅ 测试通过${NC}"
      PASSED_TESTS=$((PASSED_TESTS + 1))
    else
      echo -e "${RED}❌ 测试失败：预期失败但实际通过${NC}"
      FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
  else
    if [ "$expected_result" = "fail" ]; then
      echo -e "${GREEN}✅ 测试通过（正确失败）${NC}"
      PASSED_TESTS=$((PASSED_TESTS + 1))
    else
      echo -e "${RED}❌ 测试失败：预期通过但实际失败${NC}"
      FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
  fi

  echo ""
}

write_completed_state() {
  local state_file="$1"
  cat > "$state_file" << 'EOF'
{
  "caseCode": "260611-TEST",
  "name": "测试案例",
  "gateStatus": {
    "phase-1": "completed",
    "phase-2": "completed",
    "one-pager": "completed",
    "gate-0": "completed",
    "gate-1": "completed",
    "gate-2": "completed",
    "gate-3": "completed",
    "gate-4": "completed",
    "gate-5": "completed",
    "phase-4-battle": "completed",
    "phase-5-merge": "completed"
  }
}
EOF
}

write_minimal_outputs() {
  local dir="$1"
  mkdir -p "$dir/02-gate-by-chapter" "$dir/battle" "$dir/references"
  echo "# 01-discovery.md" > "$dir/01-discovery.md"
  echo "# One-pager" > "$dir/02-gate-by-chapter/One-pager.md"
  echo "# Gate-0" > "$dir/02-gate-by-chapter/Gate-0-precondition.md"
  echo "# Gate-1" > "$dir/02-gate-by-chapter/Gate-1-premise.md"
  echo "# Gate-2" > "$dir/02-gate-by-chapter/Gate-2-positioning.md"
  echo "# Gate-3" > "$dir/02-gate-by-chapter/Gate-3-evidence.md"
  echo "# Gate-4" > "$dir/02-gate-by-chapter/Gate-4-payment.md"
  echo "# Gate-5" > "$dir/02-gate-by-chapter/Gate-5-cost.md"
  echo "# Battle Summary" > "$dir/03-battle-summary.md"
  echo "# Final Report $(printf '%100s' | tr ' ' 'A')" > "$dir/04-final-report.md"
}

# v0.10.1 新增：为正向案例造满 v0.10.0 9-gate 搜索证据
# phase-1/phase-2/one-pager 各需 ≥2 个 ref，gate-1≥2/gate-2≥3/gate-3≥3/gate-4≥2/gate-5≥2
# 且章节文件需含 [PREFIX-NNN] 引用，ref 文件需含 URL/抓取时间/关键数据点
write_search_evidence() {
  local dir="$1"
  
  # phase-1: P1 ≥2
  mkdir -p "$dir/references/P1"
  for i in 1 2; do
    cat > "$dir/references/P1/P1-00$i.md" <<EOF
# [P1-00$i] Test
- **URL**: https://example.com/p1-$i
- **抓取时间**: 2026-06-14
- **来源类型**: 官方

## 关键数据点
- p
EOF
  done
  echo "看 [P1-001] [P1-002]" > "$dir/01-discovery.md"
  
  # phase-2: P2 ≥2（章节路径为 02-discovery/01-background.md，详见 SKILL.md）
  mkdir -p "$dir/references/P2"
  for i in 1 2; do
    cat > "$dir/references/P2/P2-00$i.md" <<EOF
# [P2-00$i] Test
- **URL**: https://example.com/p2-$i
- **抓取时间**: 2026-06-14
- **来源类型**: 官方

## 关键数据点
- p
EOF
  done
  mkdir -p "$dir/02-discovery"
  echo "看 [P2-001] [P2-002]" > "$dir/02-discovery/01-background.md"
  
  # one-pager: OP ≥1
  mkdir -p "$dir/references/OP"
  cat > "$dir/references/OP/OP-001.md" <<'EOF'
# [OP-001] Test
- **URL**: https://example.com/op
- **抓取时间**: 2026-06-14
- **来源类型**: 官方

## 关键数据点
- p
EOF
  echo "看 [OP-001]" > "$dir/02-gate-by-chapter/One-pager.md"
  
  # gate-1: G1 ≥2
  mkdir -p "$dir/references/G1"
  for i in 1 2; do
    cat > "$dir/references/G1/G1-00$i.md" <<EOF
# [G1-00$i] Test
- **URL**: https://example.com/g1-$i
- **抓取时间**: 2026-06-14
- **来源类型**: 官方

## 关键数据点
- p
EOF
  done
  echo "看 [G1-001] [G1-002]" > "$dir/02-gate-by-chapter/Gate-1-premise.md"
  
  # gate-2: G2 ≥3
  mkdir -p "$dir/references/G2"
  for i in 1 2 3; do
    cat > "$dir/references/G2/G2-00$i.md" <<EOF
# [G2-00$i] Test
- **URL**: https://example.com/g2-$i
- **抓取时间**: 2026-06-14
- **来源类型**: 官方

## 关键数据点
- p
EOF
  done
  echo "看 [G2-001] [G2-002] [G2-003]" > "$dir/02-gate-by-chapter/Gate-2-positioning.md"
  
  # gate-3: G3 ≥3
  mkdir -p "$dir/references/G3"
  for i in 1 2 3; do
    cat > "$dir/references/G3/G3-00$i.md" <<EOF
# [G3-00$i] Test
- **URL**: https://example.com/g3-$i
- **抓取时间**: 2026-06-14
- **来源类型**: 官方

## 关键数据点
- p
EOF
  done
  echo "看 [G3-001] [G3-002] [G3-003]" > "$dir/02-gate-by-chapter/Gate-3-evidence.md"
  
  # gate-4: G4 ≥2
  mkdir -p "$dir/references/G4"
  for i in 1 2; do
    cat > "$dir/references/G4/G4-00$i.md" <<EOF
# [G4-00$i] Test
- **URL**: https://example.com/g4-$i
- **抓取时间**: 2026-06-14
- **来源类型**: 官方

## 关键数据点
- p
EOF
  done
  echo "看 [G4-001] [G4-002]" > "$dir/02-gate-by-chapter/Gate-4-payment.md"
  
  # gate-5: G5 ≥2
  mkdir -p "$dir/references/G5"
  for i in 1 2; do
    cat > "$dir/references/G5/G5-00$i.md" <<EOF
# [G5-00$i] Test
- **URL**: https://example.com/g5-$i
- **抓取时间**: 2026-06-14
- **来源类型**: 官方

## 关键数据点
- p
EOF
  done
  echo "看 [G5-001] [G5-002]" > "$dir/02-gate-by-chapter/Gate-5-cost.md"
}

TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT

echo "临时测试目录: $TEST_DIR"
echo ""

# 1. 正向最小案例
POSITIVE_DIR="$TEST_DIR/positive-case"
mkdir -p "$POSITIVE_DIR"
write_completed_state "$POSITIVE_DIR/state.json"
write_minimal_outputs "$POSITIVE_DIR"
write_search_evidence "$POSITIVE_DIR"
run_test "正向最小案例（所有关键产物齐全）" "$POSITIVE_DIR" "pass"

# 2. 缺少 01-discovery.md
NEGATIVE_DIR="$TEST_DIR/negative-missing-discovery"
mkdir -p "$NEGATIVE_DIR"
write_completed_state "$NEGATIVE_DIR/state.json"
write_minimal_outputs "$NEGATIVE_DIR"
rm -f "$NEGATIVE_DIR/01-discovery.md"
run_test "负向缺失案例（缺少 01-discovery.md）" "$NEGATIVE_DIR" "fail"

# 3. 缺少 04-final-report.md
NEGATIVE_DIR2="$TEST_DIR/negative-missing-final-report"
mkdir -p "$NEGATIVE_DIR2"
write_completed_state "$NEGATIVE_DIR2/state.json"
write_minimal_outputs "$NEGATIVE_DIR2"
rm -f "$NEGATIVE_DIR2/04-final-report.md"
run_test "负向缺失案例（缺少 04-final-report.md）" "$NEGATIVE_DIR2" "fail"

# 4. gateStatus 未完成
NEGATIVE_DIR3="$TEST_DIR/negative-incomplete-gate"
mkdir -p "$NEGATIVE_DIR3"
write_completed_state "$NEGATIVE_DIR3/state.json"
write_minimal_outputs "$NEGATIVE_DIR3"
python3 - "$NEGATIVE_DIR3/state.json" <<'PY'
import json, sys
p=sys.argv[1]
d=json.load(open(p))
d['gateStatus']['gate-3']='in_progress'
open(p,'w').write(json.dumps(d, ensure_ascii=False, indent=2))
PY
run_test "负向状态案例（gate-3 未完成）" "$NEGATIVE_DIR3" "fail"

# 5. gateStatus 缺失（生产默认不放行）
NEGATIVE_DIR4="$TEST_DIR/negative-missing-gatestatus"
mkdir -p "$NEGATIVE_DIR4"
echo '{"caseCode":"legacy-case"}' > "$NEGATIVE_DIR4/state.json"
write_minimal_outputs "$NEGATIVE_DIR4"
run_test "负向状态案例（缺少 gateStatus）" "$NEGATIVE_DIR4" "fail"

# 6. 缺少 Gate-0 物理产物
NEGATIVE_DIR5="$TEST_DIR/negative-missing-gate0-file"
mkdir -p "$NEGATIVE_DIR5"
write_completed_state "$NEGATIVE_DIR5/state.json"
write_minimal_outputs "$NEGATIVE_DIR5"
rm -f "$NEGATIVE_DIR5/02-gate-by-chapter/Gate-0-precondition.md"
run_test "负向产物案例（缺少 Gate-0 文件）" "$NEGATIVE_DIR5" "fail"

# 7. 实际完整案例 Epioxa
EPIOXA_DIR="$SKILL_ROOT/Epioxa"
if [ -d "$EPIOXA_DIR" ]; then
  run_test "实际案例测试（Epioxa 完整案例）" "$EPIOXA_DIR" "pass"
else
  echo -e "${YELLOW}⚠️  跳过实际案例测试：Epioxa 目录不存在${NC}"
  echo ""
fi

# 8. 旧案例回放跳过路径
LEGACY_DIR="$SKILL_ROOT/MB-001-Mage-Biologics"
if [ -d "$LEGACY_DIR" ]; then
  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  echo "测试 $TOTAL_TESTS: 旧案例回放跳过路径（BD_EVAL_CMS_SKIP_PREFLIGHT=1）"
  if BD_EVAL_CMS_SKIP_PREFLIGHT=1 bash "$PREFLIGHT_SCRIPT" "$LEGACY_DIR" >/tmp/bd-eval-preflight-skip.log 2>&1; then
    echo -e "${GREEN}✅ 测试通过${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
  else
    echo -e "${RED}❌ 测试失败：跳过路径未生效${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
  fi
  echo ""
fi

echo "=== 测试汇总 ==="
echo "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
  echo -e "${GREEN}🎉 所有测试通过！${NC}"
  exit 0
else
  echo -e "${RED}❌ 部分测试失败${NC}"
  exit 1
fi
