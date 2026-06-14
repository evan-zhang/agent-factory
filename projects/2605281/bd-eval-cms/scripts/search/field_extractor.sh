#!/usr/bin/env bash
# field_extractor.sh — 字段抽取（v0.10.0 半自动）
# v0.10.0 草案
#
# 职责（v0.10.0 半自动）：
#   1. 接收 URL + 抓取内容（来自 core_search）
#   2. 输出"抽取提示词模板"（prefill 给 sub-agent）
#   3. 不做实际抽取 → 由 sub-agent 用 LLM 抽取 + 人工确认
#
# 职责（v0.10.1 全自动 - 占位）：
#   1. 正则匹配 + LLM 抽取
#   2. 输出结构化 JSON
#   3. 准确率 >85% 才允许 v0.10.1 上线
#
# 不做什么：
#   - 不做搜索本身
#   - 不做字段值校验
#   - 不做字段补全

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_DIR="$SCRIPT_DIR/lib/extraction_prompts"

# 取提示词模板
# 用法：get_prompt <gate-type>
# 返回 markdown 提示词
get_prompt() {
  local gate="$1"
  local file="$PROMPT_DIR/${gate}.md"
  if [ -f "$file" ]; then
    cat "$file"
  else
    cat "$PROMPT_DIR/default.md" 2>/dev/null || echo "ERROR: 无提示词模板"
    return 1
  fi
}

# 列出所有 gate 类型
list_gates() {
  ls "$PROMPT_DIR"/*.md 2>/dev/null | xargs -n1 basename | sed 's/\.md$//'
}

# 单元测试
if [ "${1:-}" = "--test" ]; then
  echo "=== Gate 1 监管字段抽取提示词（前 10 行）==="
  get_prompt "gate-1-regulatory" | head -10
  echo ""
  echo "=== 所有 gate 类型 ==="
  list_gates
  exit 0
fi

case "${1:-}" in
  --list) shift; list_gates "$@" ;;
  --gate) shift; get_prompt "$@" ;;
  *) echo "用法: field_extractor.sh --list | --gate <gate-type>" >&2; exit 1 ;;
esac
