#!/bin/bash
# merge-report.sh — Phase 5 报告合并脚本（纯程序行为）
# 用法: bash scripts/merge-report.sh {品种目录路径}
# 示例: bash scripts/merge-report.sh projects/2605281/bd-eval-cms/MB-001-Mage-Biologics
#
# 原则：
# 1. Phase 5 只做“合并”，不改写、不缩写 Gate 原文。
# 2. Gate 正文必须通过 cat 原样进入 04-final-report.md。
# 3. 脚本只允许增加封面、章节包装标题、分隔线和执行摘要占位符。

set -euo pipefail

DIR="${1:?merge-report.sh requires a directory path}"

if [ ! -d "$DIR" ]; then
  echo "错误: 目录不存在 $DIR"
  exit 1
fi

STATE="$DIR/state.json"
REPORT="$DIR/04-final-report.md"
GATE_DIR="$DIR/02-gate-by-chapter"

if [ ! -f "$STATE" ]; then
  echo "错误: state.json 不存在"
  exit 1
fi

# ===== 0. 预检：合并零件存在性 + 兼容 v0.9.2 新命名 =====
echo "=== Phase 5 合并预检 ==="

# v0.7.1 之前案例：缺目录 → 跳过 merge 主体，避免覆盖原 04-final-report.md
if [ ! -d "$GATE_DIR" ]; then
  echo "⚠️ 02-gate-by-chapter/ 目录不存在（旧案例）"
  echo "  说明：不重跑 merge，避免覆盖原 04-final-report.md"
  echo "  如确需重跑，请先生成 Gate 分件后再执行本脚本"
  exit 0
fi

# 记录本次实际合并的文件和章节标题，避免旧/新 alias 重复计入。
MERGE_FILES=()
MERGE_TITLES=()
SOURCE_FILES=()
MISSING_WARNINGS=0

add_merge_file() {
  local filepath="$1"
  local title="$2"

  if [ -f "$filepath" ]; then
    MERGE_FILES+=("$filepath")
    MERGE_TITLES+=("$title")
    SOURCE_FILES+=("$filepath")
    echo "  ✅ $title ← $(basename "$filepath")"
  else
    echo "  ❌ 文件不存在（FAIL）: $filepath"
    MISSING_WARNINGS=$((MISSING_WARNINGS + 1))
  fi
}

add_first_existing() {
  local title="$1"
  shift
  local name=""
  for name in "$@"; do
    if [ -f "$GATE_DIR/$name" ]; then
      add_merge_file "$GATE_DIR/$name" "$title"
      return 0
    fi
  done
  echo "  ❌ $title 未找到候选文件（FAIL）: $*"
  MISSING_WARNINGS=$((MISSING_WARNINGS + 1))
  return 1
}

