#!/bin/bash
# render_report.sh — bd-eval-cms 报告渲染统一入口
# 内部调用，不依赖 doc-viewer skill（v0.7.0 起彻底解耦）
#
# 用法：
#   bash render_report.sh <品种目录> [风格] [配色] [输出HTML路径] [profile]
#
# 参数：
#   品种目录    必填，包含 04-final-report.md
#   风格        选填，12、13 或 a1（默认从 config.yaml 读 defaultStyle）
#   配色        选填，风格 12/a1 时有效（mckinsey-navy / investment-blue / burgundy-wine / forest-teal）
#                       风格 13 时忽略（硬编码 navy）
#   输出HTML    选填，默认 <品种目录>/REPORT.html
#   profile     选填，仅风格 a1 时有效（A-1/A-5/A-7 等），默认从 Markdown 元数据自动检测
#
# 示例：
#   bash render_report.sh bd-eval-cms/260612-TEST
#   bash render_report.sh bd-eval-cms/Epioxa 12 mckinsey-navy
#   bash render_report.sh bd-eval-cms/Epioxa a1 mckinsey-navy
#   bash render_report.sh bd-eval-cms/Epioxa a1 mckinsey-navy /tmp/report.html A-1
#   bash render_report.sh bd-eval-cms/Epioxa 13

set -euo pipefail

CASE_DIR="$1"
STYLE="${2:-}"
COLOR_THEME="${3:-}"
OUTPUT_HTML="${4:-}"
PROFILE="${5:-}"

# ========== 读 config.yaml 拿默认值 ==========
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$SKILL_DIR/config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ 错误：未找到 config.yaml: $CONFIG_FILE"
  exit 1
fi
if ! command -v yq &> /dev/null; then
  echo "❌ 错误：需要 yq 工具读取 config.yaml"
  exit 1
fi

# 默认风格：config.yaml.reportRenderer.defaultStyle
if [ -z "$STYLE" ]; then
  STYLE=$(yq '.reportRenderer.defaultStyle' "$CONFIG_FILE")
fi

# 默认配色：config.yaml.reportRenderer.defaultColorTheme
if [ -z "$COLOR_THEME" ]; then
  COLOR_THEME=$(yq '.reportRenderer.defaultColorTheme' "$CONFIG_FILE")
fi

# 默认输出路径
if [ -z "$OUTPUT_HTML" ]; then
  OUTPUT_HTML="$CASE_DIR/REPORT.html"
fi

# ========== 校验参数 ==========
if [ -z "$STYLE" ] || [ "$STYLE" = "null" ]; then
  echo "❌ 错误：未指定风格且 config.yaml 中没有 reportRenderer.defaultStyle"
  exit 1
fi

if [ "$STYLE" != "12" ] && [ "$STYLE" != "13" ] && [ "$STYLE" != "a1" ]; then
  echo "❌ 错误：风格必须是 12、13 或 a1，当前：$STYLE"
  exit 1
fi

if [ ! -d "$CASE_DIR" ]; then
  echo "❌ 错误：品种目录不存在: $CASE_DIR"
  exit 1
fi

if [ ! -f "$CASE_DIR/04-final-report.md" ]; then
  echo "❌ 错误：未找到 04-final-report.md: $CASE_DIR/04-final-report.md"
  exit 1
fi

# ========== 调度 ==========
echo "=== bd-eval-cms 报告渲染 ==="
echo "品种目录: $CASE_DIR"
echo "风格: $STYLE"
if [ "$STYLE" = "12" ] || [ "$STYLE" = "a1" ]; then
  echo "配色: $COLOR_THEME"
fi
echo "输出: $OUTPUT_HTML"
echo ""

TEMPLATE_DIR="$SKILL_DIR/templates/style-$STYLE"

if [ "$STYLE" = "12" ]; then
  # 风格 12：调 convert-md-to-html.py
  PY_SCRIPT="$TEMPLATE_DIR/convert-md-to-html.py"
  if [ ! -f "$PY_SCRIPT" ]; then
    echo "❌ 错误：风格 12 转换脚本不存在: $PY_SCRIPT"
    exit 1
  fi
  python3 "$PY_SCRIPT" "$CASE_DIR" "$COLOR_THEME" "$OUTPUT_HTML"
elif [ "$STYLE" = "13" ]; then
  # 风格 13：调 report_renderer.py
  PY_SCRIPT="$TEMPLATE_DIR/report_renderer.py"
  if [ ! -f "$PY_SCRIPT" ]; then
    echo "❌ 错误：风格 13 渲染脚本不存在: $PY_SCRIPT"
    exit 1
  fi
  # 风格 13 是单文件渲染：python3 report_renderer.py <input.md> <output.html>
  python3 "$PY_SCRIPT" "$CASE_DIR/04-final-report.md" "$OUTPUT_HTML"
elif [ "$STYLE" = "a1" ]; then
  # 风格 A1：调 render.py
  PY_SCRIPT="$TEMPLATE_DIR/render.py"
  if [ ! -f "$PY_SCRIPT" ]; then
    echo "❌ 错误：风格 A1 渲染脚本不存在: $PY_SCRIPT"
    exit 1
  fi
  # 风格 A1 用法：python3 render.py <报告目录> [配色名] [输出路径] [profile]
  # 保持向后兼容：profile 参数可选
  if [ -n "$PROFILE" ]; then
    python3 "$PY_SCRIPT" "$CASE_DIR" "$COLOR_THEME" "$OUTPUT_HTML" "$PROFILE"
  else
    # 向后兼容：不传 profile 参数，让 render.py 自动检测
    python3 "$PY_SCRIPT" "$CASE_DIR" "$COLOR_THEME" "$OUTPUT_HTML"
  fi
fi

# ========== 验证：模板变量残留检查 ==========
TEMPLATE_COUNT=$(grep -c '{{' "$OUTPUT_HTML" 2>/dev/null || true)
TEMPLATE_COUNT=${TEMPLATE_COUNT:-0}
if [ "$TEMPLATE_COUNT" -gt 0 ] 2>/dev/null; then
  echo "❌ FAIL: 发现 $TEMPLATE_COUNT 个未替换的模板变量"
  grep -n '{{' "$OUTPUT_HTML" | head -10
  exit 1
fi
echo ""
echo "✅ 渲染完成：$OUTPUT_HTML"
echo "   模板变量残留: 0"
echo "   零网络副作用（未调任何上传 API）"
