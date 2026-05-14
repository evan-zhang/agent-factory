#!/usr/bin/env bash
# tts.sh — MiniMax TTS 调用 + 音频拼接
# 优先使用 mmx-cli（官方推荐），降级到直接 API 调用
# 用法: tts.sh <text_file> <output_file> <voice_id> <format> <sample_rate> <speed>
set -euo pipefail

TEXT_FILE="$1"
OUTPUT="$2"
VOICE_ID="${3:-Chinese (Mandarin)_Male_Announcer}"
FORMAT="${4:-mp3}"
SAMPLE_RATE="${5:-32000}"
SPEED="${6:-1}"

# 检测 mmx-cli 是否可用（PATH 可能不完整，手动扩展）
export PATH="$PATH:/opt/homebrew/bin:$HOME/.npm-global/bin"
MMX_BIN=$(command -v mmx 2>/dev/null || echo "")

# 参数验证
if [[ ! -f "$TEXT_FILE" ]]; then
  echo "错误：文本文件不存在: $TEXT_FILE" >&2
  exit 1
fi

# 创建临时目录
TMPDIR=$(mktemp -d /tmp/file2voice_tts.XXXXXX)
trap 'rm -rf "$TMPDIR"' EXIT

# ── 文本分段 ──
python3 - "$TEXT_FILE" "$TMPDIR" <<'PYEOF'
import sys, re

text_path = sys.argv[1]
tmpdir = sys.argv[2]

with open(text_path, "r", encoding="utf-8") as f:
    text = f.read()

MAX_CHARS = 2000

# 跳过 HTML 注释（预处理元信息）
lines = text.split("\n")
lines = [l for l in lines if not l.strip().startswith("<!--")]
text = "\n".join(lines)

# 按段落分割
paragraphs = text.split("\n\n")

segments = []
current = ""

for para in paragraphs:
    para = para.strip()
    if not para:
        continue
    
    if len(current) + len(para) + 2 <= MAX_CHARS:
        current = (current + "\n\n" + para).strip() if current else para
    else:
        if current:
            segments.append(current)
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

for i, seg in enumerate(segments):
    seg_path = f"{tmpdir}/seg_{i:04d}.txt"
    with open(seg_path, "w", encoding="utf-8") as f:
        f.write(seg)

print(len(segments))
PYEOF

SEG_COUNT=$(ls "$TMPDIR"/seg_*.txt 2>/dev/null | wc -l | tr -d ' ')

if [[ "$SEG_COUNT" -eq 0 ]]; then
  echo "错误：未生成任何文本分段" >&2
  exit 1
fi

echo "[tts] 共 ${SEG_COUNT} 个分段，方式: $([ -n "$MMX_BIN" ] && echo "mmx-cli" || echo "API")"

CONCAT_LIST="$TMPDIR/concat.txt"
> "$CONCAT_LIST"

SUCCESS=0
FAIL=0

# ── 方案 A: mmx-cli（优先） ──
if [[ -n "$MMX_BIN" ]]; then
  for seg_file in "$TMPDIR"/seg_*.txt; do
    seg_idx=$(basename "$seg_file" .txt | sed 's/seg_//')
    audio_file="$TMPDIR/part_${seg_idx}.${FORMAT}"
    
    echo "[tts] 合成分段 ${seg_idx} ($(wc -m < "$seg_file" | tr -d ' ') 字符)..."
    
    # mmx speech synthesize 参数
    mmx_args=(speech synthesize)
    mmx_args+=(--text "$(cat "$seg_file")")
    mmx_args+=(--out "$audio_file")
    
    # 可选参数
    if [[ -n "$VOICE_ID" ]]; then
      mmx_args+=(--voice "$VOICE_ID")
    fi
    if [[ -n "$FORMAT" ]]; then
      mmx_args+=(--format "$FORMAT")
    fi
    
    # 调用 mmx-cli
    if $MMX_BIN "${mmx_args[@]}" 2>/dev/null; then
      if [[ -s "$audio_file" ]]; then
        echo "[tts] 分段 ${seg_idx} 完成 (mmx-cli)"
        echo "file '${audio_file}'" >> "$CONCAT_LIST"
        SUCCESS=$((SUCCESS + 1))
      else
        echo "[tts] 分段 ${seg_idx} mmx-cli 未生成文件，降级到 API" >&2
        # 单段降级到 API
        if _tts_api "$seg_file" "$audio_file" "$VOICE_ID" "$FORMAT" "$SAMPLE_RATE" "$SPEED"; then
          echo "[tts] 分段 ${seg_idx} 完成 (API 降级)"
          echo "file '${audio_file}'" >> "$CONCAT_LIST"
          SUCCESS=$((SUCCESS + 1))
        else
          FAIL=$((FAIL + 1))
        fi
      fi
    else
      echo "[tts] 分段 ${seg_idx} mmx-cli 失败，降级到 API" >&2
      if _tts_api "$seg_file" "$audio_file" "$VOICE_ID" "$FORMAT" "$SAMPLE_RATE" "$SPEED"; then
        echo "[tts] 分段 ${seg_idx} 完成 (API 降级)"
        echo "file '${audio_file}'" >> "$CONCAT_LIST"
        SUCCESS=$((SUCCESS + 1))
      else
        FAIL=$((FAIL + 1))
      fi
    fi
  done

