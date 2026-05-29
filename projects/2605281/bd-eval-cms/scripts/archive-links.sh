#!/bin/bash
# archive-links.sh — 归档BD评估报告链接到品种目录

set -e

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
  echo "用法: $0 <品种目录名> <整体报告URL> <Battle报告URL>"
  echo "示例: $0 CG-0255 https://doc.20100706.xyz/raw/xxx https://doc.20100706.xyz/raw/yyy"
  exit 1
fi

NAME="$1"
REPORT_URL="$2"
BATTLE_URL="$3"
BASE="projects/bd-eval/$NAME"

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

## 整体评估报告（琥珀金版）

- 🔗 [HTML 在线预览]($REPORT_URL)

## Battle 对抗报告

- 🔗 [HTML 在线预览]($BATTLE_URL)
EOF

# 更新 state.json
python3 -c "
import json
with open('$BASE/state.json') as f:
    s = json.load(f)
s['reportHtmlUrl'] = '$REPORT_URL'
s['battleHtmlUrl'] = '$BATTLE_URL'
with open('$BASE/state.json', 'w') as f:
    json.dump(s, f, indent=2, ensure_ascii=False)
"

echo "✅ $NAME 归档完成"
echo "   整体报告: $REPORT_URL"
echo "   Battle报告: $BATTLE_URL"
