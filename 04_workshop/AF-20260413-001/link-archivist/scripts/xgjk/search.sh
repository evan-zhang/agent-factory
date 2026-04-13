#!/bin/bash
# search.sh — 搜索知识库文件
# 用法: ./search.sh <projectId> <keyword> [appKey]

BASE_URL="https://sg-al-cwork-web.mediportal.com.cn/open-api"
APP_KEY="${3:-$KH_APP_KEY}"
[ -z "$APP_KEY" ] && [ -f ~/.openclaw/knowledge-hub-key ] && APP_KEY=$(cat ~/.openclaw/knowledge-hub-key)
[ -z "$APP_KEY" ] && { echo "错误: 缺少 appKey"; exit 1; }
PROJECT_ID="$1"; KEYWORD="$2"
[ -z "$KEYWORD" ] && { echo "用法: $0 <projectId> <keyword> [appKey]"; exit 1; }

ENC_KEYWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$KEYWORD'))")
URL="${BASE_URL}/document-database/file/searchFile?projectId=${PROJECT_ID}&keyword=${ENC_KEYWORD}"
RESP=$(curl -s -H "appKey: $APP_KEY" "$URL")

CODE=$(echo "$RESP" | jq -r '.resultCode')
if [ "$CODE" = "1" ]; then
  COUNT=$(echo "$RESP" | jq '.data | length')
  echo "=== 找到 ${COUNT} 个结果 ==="
  echo "$RESP" | jq -r '.data[] | "[\(.fileId)] \(.fileName) — \(.summary // "无摘要")"'
else
  echo "SEARCH_ERROR: $RESP"; exit 1
fi
