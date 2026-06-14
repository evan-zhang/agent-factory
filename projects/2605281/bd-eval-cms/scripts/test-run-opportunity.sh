#!/usr/bin/env bash
# test-run-opportunity.sh — 单元测试
# 用法：bash scripts/test-run-opportunity.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"
SCRIPT="$SCRIPT_DIR/run-opportunity.sh"
TMPDIR_RUN="$(mktemp -d -t bd-run-opp-test-XXXXXX)"
trap 'rm -rf "$TMPDIR_RUN"' EXIT

PASS=0
FAIL=0
TEST_NUM=0

# 临时把 SKILL_ROOT 指到 sandbox，避免污染真实 bd-eval-cms 工作区
SANDBOX_ROOT="$(mktemp -d -t bd-sandbox-XXXXXX)"
mkdir -p "$SANDBOX_ROOT/scripts" "$SANDBOX_ROOT/templates" "$SANDBOX_ROOT/references"

# 复制 run-opportunity.sh 之外不必要；改为直接用 SCRIPT 调用时覆盖 SKILL_ROOT
# 我们的脚本通过 SKILL_ROOT=$(dirname $SCRIPT_DIR) 推断，无法外部覆盖
# 改为 monkey-patch：复制整个 run-opportunity.sh 到 sandbox，substitute SCRIPT_DIR 路径
# 简单做法：临时建立真实 $SKILL_ROOT 下的 _test_run 子目录做测试，跑完清理

REAL_RUN_DIR="$SKILL_ROOT/_test_run_opp_$$"
mkdir -p "$REAL_RUN_DIR"
cleanup_real() {
  rm -rf "$REAL_RUN_DIR" "$SANDBOX_ROOT"
}
trap 'cleanup_real; rm -rf "$TMPDIR_RUN"' EXIT

pass() { PASS=$((PASS + 1)); echo "  ✅ $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  ❌ $1"; }
new_test() { TEST_NUM=$((TEST_NUM + 1)); echo ""; echo "[$TEST_NUM] $1"; }

# ============ 测试 ============

new_test "缺少 product → exit 1"
if bash "$SCRIPT" --company "X" >/dev/null 2>&1; then
  fail "应 exit 1，实际 exit 0"
else
  pass "缺少 product 报错"
fi

new_test "缺少 company → exit 1"
if bash "$SCRIPT" --product "X" >/dev/null 2>&1; then
  fail "应 exit 1，实际 exit 0"
else
  pass "缺少 company 报错"
fi

new_test "无效 mode → exit 1"
if bash "$SCRIPT" --product "X" --company "Y" --mode=invalid >/dev/null 2>&1; then
  fail "应 exit 1，实际 exit 0"
else
  pass "无效 mode 报错"
fi

new_test "无效 scheme → exit 1"
if bash "$SCRIPT" --product "X" --company "Y" --scheme=D >/dev/null 2>&1; then
  fail "应 exit 1，实际 exit 0"
else
  pass "无效 scheme 报错"
fi

new_test "--ext 不存在文件 → exit 1"
if bash "$SCRIPT" --product "X" --company "Y" --ext /nonexistent/foo.pdf >/dev/null 2>&1; then
  fail "应 exit 1"
else
  pass "--ext 不存在报错"
fi

new_test "--help → exit 0"
if bash "$SCRIPT" --help >/dev/null 2>&1; then
  pass "--help 正常"
else
  fail "--help 失败"
fi

# 真实创建测试 — 用子目录隔离
TEST_PRODUCT="RUNT-$$"
TEST_COMPANY="TST-$$"
TEST_PRODUCT2="RNT2-$$"

# 注意：后续测试中用 --semi 模式（避免自动调起 orchestrator）
# orchestrator-resume.sh 不会创建实际报告，只会标 in_progress + 退出
# 而 start-phase.sh 当前是占位实现，会在 state.json 写 in_progress 后 echo

