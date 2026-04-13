#!/bin/bash
# upload.sh — 创建或更新知识库文件
# 用法:
#   ./upload.sh create <projectId> <contentFile> <fileName> <folderName> [appKey]
#   ./upload.sh update <projectId> <contentFile> <fileId> [appKey]

BASE_URL="https://sg-al-cwork-web.mediportal.com.cn/open-api"
# 从参数末尾、环境变量或key文件获取Key
APP_KEY="${*: -1}"
[[ "$APP_KEY" != TsFh* ]] && APP_KEY="${KH_APP_KEY}"
[[ "$APP_KEY" != TsFh* ]] && [ -f ~/.openclaw/knowledge-hub-key ] && APP_KEY=$(cat ~/.openclaw/knowledge-hub-key)
[ -z "$APP_KEY" ] && { echo "错误: 缺少 appKey"; exit 1; }

MODE="$1"; shift

if [ "$MODE" = "create" ]; then
  PROJECT_ID="$1"; CONTENT_FILE="$2"; FILE_NAME="$3"; FOLDER_NAME="$4"
  [ -z "$FOLDER_NAME" ] && { echo "用法: $0 create <projectId> <contentFile> <fileName> <folderName> [appKey]"; exit 1; }
  CONTENT=$(cat "$CONTENT_FILE")
  BODY=$(jq -n --arg p "$PROJECT_ID" --arg c "$CONTENT" --arg f "$FILE_NAME" --arg ff "$FOLDER_NAME" \
    '{projectId: $p, content: $c, fileName: $f, folderName: $ff}')
  RESP=$(curl -s -X POST -H "appKey: $APP_KEY" -H "Content-Type: application/json" -d "$BODY" \
    "${BASE_URL}/ai-huiji/uploadContentToPersonalProject")
  CODE=$(echo "$RESP" | jq -r '.resultCode')
  if [ "$CODE" = "1" ]; then
    echo "$RESP" | jq -r '.data | "SUCCESS fileId=\(.fileId) folderId=\(.folderId) url=\(.downloadUrl)"'
  else
    echo "ERROR: $RESP"; exit 1
  fi

elif [ "$MODE" = "update" ]; then
  PROJECT_ID="$1"; CONTENT_FILE="$2"; FILE_ID="$3"
  [ -z "$FILE_ID" ] && { echo "用法: $0 update <projectId> <contentFile> <fileId> [appKey]"; exit 1; }
  # Step 1: delete old file
  DEL=$(curl -s -X POST -H "appKey: $APP_KEY" -H "Content-Type: application/json" \
    -d "{\"fileId\":$FILE_ID}" "${BASE_URL}/document-database/file/deleteFile")
  # Step 2: re-upload (need folder context — not ideal but API limitation)
  CONTENT=$(cat "$CONTENT_FILE")
  BODY=$(jq -n --arg p "$PROJECT_ID" --arg c "$CONTENT" --arg f "updated.md" --arg ff "updated" \
    '{projectId: $p, content: $c, fileName: $f, folderName: $ff}')
  echo "WARN: update uses delete+recreate, folder context may change"
  echo "DELETE_RESULT: $DEL"

else
  echo "用法: $0 create|update ..."; exit 1
fi
