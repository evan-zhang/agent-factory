#!/usr/bin/env bash
# core_search.sh — 搜索核心封装
# v0.10.0
#
# 职责：
#   1. 调用 OpenClaw web_search 工具（内置，不走 MCP 配置层）
#   2. 配额管理：60 秒窗口计数（持久化到 lib/quota.json + 原子文件锁）
#   3. 超时控制：timeout 30
#   4. 失败/降级：错误返回 JSON 数组
#
# 不做什么：
#   - 不做来源分级（交给 source_ranker）
#   - 不做关键词生成（交给 keyword_mapper）
#   - 不做字段抽取（交给 field_extractor）
#   - 不做搜索结果排序（源分级在下游做）
#
# 用法：core_search.sh "query1" "query2" ...   # 1-5 个 query
# 输出：JSON 数组 [{query, url, title, snippet, source_tier, fetch_status}]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUOTA_FILE="$SCRIPT_DIR/lib/quota.json"
QUOTA_LOCKDIR="$SCRIPT_DIR/lib/quota.lockdir"
WINDOW_SECONDS=60
MAX_CALLS_PER_WINDOW=100
TIMEOUT_SECONDS=30
LOCK_WAIT_MAX=50  # 最多等 5 秒（50 * 0.1s）

# 跨平台 ISO 时间戳（macOS BSD date 老版本不支持 -Iseconds）
iso_now() {
  python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'))"
}

# ============ 配额管理 ============
# 数据结构：{ window_start: ISO8601, calls: [ISO8601, ...] }
# 文件锁：mkdir（POSIX 原子，跨平台；macOS/Linux 都支持）
#   - mkdir 失败说明锁已被持
#   - rmdir 释放锁
#   - trap 确保异常退出也清锁

# 抢锁（最多等 5 秒）
acquire_lock() {
  local wait=0
  while ! mkdir "$QUOTA_LOCKDIR" 2>/dev/null; do
    wait=$((wait + 1))
    if [ $wait -ge $LOCK_WAIT_MAX ]; then
      return 1  # 抢不到锁
    fi
    sleep 0.1
  done
  trap 'release_lock 2>/dev/null || true' EXIT INT TERM
  return 0
}

# 释放锁
release_lock() {
  rmdir "$QUOTA_LOCKDIR" 2>/dev/null || true
}

# 读 + 计算当前窗口有效调用数
# 窗口起点过期则返回 0（未启动或已过期）
current_window_count() {
  local now="$1"
  local cfg
  cfg=$(cat "$QUOTA_FILE" 2>/dev/null) || cfg='{"window_start": null, "calls": []}'
  
  python3 -c "
import json, sys
from datetime import datetime

now_str = sys.argv[1]
window = int(sys.argv[2])
data = json.loads(sys.argv[3])

now = datetime.fromisoformat(now_str.replace('Z', '+00:00') if now_str.endswith('Z') else now_str)
ws = data.get('window_start')
calls = data.get('calls', [])

if not ws:
    print('NEED_RESET')
    sys.exit(0)

try:
    ws_dt = datetime.fromisoformat(ws.replace('Z', '+00:00') if ws.endswith('Z') else ws)
except Exception:
    print('NEED_RESET')
    sys.exit(0)

# 窗口起点 + window_seconds = 窗口结束
window_end = ws_dt.timestamp() + window
if now.timestamp() >= window_end:
    print('NEED_RESET')
    sys.exit(0)

# 统计在当前窗口内的 calls
in_window = 0
for c in calls:
    try:
        c_dt = datetime.fromisoformat(c.replace('Z', '+00:00') if c.endswith('Z') else c)
        # 包含首笔调用（== window_start 也要算）
        if c_dt.timestamp() >= ws_dt.timestamp():
            in_window += 1
    except Exception:
        continue
print(in_window)
" "$now" "$WINDOW_SECONDS" "$cfg"
}

# 抢配额（原子）
# 返回 0 = 成功 / 1 = 配额耗尽 / 2 = 抢不到锁
acquire_quota() {
  local now
  now=$(iso_now)
  
  if ! acquire_lock; then
    return 2
  fi
  
  local result
  result=$(current_window_count "$now")
  
  if [ "$result" = "NEED_RESET" ]; then
    # 重置窗口（不预填首笔调用，调用者会自己追加，避免 off-by-one）
    cat > "$QUOTA_FILE" <<EOF
{"window_start": "$now", "calls": []}
EOF
    release_lock
    return 0
  fi
  
  local count="$result"
  if [ "$count" -ge "$MAX_CALLS_PER_WINDOW" ]; then
    release_lock
    return 1
  fi
  
  # 追加本次调用
  python3 -c "
import json
with open('$QUOTA_FILE') as f:
    data = json.load(f)
calls = data.get('calls', [])
calls.append('$now')
data['calls'] = calls
with open('$QUOTA_FILE.tmp', 'w') as f:
    json.dump(data, f, indent=2)
" && mv "$QUOTA_FILE.tmp" "$QUOTA_FILE"
  
  release_lock
  return 0
}

# ============ 实际搜索 ============
# 调用 web_search（OpenClaw 内置工具，通过 environment 暴露）
do_search() {
  local query="$1"
  local num_results="${2:-10}"
  # web_search 是 OpenClaw 内置 CLI，输出 JSON 数组
  # 失败/超时/无结果 → 返回空数组
  timeout "$TIMEOUT_SECONDS" web_search "$query" "$num_results" 2>/dev/null || echo "[]"
}

# ============ 抓取（可选） ============
# 仅对 top N 结果做 web_fetch
do_fetch() {
  local url="$1"
  timeout "$TIMEOUT_SECONDS" web_fetch "$url" 2>/dev/null || echo ""
}

# ============ 主流程 ============
main() {
  local queries=("$@")
  [ ${#queries[@]} -eq 0 ] && { echo "[]"; exit 1; }
  
  if ! acquire_quota; then
    local rc=$?
    # rc=1 配额耗尽 / rc=2 锁竞争（if ! 不会反转后为表/品不一样）
    if [ $rc -eq 2 ]; then
      echo "❌ 抢不到配额锁（其他进程持有）" >&2
    else
      echo "❌ 搜索配额耗尽（$WINDOW_SECONDS 秒窗口最多 $MAX_CALLS_PER_WINDOW 次）" >&2
    fi
    echo "[]"
    exit 2
  fi
  
  local results="[]"
  for q in "${queries[@]}"; do
    local raw
    raw=$(do_search "$q" 10)
    # 合并到 results
    results=$(echo "$results" "$raw" | jq -s 'add' 2>/dev/null || echo "[]")
  done
  
  echo "$results"
}

main "$@"