new_test "英文 product 缩写生成 (4字母大写)"
ABBREV=$(python3 - "$TEST_PRODUCT" <<'PY'
import sys, re
name = sys.argv[1]
ascii_letters = re.findall(r'[A-Za-z0-9]+', name)
print(''.join(ascii_letters)[:4].upper())
PY
)
if [ "$ABBREV" = "RUNT" ]; then
  pass "英文 4字母缩写 = RUNT"
else
  fail "英文 4字母缩写 = $ABBREV (期望 RUNT)"
fi

new_test "中文 product pypinyin 缩写"
ABBREV_CN=$(python3 - "乌司他丁" <<'PY'
import sys, re
from pypinyin import lazy_pinyin, Style
name = sys.argv[1]
chinese_chars = re.findall(r'[\u4e00-\u9fff]+', name)
chinese_part = ''
for chunk in chinese_chars:
    chinese_part += ''.join(lazy_pinyin(chunk, style=Style.FIRST_LETTER))
print(chinese_part[:4].upper())
PY
)
if [ "$ABBREV_CN" = "WSTD" ]; then
  pass "中文 pypinyin 缩写 = WSTD"
else
  fail "中文 pypinyin 缩写 = $ABBREV_CN (期望 WSTD)"
fi

# 真实跑一次（用 semi 模式避免 orchestrator 干扰）
TEST_CASE_DIR=""

new_test "真实创建 (semi 模式，不调 orchestrator)"
OUT=$(cd "$SKILL_ROOT" && bash "$SCRIPT" --product "$TEST_PRODUCT" --company "$TEST_COMPANY" --mode semi 2>&1)
RC=$?
TEST_CASE_DIR=$(echo "$OUT" | grep '^CASE_PATH=' | head -1 | cut -d= -f2-)
TEST_CASE_CODE=$(echo "$OUT" | grep '^CASE_CODE=' | head -1 | cut -d= -f2-)
if [ "$RC" -eq 0 ] && [ -n "$TEST_CASE_DIR" ] && [ -d "$TEST_CASE_DIR" ]; then
  pass "case 已创建: $TEST_CASE_CODE @ $TEST_CASE_DIR"
else
  fail "case 创建失败 (rc=$RC, dir=$TEST_CASE_DIR)"
fi

new_test "case dir 包含必要子目录"
if [ -d "$TEST_CASE_DIR/02-gate-by-chapter" ] \
   && [ -d "$TEST_CASE_DIR/battle" ] \
   && [ -d "$TEST_CASE_DIR/references/P1" ] \
   && [ -d "$TEST_CASE_DIR/EXT" ]; then
  pass "子目录齐"
else
  fail "子目录不全"
fi

new_test "state.json 存在 + 包含 12 gateStatus"
if [ -f "$TEST_CASE_DIR/state.json" ] && jq -e '.gateStatus | length == 12' "$TEST_CASE_DIR/state.json" >/dev/null 2>&1; then
  pass "state.json 12 gateStatus"
else
  fail "state.json 不全"
fi

new_test "00-opportunity.md 存在 + 含 product/company"
if [ -f "$TEST_CASE_DIR/00-opportunity.md" ] \
   && grep -q "$TEST_PRODUCT" "$TEST_CASE_DIR/00-opportunity.md" \
   && grep -q "$TEST_COMPANY" "$TEST_CASE_DIR/00-opportunity.md"; then
  pass "00-opportunity.md 内容正确"
else
  fail "00-opportunity.md 内容缺失"
fi

new_test "幂等续跑（同 input 二次调用）"
OUT2=$(cd "$SKILL_ROOT" && bash "$SCRIPT" --product "$TEST_PRODUCT" --company "$TEST_COMPANY" --mode semi 2>&1)
TEST_CASE_DIR2=$(echo "$OUT2" | grep '^CASE_PATH=' | head -1 | cut -d= -f2-)
TEST_CASE_CODE2=$(echo "$OUT2" | grep '^CASE_CODE=' | head -1 | cut -d= -f2-)
if [ "$TEST_CASE_DIR" = "$TEST_CASE_DIR2" ] && [ "$TEST_CASE_CODE" = "$TEST_CASE_CODE2" ]; then
  pass "幂等：caseCode / dir 不变"
