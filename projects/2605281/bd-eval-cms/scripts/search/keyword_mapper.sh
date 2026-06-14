#!/usr/bin/env bash
# keyword_mapper.sh — 关键词模板查询
# v0.10.0 草案
#
# 职责：
#   1. 读 lib/keyword_templates.json（按 skill 名/类型查表）
#   2. 返回该 skill 的 3-5 个检索词
#   3. 支持占位符替换（{品种}、{公司}、{target}）
#
# 不做什么：
#   - 不做搜索本身
#   - 不做关键词权重排序
#   - 不做跨语言切换（v0.10.0 阶段由 caller 决定）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/lib/keyword_templates.json"

# 取关键词列表
# 用法：get_keywords <skill-name> [{placeholders_json}]
# 占位符：{"品种":"乌司他丁","公司":"康哲"}
get_keywords() {
  local skill="$1"
  local placeholders="${2:-{\}}"
  local tmpls
  tmpls=$(jq -r --arg s "$skill" '.[$s] // []' "$TEMPLATE_FILE" 2>/dev/null)
  # 占位符替换
  echo "$tmpls" | jq -r --argjson ph "$placeholders" \
    '.[] | . as $tpl |
     reduce ($ph | to_entries[]) as $p (.;
       gsub("{" + $p.key + "}"; $p.value)
     )'
}

# 列出所有 skill 名
list_skills() {
  jq -r 'keys[]' "$TEMPLATE_FILE" 2>/dev/null
}

# 单元测试
if [ "${1:-}" = "--test" ]; then
  echo "=== A-1 海外未上市 ==="
  get_keywords "A-1" '{"品种":"TRTL-729"}'
  echo "=== D-1 通用 DD ==="
  get_keywords "D-1" '{"target":"Acme Pharma"}'
  exit 0
fi

# CLI
case "${1:-}" in
  --list) shift; list_skills "$@" ;;
  --skill) shift; get_keywords "$@" ;;
  *) echo "用法: keyword_mapper.sh --list | --skill <name> [{placeholders}]" >&2; exit 1 ;;
esac
