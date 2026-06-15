#!/usr/bin/env bash
# preflight-config.sh — bd-eval-cms 执行前必检清单
#
# 目的（v0.10.5 新增）：
#   在 run-opportunity / render_report / sync-to-knowledge-base 跑之前，
#   一次性检查所有必填配置项。任何一个 ❌ 立即退出，给可操作提示。
#   不静默走默认值。
#
# 退出码：
#   0 = 全部就绪
#   1 = 有必填项缺失（脚本会列出缺失项和修复命令）
#
# 用法：
#   bash scripts/preflight-config.sh
#   bash scripts/preflight-config.sh --json       # JSON 输出（程序化用）
#   bash scripts/preflight-config.sh --strict    # 严格模式（⚠️ 也算失败）

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$SKILL_DIR/config.yaml"

# 解析 flag
JSON_MODE=false
STRICT_MODE=false
for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --strict) STRICT_MODE=true ;;
  esac
done

# 收集结果
ERRORS=()
WARNINGS=()
PASSED=0

add_err() { ERRORS+=("$1"); }
add_warn() { WARNINGS+=("$1"); }

# 工具：判断分支结果
fail() {
  local item="$1" detail="$2" fix="${3:-}"
  add_err "$item|$detail|$fix"
}

warn() {
  local item="$1" detail="$2" fix="${3:-}"
  add_warn "$item|$detail|$fix"
}

ok() {
  PASSED=$((PASSED + 1))
}

# ========== 1. config.yaml 存在 ==========
if [ ! -f "$CONFIG_FILE" ]; then
  fail "config.yaml" "未找到: $CONFIG_FILE" "确认 Skill 目录完整（sparse-checkout 是否勾上）"
else
  ok
fi

# ========== 2. config.yaml 关键字段（用 python3 解析，避免 yq 依赖） ==========
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

if [ -f "$CONFIG_FILE" ]; then
  KB_PROJECT_ID=$(read_config_field projectId)
  KB_ROOT_DIR=$(read_config_field rootDir)
  KB_APPKEY_FILE=$(read_config_field appKeyFile)
  KB_PATH_TEMPLATE=$(read_config_field pathTemplate)
  RR_DEFAULT_STYLE=$(read_config_field defaultStyle)

  if [ -z "$KB_PROJECT_ID" ]; then
    fail "config.yaml: projectId" "未配置 knowledgeBase.projectId" "在 config.yaml 加 projectId: '<玄关产品引进知识库空间ID>'"
  else
    ok
  fi

  if [ -z "$KB_ROOT_DIR" ]; then
    fail "config.yaml: rootDir" "未配置 knowledgeBase.rootDir" "在 config.yaml 加 rootDir: 'CPYJ'"
  else
    ok
  fi

  if [ -z "$KB_APPKEY_FILE" ]; then
    KB_APPKEY_FILE=".secrets/kb_appkey"
  fi

  if [ -z "$KB_PATH_TEMPLATE" ]; then
    warn "config.yaml: pathTemplate" "未配置，使用默认 {ROOT}/{YYYYMM}/{caseCode}" "可选：在 config.yaml 显式配置 pathTemplate"
  else
    ok
  fi

  if [ -z "$RR_DEFAULT_STYLE" ]; then
    warn "config.yaml: reportRenderer.defaultStyle" "未配置，使用环境默认 a1" "可选：在 config.yaml 加 defaultStyle: 'a1'"
  else
    ok
  fi
fi

# ========== 3. AppKey 文件（v0.10.3 起：skill 专享文件） ==========
APPKEY_PATH="$SKILL_DIR/$KB_APPKEY_FILE"
if [ ! -f "$APPKEY_PATH" ]; then
  fail "AppKey 文件" "未找到: $APPKEY_PATH" "mkdir -p \"$(dirname "$APPKEY_PATH")\" && echo -n '你的系统级AppKey' > \"$APPKEY_PATH\""
