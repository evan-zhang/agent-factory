#!/bin/bash
# init-check.sh — 验证 API Key 权限，探测 3 个接口
# 用法: ./init-check.sh <appKey>
# 返回: OK / FAIL

BASE_URL="https://sg-al-cwork-web.mediportal.com.cn/open-api"
APP_KEY="${1:-$KH_APP_KEY}"
[ -z "$APP_KEY" ] && [ -f ~/.openclaw/knowledge-hub-key ] && APP_KEY=$(cat ~/.openclaw/knowledge-hub-key)
[ -z "$APP_KEY" ] && { echo "FAIL: 缺少 appKey"; exit 1; }

H="appKey: $APP_KEY"
OK=0; FAIL=0

check() {
  local label="$1" method="$2" path="$3" body="$4"
  if [ "$method" = "GET" ]; then
    rc=$(curl -s -o /dev/null -w "%{http_code}" -H "$H" "${BASE_URL}${path}")
  else
    rc=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "$H" -H "Content-Type: application/json" -d "$body" "${BASE_URL}${path}")
  fi
  case "$rc" in 200) echo "  ✓ $label"; OK=$((OK+1));; 401|403) echo "  ✗ $label (权限不足)"; FAIL=$((FAIL+1));; *) echo "  ✗ $label (错误:$rc)"; FAIL=$((FAIL+1));; esac
}

echo "=== 验权检测 ==="
check "获取项目ID" GET "/document-database/project/personal/getProjectId"
check "搜索文件" GET "/document-database/file/searchFile?keyword=test"
check "上传接口" POST "/ai-huiji/uploadContentToPersonalProject" '{"projectId":"x","content":"x","fileName":"x","folderName":"x"}'

if [ "$FAIL" -eq 0 ]; then
  echo "=== 全部通过，写入 ~/.openclaw/knowledge-hub-key ==="
  echo "$APP_KEY" > ~/.openclaw/knowledge-hub-key
  echo "OK"
else
  echo "=== 有 $FAIL 项失败 ==="
  echo "FAIL"
fi
