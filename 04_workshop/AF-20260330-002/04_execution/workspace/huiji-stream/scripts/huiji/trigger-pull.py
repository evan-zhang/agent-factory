#!/usr/bin/env python3
"""
trigger-pull.py — 手动提前触发一次 pull-once
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PULL_ONCE = SCRIPT_DIR / "pull-once.py"


def append_notify(notify_file: str, meeting_chat_id: str, payload: dict):
    if not notify_file:
        return
    entry = {
        "meetingChatId": meeting_chat_id,
        "status": payload.get("status", "unknown"),
        "new_fragments": int(payload.get("fragment_count") or payload.get("new_fragments") or 0),
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    path = Path(notify_file).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="提前触发一次会议拉取")
    parser.add_argument("meeting_chat_id", help="meetingChatId")
    parser.add_argument("--gateway", default="", help="可选 gateway")
    parser.add_argument("--notify-file", default="", help="可选：将执行结果追加写入 JSONL 文件")
    args = parser.parse_args()

    cmd = [sys.executable, str(PULL_ONCE), "--meeting-chat-id", args.meeting_chat_id]
    if args.gateway:
        cmd.extend(["--gateway", args.gateway])

    proc = subprocess.run(cmd, capture_output=True, text=True)

    raw = (proc.stdout or "").strip()
    payload = {}
    if raw:
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"raw": raw}

    if payload.get("skipped_locked"):
        status = "running"
        reason = "running_skip"
    elif payload.get("status") in ("ok", "completed", "stopped"):
        status = "accepted"
        reason = payload.get("status")
    else:
        status = "skipped"
        reason = payload.get("reason") or payload.get("status") or "unknown"

    out = {
        "status": status,
        "reason": reason,
        "meeting_chat_id": args.meeting_chat_id,
        "checkpoint": payload.get("checkpoint"),
        "fragment_count": payload.get("fragment_count"),
        "runtime_status": payload.get("runtime_status"),
        "raw": payload,
    }
    append_notify(args.notify_file, args.meeting_chat_id, {
        "status": status,
        "new_fragments": payload.get("new_fragments") or payload.get("fragment_count") or 0,
        "fragment_count": payload.get("fragment_count") or 0,
    })
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