is_legacy_longform_gate() {
  case "$(basename "$1")" in
    Gate-1-premise.md|Gate-1-precondition.md|Gate-2-positioning.md|Gate-3-evidence.md|Gate-4-payment.md|Gate-5-cost.md|Gate-6-dealability.md|Gate-6-feasibility.md|Gate-6-doability.md|Gate-6-deal.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

check_legacy_gate_contract() {
  local fpath="$1"
  local gfile
  gfile="$(basename "$fpath")"

  # v0.9.2 新命名是短分件/真实验收格式，不再用 v0.7.1 的 200 行硬门槛阻断。
  # 旧 longform gate 仍保留 TL;DR 5 字段强检查；体量改为警告，避免“合并动作”因为长度判断阻断。
  if is_legacy_longform_gate "$fpath"; then
    local missing=()
    grep -q "^| \*\*评级\*\*" "$fpath" || missing+=("评级")
    grep -q "^| \*\*评分\*\*" "$fpath" || missing+=("评分")
    grep -q "^| \*\*关键风险\*\*" "$fpath" || missing+=("关键风险")
    grep -q "^| \*\*推荐路径\*\*" "$fpath" || missing+=("推荐路径")
    grep -q "^| \*\*下一步\*\*" "$fpath" || missing+=("下一步")
    if [ ${#missing[@]} -gt 0 ]; then
      echo "  ❌ $gfile 缺 TL;DR 字段: ${missing[*]}"
      return 1
    fi

    local lines
    lines=$(wc -l < "$fpath")
    if [ "$lines" -lt 200 ]; then
      echo "  ⚠️ $gfile 仅 ${lines} 行 (<200)，保留为警告；合并仍按原文 cat 执行"
    else
      echo "  ✅ $gfile TL;DR + 体量检查通过"
    fi
  fi
}

echo "--- 本次合并映射 ---"
if [ -f "$DIR/01-discovery.md" ]; then
  SOURCE_FILES+=("$DIR/01-discovery.md")
  echo "  ✅ Discovery ← 01-discovery.md"
else
  echo "  ❌ Discovery 缺失（FAIL）: 01-discovery.md"
  MISSING_WARNINGS=$((MISSING_WARNINGS + 1))
fi

add_merge_file "$GATE_DIR/One-pager.md" "One-pager 终局先立"

# v0.9.2 新命名优先；legacy 命名兼容。
add_first_existing "Gate 0 前提与路由确认" \
  Gate-0-premise.md Gate-0-precondition.md || true
add_first_existing "Gate 1 权属与合作可能性" \
  Gate-1-rights.md Gate-1-premise.md Gate-1-precondition.md || true
add_first_existing "Gate 2 临床与注册路径" \
  Gate-2-clinical-regulatory.md Gate-2-positioning.md || true
add_first_existing "Gate 3 市场与竞争格局" \
  Gate-3-market.md Gate-3-evidence.md || true
add_first_existing "Gate 4 商业化与财务测算" \
  Gate-4-commercial-finance.md Gate-4-payment.md || true
add_first_existing "Gate 5 综合决策与投委会建议" \
  Gate-5-decision.md Gate-5-cost.md || true
add_first_existing "Gate 6 可做门" \
  Gate-6-dealability.md Gate-6-feasibility.md Gate-6-doability.md Gate-6-deal.md || true

if [ -f "$DIR/03-battle-summary.md" ]; then
  SOURCE_FILES+=("$DIR/03-battle-summary.md")
  echo "  ✅ Battle Summary ← 03-battle-summary.md"
else
  echo "  ❌ Battle Summary 缺失（FAIL）: 03-battle-summary.md"
  MISSING_WARNINGS=$((MISSING_WARNINGS + 1))
fi

if [ -f "$DIR/references/REFERENCES.md" ]; then
  SOURCE_FILES+=("$DIR/references/REFERENCES.md")
  echo "  ✅ References ← references/REFERENCES.md"
else
  echo "  ⚠️ References 缺失（WARN）: references/REFERENCES.md（程序化产物，可能未生成）"
fi

if [ ${#MERGE_FILES[@]} -eq 0 ]; then
  echo "❌ 未找到任何可合并的 Gate/One-pager 文件"
  exit 2
fi

echo "--- Legacy Gate 契约检查 ---"
PRECHECK_FAILED=0
for f in "${MERGE_FILES[@]}"; do
  if ! check_legacy_gate_contract "$f"; then
    PRECHECK_FAILED=1
  fi
done

if [ "$PRECHECK_FAILED" -eq 1 ]; then
  echo ""
  echo "❌ 预检未通过，请修正后重跑"
  exit 2
fi

if [ "$MISSING_WARNINGS" -gt 0 ]; then
  echo ""
  echo "❌ 预检未通过：发现 ${MISSING_WARNINGS} 个缺失项（FAIL）"
  echo "   v0.10.6：缺正式零件不再只是警告，而是阻断合并"
  exit 1
fi

echo "✅ 合并预检通过（缺失候选仅警告数: ${MISSING_WARNINGS}）"
echo ""

# 从 state.json 提取关键字段
CASE_CODE=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('caseCode','unknown'))")
DISPLAY_NAME=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('displayName') or d.get('productName') or d.get('product') or 'unknown')")
SCHEME=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('scheme','B'))")
ENTITY=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('businessEntity','待确认'))")
SKILL=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('routedSkill','待路由'))")
DATE=$(date '+%Y-%m-%d')

echo "=== 报告合并开始 ==="
echo "品种: $DISPLAY_NAME"
echo "案件代号: $CASE_CODE"
echo "方案: $SCHEME"

# 临时文件
TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

# ===== 1. 封面 =====
cat > "$TMPFILE" << EOF
# ${DISPLAY_NAME} — CMS投前评估报告

---

**案件代号**：${CASE_CODE}
**评估品种**：${DISPLAY_NAME}
**业务主体**：${ENTITY}
**评估技能**：${SKILL}
**评估日期**：${DATE}

---

EOF

# ===== 2. 执行摘要占位 =====
# 执行摘要需要上游生成独立源文件；本脚本只放占位，绝不根据 Gate 重写。
cat >> "$TMPFILE" << 'EOF'
## 第一章：执行摘要

<!-- EXECUTIVE_SUMMARY_PLACEHOLDER -->
<!-- 合并脚本不重写、不缩写 Gate 原文；如需执行摘要，请在上游生成独立源文件后再合并。 -->

---

EOF

# ===== 3. Discovery =====
if [ -f "$DIR/01-discovery.md" ]; then
  echo "--- 合并 Discovery ---"
  echo "## 第二章：标的发现（DISCOVERY）" >> "$TMPFILE"
  echo "" >> "$TMPFILE"
  cat "$DIR/01-discovery.md" >> "$TMPFILE"
  echo "" >> "$TMPFILE"
  echo "---" >> "$TMPFILE"
  echo "" >> "$TMPFILE"
fi

# ===== 4. One-pager + Gate 分件 =====
CHAPTER_NUM=3
merge_file() {
  local filepath="$1"
  local chapter_title="$2"

  echo "--- 合并 ${chapter_title} ---"
  echo "## 第${CHAPTER_NUM}章：${chapter_title}" >> "$TMPFILE"
  echo "" >> "$TMPFILE"
  # 核心约束：正文用 cat 原样合并，不做任何改写/摘要/过滤。
  cat "$filepath" >> "$TMPFILE"
  echo "" >> "$TMPFILE"
  echo "---" >> "$TMPFILE"
  echo "" >> "$TMPFILE"
  CHAPTER_NUM=$((CHAPTER_NUM + 1))
}

