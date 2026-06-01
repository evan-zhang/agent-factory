#!/bin/bash
# merge-report.sh — Phase 5 报告合并脚本（纯程序行为）
# 用法: bash scripts/merge-report.sh {品种目录路径}
# 示例: bash scripts/merge-report.sh projects/2605281/bd-eval-cms/MB-001-Mage-Biologics

set -euo pipefail

DIR="${1:?merge-report.sh requires a directory path}"

if [ ! -d "$DIR" ]; then
  echo "错误: 目录不存在 $DIR"
  exit 1
fi

STATE="$DIR/state.json"
REPORT="$DIR/04-final-report.md"

if [ ! -f "$STATE" ]; then
  echo "错误: state.json 不存在"
  exit 1
fi

# 从 state.json 提取关键字段
CASE_CODE=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('caseCode','unknown'))")
DISPLAY_NAME=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('displayName','unknown'))")
SCHEME=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('scheme','B'))")
ENTITY=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('businessEntity','待确认'))")
SKILL=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('routedSkill','待路由'))")
DATE=$(date '+%Y-%m-%d')

echo "=== 报告合并开始 ==="
echo "品种: $DISPLAY_NAME"
echo "案件代号: $CASE_CODE"

# 临时文件
TMPFILE=$(mktemp)
trap "rm -f $TMPFILE" EXIT

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
# 执行摘要需要 AI 生成，标记占位
cat >> "$TMPFILE" << 'EOF'
## 第一章：执行摘要

<!-- EXECUTIVE_SUMMARY_PLACEHOLDER -->
<!-- 此章节由 AI 根据所有 Gate 结论卡生成，合并脚本只做占位标记 -->

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

# ===== 4. One-pager =====
CHAPTER_NUM=3
merge_file() {
  local filepath="$1"
  local chapter_title="$2"
  
  if [ -f "$filepath" ]; then
    echo "--- 合并 ${chapter_title} ---"
    echo "## 第${CHAPTER_NUM}章：${chapter_title}" >> "$TMPFILE"
    echo "" >> "$TMPFILE"
    cat "$filepath" >> "$TMPFILE"
    echo "" >> "$TMPFILE"
    echo "---" >> "$TMPFILE"
    echo "" >> "$TMPFILE"
    CHAPTER_NUM=$((CHAPTER_NUM + 1))
  else
    echo "⚠️ 文件不存在: $filepath"
  fi
}

# One-pager
merge_file "$DIR/02-gate-by-chapter/One-pager.md" "One-pager 终局先立"

# Gate 1-6
merge_file "$DIR/02-gate-by-chapter/Gate-1-premise.md" "Gate 1 前提门"
merge_file "$DIR/02-gate-by-chapter/Gate-2-positioning.md" "Gate 2 定调门"
merge_file "$DIR/02-gate-by-chapter/Gate-3-evidence.md" "Gate 3 证据门"
merge_file "$DIR/02-gate-by-chapter/Gate-4-payment.md" "Gate 4 支付门"
merge_file "$DIR/02-gate-by-chapter/Gate-5-cost.md" "Gate 5 成本门"
# Gate 6（兼容多种命名变体）
G6_FILE=""
for name in Gate-6-dealability.md Gate-6-feasibility.md Gate-6-doability.md Gate-6-deal.md; do
  if [ -f "$DIR/02-gate-by-chapter/$name" ]; then
    G6_FILE="$DIR/02-gate-by-chapter/$name"
    break
  fi
done
if [ -n "$G6_FILE" ]; then
  merge_file "$G6_FILE" "Gate 6 可做门"
else
  echo "⚠️ Gate 6 文件不存在"
fi

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
for bf in "$DIR/battle/"BATTLE-R1-AUDITOR.md "$DIR/battle/BATTLE-R1-EXECUTOR.md"; do
  if [ -f "$bf" ]; then
    bname=$(basename "$bf" .md)
    echo "--- 合并 Battle: $bname ---"
    echo "### ${bname}" >> "$TMPFILE"
    echo "" >> "$TMPFILE"
    cat "$bf" >> "$TMPFILE"
    echo "" >> "$TMPFILE"
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

# 检查源文件总行数
SOURCE_LINES=0
for f in "$DIR/01-discovery.md" \
         "$DIR/02-gate-by-chapter/One-pager.md" \
         "$DIR/02-gate-by-chapter/Gate-1-premise.md" \
         "$DIR/02-gate-by-chapter/Gate-2-positioning.md" \
         "$DIR/02-gate-by-chapter/Gate-3-evidence.md" \
         "$DIR/02-gate-by-chapter/Gate-4-payment.md" \
         "$DIR/02-gate-by-chapter/Gate-5-cost.md" \
         "$DIR/02-gate-by-chapter/Gate-6-feasibility.md" \
         "$DIR/03-battle-summary.md" \
         "$DIR/references/REFERENCES.md"; do
  if [ -f "$f" ]; then
    L=$(wc -l < "$f")
    SOURCE_LINES=$((SOURCE_LINES + L))
  fi
done
echo "源文件总行数: ${SOURCE_LINES}"

# 计算占比（报告包含封面和章节标题等额外行，所以应该 >= 95%）
# 但如果 AI 重写执行摘要，占比可能更高
RATIO=$(python3 -c "print(f'{$TOTAL_LINES / $SOURCE_LINES * 100:.1f}%')" 2>/dev/null || echo "N/A")
echo "报告/源文件比: ${RATIO}（预期 ≥95% 因为是纯合并+少量封面行）"

# 检查关键章节标题
echo ""
echo "章节完整性检查:"
for title in "执行摘要" "One-pager" "Gate 1" "Gate 2" "Gate 3" "Gate 4" "Gate 5" "Gate 6" "Battle"; do
  if grep -q "$title" "$REPORT"; then
    echo "  ✅ ${title}"
  else
    echo "  ❌ ${title} — 缺失!"
  fi
done

# 检查 Gate 结论卡
echo ""
echo "结论卡检查:"
for gate in "Gate 1" "Gate 2" "Gate 3" "Gate 4" "Gate 5" "Gate 6"; do
  if grep -q "结论卡" "$REPORT" | head -1; then
    # 更精确地检查每个 Gate 区域内是否有结论卡
    echo "  检查 ${gate} 结论卡..."
  fi
done

echo ""
echo "=== 报告合并完成 ==="
echo "输出文件: $REPORT"
echo "报告行数: ${TOTAL_LINES}"
