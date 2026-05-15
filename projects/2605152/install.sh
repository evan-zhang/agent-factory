#!/bin/bash
#
# bd-eval 安装脚本
# 用法: bash install.sh [--target ~/.openclaw/skills] [--force]
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/skills}"
FORCE=false

# ──────────────────────────────────────────
# 帮助
# ──────────────────────────────────────────
usage() {
  cat <<'EOF'
用法: install.sh [选项]

选项:
  --target <目录>   安装目录（默认 ~/.openclaw/skills）
  --force           覆盖已存在的同名 skill
  -h, --help        显示帮助

───────────────────────────────────────────
Skill 分层说明

【主 Skill】（本包必须包含）
  ✅ bd-eval         BD品种评估主流水线（Phase 1-5.5）
  ✅ doc-viewer      整体报告 HTML 生成（风格03琥珀金，Phase 5.5）
  ✅ multi-search    多源搜索基础设施（Phase 1/3 搜索降级）

【参考 Skill】（建议安装，非强制）
  ✅ tpr-framework   Battle/GRV 规范参考（Phase 2/4）

前置要求:
  - OpenClaw ≥ 0.9.0
  - 内置工具: web_search, sessions_spawn, exec, message
EOF
}

# ──────────────────────────────────────────
# 解析参数
# ──────────────────────────────────────────
for arg in "$@"; do
  case $arg in
    --target)
      TARGET_DIR="$2"
      shift 2
      ;;
    --force)
      FORCE=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
  esac
done

# ──────────────────────────────────────────
# 前置检查
# ──────────────────────────────────────────
echo "============================================"
echo "  BD 品种评估流水线 安装程序"
echo "============================================"
echo "安装目录: $TARGET_DIR"
echo ""

if [ ! -d "$TARGET_DIR" ]; then
  echo "❌ 错误: 目录不存在 $TARGET_DIR"
  echo "请确认 OpenClaw 已正确安装"
  exit 1
fi

# ──────────────────────────────────────────
# Skill 清单
# 格式: name:required:description
# ──────────────────────────────────────────
SKILLS=(
  "bd-eval:required:BD品种评估主流水线（核心 Skill）"
  "doc-viewer:required:整体报告 HTML 生成（Phase 5.5 必须）"
  "multi-search:required:多源搜索基础设施（Phase 1/3 必须）"
  "tpr-framework:optional:Battle/GRV 规范参考（Phase 2/4）"
)

# ──────────────────────────────────────────
# 安装函数
# ──────────────────────────────────────────
install_skill() {
  local name="$1"
  local required="$2"
  local desc="$3"

  local src="$SCRIPT_DIR/skills/$name"

  if [ ! -d "$src" ]; then
    if [ "$required" = "required" ]; then
      echo "❌ 错误: 缺少必需 skill: $name"
      echo "请确认安装包完整，解压后重新运行"
      exit 1
    else
      echo "⚠️  跳过(不存在): $name"
      return 0
    fi
  fi

  local dst="$TARGET_DIR/$name"

  if [ -d "$dst" ] && [ "$FORCE" = false ]; then
    echo "⏭️  已存在，跳过: $name"
    return 0
  fi

  if [ -d "$dst" ]; then
    echo "🔄 覆盖安装: $name"
    rm -rf "$dst"
  else
    echo "✅ 安装: $name"
  fi

  cp -r "$src" "$dst"
}

# ──────────────────────────────────────────
# 执行安装
# ──────────────────────────────────────────
echo "开始安装..."
echo ""

for entry in "${SKILLS[@]}"; do
  IFS=':' read -r name required desc <<< "$entry"
  install_skill "$name" "$required" "$desc"
done

# ──────────────────────────────────────────
# 验证
# ──────────────────────────────────────────
echo ""
echo "============================================"
echo "  安装完成 ✅"
echo "============================================"
echo ""
echo "已安装 Skills:"
for entry in "${SKILLS[@]}"; do
  IFS=':' read -r name required desc <<< "$entry"
  dst="$TARGET_DIR/$name"
  if [ -d "$dst" ]; then
    echo "  ✅ $name"
    echo "      $desc"
  fi
done

echo ""
echo "============================================"
echo "  触发词"
echo "============================================"
echo "  BD评估 / 跑品种 / 评估新药 / BD品种筛选 / 新批次"
echo ""
echo "Agent 使用方式:"
echo ""
echo '  用户: "BD评估：CG-0255、RHOFADE、门冬氨酸钙片"'
echo ""
echo "  Agent → 检测到触发词"
echo "  Agent → 读取 ~/.openclaw/skills/bd-eval/SKILL.md"
echo "  Agent → 按 Phase 1 → Phase 5.5 执行"
echo "  Agent → 返回 doc.20100706.xyz 报告链接"
echo ""
echo "文档位置:"
echo "  主 Skill:   $TARGET_DIR/bd-eval/SKILL.md"
echo "  快速开始:  $TARGET_DIR/bd-eval/QUICKREF.md"
echo "  完整流程:  $TARGET_DIR/bd-eval/references/SOP.md"
