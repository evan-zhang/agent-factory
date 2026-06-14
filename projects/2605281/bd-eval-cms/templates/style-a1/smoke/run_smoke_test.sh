#!/bin/bash
# Style A1 v0.9.1 smoke 测试入口
# 默认使用 fixture 派生临时案例，不修改历史案例数据。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RENDER_SCRIPT="$PROJECT_ROOT/templates/style-a1/render.py"
FIXTURE_DIR="$PROJECT_ROOT/templates/style-a1/fixtures"

printf '=== Style A1 v0.9.1 Smoke 测试 ===\n'
printf '项目根目录: %s\n' "$PROJECT_ROOT"
printf '渲染脚本: %s\n' "$RENDER_SCRIPT"
printf 'Fixture 目录: %s\n\n' "$FIXTURE_DIR"

if [ ! -f "$RENDER_SCRIPT" ]; then
  echo "❌ 渲染脚本不存在: $RENDER_SCRIPT"
  exit 1
fi

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

run_profile() {
  local profile="$1"
  local sample_suffix
  sample_suffix="$(echo "$profile" | tr 'A-Z' 'a-z')"
  local sample_file="$FIXTURE_DIR/sample-${sample_suffix}.md"
  local case_dir="$TEMP_DIR/smoke-${profile}"
  local output_file="$case_dir/REPORT.html"

  echo "=== 测试 ${profile} Profile ==="

  if [ ! -f "$sample_file" ]; then
    echo "❌ 样本不存在: $sample_file"
    exit 1
  fi

  mkdir -p "$case_dir"
  cp "$sample_file" "$case_dir/04-final-report.md"
  cat > "$case_dir/state.json" <<JSON
{
  "case_code": "2605-SMOKE-${profile}",
  "skill_code": "${profile}",
  "business_entity": "深康",
  "evaluation_date": "2026-06-13",
  "species_id": "SMOKE-${profile}"
}
JSON

  python3 "$RENDER_SCRIPT" "$case_dir" mckinsey-navy "$output_file" "$profile" >/tmp/bd-eval-smoke-${profile}.log 2>&1

  if [ ! -f "$output_file" ]; then
    echo "❌ ${profile} 未生成 HTML"
    cat /tmp/bd-eval-smoke-${profile}.log
    exit 1
  fi

  if grep -q '{{' "$output_file"; then
    echo "❌ ${profile} HTML 存在模板变量残留"
    exit 1
  fi

  echo "✅ ${profile} 通过：$(wc -c < "$output_file") 字节"
}

run_profile A-1

printf '\n=== Smoke 测试完成 ===\nA-1 通过 ✅\n'
