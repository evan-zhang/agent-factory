#!/usr/bin/env bash
# file2voice.sh — File2Voice 主入口脚本
# 读取文件 → 提取文本 → AI 改写口播稿 → MiniMax TTS → 输出音频
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# 默认配置
DEFAULT_VOICE="Chinese (Mandarin)_Male_Announcer"
DEFAULT_FORMAT="mp3"
DEFAULT_SAMPLE_RATE=32000
DEFAULT_SPEED=1
DEFAULT_MAX_DURATION=5

# 从 config.json 加载配置（如果存在）
if [[ -f "$SKILL_DIR/config.json" ]]; then
  # 用 python 解析 JSON 配置
  eval "$(python3 -c "
import json, sys
try:
    cfg = json.load(open('$SKILL_DIR/config.json'))
    d = cfg.get('defaults', {})
    for k, v in d.items():
        print(f\"CFG_{k.upper()}='{v}'\")
except: pass
")"
fi

# 参数解析
INPUT_FILE=""
OUTPUT=""
STYLE=""
DURATION=""
VOICE=""
AUTO=false
FORMAT=""

show_help() {
  cat <<EOF
File2Voice — 文件转口播语音

用法: file2voice.sh <input_file> [选项]

选项:
  -o, --output <path>     输出文件路径（默认：与输入同目录）
  -s, --style <style>     口播风格（讲解风/播报风/叙事风/专业风/轻松风）
  -d, --duration <min>    目标时长（3/5/10，默认自动）
  -v, --voice <id>        音色 ID（覆盖自动匹配）
  --auto                  跳过确认直接生成
  --format <fmt>          输出格式（mp3/wav，默认 mp3）
  -h, --help              显示帮助

示例:
  file2voice.sh report.pdf
  file2voice.sh article.md -s 播报风 -d 3
  file2voice.sh input.txt --auto -o /tmp/output.mp3
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)  OUTPUT="$2"; shift 2 ;;
    -s|--style)   STYLE="$2"; shift 2 ;;
    -d|--duration) DURATION="$2"; shift 2 ;;
    -v|--voice)   VOICE="$2"; shift 2 ;;
    --auto)       AUTO=true; shift ;;
    --format)     FORMAT="$2"; shift 2 ;;
    -h|--help)    show_help; exit 0 ;;
    -*)           echo "未知选项: $1"; show_help; exit 1 ;;
    *)            INPUT_FILE="$1"; shift ;;
  esac
done

# 验证输入
if [[ -z "$INPUT_FILE" ]]; then
  echo "错误：请指定输入文件" >&2
  show_help
  exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "错误：文件不存在: $INPUT_FILE" >&2
  exit 1
fi

# 检查 ffmpeg
if ! command -v ffmpeg &>/dev/null; then
  echo "错误：需要 ffmpeg，请先安装（brew install ffmpeg）" >&2
  exit 1
fi

# 检查 API Key
API_KEY="${MINIMAX_API_KEY:-}"
if [[ -z "$API_KEY" ]]; then
  echo "错误：请设置环境变量 MINIMAX_API_KEY" >&2
  exit 1
fi

# 应用默认值
FORMAT="${FORMAT:-${DEFAULT_FORMAT:-mp3}}"
VOICE="${VOICE:-}"
DURATION="${DURATION:-}"
STYLE="${STYLE:-}"

# 确定输出路径
FILENAME=$(basename "$INPUT_FILE")
BASENAME="${FILENAME%.*}"
DIRNAME=$(dirname "$INPUT_FILE")
OUTPUT="${OUTPUT:-${DIRNAME}/${BASENAME}._file2voice.${FORMAT}}"

# 创建临时目录
TMPDIR=$(mktemp -d /tmp/file2voice.XXXXXX)
trap 'rm -rf "$TMPDIR"' EXIT

echo "[file2voice] 输入文件: $INPUT_FILE"
echo "[file2voice] 临时目录: $TMPDIR"

# ── Step 1: 文本提取 ──
echo "[file2voice] Step 1/4: 提取文本..."
TEXT_FILE="$TMPDIR/extracted.txt"
bash "$SCRIPT_DIR/extract_text.sh" "$INPUT_FILE" "$TEXT_FILE"

# 统计字数
CHAR_COUNT=$(wc -m < "$TEXT_FILE" | tr -d ' ')
LINE_COUNT=$(wc -l < "$TEXT_FILE" | tr -d ' ')
echo "[file2voice] 提取完成: ${CHAR_COUNT} 字符, ${LINE_COUNT} 行"

if [[ "$CHAR_COUNT" -eq 0 ]]; then
  echo "错误：文件中未提取到文本内容" >&2
  exit 1
fi

