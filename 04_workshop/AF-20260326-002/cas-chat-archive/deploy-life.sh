#!/bin/bash
# CAS 部署脚本 - Life Gateway
# 用于手动部署 CAS 到 life gateway

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAS_SCRIPT="$SCRIPT_DIR/scripts/cas_archive.py"
GATEWAY_NAME="life"
ARCHIVE_ROOT="$HOME/.openclaw/chat-archive"

echo "=== CAS Chat Archive 部署脚本 ==="
echo "Gateway: $GATEWAY_NAME"
echo "Archive Root: $ARCHIVE_ROOT"
echo ""

# 1. 初始化归档目录
echo "1. 初始化归档目录..."
python3 "$CAS_SCRIPT" --archive-root "$ARCHIVE_ROOT" init --gateway "$GATEWAY_NAME"

# 2. 测试记录一条消息
echo ""
echo "2. 测试记录消息..."
python3 "$CAS_SCRIPT" --archive-root "$ARCHIVE_ROOT" record-message \
  --gateway "$GATEWAY_NAME" \
  --direction inbound \
  --sender "Evan" \
  --text "CAS 部署测试 - $(date '+%Y-%m-%d %H:%M:%S')"

# 3. 显示归档目录结构
echo ""
echo "3. 归档目录结构:"
find "$ARCHIVE_ROOT/$GATEWAY_NAME" -type f | head -20

# 4. 显示最新日志内容
echo ""
echo "4. 最新日志内容:"
TODAY=$(date '+%Y-%m-%d')
LOG_FILE="$ARCHIVE_ROOT/$GATEWAY_NAME/logs/$TODAY.md"
if [ -f "$LOG_FILE" ]; then
  cat "$LOG_FILE"
else
  echo "日志文件不存在: $LOG_FILE"
fi

echo ""
echo "=== 部署完成 ==="
echo ""
echo "下一步："
echo "1. 在 gateway openclaw.json 启用 internal hook: hooks.internal.entries.cas-chat-archive-auto.enabled=true"
echo "2. 建议测试期保持 CAS_SCOPE_MODE=gateway；稳定后切换到 agent"
echo "3. 或者使用以下命令手动记录消息："
echo "   python3 $CAS_SCRIPT record-message --gateway $GATEWAY_NAME --direction inbound --text '你的消息'"
