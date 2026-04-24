#!/bin/bash
set -e

RUN_ROOT="/tmp/pharma-test/network-search-runs/test-2604241/杭州-院外全景/run-001"
SKILL_DIR="/Users/evan/.openclaw/gateways/life/domains/agent-factory/projects/2604241"

echo "=== Step 4: audit_run.py ==="
python3 "$SKILL_DIR/pharma-evidence-audit-loop/scripts/audit/audit_run.py" --run-root "$RUN_ROOT" 2>&1
echo "---"
echo "=== audit_report.json ==="
cat "$RUN_ROOT/audit_report.json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps({'field_verdicts':[{k:v for k,v in fv.items() if k in ['field_name','stance']} for fv in d.get('field_verdicts',[])]},ensure_ascii=False,indent=2))"
echo "---"
echo "=== gap_report.md ==="
cat "$RUN_ROOT/gap_report.md"
