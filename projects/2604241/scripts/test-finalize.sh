#!/bin/bash
# test-finalize.sh — 测试收口
# 用法: bash scripts/test-finalize.sh [RUN_ROOT] [SKILL_DIR]

set -e

RUN_ROOT="${1:-/tmp/pharma-test/network-search-runs/test-2604241/杭州-院外全景/run-001}"
SKILL_DIR="${2:-$(cd "$(dirname "$0")/.." && pwd)}"

# 如果 summary.md 不存在，创建测试版
if [ ! -f "$RUN_ROOT/summary.md" ]; then
  cat > "$RUN_ROOT/summary.md" << 'EOF'
# {city_or_topic} — 院外药品公开信息检索摘要（测试）

## 整体结论
流程验证测试。

## 分维度结论
### 本地医保与双通道政策
判定: uncertain | 需补检

## 待补充项
其余5个维度无证据，需补检。
EOF
fi

echo "=== Step 6: finalize_run.py ==="
python3 "$SKILL_DIR/pharma-outpatient-orchestrator/scripts/run/finalize_run.py" --run-root "$RUN_ROOT" 2>&1
echo "---"
echo "=== run_meta.json ==="
cat "$RUN_ROOT/run_meta.json" | python3 -m json.tool
echo "---"
echo "=== 最终文件列表 ==="
ls -la "$RUN_ROOT"
