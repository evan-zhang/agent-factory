#!/usr/bin/env bash
# install.sh — TPR Framework Skill 安装/升级脚本
# 用法：bash install.sh [目标目录]
# 示例：bash install.sh ~/.agents/skills/tpr-framework
set -euo pipefail

REPO_BASE="https://raw.githubusercontent.com/evan-zhang/agent-factory/master/projects/2604011/tpr-framework"
TARGET="${1:-./tpr-framework}"

echo "📦 安装 TPR Framework Skill → ${TARGET}"

# 创建目录结构
mkdir -p "${TARGET}"/{references,design,self-improving}

# 文件列表（相对路径）
FILES=(
  "SKILL.md"
  "_meta.json"
  "references/best-practices.md"
  "references/bindings-guide.md"
  "references/maintenance.md"
  "references/spawning-guide.md"
  "references/tpr-bridge-protocol.md"
  "design/DESIGN.md"
  "design/DISCUSSION-LOG.md"
  "design/LEARNING-LOOP.md"
  "design/SHARE-LOG.jsonl"
  "self-improving/corrections.md"
  "self-improving/patterns.md"
)

SUCCESS=0
FAIL=0

for file in "${FILES[@]}"; do
  URL="${REPO_BASE}/${file}"
  DEST="${TARGET}/${file}"
  if curl -fsSL -o "${DEST}" "${URL}"; then
    echo "  ✅ ${file}"
    ((SUCCESS++))
  else
    echo "  ❌ ${file} (下载失败)"
    ((FAIL++))
  fi
done

echo ""
echo "─── 安装完成 ───"
echo "  成功：${SUCCESS} 个文件"
if [ "${FAIL}" -gt 0 ]; then
  echo "  失败：${FAIL} 个文件（请检查网络连接）"
  exit 1
fi

echo ""
echo "验证：检查 SKILL.md 文件头"
head -3 "${TARGET}/SKILL.md"
echo ""
echo "✅ TPR Framework Skill 已安装到：${TARGET}"
echo ""
echo "下一步："
echo "  1. 在 AGENTS.md 或 skill 配置中引用此目录"
echo "  2. 如需使用 Phase 4 Mode B（Ralph Loop），还需安装 Ralph Loop skill"
echo "     参见：${TARGET}/SKILL.md 中的「安装」章节"