else
  fail "幂等失败：dir1=$TEST_CASE_DIR dir2=$TEST_CASE_DIR2"
fi

new_test "stdout 包含 4 个结构化 prefix"
PREFIX_OK=true
for p in CASE_PATH CASE_CODE PHASE_STATUS OPPORTUNITY_ID; do
  if ! echo "$OUT" | grep -q "^$p="; then
    PREFIX_OK=false
    fail "缺 prefix: $p"
  fi
done
$PREFIX_OK && pass "4 个 prefix 齐全"

new_test "--json 形式（从 stdin）"
JSON_TEST_PROD="JSTN-$$"
JSON_TEST_CO="JCO-$$"
JSON_CONTENT="{\"product\":\"$JSON_TEST_PROD\",\"company\":\"$JSON_TEST_CO\",\"indication\":\"测试\",\"scheme\":\"A\"}"
OUT3=$(cd "$SKILL_ROOT" && echo "$JSON_CONTENT" | bash "$SCRIPT" --json - --mode semi 2>&1)
TEST_CODE3=$(echo "$OUT3" | grep '^CASE_CODE=' | head -1 | cut -d= -f2-)
TEST_DIR3=$(echo "$OUT3" | grep '^CASE_PATH=' | head -1 | cut -d= -f2-)
if [ -n "$TEST_DIR3" ] && [ -d "$TEST_DIR3" ] && grep -q "测试" "$TEST_DIR3/00-opportunity.md"; then
  pass "--json - 模式 OK: $TEST_CODE3"
else
  fail "--json - 模式失败"
fi

new_test "同日不同 product → 走 -1 / -2 后缀"
# TEST_PRODUCT 已占 BASE_CODE 第一个；同缩写再 create 一个
OUT4=$(cd "$SKILL_ROOT" && bash "$SCRIPT" --product "${TEST_PRODUCT}-ALT" --company "OtherCo" --mode semi 2>&1)
# abbrev of "RUNT-$$-ALT" = RUNT，但 company 不同 → 应走 -1
TEST_CODE4=$(echo "$OUT4" | grep '^CASE_CODE=' | head -1 | cut -d= -f2-)
if echo "$TEST_CODE4" | grep -qE -- '(-1|-01|-02)$'; then
  pass "冲突后缀生效: $TEST_CODE4"
else
  fail "冲突后缀未生效: $TEST_CODE4"
fi

new_test "dry-run 模式零副作用"
BEFORE=$(ls "$SKILL_ROOT" | wc -l)
OUT5=$(cd "$SKILL_ROOT" && bash "$SCRIPT" --product "DRYR-$$" --company "DryCo" --dry-run 2>&1)
RC5=$?
AFTER=$(ls "$SKILL_ROOT" | wc -l)
if [ "$RC5" -eq 0 ] && [ "$BEFORE" = "$AFTER" ] && echo "$OUT5" | grep -q "CASE_CODE="; then
  pass "dry-run 零副作用"
else
  fail "dry-run 副作用 (rc=$RC5, before=$BEFORE, after=$AFTER)"
fi

# 清理
[ -n "$TEST_CASE_DIR" ] && rm -rf "$TEST_CASE_DIR"
[ -n "$TEST_DIR3" ] && rm -rf "$TEST_DIR3"
OUT4_DIR=$(echo "$OUT4" | grep '^CASE_PATH=' | head -1 | cut -d= -f2-)
[ -n "$OUT4_DIR" ] && [ -d "$OUT4_DIR" ] && rm -rf "$OUT4_DIR"

# ============ 汇总 ============
echo ""
echo "==================================="
echo "总测试数: $TEST_NUM"
echo -e "通过: \033[32m$PASS\033[0m"
echo -e "失败: \033[31m$FAIL\033[0m"
echo "==================================="

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
