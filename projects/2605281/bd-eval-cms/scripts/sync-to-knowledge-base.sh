#!/bin/bash
# sync-to-knowledge-base.sh — 将品种目录同步到玄关知识库
# 用法：bash scripts/sync-to-knowledge-base.sh {品种目录路径} [{案件代号}]
# 示例：bash scripts/sync-to-knowledge-base.sh "projects/2605281/bd-eval-cms/利奈昔巴特"
#        bash scripts/sync-to-knowledge-base.sh "projects/2605281/bd-eval-cms/利奈昔巴特" "260531-LNXB"
#
# 案件代号生成规则（优先级从高到低）：
#   1. 手动传入第二个参数
#   2. state.json 中已有的 caseCode（如果符合 YYMMDD-XXXX 格式）
#   3. 自动生成：YYMMDD-{4字母品种缩写}
#
# 目录结构：{YYMMDD}/{YYMMDD-XXXX}/
# 例如：260531/260531-LNXB/

set -euo pipefail

CASE_DIR="$1"
CASE_CODE="${2:-}"

API_BASE="https://sg-al-cwork-web.mediportal.com.cn/open-api"
APP_KEY="mN6bVc2Xz9Lk4Jh7Gt5Rf3Wp1Yq8As0D"
PROJECT_ID="2060176831872499713"

if [ -z "$CASE_DIR" ]; then
  echo "用法: $0 {品种目录路径} [{案件代号}]"
  exit 1
fi

if [ ! -d "$CASE_DIR" ]; then
  echo "错误：品种目录不存在: $CASE_DIR"
  exit 1
fi

# ========== 案件代号自动生成 ==========

# 从 state.json 读取品种名（用于自动生成代号）
read_product_name() {
  python3 -c "
import json
try:
    with open('$CASE_DIR/state.json', 'r') as f:
        state = json.load(f)
    print(state.get('productName', state.get('品种名', '')))
except:
    print('')
" 2>/dev/null
}

# 从品种名生成 4 字母缩写
# 中文品种名：取每个字的拼音首字母（最多 4 个）
# 英文品种名：取前 4 个辅音字母（大写）
generate_code() {
  local name="$1"
  python3 -c "
import re
name = '$name'.strip()
if not name:
    print('UNKN')
elif re.match(r'^[a-zA-Z]', name):
    # 英文名：取前4个字母（大写），去掉空格和连字符
    clean = re.sub(r'[^a-zA-Z]', '', name).upper()
    print(clean[:4] if len(clean) >= 4 else clean.ljust(4, 'X'))
else:
    # 中文名：用拼音首字母
    try:
        from pypinyin import lazy_pinyin
        pinyin_list = lazy_pinyin(name)
        initials = ''.join([p[0].upper() for p in pinyin_list])
        print(initials[:4] if len(initials) >= 4 else initials.ljust(4, 'X'))
    except ImportError:
        # 没有 pypinyin，用 Unicode 编码映射
        # 取前4个字符的 Unicode 编码后两位
        codes = [str(ord(c) % 10000).zfill(4)[:4] for c in name[:4]]
        print(''.join(codes)[:4])
" 2>/dev/null
}

# 生成日期部分 YYMMDD
DATE_PART=$(date +%y%m%d)

# 确定案件代号
if [ -n "$CASE_CODE" ]; then
  # 手动传入
  echo "案件代号：手动指定 → $CASE_CODE"
elif [ -f "$CASE_DIR/state.json" ]; then
  # 检查 state.json 中是否已有符合新格式的 caseCode
  EXISTING_CODE=$(python3 -c "
import json, re
try:
    with open('$CASE_DIR/state.json', 'r') as f:
        state = json.load(f)
    code = state.get('caseCode', '')
    # 检查是否 YYMMDD-XXXX 格式
    if re.match(r'^\d{6}-[A-Z0-9]{4}$', code):
        print(code)
    else:
        print('')
except:
    print('')
" 2>/dev/null)
  if [ -n "$EXISTING_CODE" ]; then
    CASE_CODE="$EXISTING_CODE"
    echo "案件代号：从 state.json 复用 → $CASE_CODE"
  fi
fi

# 如果还是没有，自动生成
if [ -z "$CASE_CODE" ]; then
  PRODUCT_NAME=$(read_product_name)
  if [ -n "$PRODUCT_NAME" ]; then
    ABBR=$(generate_code "$PRODUCT_NAME")
    CASE_CODE="${DATE_PART}-${ABBR}"
    echo "案件代号：自动生成 → $CASE_CODE（品种：${PRODUCT_NAME}）"
  else
    # 兜底：用目录名
    DIR_NAME=$(basename "$CASE_DIR")
    ABBR=$(generate_code "$DIR_NAME")
    CASE_CODE="${DATE_PART}-${ABBR}"
    echo "案件代号：从目录名生成 → $CASE_CODE（目录：${DIR_NAME}）"
  fi
fi

# 月份目录取日期前 6 位（YYMMDD）
MONTH_DIR="${CASE_CODE:0:6}"

echo ""
echo "=== 知识库同步开始 ==="
echo "案件代号: $CASE_CODE"
echo "同步目录: $MONTH_DIR/$CASE_CODE/"
echo "品种目录: $CASE_DIR"
echo ""

# ========== 将 caseCode 写入 state.json ==========
if [ -f "$CASE_DIR/state.json" ]; then
  python3 -c "
import json
state_file = '$CASE_DIR/state.json'
with open(state_file, 'r') as f:
    state = json.load(f)
state['caseCode'] = '$CASE_CODE'
with open(state_file, 'w') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
" 2>/dev/null
fi

# ========== 文件同步逻辑 ==========

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

# 同步 references/
if [ -d "$CASE_DIR/references" ]; then
  if [ -f "$CASE_DIR/references/REFERENCES.md" ]; then
    sync_file "$CASE_DIR/references/REFERENCES.md" "references/"
  fi
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
echo "知识库路径: $MONTH_DIR/$CASE_CODE/"

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

# 回写同步结果到 state.json
if [ -f "$CASE_DIR/state.json" ]; then
  python3 -c "
import json, sys, datetime
state_file = '$CASE_DIR/state.json'
with open(state_file, 'r') as f:
    state = json.load(f)
state['caseCode'] = '$CASE_CODE'
state['knowledgeBaseSync'] = {
    'syncedAt': datetime.datetime.now().isoformat(),
    'syncedFiles': $SUCCESS,
    'failedFiles': $FAIL,
    'totalFiles': $TOTAL,
    'caseCode': '$CASE_CODE',
    'kbPath': '$MONTH_DIR/$CASE_CODE/'
}
with open(state_file, 'w') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
print('state.json 已更新: caseCode=$CASE_CODE, kbPath=$MONTH_DIR/$CASE_CODE/')
" 2>/dev/null || echo "⚠️ state.json 回写失败"
fi

exit 0
