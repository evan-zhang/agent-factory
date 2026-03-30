#!/usr/bin/env python3
"""
stop-pull.py — 安全停止进行中的 pull-meeting 轮询

用途：
    向指定 meetingChatId 的落盘目录写入 .stop 标记文件，
    pull-meeting.py 的轮询循环会在下次检测时（≤1秒内）安全退出。

    不会强制杀死进程，保证已写数据完整。

用法：
    python3 stop-pull.py <meetingChatId>

参数：
    meetingChatId   必填，慧记会议 ID
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime


def resolve_gateway_name() -> str:
    """返回当前 gateway 名称，默认 default。"""
    for key in ("OPENCLAW_GATEWAY", "OPENCLAW_GATEWAY_NAME", "GATEWAY", "GATEWAY_NAME"):
        val = os.environ.get(key)
        if val:
            return str(val).strip()
    return "default"


def resolve_materials_root() -> Path:
    """
    解析会议素材根目录：
      <base>/cms-meeting-materials/<gateway>/

    优先级：
      1) CMS_MEETING_MATERIALS_ROOT（显式基路径）
      2) ~/.openclaw/cms-meeting-materials（默认共享基路径）

    说明：
      - 默认走用户级共享目录，支持多个 agent 共用。
      - 通过 gateway 分桶，避免跨 gateway 混淆。
    """
    explicit = os.environ.get("CMS_MEETING_MATERIALS_ROOT")
    if explicit:
        base = Path(explicit).expanduser().resolve()
    else:
        base = (Path.home() / ".openclaw" / "cms-meeting-materials").resolve()

    gateway = resolve_gateway_name()
    root = base / gateway
    root.mkdir(parents=True, exist_ok=True)
    return root

def find_materials_dir(meeting_chat_id: str) -> Path:
    return resolve_materials_root() / meeting_chat_id


def main():
    parser = argparse.ArgumentParser(
        description="写入 .stop 标记，安全停止 pull-meeting 轮询"
    )
    parser.add_argument("meeting_chat_id", help="慧记会议 ID")
    args = parser.parse_args()

    meeting_chat_id = args.meeting_chat_id
    mat_dir = find_materials_dir(meeting_chat_id)
    stop_path = mat_dir / ".stop"

    if not mat_dir.exists():
        print(f"⚠️  目录不存在，可能该会议从未被拉取：{mat_dir}")
        print("   .stop 文件将仍然写入，以防进程刚刚启动。")
        mat_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().astimezone().isoformat(timespec="seconds")
    payload = json.dumps({
        "meeting_chat_id": meeting_chat_id,
        "stop_requested_at": ts,
        "reason": "user_requested",
    }, ensure_ascii=False, indent=2)

    try:
        stop_path.write_text(payload, encoding="utf-8")
        print(f"✅ .stop 标记已写入：{stop_path}")
        print(f"   pull-meeting.py 将在下次检测时（≤1s）安全退出。")
    except Exception as e:
        print(f"❌ 写入 .stop 失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
