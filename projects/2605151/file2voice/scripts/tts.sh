#!/usr/bin/env bash
# tts.sh — MiniMax TTS 调用 + 音频拼接
# 用法: tts.sh <text_file> <output_file> <voice_id> <format> <sample_rate> <speed>
set -euo pipefail

TEXT_FILE="$1"
OUTPUT="$2"
VOICE_ID="${3:-Chinese (Mandarin)_Male_Announcer}"
FORMAT="${4:-mp3}"
SAMPLE_RATE="${5:-32000}"
SPEED="${6:-1}"

API_KEY="${MINIMAX_API_KEY:-}"
API_URL="https://api.minimax.io/v1/t2a_v2"

# 参数验证
if [[ -z "$API_KEY" ]]; then
  echo "错误：MINIMAX_API_KEY 未设置" >&2
  exit 1
fi

if [[ ! -f "$TEXT_FILE" ]]; then
  echo "错误：文本文件不存在: $TEXT_FILE" >&2
  exit 1
fi

# 创建临时目录
TMPDIR=$(mktemp -d /tmp/file2voice_tts.XXXXXX)
trap 'rm -rf "$TMPDIR"' EXIT

# 读取文本并按自然段落分段（MiniMax 支持最长 10000 字符）
# 但分段太长可能导致合成质量下降，控制在 2000 字符左右
python3 - "$TEXT_FILE" "$TMPDIR" <<'PYEOF'
import sys, re

text_path = sys.argv[1]
tmpdir = sys.argv[2]

with open(text_path, "r", encoding="utf-8") as f:
    text = f.read()

MAX_CHARS = 2000

# 按段落分割
paragraphs = text.split("\n\n")

segments = []
current = ""

for para in paragraphs:
    para = para.strip()
    if not para:
        continue
    
    # 跳过 HTML 注释（预处理元信息）
    if para.startswith("<!--"):
        continue
    
    if len(current) + len(para) + 2 <= MAX_CHARS:
        current = (current + "\n\n" + para).strip() if current else para
    else:
        if current:
            segments.append(current)
        # 如果单个段落超过限制，按句子拆分
        if len(para) > MAX_CHARS:
            sentences = re.split(r'(?<=[。！？；\.\!\?\;])', para)
            current = ""
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                if len(current) + len(sent) > MAX_CHARS and current:
                    segments.append(current)
                    current = sent
                else:
                    current = (current + sent).strip()
        else:
            current = para

if current:
    segments.append(current)

# 写入分段文件
for i, seg in enumerate(segments):
    seg_path = f"{tmpdir}/seg_{i:04d}.txt"
    with open(seg_path, "w", encoding="utf-8") as f:
        f.write(seg)

# 输出分段数
print(len(segments))
PYEOF

# 获取分段数量
SEG_COUNT=$(ls "$TMPDIR"/seg_*.txt 2>/dev/null | wc -l | tr -d ' ')

if [[ "$SEG_COUNT" -eq 0 ]]; then
  echo "错误：未生成任何文本分段" >&2
  exit 1
fi

echo "[tts] 共 ${SEG_COUNT} 个分段"

# 逐段调用 MiniMax TTS API
CONCAT_LIST="$TMPDIR/concat.txt"
> "$CONCAT_LIST"

SUCCESS=0
FAIL=0

for seg_file in "$TMPDIR"/seg_*.txt; do
  seg_idx=$(basename "$seg_file" .txt | sed 's/seg_//')
  seg_text=$(cat "$seg_file")
  audio_file="$TMPDIR/part_${seg_idx}.${FORMAT}"
  
  echo "[tts] 合成分段 ${seg_idx} ($(echo "$seg_text" | wc -m | tr -d ' ') 字符)..."
  
  # 转义 JSON 特殊字符
  json_text=$(python3 -c "
import json, sys
text = open(sys.argv[1], 'r').read()
print(json.dumps(text, ensure_ascii=False))
" "$seg_file")
  
  # 调用 MiniMax API（非流式，返回 JSON 含 hex 编码音频）
  resp_file="$TMPDIR/resp_${seg_idx}.json"
  http_code=$(curl -s -w "%{http_code}" -o "$resp_file" \
    -X POST "$API_URL" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"speech-2.8-hd\",
      \"text\": ${json_text},
      \"stream\": false,
      \"output_format\": \"hex\",
      \"voice_setting\": {
        \"voice_id\": \"${VOICE_ID}\",
        \"speed\": ${SPEED},
        \"vol\": 1,
        \"pitch\": 0
      },
      \"audio_setting\": {
        \"sample_rate\": ${SAMPLE_RATE},
        \"bitrate\": 128000,
        \"format\": \"${FORMAT}\",
        \"channel\": 1
      }
    }")
  
  if [[ "$http_code" == "200" ]]; then
    # 从 JSON 响应中提取 hex 编码的音频数据，转为二进制
    python3 - "$resp_file" "$audio_file" <<'PYEOF'
import json, sys

with open(sys.argv[1], "r") as f:
    resp = json.load(f)

status = resp.get("base_resp", {}).get("status_code", -1)
if status != 0:
    msg = resp.get("base_resp", {}).get("status_msg", "unknown error")
    print(f"API error: {status} - {msg}", file=sys.stderr)
    sys.exit(1)

audio_hex = resp.get("data", {}).get("audio", "")
if not audio_hex:
    print("No audio data in response", file=sys.stderr)
    sys.exit(1)

audio_bytes = bytes.fromhex(audio_hex)
with open(sys.argv[2], "wb") as f:
    f.write(audio_bytes)
print(f"OK: {len(audio_bytes)} bytes")
PYEOF
    
    if [[ -s "$audio_file" ]]; then
      echo "[tts] 分段 ${seg_idx} 完成"
      echo "file '${audio_file}'" >> "$CONCAT_LIST"
      SUCCESS=$((SUCCESS + 1))
    else
      echo "[tts] 分段 ${seg_idx} 音频解码失败" >&2
      FAIL=$((FAIL + 1))
    fi
  else
    echo "[tts] 分段 ${seg_idx} 失败 (HTTP ${http_code})" >&2
    if [[ -f "$resp_file" ]]; then
      python3 -c "
import json, sys
try:
    resp = json.load(open(sys.argv[1]))
    print(resp.get('base_resp', {}).get('status_msg', 'unknown'), file=sys.stderr)
except:
    print(open(sys.argv[1]).read()[:200], file=sys.stderr)
" "$resp_file" >&2
    fi
    FAIL=$((FAIL + 1))
  fi
done

echo "[tts] 合成结果: ${SUCCESS} 成功, ${FAIL} 失败"

if [[ "$SUCCESS" -eq 0 ]]; then
  echo "错误：所有分段合成失败" >&2
  exit 1
fi

# ── 音频拼接 ──
if [[ "$SUCCESS" -eq 1 ]]; then
  # 只有一段，直接复制
  cp "$(head -1 "$CONCAT_LIST" | sed "s/file '//;s/'//")" "$OUTPUT"
else
  # 多段拼接
  echo "[tts] 拼接 ${SUCCESS} 个音频片段..."
  ffmpeg -y -f concat -safe 0 -i "$CONCAT_LIST" -c copy "$OUTPUT" 2>/dev/null
fi

echo "[tts] 音频输出: $OUTPUT"

# 输出最终时长
if command -v ffprobe &>/dev/null; then
  duration=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$OUTPUT" 2>/dev/null || echo "?")
  echo "[tts] 最终时长: ${duration} 秒"
fi
