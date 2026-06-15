#!/bin/bash
# sync-to-knowledge-base.sh — 将品种目录同步到玄关知识库
#
# 硬隔离职责：
#   本脚本仅负责知识库同步（文件上传 + state.json 回写）
#   报告渲染由 scripts/render_report.sh 独立负责
#   不得调用 doc-viewer 生成/上传一体化路径（v0.7.0 起彻底解耦）
#
# 用法：bash scripts/sync-to-knowledge-base.sh {品种目录路径} [{案件代号}]
# 示例：bash scripts/sync-to-knowledge-base.sh "projects/2605281/bd-eval-cms/利奈昔巴特"
#        bash scripts/sync-to-knowledge-base.sh "projects/2605281/bd-eval-cms/利奈昔巴特" "260531-LNXB"
#
# 案件代号生成规则（优先级从高到低，v0.9.4）：
#   1. 手动传入第二个参数
#   2. state.json 中已有的 caseCode
#   3. 兜底生成：YYMMDD-HHMMSS
#
# 目录结构（v0.9.4）：{ROOT}/{YYYYMM}/{caseCode}/
# 例如：CPYJ/202606/CP202412200012/

set -euo pipefail

CASE_DIR="$1"
CASE_CODE="${2:-}"

# ========== 前置门：Manifest 校验（最高优先） ==========
# v0.10.6：未过 verify-manifest 拒绝归档
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFY_MANIFEST="$SCRIPT_DIR/verify-manifest.sh"

if [ ! -f "$VERIFY_MANIFEST" ]; then
  echo "❌ 错误：verify-manifest.sh 不存在: $VERIFY_MANIFEST"
  exit 1
fi

if [ ! -x "$VERIFY_MANIFEST" ]; then
  echo "❌ 错误：verify-manifest.sh 不可执行: $VERIFY_MANIFEST"
  exit 1
fi

echo "=== 前置门：Manifest 校验 ==="
if "$VERIFY_MANIFEST" "$CASE_DIR"; then
  echo "✅ Manifest 校验通过，继续同步到知识库"
else
  echo "❌ Manifest 校验失败，拒绝归档到知识库"
  echo "   请补全缺失零件后再运行 sync-to-knowledge-base.sh"
  exit 1
fi
echo ""

# 凭证注入（v0.10.2 修订）：
# bd-eval-cms 专享系统级 AppKey —— 后台 BP 报告流水线使用，不走个人鉴权
# 读取顺序：config.yaml 的 knowledgeBase.appKeyFile → 默认 .secrets/kb_appkey
# 文件不存在或为空 → 报可操作错误
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$SKILL_DIR/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ 错误：未找到 config.yaml: $CONFIG_FILE"
  exit 1
fi

# read_config_field：用 python3 读 config.yaml（纯字符串字段，不需要 yq）
read_config_field() {
  local field="$1"
  python3 -c "
import re
with open('$CONFIG_FILE') as f:
    for line in f:
        m = re.match(r'^\s*' + '${field}' + r':\s*[\"\']?(.+?)[\"\']?\s*$', line)
        if m:
            print(m.group(1))
            break
" 2>/dev/null
}

# 读取 appKeyFile 路径（默认 .secrets/kb_appkey）
APPKEY_FILE=$(read_config_field appKeyFile)
if [ -z "$APPKEY_FILE" ]; then
  APPKEY_FILE=".secrets/kb_appkey"
fi

# 解析为绝对路径（相对 skill 目录）
APPKEY_PATH="$SKILL_DIR/$APPKEY_FILE"
if [ ! -f "$APPKEY_PATH" ]; then
  echo "❌ 错误：未找到 AppKey 文件: $APPKEY_PATH"
  echo "   请创建该文件并写入系统级 AppKey："
  echo "     mkdir -p \"$(dirname "$APPKEY_PATH")\""
  echo "     echo -n '你的AppKey' > \"$APPKEY_PATH\""
  exit 1
fi
APP_KEY=$(cat "$APPKEY_PATH" | tr -d '[:space:]')
if [ -z "$APP_KEY" ]; then
  echo "❌ 错误：AppKey 文件为空: $APPKEY_PATH"
  echo "   请写入有效的系统级 AppKey"
  exit 1
