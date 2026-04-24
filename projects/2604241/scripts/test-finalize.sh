#!/bin/bash
set -e

RUN_ROOT="/tmp/pharma-test/network-search-runs/test-2604241/杭州-院外全景/run-001"
SKILL_DIR="/Users/evan/.openclaw/gateways/life/domains/agent-factory/projects/2604241"

# 创建 summary.md（Step 5 — 总控写）
cat > "$RUN_ROOT/summary.md" << 'EOF'
# 杭州-院外全景 检索摘要

## 测试运行
本 run 为流程验证测试，仅完成 1 条证据采集。

### 已覆盖维度
- 本地医保与双通道政策：1条证据（uncertain，需补检）

### 未覆盖维度
- 处方外流与院外衔接
- DTP与定点药店管理公示
- 药监卫健院外相关通报
- 互联网医院与电子处方试点
- 集采与院外衔接公开信息

## 结论
流程验证通过。完整采集需要补充证据。
EOF

echo "=== Step 6: finalize_run.py ==="
python3 "$SKILL_DIR/pharma-outpatient-orchestrator/scripts/run/finalize_run.py" --run-root "$RUN_ROOT" 2>&1
echo "---"
echo "=== run_meta.json ==="
cat "$RUN_ROOT/run_meta.json" | python3 -m json.tool
echo "---"
echo "=== 最终文件列表 ==="
ls -la "$RUN_ROOT"
