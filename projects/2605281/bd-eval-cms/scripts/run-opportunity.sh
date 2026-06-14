#!/usr/bin/env bash
# run-opportunity.sh — 单一入口（商机驱动）
#
# 设计原则（v0.9.2）：
#   - 入口 = (product, company) 唯一对
#   - 自动生成 caseCode = YYMMDD-XXXX
#   - 重复调用同 (product, company) → 幂等续跑
#   - 输出结构化 prefix，方便程序解析：
#       CASE_PATH=...
#       CASE_CODE=...
#       PHASE_STATUS=...
#       OPPORTUNITY_ID=...
#
# 用法：
#   run-opportunity.sh --product "TRTL-729" --company "TestCo Pharma"
#   run-opportunity.sh --json /path/to/opportunity.json
#   run-opportunity.sh --json -        # 从 stdin 读取
#   run-opportunity.sh --product X --company Y --dry-run
#
# 可选 flag：
#   --indication    适应症
#   --region        地区
#   --notes         业务备注
#   --scheme        A / B / C（默认 B）
#   --mode          auto / semi（默认 auto）
#   --ext <path>    外部资料（可重复）
#   --json <path|-> JSON 输入
#   --dry-run       仅打印动作，不写文件、不调 orchestrator
#   --help          显示帮助

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"

PRODUCT=""
COMPANY=""
INDICATION=""
REGION=""
NOTES=""
SCHEME="B"
MODE="auto"
EXT_PATHS=()
JSON_PATH=""
DRY_RUN=false
SHOW_HELP=false

# ============ 帮助 ============
print_help() {
  cat <<'EOF'
run-opportunity.sh — bd-eval-cms 单一入口

用法：
  run-opportunity.sh --product "NAME" --company "CO" [options]
  run-opportunity.sh --json <file|-> [options]
  run-opportunity.sh --help

必填：
  --product NAME        品种名称
  --company CO          公司名称

可选：
  --indication IND      适应症
  --region REG          目标地区
  --notes TXT           业务备注
  --scheme A|B|C        评估阶段（默认 B）
  --mode auto|semi      执行模式（默认 auto）
  --ext PATH            外部资料文件（可重复）
  --json PATH|-         JSON 输入（与 flag 互斥时 JSON 优先）
  --dry-run             仅打印动作，不写文件
  --help                显示本帮助

输出（程序可解析）：
  CASE_PATH=...
  CASE_CODE=...
  PHASE_STATUS=...
  OPPORTUNITY_ID=...

示例：
  run-opportunity.sh --product "TRTL-729" --company "TestCo" --dry-run
  run-opportunity.sh --json opportunity.json
EOF
}

# ============ 参数解析 ============
while [ $# -gt 0 ]; do
  arg="${1:-}"
  case "$arg" in
    --product)   shift; PRODUCT="${1:-}"; shift ;;
    --company)   shift; COMPANY="${1:-}"; shift ;;
    --indication) shift; INDICATION="${1:-}"; shift ;;
    --region)    shift; REGION="${1:-}"; shift ;;
    --notes)     shift; NOTES="${1:-}"; shift ;;
    --scheme)    shift; SCHEME="${1:-}"; shift ;;
    --mode)      shift; MODE="${1:-}"; shift ;;
    --ext)       shift; EXT_PATHS+=("${1:-}"); shift ;;
    --json)      shift; JSON_PATH="${1:-}"; shift ;;
    --dry-run)   DRY_RUN=true; shift ;;
    --help|-h)   SHOW_HELP=true; shift ;;
    *) echo "❌ 未知参数：$arg" >&2; exit 1 ;;
  esac
done

if $SHOW_HELP; then
  print_help
  exit 0
fi