fi

# 从 config.yaml 读取固定 projectId / rootDir（业务固定，不允许覆盖）
PROJECT_ID=$(read_config_field projectId)
if [ -z "$PROJECT_ID" ]; then
  echo "❌ 错误：config.yaml 中未配置 knowledgeBase.projectId"
  exit 1
fi
KB_ROOT_DIR=$(read_config_field rootDir)
if [ -z "$KB_ROOT_DIR" ]; then
  echo "❌ 错误：config.yaml 中未配置 knowledgeBase.rootDir"
  exit 1
fi
echo "项目级 projectId（从 config.yaml 读）: $PROJECT_ID"
echo "知识库根目录（从 config.yaml 读）: $KB_ROOT_DIR"

# 玄关 API 根地址
API_BASE="https://sg-al-cwork-web.mediportal.com.cn/open-api"

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

# 如果还是没有，自动生成（v0.9.4：不依赖 pypinyin，兜底 YYMMDD-HHMMSS）
if [ -z "$CASE_CODE" ]; then
  CASE_CODE="$(date +%y%m%d-%H%M%S)"
  echo "案件代号：兜底生成 → $CASE_CODE"
fi

# 路径规则（v0.9.4 改造）：{rootDir}/{YYYYMM}/{caseCode}/
# YYYYMM = 业务月（系统当天，标识本项目正式评估的月份）
# caseCode = 外部商机 ID（如 CP202412200012）或 YYMMDD-HHMMSS
DATE_DIR="$(date +%Y%m)"
KB_CASE_PATH="${KB_ROOT_DIR}/${DATE_DIR}/${CASE_CODE}"

echo ""
echo "=== 知识库同步开始 ==="
echo "案件代号: $CASE_CODE"
echo "同步目录: $KB_CASE_PATH/"
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
      \"folderName\": \"${KB_CASE_PATH}/${folder_name}\",
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

# 同步根目录文件（REPORT.html 单独走下面 范式 4 Stage 2）
for f in state.json 01-discovery.md 03-battle-summary.md 04-final-report.md links.md execution-log.md; do
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

# ============== REPORT.html 范式 4 Stage 2（v0.4.0 起） ==============
# 1) 跳过普通 sync_file 循环中的 REPORT.html（上一句 for 循环跳过）
# 2) 这里走玄关知识库 5 步 API（v0.7.0 起不依赖 doc-viewer，自己调玄关 API）
# 3) 拿 5 年 doc.aishuo.co 链接，写入 state.json.reportHtmlUrl