# ── Step 2: 判断时长和风格 ──
# 按字符数自动判断目标时长（250字/分钟）
if [[ -z "$DURATION" ]]; then
  if [[ "$CHAR_COUNT" -le 1000 ]]; then
    TARGET_MINUTES=3
    TARGET_CHARS=750
  elif [[ "$CHAR_COUNT" -le 2500 ]]; then
    TARGET_MINUTES=5
    TARGET_CHARS=1250
  else
    TARGET_MINUTES=5
    TARGET_CHARS=1250
  fi
else
  TARGET_MINUTES="$DURATION"
  TARGET_CHARS=$((DURATION * 250))
fi

echo "[file2voice] 目标时长: ${TARGET_MINUTES} 分钟（约 ${TARGET_CHARS} 字）"

# ── Step 3: AI 改写口播稿 ──
# 如果指定了 --auto 或者脚本独立运行，输出改写 prompt 供 Agent 使用
# 如果由 Agent 调用，Agent 会直接用大模型处理改写
DRAFT_FILE="$TMPDIR/draft.txt"
PROMPT_FILE="$SKILL_DIR/prompts/rewrite-prompt.md"

echo "[file2voice] Step 2/4: 准备口播稿改写..."

# 生成填充后的 prompt
if [[ -f "$PROMPT_FILE" ]]; then
  # 读取原始文本
  ORIGINAL_TEXT=$(cat "$TEXT_FILE")
  
  # 构建改写请求
  cat > "$TMPDIR/rewrite-request.md" <<REWRITE_EOF
你是一位专业口播稿撰稿人。请将以下内容改写为一篇适合语音播报的口播稿。

要求：
1. 时长目标：${TARGET_MINUTES} 分钟（约 ${TARGET_CHARS} 字）
2. 风格：${STYLE:-自动判断（请根据内容选择最合适的风格）}
3. 口播稿要求：
   - 开头有吸引人的引入（3-5 句）
   - 中间内容分段清晰，每段有自然过渡
   - 结尾有总结或引导
   - 避免书面化表达，适合口语朗读
   - 数字、专有名词要读出来自然
   - 按段落输出，每段之间空一行

原始内容：
---
${ORIGINAL_TEXT}
---

请直接输出改写后的口播稿，不要输出分析过程。
REWRITE_EOF

  echo "[file2voice] 改写请求已生成: $TMPDIR/rewrite-request.md"
  
  # 尝试用 python 预处理（分段、字数统计）
  python3 "$SCRIPT_DIR/rewrite.py" "$TEXT_FILE" "$TMPDIR/preprocessed.txt" "$TARGET_MINUTES" "$TARGET_CHARS" "${STYLE:-auto}" 2>/dev/null || true
else
  echo "[file2voice] 警告：未找到 prompt 模板文件"
fi

# 检查是否已有口播稿（Agent 可能已经改写好放在 DRAFT_FILE）
if [[ -f "$DRAFT_FILE" && -s "$DRAFT_FILE" ]]; then
  echo "[file2voice] 检测到已改写的口播稿: $DRAFT_FILE"
else
  # 如果没有预处理的口播稿，尝试读取 preprocessed 或原文
  if [[ -f "$TMPDIR/preprocessed.txt" && -s "$TMPDIR/preprocessed.txt" ]]; then
    cp "$TMPDIR/preprocessed.txt" "$DRAFT_FILE"
    echo "[file2voice] 使用预处理文本作为口播稿"
  else
    # 没有改写稿时，使用原始提取文本
    cp "$TEXT_FILE" "$DRAFT_FILE"
    echo "[file2voice] 警告：未找到改写稿，使用原始文本"
  fi
fi

DRAFT_CHARS=$(wc -m < "$DRAFT_FILE" | tr -d ' ')
echo "[file2voice] 口播稿: ${DRAFT_CHARS} 字符"

# ── Step 4: TTS 合成 ──
echo "[file2voice] Step 3/4: TTS 合成..."

# 确定音色
if [[ -z "$VOICE" ]]; then
  # 默认音色
  VOICE="${DEFAULT_VOICE:-Chinese (Mandarin)_Male_Announcer}"
fi

echo "[file2voice] 音色: $VOICE, 格式: $FORMAT"

# 调用 tts.sh 合成音频
bash "$SCRIPT_DIR/tts.sh" "$DRAFT_FILE" "$OUTPUT" "$VOICE" "$FORMAT" "${DEFAULT_SAMPLE_RATE:-32000}" "${DEFAULT_SPEED:-1}"

echo "[file2voice] Step 4/4: 完成！"
echo "[file2voice] 输出文件: $OUTPUT"

# 输出文件信息
if [[ -f "$OUTPUT" ]]; then
  FILE_SIZE=$(du -h "$OUTPUT" | cut -f1)
  DURATION_SEC=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$OUTPUT" 2>/dev/null || echo "未知")
  echo "[file2voice] 文件大小: $FILE_SIZE, 时长: ${DURATION_SEC} 秒"
fi
