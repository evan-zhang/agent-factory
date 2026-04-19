#!/usr/bin/env python3
"""
pull-meeting.py — 兼容入口（内部转 short-runner）

说明：
- 默认调度周期 120s
- 每一轮调用 pull_core.run_pull_once()，任务短执行后 sleep
- 支持 timeout 提前退出
"""

import argparse
import json
import time

from pull_core import ALLOWED_INTERVALS, DEFAULT_INTERVAL, run_pull_once, resolve_meeting_chat_id_by_number


def main():
    parser = argparse.ArgumentParser(description="会议素材镜像器（调度驱动模式）")
    parser.add_argument("meeting_chat_id", nargs="?", default="", help="meetingChatId（可选）")
    parser.add_argument("--meeting-number", default="", help="视频会议号（可解析 meetingChatId）")
    parser.add_argument("--last-ts", type=int, default=None, help="配合 --meeting-number 使用")
    parser.add_argument("--gateway", default="", help="可选，覆盖当前 gateway")
    parser.add_argument("--name", default="", help="会议名称")
    parser.add_argument("--force", action="store_true", help="忽略 is_fully_pulled")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help=f"调度周期（秒，默认 {DEFAULT_INTERVAL}，可选 {sorted(ALLOWED_INTERVALS)}）")
    parser.add_argument("--timeout", type=int, default=0, help="最长运行时间（秒，0=不限）")
    args = parser.parse_args()

    meeting_chat_id = (args.meeting_chat_id or "").strip()
    if not meeting_chat_id and args.meeting_number:
        meeting_chat_id = resolve_meeting_chat_id_by_number(args.meeting_number, args.last_ts)["meetingChatId"]
    if not meeting_chat_id:
        parser.error("必须提供 meeting_chat_id，或使用 --meeting-number")

    if args.interval not in ALLOWED_INTERVALS:
        parser.error(f"--interval 仅支持 {sorted(ALLOWED_INTERVALS)}")

    started = time.time()
    last_result = None

    while True:
        last_result = run_pull_once(
            meeting_chat_id=meeting_chat_id,
            gateway=args.gateway or None,
            name=args.name,
            force=args.force,
        )

        status = last_result.get("status")
        if status in ("completed", "stopped", "failed"):
            break

        if args.timeout > 0 and (time.time() - started) >= args.timeout:
            break

        time.sleep(args.interval)

    print(json.dumps(last_result or {"status": "unknown"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
