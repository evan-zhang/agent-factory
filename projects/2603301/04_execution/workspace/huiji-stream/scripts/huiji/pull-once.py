#!/usr/bin/env python3
"""
pull-once.py — 会议单次增量拉取（短任务）
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from pull_core import run_pull_once, resolve_meeting_chat_id_by_number


def append_notify(notify_file: str, meeting_chat_id: str, result: dict):
    if not notify_file:
        return
    entry = {
        "meetingChatId": meeting_chat_id,
        "status": result.get("status", "unknown"),
        "new_fragments": int(result.get("new_fragments") or 0),
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    path = Path(notify_file).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="执行单次增量拉取并退出")
    parser.add_argument("--meeting-chat-id", dest="meeting_chat_id", default="", help="慧记会议 meetingChatId")
    parser.add_argument("--meeting-number", default="", help="视频会议号（可解析 meetingChatId）")
    parser.add_argument("--last-ts", type=int, default=None, help="配合 --meeting-number 使用")
    parser.add_argument("--gateway", default="", help="可选，覆盖当前 gateway")
    parser.add_argument("--name", default="", help="会议名称（可选）")
    parser.add_argument("--force", action="store_true", help="忽略 is_fully_pulled 强制执行")
    parser.add_argument("--notify-file", default="", help="可选：将执行结果追加写入 JSONL 文件")
    args = parser.parse_args()

    meeting_chat_id = args.meeting_chat_id.strip()
    if not meeting_chat_id and args.meeting_number:
        resolved = resolve_meeting_chat_id_by_number(args.meeting_number, args.last_ts)
        meeting_chat_id = resolved["meetingChatId"]

    if not meeting_chat_id:
        parser.error("必须提供 --meeting-chat-id 或 --meeting-number")

    result = run_pull_once(
        meeting_chat_id=meeting_chat_id,
        gateway=args.gateway or None,
        name=args.name,
        force=args.force,
    )

    append_notify(args.notify_file, meeting_chat_id, result)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") in ("failed",):
        sys.exit(1)


if __name__ == "__main__":
    main()