# ============ JSON 解析（覆盖 flags） ============
if [ -n "$JSON_PATH" ]; then
  if [ "$JSON_PATH" = "-" ]; then
    JSON_CONTENT="$(cat)"
  elif [ -f "$JSON_PATH" ]; then
    JSON_CONTENT="$(cat "$JSON_PATH")"
  else
    echo "❌ JSON 文件不存在：$JSON_PATH" >&2
    exit 1
  fi
  if ! command -v jq >/dev/null 2>&1; then
    echo "❌ 需要 jq 来解析 JSON" >&2
    exit 1
  fi
  _p=$(printf '%s' "$JSON_CONTENT" | jq -r '.product // empty')
  _c=$(printf '%s' "$JSON_CONTENT" | jq -r '.company // empty')
  [ -n "$_p" ] && PRODUCT="$_p"
  [ -n "$_c" ] && COMPANY="$_c"
  _i=$(printf '%s' "$JSON_CONTENT" | jq -r '.indication // empty')
  [ -n "$_i" ] && INDICATION="$_i"
  _r=$(printf '%s' "$JSON_CONTENT" | jq -r '.region // empty')
  [ -n "$_r" ] && REGION="$_r"
  _n=$(printf '%s' "$JSON_CONTENT" | jq -r '.notes // empty')
  [ -n "$_n" ] && NOTES="$_n"
  _s=$(printf '%s' "$JSON_CONTENT" | jq -r '.scheme // empty')
  [ -n "$_s" ] && SCHEME="$_s"
  _m=$(printf '%s' "$JSON_CONTENT" | jq -r '.mode // empty')
  [ -n "$_m" ] && MODE="$_m"
  # ext array → bash array
  if printf '%s' "$JSON_CONTENT" | jq -e '.ext' >/dev/null 2>&1; then
    while IFS= read -r line; do
      [ -n "$line" ] && EXT_PATHS+=("$line")
    done < <(printf '%s' "$JSON_CONTENT" | jq -r '.ext[]?')
  fi
fi

# ============ 校验 ============
if [ -z "$PRODUCT" ]; then
  echo "❌ 缺少必填项：--product（或 JSON 里的 product）" >&2
  exit 1
fi
if [ -z "$COMPANY" ]; then
  echo "❌ 缺少必填项：--company（或 JSON 里的 company）" >&2
  exit 1
fi
if [ "$MODE" != "auto" ] && [ "$MODE" != "semi" ]; then
  echo "❌ --mode 仅支持 auto | semi，当前：$MODE" >&2
  exit 1
fi
if [ "$SCHEME" != "A" ] && [ "$SCHEME" != "B" ] && [ "$SCHEME" != "C" ]; then
  echo "❌ --scheme 仅支持 A | B | C，当前：$SCHEME" >&2
  exit 1
