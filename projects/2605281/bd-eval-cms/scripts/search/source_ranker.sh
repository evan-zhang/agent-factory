#!/usr/bin/env bash
# source_ranker.sh — 来源分级与排序
# v0.10.0 草案
#
# 职责：
#   1. 读 lib/source_priority.json (T1-T4 域配置)
#   2. 对 core_search 的 JSON 输出按 T1→T4 排序
#   3. 标记每条结果的 tier 和 credibility
#
# 不做什么：
#   - 不做搜索本身
#   - 不做字段抽取
#   - 不做去重

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_FILE="$SCRIPT_DIR/lib/source_priority.json"

# 给一条 url 打 tier 标签
# 用法：tier_of <url>
tier_of() {
  local url="$1"
  # 从 T1 开始匹配（jq 的 test 不支持复杂 PCRE，简化为 contains 判断）
  for tier in T1 T2 T3; do
    local hit
    hit=$(jq -r --arg url "$url" '.[ "'"$tier"'" ].domains[]' "$SOURCE_FILE" 2>/dev/null | while read -r domain; do
      if [[ "$url" == *"$domain"* ]]; then
        echo "MATCH"
        break
      fi
    done)
    if [ "$hit" = "MATCH" ]; then
      echo "$tier"
      return 0
    fi
  done
  echo "T4"
}

# 标 credibility
credibility_of() {
  local tier="$1"
  jq -r --arg t "$tier" '.[$t].credibility' "$SOURCE_FILE"
}

# 主函数：给 JSON 数组每条加 tier/credibility，按 tier 排序
rank_sources() {
  local input="$1"
  local tmp=$(mktemp)
  echo "$input" > "$tmp"
  # 用 jq 给每条标 tier
  jq -c '.[]' "$tmp" | while IFS= read -r item; do
    local url tier cred
    url=$(echo "$item" | jq -r '.url')
    tier=$(tier_of "$url")
    cred=$(credibility_of "$tier")
    echo "$item" | jq -c --arg t "$tier" --argjson c "$cred" \
      '. + {tier: $t, credibility: $c}'
  done | jq -s 'sort_by(.tier)'
  rm -f "$tmp"
}

# 单元测试
if [ "${1:-}" = "--test" ]; then
  test_input='[
    {"url":"https://www.nmpa.gov.cn/xx","title":"NMPA 公告","snippet":"a"},
    {"url":"https://clinicaltrials.gov/yy","title":"CT.gov","snippet":"b"},
    {"url":"https://pharmacompany.com/zz","title":"公司官网","snippet":"c"}
  ]'
  rank_sources "$test_input"
  exit 0
fi

# CLI: source_ranker.sh <json-array>
[ $# -ge 1 ] || { echo "用法: source_ranker.sh <json-array>" >&2; exit 1; }
rank_sources "$1"
