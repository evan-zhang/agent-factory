#!/usr/bin/env python3
"""
notifier.py — 监控通知封装

根据 tick 结果 + 模式，决定发送什么通知。
支持 Telegram / Discord（通过 message 工具）。

用法：
    python3 notifier.py <tick_result_json>
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ = timezone(timedelta(hours=8))

# ---------------------------------------------------------------------------
# 状态路径（与 monitor.py 共享）
# ---------------------------------------------------------------------------
def resolve_monitor_root() -> Path:
    explicit = os.environ.get("CMS_MEETING_MONITOR_ROOT")
    if explicit:
        base = Path(explicit).expanduser().resolve()
    else:
        base = (Path.home() / ".openclaw" / "cms-meeting-monitor").resolve()
    gateway = os.environ.get("OPENCLAW_GATEWAY", "default")
    return base / gateway


def state_path(meeting_chat_id: str) -> Path:
    return resolve_monitor_root() / meeting_chat_id / "state.json"


def materials_dir(meeting_chat_id: str) -> Path:
    explicit = os.environ.get("CMS_MEETING_MATERIALS_ROOT")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (Path.home() / ".openclaw" / "cms-meeting-materials").resolve()


def transcript_path(meeting_chat_id: str) -> Path:
    gateway = os.environ.get("OPENCLAW_GATEWAY", "default")
    return materials_dir(meeting_chat_id) / "transcript.txt"


def get_latest_fragments(meeting_chat_id: str, max_count: int = 5) -> list:
    """读取最新的 N 个片段。"""
    import subprocess
    script_dir = Path(__file__).resolve().parent.parent.parent / "cms-meeting-materials" / "scripts" / "huiji"

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
    return fragments[-max_count:]


def format_fragment(frag: dict) -> str:
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


def format_transcript_snippet(meeting_chat_id: str, max_chars: int = 500) -> str:
    """读取 transcript.txt 的末尾片段。"""
    p = transcript_path(meeting_chat_id)
    if not p.exists():
        return ""
    content = p.read_text(encoding="utf-8")
    # 取最后 max_chars 字符
    if len(content) > max_chars:
        return "..." + content[-max_chars:]
    return content


# ---------------------------------------------------------------------------
# 通知消息构建
# ---------------------------------------------------------------------------
def build_heartbeat_message(tick_result: dict) -> str:
    """静默模式心跳：简短，不打扰。"""
    return "💤 监控中"


def build_new_content_message(tick_result: dict) -> str:
    """有新内容时的通知。"""
    meeting_name = tick_result.get("meeting_name", "")
    new_count = tick_result.get("new_fragments", 0)
    mode = tick_result.get("mode", "silent")

    if mode == "caption":
        # 字幕模式：推送最新片段
        frags = get_latest_fragments(tick_result["meeting_chat_id"], max_count=5)
        lines = [f"📺 {meeting_name} — 新片段 ({new_count}段)\n"]
        for frag in frags:
            lines.append(format_fragment(frag))
        lines.append(f"\n累计 {tick_result.get('new_count', 0)} 段")
        return "\n".join(lines)
    else:
        # 静默模式：有新内容时通知
        return f"💬 {meeting_name} — 新增 {new_count} 段内容"


def build_meeting_ended_message(tick_result: dict) -> str:
    """会议结束通知。"""
    meeting_name = tick_result.get("meeting_name", "")
    total = tick_result.get("new_count", 0)
    return (f"🎉 「{meeting_name}」已结束\n"
            f"累计 {total} 段内容\n"
            f"说「总结」获取会议纪要")


# ---------------------------------------------------------------------------
# 输出（供主 Agent 或 cron job 调用）
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="CMS 监控通知")
    parser.add_argument("tick_result", help="monitor.py tick 的 JSON 输出")
    args = parser.parse_args()

    try:
        tick_result = json.loads(args.tick_result)
    except Exception:
        print(json.dumps({"error": "invalid tick_result JSON"}, ensure_ascii=False))
        sys.exit(1)

    if not tick_result.get("ok"):
        print(json.dumps({"notification": None, "should_send": False}, ensure_ascii=False))
        sys.exit(0)

    event = tick_result.get("event", "heartbeat")
    mode = tick_result.get("mode", "silent")

    if event == "meeting_ended":
        message = build_meeting_ended_message(tick_result)
        should_send = True
        notification_type = "meeting_ended"
    elif event == "new_content":
        message = build_new_content_message(tick_result)
        should_send = (mode == "caption")  # 静默模式默认不发新内容通知
        notification_type = "new_content"
    else:
        # heartbeat
        message = build_heartbeat_message(tick_result)
        should_send = False  # 心跳不发消息，靠 emoji reaction
        notification_type = "heartbeat"

    result = {
        "should_send": should_send,
        "notification_type": notification_type,
        "message": message if should_send else None,
        "tick_result": tick_result,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