REPORT_FILE="$CASE_DIR/REPORT.html"
if [ -f "$REPORT_FILE" ]; then
  echo ""
  echo "=== REPORT.html 走范式 4 Stage 2（产品引进知识库） ==="

  # 从 state.json 读品种名（用于文件命名）
  PRODUCT_NAME=$(read_product_name)
  if [ -z "$PRODUCT_NAME" ]; then
    PRODUCT_NAME=$(basename "$CASE_DIR")
  fi
  REPORT_FILENAME="${PRODUCT_NAME}-CMS投前评估报告.html"
  REPORT_SIZE=$(stat -f%z "$REPORT_FILE" 2>/dev/null || stat -c%s "$REPORT_FILE")

  # Step 1: 物理文件上传
  echo "Step 1/4: 物理文件上传..."
  RESOURCE_ID=$(curl -s -X POST \
    "${API_BASE}/cwork-file/uploadWholeFile" \
    -H "appKey: ${APP_KEY}" \
    -F "file=@${REPORT_FILE};filename=${REPORT_FILENAME}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])" 2>/dev/null)

  if [ -z "$RESOURCE_ID" ]; then
    echo "❌ 物理文件上传失败，跳过 Stage 2"
    REPORT_STATUS="failed"
  else
    echo "✅ resourceId=$RESOURCE_ID"

    # Step 2: 绑定到产品引进知识库
    echo "Step 2/4: 绑定到产品引进知识库（projectId=$PROJECT_ID）..."
    SAVE_RESPONSE=$(curl -s -X POST \
      "${API_BASE}/document-database/file/saveFileByPath" \
      -H "appKey: ${APP_KEY}" \
      -H "Content-Type: application/json" \
      -d "{
        \"projectId\": ${PROJECT_ID},
        \"path\": \"${KB_CASE_PATH}\",
        \"name\": \"${REPORT_FILENAME}\",
        \"fileType\": \"file\",
        \"resourceId\": ${RESOURCE_ID},
        \"suffix\": \"html\",
        \"size\": ${REPORT_SIZE}
      }")
    # 解析：data 可能是字符串 fileId、可能是对象 {id, fileId, ...}、可能为 null（权限问题但实际成功）
    FILE_ID=$(echo "$SAVE_RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if d.get('resultCode') != 1:
        print(f\"__FAIL__{d.get('resultMsg','未知错误')}\", file=sys.stderr)
        sys.exit(0)
    data = d.get('data')
    if isinstance(data, str):
        print(data)
    elif isinstance(data, dict):
        # 常见 key: id / fileId / nodeId
        print(data.get('id') or data.get('fileId') or data.get('nodeId') or data.get('data') or '')
    else:
        # data 为 null，但 resultCode=1  → 使用 resourceId 作为占位 fileId
        print(f\"__NULL_USING_RESOURCE__\")
except Exception as e:
    print(f\"__PARSE_ERROR__{e}\", file=sys.stderr)
" 2>&1)

    if [[ "$FILE_ID" == __FAIL__* ]]; then
      echo "❌ 绑定 KB 节点失败: ${FILE_ID#__FAIL__}"
      REPORT_STATUS="failed"
    elif [[ "$FILE_ID" == __PARSE_ERROR__* ]]; then
      echo "❌ 绑定 KB 节点响应解析失败: ${FILE_ID#__PARSE_ERROR__}"
      REPORT_STATUS="failed"
    elif [[ "$FILE_ID" == __NULL_USING_RESOURCE__ ]]; then
      # 玄关返回 data=null 但实际成功（权限元数据不全）→ 用 resourceId 占位
      echo "⚠️ saveFileByPath 返回 data=null（玄关权限元数据问题，但绑定应已成功），用 resourceId 占位 fileId"
      FILE_ID="placeholder_${RESOURCE_ID}"
    elif [ -z "$FILE_ID" ]; then
      echo "❌ 绑定 KB 节点返回 data 为空"
      REPORT_STATUS="failed"
    else
      echo "✅ fileId=$FILE_ID"

      # Step 3: 换 access-token
      echo "Step 3/4: 换 access-token..."
      ACCESS_TOKEN=$(curl -s \
        "https://sg-al-cwork-web.mediportal.com.cn/user/login/appkey?appCode=cms_gpt&appKey=${APP_KEY}" \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['xgToken'])" 2>/dev/null)

      if [ -z "$ACCESS_TOKEN" ]; then
        echo "❌ access-token 换取失败，跳过 Stage 2"
        REPORT_STATUS="failed"
      else
        # Step 4: 拿 5 年公网预览链接
        echo "Step 4/4: 获取 5 年公网预览链接..."
        PREVIEW_URL=$(curl -s -X POST \
          "https://sg-al-cwork-web.mediportal.com.cn/doc-preview/api/preview/ticket" \
          -H "access-token: ${ACCESS_TOKEN}" \
          -H "Content-Type: application/json" \
          -d "{
            \"bizType\": \"kb\",
            \"bizId\": \"${FILE_ID}\",
            \"format\": \"html\",
            \"title\": \"${REPORT_FILENAME}\"
          }" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['previewUrl'])" 2>/dev/null)

        if [ -z "$PREVIEW_URL" ]; then
          echo "❌ previewUrl 获取失败"
          REPORT_STATUS="failed"
        else
          echo "✅ previewUrl=$PREVIEW_URL"
          REPORT_STATUS="success"
          REPORT_PREVIEW_URL="$PREVIEW_URL"
          REPORT_FILE_ID="$FILE_ID"
        fi
      fi
    fi
  fi
fi
# ============== REPORT.html 处理结束 ==============

echo ""
echo "=== 同步完成 ==="
echo "成功: $SUCCESS / $TOTAL"
echo "失败: $FAIL / $TOTAL"
echo "知识库路径: $KB_CASE_PATH/"

if [ $FAIL -gt 0 ]; then
  echo ""
  echo "失败文件："
  echo -e "$FAILED_FILES"
fi

SYNC_SEVERE_FAILURE=false
if [ $FAIL -gt $((TOTAL / 2)) ] && [ $TOTAL -gt 0 ]; then
  echo ""
  echo "⚠️ 超过50%文件同步失败，请检查网络或API配置"
  SYNC_SEVERE_FAILURE=true
fi

# 回写同步结果到 state.json（即使失败也必须回写，便于程序读取失败原因）
if [ -f "$CASE_DIR/state.json" ]; then
  REPORT_STATUS_SAFE="${REPORT_STATUS:-}"
  REPORT_PREVIEW_URL_SAFE="${REPORT_PREVIEW_URL:-}"
  REPORT_FILE_ID_SAFE="${REPORT_FILE_ID:-}"
  CASE_DIR_ENV="$CASE_DIR" \
  CASE_CODE_ENV="$CASE_CODE" \
  KB_CASE_PATH_ENV="$KB_CASE_PATH" \
  SUCCESS_ENV="$SUCCESS" \
  FAIL_ENV="$FAIL" \
  TOTAL_ENV="$TOTAL" \
  REPORT_STATUS_ENV="$REPORT_STATUS_SAFE" \
  REPORT_PREVIEW_URL_ENV="$REPORT_PREVIEW_URL_SAFE" \
  REPORT_FILE_ID_ENV="$REPORT_FILE_ID_SAFE" \
  python3 - <<'PY' || echo "⚠️ state.json 回写失败"
import json, os, datetime
state_file = os.path.join(os.environ['CASE_DIR_ENV'], 'state.json')
with open(state_file, 'r') as f:
    state = json.load(f)
case_code = os.environ['CASE_CODE_ENV']
kb_case_path = os.environ['KB_CASE_PATH_ENV']
report_status = os.environ.get('REPORT_STATUS_ENV', '')
state['caseCode'] = case_code
state['knowledgeBaseSync'] = {
    'syncedAt': datetime.datetime.now().isoformat(),
    'syncedFiles': int(os.environ['SUCCESS_ENV']),
    'failedFiles': int(os.environ['FAIL_ENV']),
    'totalFiles': int(os.environ['TOTAL_ENV']),
    'caseCode': case_code,
    'kbPath': f'{kb_case_path}/'
}
# v0.4.0：回写 REPORT.html 的知识库预览链接（覆盖原临时预览链接）
if report_status == 'success':
    state['reportHtmlUrl'] = os.environ.get('REPORT_PREVIEW_URL_ENV', '')
    state['reportHtmlFileId'] = os.environ.get('REPORT_FILE_ID_ENV', '')
    state['reportHtmlUploadedAt'] = datetime.datetime.now().isoformat()
    state['reportHtmlStorage'] = 'kb'  # 标记走的是产品引进知识库
    state['reportHtmlTtl'] = '5y'  # 配置记录为 5y（doc.aishuo.co 长期预览，实际有效期由服务端策略决定）
    state.setdefault('gateStatus', {})['phase-5-5-html'] = 'completed'
elif report_status == 'failed':
    state['reportHtmlStorage'] = 'kb-failed'
    state['reportHtmlUrl'] = state.get('reportHtmlUrl')
    state['reportHtmlSyncError'] = 'REPORT.html upload/bind/preview failed; see sync output for API response'
    state.setdefault('gateStatus', {})['phase-5-5-html'] = 'failed'
with open(state_file, 'w') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
print(f'state.json 已更新: caseCode={case_code}, kbPath={kb_case_path}/')
if report_status == 'success':
    print('REPORT.html 预览链接（5 年）: ' + os.environ.get('REPORT_PREVIEW_URL_ENV', ''))
PY
fi

if [ "$SYNC_SEVERE_FAILURE" = "true" ] || [ "${REPORT_STATUS:-}" = "failed" ]; then
  exit 1
fi

exit 0
