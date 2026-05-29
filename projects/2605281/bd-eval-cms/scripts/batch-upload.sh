#!/bin/bash
# batch-upload.sh — 批量上传BD评估HTML报告

set -e

API="https://doc.20100706.xyz/upload"
TMP="/tmp/bd-eval-upload"

mkdir -p "$TMP"

upload() {
  local_file="$1"
  remote_name="$2"
  cp "$local_file" "$TMP/$remote_name"
  echo "Uploading $remote_name..."
  resp=$(curl -s -X POST "$API" \
    -F "file=@$TMP/$remote_name;filename=$remote_name")
  raw_url=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('raw_url','ERROR'))" 2>/dev/null)
  echo "$remote_name|$raw_url"
}

# 用法说明
if [ $# -eq 0 ]; then
  echo "用法: $0 <文件1> <名称1> [<文件2> <名称2> ...]"
  echo "示例: $0 /tmp/report-CG-0255.html CG-0255_报告.html"
  exit 1
fi

# 处理成对参数
i=0
results=()
while [ $# -gt 0 ]; do
  file="$1"; name="$2"
  shift 2
  result=$(upload "$file" "$name")
  results+=("$result")
done

echo ""
echo "=== 上传结果 ==="
for r in "${results[@]}"; do
  echo "$r"
done

rm -rf "$TMP"
