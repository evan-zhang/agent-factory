#!/bin/bash
# preflight-phase.sh — Phase 5.5 HTML 生成前的 readiness 检查
#
# 用法：bash preflight-phase.sh <品种目录>
#
# 检查项：
#   v0.10.6 改造：委托给 verify-manifest.sh 统一校验
#   1. state.json 存在且 JSON 有效
#   2. 所有零件文件存在且符合体量要求
#   3. state.json.gateStatus 所有前置 gate 均为 completed
#
# 环境变量：
#   BD_EVAL_CMS_SKIP_PREFLIGHT=1  跳过检查（仅限测试/历史回放）
#
# 退出码：
#   0 - 所有检查通过
#   1 - 检查失败，列出缺失项

set -euo pipefail

# 允许跳过检查（测试/历史回放用）
if [ "${BD_EVAL_CMS_SKIP_PREFLIGHT:-}" = "1" ]; then
  echo "⚠️  跳过 preflight 检查（BD_EVAL_CMS_SKIP_PREFLIGHT=1，仅限测试/历史回放）"
  exit 0
fi

CASE_DIR="${1:-}"

if [ -z "$CASE_DIR" ]; then
  echo "❌ preflight 错误：必须提供品种目录路径"
  exit 1
fi

if [ ! -d "$CASE_DIR" ]; then
  echo "❌ preflight 错误：品种目录不存在: $CASE_DIR"
  exit 1
fi

# ========== v0.10.6 改造：委托给 verify-manifest.sh ==========
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

echo "=== Phase 5.5 Readiness Preflight（v0.10.6 统一校验） ==="
echo "检查目录: $CASE_DIR"
echo ""

# 调用 verify-manifest.sh 进行校验
if "$VERIFY_MANIFEST" "$CASE_DIR"; then
  echo ""
  echo "✅ Preflight 检查通过：所有关键产物齐全，可以进行 Phase 5.5 HTML 生成"
  exit 0
else
  echo ""
  echo "❌ Preflight 检查失败：无法进行 Phase 5.5 HTML 生成"
  echo ""
  echo "建议："
  echo "  1. 补全缺失的上游产物"
  echo "  2. 确保 state.json.gateStatus 中所有 Phase 5.5 前置 gate 均为 completed"
  echo "  3. 如为测试/历史回放，可设置 BD_EVAL_CMS_SKIP_PREFLIGHT=1 跳过检查"
  exit 1
fi