for idx in "${!MERGE_FILES[@]}"; do
  merge_file "${MERGE_FILES[$idx]}" "${MERGE_TITLES[$idx]}"
done

# ===== 5. Battle =====
if [ -f "$DIR/03-battle-summary.md" ]; then
  echo "--- 合并 Battle Summary ---"
  echo "## 第${CHAPTER_NUM}章：Gate Battle 对抗审查总结" >> "$TMPFILE"
  echo "" >> "$TMPFILE"
  cat "$DIR/03-battle-summary.md" >> "$TMPFILE"
  echo "" >> "$TMPFILE"
  echo "---" >> "$TMPFILE"
  echo "" >> "$TMPFILE"
  CHAPTER_NUM=$((CHAPTER_NUM + 1))
fi

# Battle 详细文件
for bf in "$DIR/battle/BATTLE-R1-AUDITOR.md" "$DIR/battle/BATTLE-R1-EXECUTOR.md"; do
  if [ -f "$bf" ]; then
    bname=$(basename "$bf" .md)
    echo "--- 合并 Battle: $bname ---"
    echo "### ${bname}" >> "$TMPFILE"
    echo "" >> "$TMPFILE"
    cat "$bf" >> "$TMPFILE"
    echo "" >> "$TMPFILE"
    SOURCE_FILES+=("$bf")
  fi
done

# ===== 6. 参考文献索引 =====
if [ -f "$DIR/references/REFERENCES.md" ]; then
  echo "--- 合并参考文献 ---"
  echo "## 附录：参考文献" >> "$TMPFILE"
  echo "" >> "$TMPFILE"
  cat "$DIR/references/REFERENCES.md" >> "$TMPFILE"
  echo "" >> "$TMPFILE"
fi

# ===== 写入最终报告 =====
cp "$TMPFILE" "$REPORT"

# ===== 7. 格式校验 =====
echo ""
echo "=== 格式校验 ==="

TOTAL_LINES=$(wc -l < "$REPORT")
echo "报告总行数: ${TOTAL_LINES}"

# 检查本次实际合并源文件总行数；只计算选中的 alias，避免旧/新文件重复计入。
SOURCE_LINES=0
for f in "${SOURCE_FILES[@]}"; do
  if [ -f "$f" ]; then
    L=$(wc -l < "$f")
    SOURCE_LINES=$((SOURCE_LINES + L))
  fi
done
echo "源文件总行数: ${SOURCE_LINES}"

# 报告包含封面、章节标题、分隔线和占位符，所以应该 >= 源文件行数。
if [ "$SOURCE_LINES" -gt 0 ]; then
  RATIO_VALUE=$(python3 -c "print($TOTAL_LINES / $SOURCE_LINES * 100)")
  RATIO=$(python3 -c "print(f'{$TOTAL_LINES / $SOURCE_LINES * 100:.1f}%')")
  echo "报告/源文件比: ${RATIO}（预期 ≥100%，因为是纯合并+少量包装行）"
  if python3 -c "import sys; sys.exit(0 if $RATIO_VALUE >= 100 else 1)"; then
    echo "  ✅ 行数比通过"
  else
    echo "  ❌ 行数比 <100%，合并可能漏内容"
    exit 4
  fi
else
  echo "报告/源文件比: N/A（源文件总行数为 0）"
fi

# 精确保真检查：每个源文件的内容必须作为连续文本片段出现在最终报告中。
echo ""
echo "原文保真检查:"
python3 - "$REPORT" "${SOURCE_FILES[@]}" <<'PY'
import sys
from pathlib import Path
report = Path(sys.argv[1]).read_text(encoding='utf-8')
failed = []
for name in sys.argv[2:]:
    p = Path(name)
    if not p.exists():
        continue
    src = p.read_text(encoding='utf-8')
    if src not in report:
        failed.append(str(p))
    else:
        print(f"  ✅ {p.name} 原文连续保留")
if failed:
    print("  ❌ 以下源文件未被原样连续保留:")
    for item in failed:
        print(f"    - {item}")
    sys.exit(5)
PY

# 检查关键章节标题（仅对实际存在的源文件要求）
echo ""
echo "章节完整性检查:"
for title in "执行摘要" "One-pager" "Battle"; do
  if grep -q "$title" "$REPORT"; then
    echo "  ✅ ${title}"
  else
    echo "  ❌ ${title} — 缺失!"
  fi
done
for idx in "${!MERGE_TITLES[@]}"; do
  title="${MERGE_TITLES[$idx]}"
  if grep -q "$title" "$REPORT"; then
    echo "  ✅ ${title}"
  else
    echo "  ❌ ${title} — 缺失!"
    exit 6
  fi
done

echo ""
echo "=== 报告合并完成 ==="
echo "输出文件: $REPORT"
echo "报告行数: ${TOTAL_LINES}"