# ── 方案 B: 直接 API 调用（降级） ──
else
  API_KEY="${MINIMAX_API_KEY:-}"
  if [[ -z "$API_KEY" ]]; then
    echo "错误：MINIMAX_API_KEY 未设置且 mmx-cli 不可用" >&2
    exit 1
  fi
  
  for seg_file in "$TMPDIR"/seg_*.txt; do
    seg_idx=$(basename "$seg_file" .txt | sed 's/seg_//')
    audio_file="$TMPDIR/part_${seg_idx}.${FORMAT}"
    
    echo "[tts] 合成分段 ${seg_idx} ($(wc -m < "$seg_file" | tr -d ' ') 字符)..."
    
    if _tts_api "$seg_file" "$audio_file" "$VOICE_ID" "$FORMAT" "$SAMPLE_RATE" "$SPEED"; then
      echo "[tts] 分段 ${seg_idx} 完成"
      echo "file '${audio_file}'" >> "$CONCAT_LIST"
      SUCCESS=$((SUCCESS + 1))
    else
      FAIL=$((FAIL + 1))
    fi
  done
fi

echo "[tts] 合成结果: ${SUCCESS} 成功, ${FAIL} 失败"

if [[ "$SUCCESS" -eq 0 ]]; then
  echo "错误：所有分段合成失败" >&2
  exit 1
fi

# ── 音频拼接 ──
if [[ "$SUCCESS" -eq 1 ]]; then
  cp "$(head -1 "$CONCAT_LIST" | sed "s/file '//;s/'//")" "$OUTPUT"
else
  echo "[tts] 拼接 ${SUCCESS} 个音频片段..."
  ffmpeg -y -f concat -safe 0 -i "$CONCAT_LIST" -c copy "$OUTPUT" 2>/dev/null
fi

echo "[tts] 音频输出: $OUTPUT"

if command -v ffprobe &>/dev/null; then
  duration=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$OUTPUT" 2>/dev/null || echo "?")
  echo "[tts] 最终时长: ${duration} 秒"
fi


# ── API 降级函数 ──
_tts_api() {
  local seg_file="$1"
  local audio_file="$2"
  local voice_id="$3"
  local format="$4"
  local sample_rate="$5"
  local speed="$6"
  
  local api_key="${MINIMAX_API_KEY:-}"
  local api_url="https://api.minimax.io/v1/t2a_v2"
  
  if [[ -z "$api_key" ]]; then
    echo "错误：API Key 未设置" >&2
    return 1
  fi
  
  local json_text
  json_text=$(python3 -c "
import json, sys
text = open(sys.argv[1], 'r').read()
print(json.dumps(text, ensure_ascii=False))
" "$seg_file")
  
  local resp_file="${audio_file%.${format}}_resp.json"
  
  local http_code
  http_code=$(curl -s -w "%{http_code}" -o "$resp_file" \
    -X POST "$api_url" \
    -H "Authorization: Bearer ${api_key}" \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"speech-2.8-hd\",
      \"text\": ${json_text},
      \"stream\": false,
      \"output_format\": \"hex\",
      \"voice_setting\": {
        \"voice_id\": \"${voice_id}\",
        \"speed\": ${speed},
        \"vol\": 1,
        \"pitch\": 0
      },
      \"audio_setting\": {
        \"sample_rate\": ${sample_rate},
        \"bitrate\": 128000,
        \"format\": \"${format}\",
        \"channel\": 1
      }
    }")
  
  if [[ "$http_code" == "200" ]]; then
    python3 - "$resp_file" "$audio_file" <<'PYEOF'
import json, sys
with open(sys.argv[1], "r") as f:
    resp = json.load(f)
status = resp.get("base_resp", {}).get("status_code", -1)
if status != 0:
    msg = resp.get("base_resp", {}).get("status_msg", "unknown")
    print(f"API error: {status} - {msg}", file=sys.stderr)
    sys.exit(1)
audio_hex = resp.get("data", {}).get("audio", "")
if not audio_hex:
    print("No audio data", file=sys.stderr)
    sys.exit(1)
audio_bytes = bytes.fromhex(audio_hex)
with open(sys.argv[2], "wb") as f:
    f.write(audio_bytes)
PYEOF
    [[ -s "$audio_file" ]] && return 0 || return 1
  else
    echo "API HTTP ${http_code}" >&2
    return 1
  fi
}