else
  APP_KEY=$(cat "$APPKEY_PATH" | tr -d '[:space:]')
  if [ -z "$APP_KEY" ]; then
    fail "AppKey 文件" "文件为空: $APPKEY_PATH" "echo -n '你的系统级AppKey' > \"$APPKEY_PATH\""
  elif [ ${#APP_KEY} -lt 16 ]; then
    warn "AppKey 文件" "AppKey 长度异常（${#APP_KEY} 字节），可能不是完整 key" "确认是完整的系统级 AppKey（通常 32 字节）"
  else
    ok
  fi
fi

# ========== 4. 系统工具 ==========
for tool in curl python3; do
  if command -v "$tool" &> /dev/null; then
    ok
  else
    fail "系统工具: $tool" "未安装" "macOS: brew install $tool  |  Linux: apt install $tool"
  fi
done

# ========== 5. OpenClaw 环境（best effort） ==========
if [ -d "$HOME/.openclaw" ]; then
  ok
else
  warn "OpenClaw" "~/.openclaw 目录不存在" "确认 OpenClaw 已安装并初始化（https://docs.openclaw.ai）"
fi

# ========== 6. 关键 Skill 文件存在性 ==========
for f in "SKILL.md" "references/SOP.md" "scripts/run-opportunity.sh" "scripts/render_report.sh" "scripts/sync-to-knowledge-base.sh"; do
  if [ -f "$SKILL_DIR/$f" ]; then
    ok
  else
    fail "Skill 文件: $f" "未找到" "确认 sparse-checkout 完整：git sparse-checkout set projects/2605281/bd-eval-cms"
  fi
done

# ========== 7. 搜索子系统（v0.10.0 起自包含） ==========
for f in "scripts/search/core_search.sh" "scripts/search/source_ranker.sh" "scripts/search/keyword_mapper.sh" "scripts/search/field_extractor.sh" "scripts/search/validate_gate_search.sh"; do
  if [ -f "$SKILL_DIR/$f" ]; then
    ok
  else
    fail "搜索子系统: $f" "未找到" "升级到 v0.10.0+（v0.10.0 起搜索内化）"
  fi
done

# ========== 8. .secrets 目录权限（不应被提交） ==========
if [ -d "$SKILL_DIR/.secrets" ]; then
  PERMS=$(stat -f "%Lp" "$SKILL_DIR/.secrets" 2>/dev/null || stat -c "%a" "$SKILL_DIR/.secrets" 2>/dev/null)
  if [ -n "$PERMS" ] && [ "$PERMS" != "700" ] && [ "$PERMS" != "755" ]; then
    warn ".secrets 权限" "当前 $PERMS，建议 700" "chmod 700 \"$SKILL_DIR/.secrets\""
  else
    ok
  fi
fi

# ========== 输出 ==========
TOTAL=$((PASSED + ${#ERRORS[@]} + ${#WARNINGS[@]}))

if $JSON_MODE; then
  # JSON 模式（程序化）
  echo "{"
  echo "  \"passed\": $PASSED,"
  echo "  \"warnings\": ${#WARNINGS[@]},"
  echo "  \"errors\": ${#ERRORS[@]},"
  echo "  \"items\": ["
  first=true
  for e in "${ERRORS[@]}"; do
    IFS='|' read -r name detail fix <<< "$e"
    $first || echo ","
    first=false
    printf "    {\"status\":\"error\",\"name\":%s,\"detail\":%s,\"fix\":%s}" \
      "$(python3 -c "import json; print(json.dumps('$name'))")" \
      "$(python3 -c "import json; print(json.dumps('$detail'))")" \
      "$(python3 -c "import json; print(json.dumps('$fix'))")"
  done
  for w in "${WARNINGS[@]}"; do
    IFS='|' read -r name detail fix <<< "$w"
    $first || echo ","
    first=false
    printf "    {\"status\":\"warning\",\"name\":%s,\"detail\":%s,\"fix\":%s}" \
      "$(python3 -c "import json; print(json.dumps('$name'))")" \
      "$(python3 -c "import json; print(json.dumps('$detail'))")" \
      "$(python3 -c "import json; print(json.dumps('$fix'))")"
  done
  echo ""
  echo "  ]"
  echo "}"
else
  # 人读模式
  echo ""
  echo "=== bd-eval-cms 执行前必检 ==="
  echo ""
  if [ ${#ERRORS[@]} -gt 0 ]; then
    echo "❌ 失败项（必须修复）："
    for e in "${ERRORS[@]}"; do
      IFS='|' read -r name detail fix <<< "$e"
      echo "  ❌ $name"
      echo "     原因：$detail"
      if [ -n "$fix" ]; then
        echo "     修复：$fix"
      fi
      echo ""
    done
  fi

  if [ ${#WARNINGS[@]} -gt 0 ]; then
    echo "⚠️  提示项（建议处理）："
    for w in "${WARNINGS[@]}"; do
      IFS='|' read -r name detail fix <<< "$w"
      echo "  ⚠️  $name"
      echo "     说明：$detail"
      if [ -n "$fix" ]; then
        echo "     建议：$fix"
      fi
      echo ""
    done
  fi

  echo "════════════════════════════════════════"
  echo "  ✅ ${PASSED}  ⚠️ ${#WARNINGS[@]}  ❌ ${#ERRORS[@]}"
  echo "════════════════════════════════════════"
fi

# 退出码（不依赖 unbound 数组）
ERR_COUNT=${#ERRORS[@]}
WARN_COUNT=${#WARNINGS[@]}
if [ "${ERR_COUNT:-0}" -gt 0 ]; then
  exit 1
fi
if $STRICT_MODE && [ "${WARN_COUNT:-0}" -gt 0 ]; then
  exit 1
fi
exit 0
