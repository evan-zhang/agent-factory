#!/bin/bash
# archive-links.sh — 归档BD评估报告链接到品种目录
# 说明：仅接受产品引进知识库 / doc.aishuo.co 长链接；旧临时上传服务链接已废弃。

set -euo pipefail

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
  echo "用法: $0 <品种目录名> <知识库报告URL> [Battle报告URL]"
  echo "示例: $0 CG-0255 https://doc.aishuo.co/preview/xxx"
  exit 1
fi

NAME="$1"
REPORT_URL="$2"
BATTLE_URL="${3:-}"
BASE="projects/bd-eval/$NAME"

if [[ "$REPORT_URL" != https://doc.aishuo.co/* ]]; then
  echo "❌ 仅允许归档产品引进知识库 doc.aishuo.co 长链接"
  exit 1
fi

# 品种中文名（从state.json读取或用目录名）
DISPLAY_NAME=$(python3 -c "
import json
with open('$BASE/state.json') as f:
    s = json.load(f)
print(s.get('displayName', '$NAME'))
" 2>/dev/null || echo "$NAME")

# 写 links.md
cat > "$BASE/links.md" << EOF
# $DISPLAY_NAME — 在线报告链接

> 更新时间：$(date +%Y-%m-%d)

## 整体评估报告（产品引进知识库）

- 🔗 [HTML 在线预览]($REPORT_URL)
EOF

if [ -n "$BATTLE_URL" ]; then
  if [[ "$BATTLE_URL" != https://doc.aishuo.co/* ]]; then
    echo "❌ Battle 报告仅允许归档 doc.aishuo.co 长链接"
    exit 1
  fi
  cat >> "$BASE/links.md" << EOF

## Battle 对抗报告

- 🔗 [HTML 在线预览]($BATTLE_URL)
EOF
fi

# 更新 state.json
python3 -c "
import json
with open('$BASE/state.json') as f:
    s = json.load(f)
s['reportHtmlUrl'] = '$REPORT_URL'
if '$BATTLE_URL':
    s['battleHtmlUrl'] = '$BATTLE_URL'
with open('$BASE/state.json', 'w') as f:
    json.dump(s, f, indent=2, ensure_ascii=False)
"

echo "✅ $NAME 归档完成"
echo "   整体报告: $REPORT_URL"
if [ -n "$BATTLE_URL" ]; then
  echo "   Battle报告: $BATTLE_URL"
fi
