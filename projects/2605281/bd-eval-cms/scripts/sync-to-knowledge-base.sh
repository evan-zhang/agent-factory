#!/bin/bash
# sync-to-knowledge-base.sh — 将品种目录同步到玄关知识库
# 用法：bash scripts/sync-to-knowledge-base.sh {品种目录路径} {案件代号}
# 示例：bash scripts/sync-to-knowledge-base.sh "projects/2605281/bd-eval-cms/利奈昔巴特" "2605-2901"

set -euo pipefail

CASE_DIR="$1"
CASE_CODE="$2"
API_BASE="https://sg-al-cwork-web.mediportal.com.cn/open-api"
APP_KEY="mN6bVc2Xz9Lk4Jh7Gt5Rf3Wp1Yq8As0D"
PROJECT_ID="2060176831872499713"

# 月份目录取 caseCode 前4位
MONTH_DIR="${CASE_CODE:0:4}"

if [ -z "$CASE_DIR" ] || [ -z "$CASE_CODE" ]; then
  echo "用法: $0 {品种目录路径} {案件代号}"
  exit 1
fi

if [ ! -d "$CASE_DIR" ]; then
  echo "错误：品种目录不存在: $CASE_DIR"
  exit 1
fi

SUCCESS=0
FAIL=0
TOTAL=0
FAILED_FILES=""

sync_file() {
  local file_path="$1"
  local folder_name="$2"
  local file_name
  file_name=$(basename "$file_path")
  local base_name="${file_name%.*}"
  local suffix="${file_name##*.}"

  # 跳过非文本文件
  if [[ "$suffix" == "html" ]]; then
    # HTML 文件可能太大，特殊处理
    :
  fi

  local content
  content=$(cat "$file_path" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" 2>/dev/null)

  if [ -z "$content" ]; then
    echo "⚠️ 跳过（无法读取）: $file_path"
    FAIL=$((FAIL + 1))
    TOTAL=$((TOTAL + 1))
    FAILED_FILES="$FAILED_FILES\n$file_path"
    return
  fi

  local response
  response=$(curl -s -X POST "${API_BASE}/document-database/file/uploadContent" \
    -H "appKey: ${APP_KEY}" \
    -H "Content-Type: application/json" \
    -d "{
      \"projectId\": ${PROJECT_ID},
      \"content\": ${content},
      \"fileName\": \"${base_name}\",
      \"fileSuffix\": \"${suffix}\",
      \"folderName\": \"${MONTH_DIR}/${CASE_CODE}/${folder_name}\",
      \"nameConflictStrategy\": 1
    }" 2>/dev/null)

  local result_code
  result_code=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('resultCode',0))" 2>/dev/null || echo "0")

  TOTAL=$((TOTAL + 1))

  if [ "$result_code" = "1" ]; then
    SUCCESS=$((SUCCESS + 1))
    echo "✅ ${folder_name}${base_name}.${suffix}"
  else
    FAIL=$((FAIL + 1))
    FAILED_FILES="$FAILED_FILES\n$file_path"
    echo "❌ ${folder_name}${base_name}.${suffix} — ${response}"
  fi
}

echo "=== 知识库同步开始 ==="
echo "案件代号: $CASE_CODE"
echo "月份目录: $MONTH_DIR"
echo "品种目录: $CASE_DIR"
echo ""

# 同步根目录文件
for f in state.json 01-discovery.md 03-battle-summary.md 04-final-report.md links.md execution-log.md REPORT.html; do
  if [ -f "$CASE_DIR/$f" ]; then
    sync_file "$CASE_DIR/$f" ""
  fi
done

# 同步 02-gate-by-chapter/
if [ -d "$CASE_DIR/02-gate-by-chapter" ]; then
  for f in "$CASE_DIR"/02-gate-by-chapter/*.md; do
    [ -f "$f" ] && sync_file "$f" "02-gate-by-chapter/"
  done
  # 同步 history/
  if [ -d "$CASE_DIR/02-gate-by-chapter/history" ]; then
    for f in "$CASE_DIR"/02-gate-by-chapter/history/*.md; do
      [ -f "$f" ] && sync_file "$f" "02-gate-by-chapter/history/"
    done
  fi
fi

# 同步 battle/
if [ -d "$CASE_DIR/battle" ]; then
  for f in "$CASE_DIR"/battle/*.md; do
    [ -f "$f" ] && sync_file "$f" "battle/"
  done
fi

# 同步 references/（先同步根目录 REFERENCES.md，再同步各前缀子目录）
if [ -d "$CASE_DIR/references" ]; then
  # 同步根目录的 REFERENCES.md
  if [ -f "$CASE_DIR/references/REFERENCES.md" ]; then
    sync_file "$CASE_DIR/references/REFERENCES.md" "references/"
  fi
  # 同步各前缀子目录
  for prefix_dir in "$CASE_DIR"/references/*/; do
    if [ -d "$prefix_dir" ]; then
      prefix=$(basename "$prefix_dir")
      for f in "$prefix_dir"*.md; do
        [ -f "$f" ] && sync_file "$f" "references/${prefix}/"
      done
    fi
  done
fi

echo ""
echo "=== 同步完成 ==="
echo "成功: $SUCCESS / $TOTAL"
echo "失败: $FAIL / $TOTAL"

if [ $FAIL -gt 0 ]; then
  echo ""
  echo "失败文件："
  echo -e "$FAILED_FILES"
fi

if [ $FAIL -gt $((TOTAL / 2)) ] && [ $TOTAL -gt 0 ]; then
  echo ""
  echo "⚠️ 超过50%文件同步失败，请检查网络或API配置"
  exit 1
fi

exit 0