fi
if [ ${#EXT_PATHS[@]} -gt 0 ]; then
  for p in "${EXT_PATHS[@]}"; do
    if [ ! -f "$p" ]; then
      echo "❌ --ext 指向的文件不存在：$p" >&2
      exit 1
    fi
  done
fi

# ============ caseCode 生成 ============
generate_abbrev() {
  local name="$1"
  python3 - "$name" <<'PY'
import sys
import re
try:
    from pypinyin import lazy_pinyin, Style
except Exception:
    lazy_pinyin = None
    Style = None

name = sys.argv[1].strip()
if not name:
    print("XXXX")
    sys.exit(0)

# 提取所有 ASCII 字母数字
ascii_letters = re.findall(r'[A-Za-z0-9]+', name)
ascii_part = ''.join(ascii_letters)[:4].upper()

# 提取所有中文字符 → pypinyin 首字母
chinese_chars = re.findall(r'[\u4e00-\u9fff]+', name)
chinese_part = ''
for chunk in chinese_chars:
    if lazy_pinyin is not None and Style is not None:
        initials = lazy_pinyin(chunk, style=Style.FIRST_LETTER)
        chinese_part += ''.join(initials)
    else:
        chinese_part += 'X'  # 无 pypinyin 兜底
chinese_part = chinese_part[:4].upper()

# 拼接：英文字母优先，不足 4 位用拼音首字母补齐
combined = (ascii_part + chinese_part)[:4]
combined = combined.ljust(4, 'X')
print(combined)
PY
}

# 规范化 product/company 用于 opportunity_id。
# 规则：ASCII 保留；中文转 pinyin；其余字符转 -；避免纯中文输入被归一化为空。
normalize_id() {
  python3 - "$1" <<'PY'
import re
import sys
try:
    from pypinyin import lazy_pinyin
except Exception:
    lazy_pinyin = None

text = sys.argv[1].strip()
out = []
for ch in text:
    if re.match(r'[A-Za-z0-9_-]', ch):
        out.append(ch)
    elif ch.isspace():
        out.append('-')
    elif '\u4e00' <= ch <= '\u9fff':
        if lazy_pinyin is not None:
            out.append(lazy_pinyin(ch)[0])
        else:
            out.append('x')
    else:
        out.append('-')
slug = ''.join(out)
slug = re.sub(r'-+', '-', slug).strip('-_')
print(slug or 'unknown')
PY
}

same_opportunity() {
  local state_file="$1"
  jq -e --arg p "$PRODUCT" --arg c "$COMPANY" \
    '.opportunity.product == $p and .opportunity.company == $c' \
    "$state_file" >/dev/null 2>&1
}

DATE_PREFIX="$(date +%y%m%d)"
ABBREV="$(generate_abbrev "$PRODUCT")"
BASE_CODE="${DATE_PREFIX}-${ABBREV}"

# ============ 唯一性 / 冲突处理 ============
BASE_DIR="$SKILL_ROOT/$BASE_CODE"
PRODUCT_SLUG="$(normalize_id "$PRODUCT")"
COMPANY_SLUG="$(normalize_id "$COMPANY")"
case_dir=""

if [ ! -d "$BASE_DIR" ]; then
  # 全新 caseCode，零冲突
  case_dir="$BASE_DIR"
else
  # 检查是否同 opportunity（幂等续跑）
  existing_state="$BASE_DIR/state.json"
  if [ -f "$existing_state" ]; then
    if same_opportunity "$existing_state"; then
      case_dir="$BASE_DIR"
    fi
  fi
  # 未命中 → 加后缀重试
  if [ -z "$case_dir" ]; then
    found=false
    for n in $(seq 1 99); do
      if [ "$n" -ge 10 ]; then
        suffix="-$(printf '%02d' "$n")"
      else
        suffix="-$n"
      fi
      candidate="$BASE_DIR$suffix"
      if [ ! -d "$candidate" ]; then
        case_dir="$candidate"
        found=true
        break
      fi
      # 已存在 → 查 opportunity
      cand_state="$candidate/state.json"
      if [ -f "$cand_state" ]; then
        if same_opportunity "$cand_state"; then
          case_dir="$candidate"
          found=true
          break
        fi
      fi
    done
    if ! $found; then
      echo "❌ 后缀冲突超限（>99），请手动处理 $BASE_DIR 下的旧目录" >&2
      exit 1
    fi
  fi
fi

CASE_CODE="$(basename "$case_dir")"
OPPORTUNITY_ID="${CASE_CODE}::${PRODUCT_SLUG}::${COMPANY_SLUG}"

# ============ Dry-run 模式 ============
if $DRY_RUN; then
  echo "🔍 [dry-run] 即将执行："
  echo "  product    = $PRODUCT"
  echo "  company    = $COMPANY"
  echo "  indication = ${INDICATION:-<未填>}"
  echo "  region     = ${REGION:-<未填>}"
  echo "  notes      = ${NOTES:-<未填>}"
  echo "  scheme     = $SCHEME"
  echo "  mode       = $MODE"
  echo "  ext files  = ${#EXT_PATHS[@]}"
  if [ ${#EXT_PATHS[@]} -gt 0 ]; then
    for p in "${EXT_PATHS[@]}"; do echo "    - $p"; done
  fi
  echo "  case dir   = $case_dir"
  echo "  case code  = $CASE_CODE"
  echo "  opportunity_id = $OPPORTUNITY_ID"
  echo ""
  echo "CASE_PATH=$case_dir"
  echo "CASE_CODE=$CASE_CODE"
  echo "PHASE_STATUS=phase-1:pending|dry-run"
  echo "OPPORTUNITY_ID=$OPPORTUNITY_ID"
  exit 0
fi

# ============ 初始化（或续跑） ============
IS_NEW=false
if [ ! -d "$case_dir" ]; then
  IS_NEW=true
  mkdir -p "$case_dir/02-gate-by-chapter/history"
  mkdir -p "$case_dir/battle"
  mkdir -p "$case_dir/references/P1"
  mkdir -p "$case_dir/EXT"
fi

# 时间戳
NOW="$(date -Iseconds)"

# ============ 写 00-opportunity.md（仅新 case 或续跑时刷新原始输入）============
cat > "$case_dir/00-opportunity.md" <<EOF
# 商机输入

- **caseCode**: $CASE_CODE
- **opportunity_id**: $OPPORTUNITY_ID
- **product**: $PRODUCT
- **company**: $COMPANY
- **indication**: ${INDICATION:-<未填>}
- **region**: ${REGION:-<未填>}
- **scheme**: $SCHEME
- **mode**: $MODE
- **notes**: ${NOTES:-<未填>}
- **submittedAt**: $NOW
- **source**: scripts/run-opportunity.sh

## 原始输入

\`\`\`
product    = $PRODUCT
company    = $COMPANY
indication = ${INDICATION:-}
region     = ${REGION:-}
notes      = ${NOTES:-}
scheme     = $SCHEME
mode       = $MODE
ext files  = ${#EXT_PATHS[@]}
$(if [ ${#EXT_PATHS[@]} -gt 0 ]; then for p in "${EXT_PATHS[@]}"; do echo "  - $p"; done; fi)
\`\`\`

## 处置

由 \`scripts/run-opportunity.sh\` 接收。
EOF

# ============ 处理 EXT 资料 ============
ext_count=0
if [ ${#EXT_PATHS[@]} -gt 0 ]; then
  for p in "${EXT_PATHS[@]}"; do
    ext_count=$((ext_count + 1))
    ext_id=$(printf 'EXT-%03d' "$ext_count")
    ext_basename="$(basename "$p")"
    cp "$p" "$case_dir/EXT/${ext_id}-${ext_basename}"
    cat > "$case_dir/EXT/${ext_id}.md" <<MDEOF
# [$ext_id] $ext_basename
- **来源方式**: 外部传入
- **原始位置**: $p
- **提供方**: $COMPANY
- **资料类型**: 业务原始材料
- **提供时间**: $NOW
- **覆盖Gate**: 待 Phase 2 路由后由 Orchestrator 决定

## 文件已复制到
\`\`\`
EXT/${ext_id}-${ext_basename}
\`\`\`
MDEOF
  done
fi

# ============ 初始化 state.json（仅新 case）============
if $IS_NEW; then
  cat > "$case_dir/state.json" <<JSON
{
  "caseCode": "$CASE_CODE",
  "name": "$PRODUCT",
  "displayName": "$PRODUCT ($COMPANY)",
  "scheme": "$SCHEME",
  "businessEntity": "待确认",
  "routedSkill": "待路由",
  "routedChain": [],
  "phase": "opportunity_accepted",
  "opportunity": {
    "id": "$OPPORTUNITY_ID",
    "product": "$PRODUCT",
    "company": "$COMPANY",
    "indication": "${INDICATION:-}",
    "region": "${REGION:-}",
    "notes": "${NOTES:-}",
    "extFiles": [$(if [ ${#EXT_PATHS[@]} -gt 0 ]; then printf '"%s",' "${EXT_PATHS[@]}" | sed 's/,$//'; fi)],
    "submittedAt": "$NOW",
    "source": "scripts/run-opportunity.sh"
  },
  "gateStatus": {
    "phase-1": "pending",
    "phase-2": "pending",
    "one-pager": "pending",
    "gate-0": "pending",
    "gate-1": "pending",
    "gate-2": "pending",
    "gate-3": "pending",
    "gate-4": "pending",
    "gate-5": "pending",
    "phase-4-battle": "pending",
    "phase-5-merge": "pending",
    "phase-5-5-html": "pending"
  },
  "lastHeartbeat": "$NOW",
  "inProgressGate": null,
  "currentVersion": 1,
  "gateVersions": {
    "One-pager": 1, "Gate-0": 1, "Gate-1": 1, "Gate-2": 1,
    "Gate-3": 1, "Gate-4": 1, "Gate-5": 1
  },
  "financialThresholdType": "待判断",
  "routingDecision": null,
  "discovery": null,
  "updateHistory": []
}
JSON
  echo "🆕 新建 case：$CASE_CODE（$PRODUCT / $COMPANY）"
else
  # 续跑时不覆盖 gateStatus / phase / 历史状态，只刷新 opportunity 元信息。
  # 这样可以修复旧版 CJK opportunity_id 归一化为空的问题，也保证 suffix 后 OPPORTUNITY_ID 与真实 CASE_CODE 一致。
  tmp_state="$(mktemp)"
  jq --arg id "$OPPORTUNITY_ID" \
     --arg product "$PRODUCT" \
     --arg company "$COMPANY" \
     --arg indication "${INDICATION:-}" \
     --arg region "${REGION:-}" \
     --arg notes "${NOTES:-}" \
     --arg submittedAt "$NOW" \
     '.opportunity.id = $id
      | .opportunity.product = $product
      | .opportunity.company = $company
      | .opportunity.indication = $indication
      | .opportunity.region = $region
      | .opportunity.notes = $notes
      | .opportunity.submittedAt = $submittedAt
      | .opportunity.source = "scripts/run-opportunity.sh"' \
     "$case_dir/state.json" > "$tmp_state"
  mv "$tmp_state" "$case_dir/state.json"
  echo "🔄 续跑 case：$CASE_CODE（$PRODUCT / $COMPANY）"
fi

# ============ 状态摘要 ============
PHASE_STATUS="$(jq -r '.phase // "unknown"' "$case_dir/state.json" 2>/dev/null || echo 'unknown')"
GATE_FIRST_PENDING="$(jq -r '.gateStatus | to_entries[] | select(.value != "completed") | .key' "$case_dir/state.json" 2>/dev/null | head -1)"
[ -z "$GATE_FIRST_PENDING" ] && GATE_FIRST_PENDING="all_completed"

# ============ 启动 Orchestrator（仅新 case 首次跑 OR 显式续跑）============
# 在 auto 模式下：如果有未完成 gate，调用 orchestrator-resume.sh
if [ "$GATE_FIRST_PENDING" != "all_completed" ]; then
  if [ "$MODE" = "auto" ]; then
    echo "🚀 启动 Orchestrator 自驱 Phase 1..5.5（auto 模式）"
    bash "$SCRIPT_DIR/orchestrator-resume.sh" \
      --case-code="$CASE_CODE" \
      --mode="$MODE" \
      --projects-root="$SKILL_ROOT"
  else
    echo "⏸️  semi 模式：等待人工确认后再启动。"
    echo "  请运行：bash scripts/run.sh $CASE_CODE"
  fi
fi

# ============ 最终输出（程序可解析）============
echo ""
echo "CASE_PATH=$case_dir"
echo "CASE_CODE=$CASE_CODE"
echo "PHASE_STATUS=$GATE_FIRST_PENDING"
echo "OPPORTUNITY_ID=$OPPORTUNITY_ID"
