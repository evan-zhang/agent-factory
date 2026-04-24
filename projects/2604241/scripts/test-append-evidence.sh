#!/bin/bash
# test-append-evidence.sh — 测试证据追加
# 用法: bash scripts/test-append-evidence.sh [RUN_ROOT] [SKILL_DIR]

set -e

RUN_ROOT="${1:-/tmp/pharma-test/network-search-runs/test-2604241/杭州-院外全景/run-001}"
SKILL_DIR="${2:-$(cd "$(dirname "$0")/.." && pwd)}"

echo '{"evidence_id":1,"task_id":"test-2604241","subtask_id":"本地医保与双通道政策","field_name":"本地医保与双通道政策","query_kind":"positive","query":"杭州 双通道 医保 site:gov.cn","source_url":"https://zj.gov.cn/test","evidence_quote":"浙江推进双通道管理机制","captured_at":"2026-04-25T00:10:00Z"}' > /tmp/test-evidence.json

python3 "$SKILL_DIR/pharma-search-cn-policy/scripts/cn/append_evidence.py" --run-root "$RUN_ROOT" --evidence-json /tmp/test-evidence.json
echo "---"
echo "=== evidence.jsonl ==="
cat "$RUN_ROOT/evidence.jsonl"
