#!/usr/bin/env python3
"""
monitor.py — CMS AI慧记 会议监控入口

用法：
    python3 monitor.py start <meeting_chat_id> [--mode caption|silent] [--interval 60]
    python3 monitor.py status [--meeting-chat-id <id>]
    python3 monitor.py stop <meeting_chat_id>
    python3 monitor.py tick <meeting_chat_id>    # 供 Cron Job 调用

由主 Agent 调用，不自己响应用户。
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ = timezone(timedelta(hours=8))

# ---------------------------------------------------------------------------
# 路径解析
# ---------------------------------------------------------------------------
def resolve_monitor_root() -> Path:
    explicit = os.environ.get("CMS_MEETING_MONITOR_ROOT")
    if explicit:
        base = Path(explicit).expanduser().resolve()
    else:
        base = (Path.home() / ".openclaw" / "cms-meeting-monitor").resolve()
    gateway = os.environ.get("OPENCLAW_GATEWAY", "default")
    root = base / gateway
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_materials_root() -> Path:
    explicit = os.environ.get("CMS_MEETING_MATERIALS_ROOT")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (Path.home() / ".openclaw" / "cms-meeting-materials").resolve()


def meeting_dir(meeting_chat_id: str) -> Path:
    gateway = os.environ.get("OPENCLAW_GATEWAY", "default")
    return resolve_monitor_root() / gateway / meeting_chat_id


def materials_dir(meeting_chat_id: str) -> Path:
    gateway = os.environ.get("OPENCLAW_GATEWAY", "default")
    return resolve_materials_root() / gateway / meeting_chat_id


def transcript_path(meeting_chat_id: str) -> Path:
    return materials_dir(meeting_chat_id) / "transcript.txt"


def manifest_path(meeting_chat_id: str) -> Path:
    return materials_dir(meeting_chat_id) / "manifest.json"


def state_path(meeting_chat_id: str) -> Path:
    return meeting_dir(meeting_chat_id) / "state.json"


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def now_epoch() -> int:
    return int(time.time())


# ---------------------------------------------------------------------------
# State 管理
# ---------------------------------------------------------------------------
def load_state(meeting_chat_id: str) -> dict:
    p = state_path(meeting_chat_id)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "meeting_chat_id": meeting_chat_id,
        "mode": "silent",
        "interval": 60,
        "status": "unknown",
        "last_fragment_count": 0,
        "last_check_at": None,
        "started_at": now_iso(),
        "channel": None,
        "target": None,
        "account_id": None,
        "status_message_id": None,
    }


def save_state(meeting_chat_id: str, state: dict):
    p = state_path(meeting_chat_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


# ---------------------------------------------------------------------------
# manifest 读取
# ---------------------------------------------------------------------------
def load_manifest(meeting_chat_id: str) -> dict:
    p = manifest_path(meeting_chat_id)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


# ---------------------------------------------------------------------------
# fragments.ndjson 计数
# ---------------------------------------------------------------------------
def count_fragments(meeting_chat_id: str) -> int:
    p = materials_dir(meeting_chat_id) / "fragments.ndjson"
    if not p.exists():
        return 0
    count = 0
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def get_latest_fragments(meeting_chat_id: str, max_count: int = 5) -> list:
    """读取最新的 N 个片段。"""
    p = materials_dir(meeting_chat_id) / "fragments.ndjson"
    if not p.exists():
        return []
    fragments = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                fragments.append(obj)
            except Exception:
                pass
    # 返回最新的 max_count 个
    return fragments[-max_count:]


def format_fragment(frag: dict) -> str:
    """把一个片段格式化为 [HH:MM:SS] text 形式。"""
    start_ms = frag.get("startTime")
    if start_ms is not None:
        total_secs = start_ms // 1000
        hrs, rem = divmod(total_secs, 3600)
        mins, secs = divmod(rem, 60)
        ts = f"{hrs:02d}:{mins:02d}:{secs:02d}"
    else:
        ts = "??:??:??"
    text = frag.get("text", "")
    return f"[{ts}] {text}"


# ---------------------------------------------------------------------------
# trigger-pull 集成
# ---------------------------------------------------------------------------
def trigger_pull(meeting_chat_id: str) -> dict:
    """调用 trigger-pull.py，执行一次增量拉取。"""
    import subprocess
    script_dir = Path(__file__).resolve().parent.parent.parent / "cms-meeting-materials" / "scripts" / "huiji" / "trigger-pull.py"
    if not script_dir.exists():
        return {"ok": False, "error": "cms-meeting-materials skill 未安装"}
    try:
        result = subprocess.run(
            [sys.executable, str(script_dir), meeting_chat_id],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {"ok": True, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# start 命令
# ---------------------------------------------------------------------------
def cmd_start(meeting_chat_id: str, mode: str, interval: int,
              channel: str = None, target: str = None, account_id: str = None) -> dict:
    """
    启动监控。
    1. 写入状态文件
    2. 执行一次初始拉取
    3. 返回配置信息（供主 Agent 创建 Cron Job）
    """
    state = load_state(meeting_chat_id)
    state["mode"] = mode
    state["interval"] = interval
    state["status"] = "running"
    state["channel"] = channel
    state["target"] = target
    state["account_id"] = account_id
    state["started_at"] = now_iso()

    # 执行一次初始拉取
    pull_result = trigger_pull(meeting_chat_id)
    if not pull_result.get("ok"):
        return {"ok": False, "error": f"初始拉取失败: {pull_result.get('error')}"}

    # 更新片段计数
    frag_count = count_fragments(meeting_chat_id)
    state["last_fragment_count"] = frag_count
    state["last_check_at"] = now_iso()
    save_state(meeting_chat_id, state)

    manifest = load_manifest(meeting_chat_id)
    meeting_name = manifest.get("name", meeting_chat_id)

    return {
        "ok": True,
        "meeting_chat_id": meeting_chat_id,
        "meeting_name": meeting_name,
        "mode": mode,
        "interval": interval,
        "fragment_count": frag_count,
        "status": "running",
        "materials_dir": str(materials_dir(meeting_chat_id)),
    }


# ---------------------------------------------------------------------------
# status 命令
# ---------------------------------------------------------------------------
def cmd_status(meeting_chat_id: str = None) -> dict:
    """查看当前监控状态。"""
    root = resolve_monitor_root()
    results = []

    if meeting_chat_id:
        p = state_path(meeting_chat_id)
        if p.exists():
            results.append((meeting_chat_id, json.loads(p.read_text(encoding="utf-8"))))
        else:
            return {"ok": False, "error": f"未监控此会议: {meeting_chat_id}"}
    else:
        gateway = os.environ.get("OPENCLAW_GATEWAY", "default")
        base = root / gateway
        if base.exists():
            for mid_dir in base.iterdir():
                if mid_dir.is_dir():
                    sp = mid_dir / "state.json"
                    if sp.exists():
                        try:
                            results.append((mid_dir.name, json.loads(sp.read_text(encoding="utf-8"))))
                        except Exception:
                            pass

    if not results:
        return {"ok": True, "monitoring": [], "message": "当前没有会议在监控中"}

    status_list = []
    for mid, st in results:
        frag_count = count_fragments(mid)
        manifest = load_manifest(mid)
        status_list.append({
            "meeting_chat_id": mid,
            "meeting_name": manifest.get("name", mid),
            "mode": st.get("mode"),
            "status": st.get("status"),
            "fragment_count": frag_count,
            "last_check_at": st.get("last_check_at"),
            "started_at": st.get("started_at"),
        })

    return {"ok": True, "monitoring": status_list}


# ---------------------------------------------------------------------------
# stop 命令
# ---------------------------------------------------------------------------
def cmd_stop(meeting_chat_id: str) -> dict:
    """停止监控（只清理状态，不调用 stop-pull.py）。"""
    p = state_path(meeting_chat_id)
    if p.exists():
        p.unlink(missing_ok=True)
    return {"ok": True, "meeting_chat_id": meeting_chat_id, "status": "stopped"}


# ---------------------------------------------------------------------------
# tick 命令（供 Cron Job 调用）
# ---------------------------------------------------------------------------
def cmd_tick(meeting_chat_id: str) -> dict:
    """
    一次监控 tick。
    1. 读取状态文件
    2. 执行 trigger-pull
    3. 检查是否有新片段
    4. 根据模式决定通知方式
    5. 更新状态
    """
    p = state_path(meeting_chat_id)
    if not p.exists():
        return {"ok": False, "error": "未找到监控状态，请先 start"}

    state = load_state(meeting_chat_id)
    if state.get("status") != "running":
        return {"ok": False, "error": "监控已停止"}

    old_count = state.get("last_fragment_count", 0)

    # 执行拉取
    pull_result = trigger_pull(meeting_chat_id)
    new_count = count_fragments(meeting_chat_id)
    new_fragments = new_count - old_count if new_count > old_count else 0

    state["last_fragment_count"] = new_count
    state["last_check_at"] = now_iso()

    manifest = load_manifest(meeting_chat_id)
    meeting_name = manifest.get("name", meeting_chat_id)
    meeting_status = manifest.get("status", "unknown")

    result = {
        "ok": True,
        "meeting_chat_id": meeting_chat_id,
        "meeting_name": meeting_name,
        "meeting_status": meeting_status,
        "mode": state.get("mode"),
        "old_count": old_count,
        "new_count": new_count,
        "new_fragments": new_fragments,
        "last_check_at": state["last_check_at"],
    }

    if meeting_status == "completed":
        state["status"] = "completed"
        result["event"] = "meeting_ended"
    else:
        result["event"] = "heartbeat" if new_fragments == 0 else "new_content"

    save_state(meeting_chat_id, state)
    return result


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="CMS AI慧记 会议监控")
    sub = parser.add_subparsers(dest="cmd")

    # start
    p_start = sub.add_parser("start", help="启动监控")
    p_start.add_argument("meeting_chat_id", help="慧记会议 ID")
    p_start.add_argument("--mode", default="silent", choices=["caption", "silent"],
                         help="监控模式（默认 silent）")
    p_start.add_argument("--interval", type=int, default=60,
                         help="拉取间隔秒数（默认 60）")
    p_start.add_argument("--channel", default=None, help="通知渠道")
    p_start.add_argument("--target", default=None, help="通知目标")
    p_start.add_argument("--account-id", default=None, help="账户ID")

    # status
    sub.add_parser("status", help="查看监控状态")

    # stop
    p_stop = sub.add_parser("stop", help="停止监控")
    p_stop.add_argument("meeting_chat_id", help="慧记会议 ID")

    # tick
    p_tick = sub.add_parser("tick", help="Cron Job 调用：执行一次 tick")
    p_tick.add_argument("meeting_chat_id", help="慧记会议 ID")

    args = parser.parse_args()

    if args.cmd == "start":
        result = cmd_start(
            args.meeting_chat_id,
            mode=args.mode,
            interval=args.interval,
            channel=args.channel,
            target=args.target,
            account_id=args.account_id,
        )
    elif args.cmd == "status":
        result = cmd_status()
    elif args.cmd == "stop":
        result = cmd_stop(args.meeting_chat_id)
    elif args.cmd == "tick":
        result = cmd_tick(args.meeting_chat_id)
    else:
        parser.print_help()
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
