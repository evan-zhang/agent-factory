#!/usr/bin/env python3
"""
meeting-status.py — 会议素材镜像状态查询

用途：
    查询指定 meetingChatId 的本地 cms-meeting-materials 落盘状态，无需联网。

用法：
    python3 meeting-status.py <meetingChatId> [--json]

参数：
    meetingChatId   必填，慧记会议 ID
    --json          以机器可读的 JSON 格式输出（默认人类可读文本）

输出字段：
    meeting_chat_id     会议 ID
    name                会议名称（若已设置）
    status              ongoing / completed / unknown
    is_fully_pulled     是否已全量拉完
    fragment_count      已落盘片段数
    last_sync           最后同步时间（ISO 8601）
    last_start_time     最后游标值（毫秒偏移）
    materials_dir       落盘目录路径
    files               各落盘文件存在状态
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
    """定位 <workspace>/cms-meeting-materials/<meetingChatId>。"""
    return resolve_materials_root() / meeting_chat_id


def count_fragments(fragments_path: Path) -> int:
    if not fragments_path.exists():
        return 0
    count = 0
    try:
        with open(fragments_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
    except Exception:
        pass
    return count


def main():
    parser = argparse.ArgumentParser(
        description="查询会议素材镜像器落盘状态"
    )
    parser.add_argument("meeting_chat_id", help="慧记会议 ID")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="以 JSON 格式输出")
    args = parser.parse_args()

    meeting_chat_id = args.meeting_chat_id
    mat_dir = find_materials_dir(meeting_chat_id)

    manifest_path = mat_dir / "manifest.json"
    checkpoint_path = mat_dir / "checkpoint.json"
    fragments_path = mat_dir / "fragments.ndjson"
    transcript_path = mat_dir / "transcript.txt"
    log_path = mat_dir / "pull.log"
    stop_path = mat_dir / ".stop"

    # 基础信息
    result = {
        "meeting_chat_id": meeting_chat_id,
        "materials_dir": str(mat_dir),
        "dir_exists": mat_dir.exists(),
        "files": {
            "manifest.json": manifest_path.exists(),
            "checkpoint.json": checkpoint_path.exists(),
            "fragments.ndjson": fragments_path.exists(),
            "transcript.txt": transcript_path.exists(),
            "pull.log": log_path.exists(),
            ".stop": stop_path.exists(),
        },
    }

    if not mat_dir.exists():
        result.update({
            "status": "not_found",
            "is_fully_pulled": False,
            "fragment_count": 0,
            "last_sync": None,
            "last_start_time": None,
            "name": "",
        })
    else:
        # 读 manifest
        manifest = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        # 读 checkpoint
        checkpoint = {}
        if checkpoint_path.exists():
            try:
                checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        # 实际统计片段数（manifest 可能滞后）
        actual_count = count_fragments(fragments_path)

        result.update({
            "name": manifest.get("name", ""),
            "status": manifest.get("status", "unknown"),
            "is_fully_pulled": manifest.get("is_fully_pulled", False),
            "fragment_count": actual_count,
            "fragment_count_manifest": manifest.get("fragment_count", 0),
            "last_sync": manifest.get("last_sync"),
            "last_start_time": checkpoint.get("last_start_time"),
            "checkpoint_updated_at": checkpoint.get("updated_at"),
        })

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 人类可读输出
    print(f"═══════════════════════════════════════")
    print(f"  会议素材镜像状态")
    print(f"═══════════════════════════════════════")
    print(f"  meetingChatId  : {result['meeting_chat_id']}")
    if result.get("name"):
        print(f"  会议名称       : {result['name']}")
    print(f"  状态           : {result.get('status', 'unknown')}")
    print(f"  已全量拉完     : {'✅ 是' if result.get('is_fully_pulled') else '❌ 否'}")
    print(f"  已落盘片段数   : {result.get('fragment_count', 0)}")
    if result.get("last_start_time") is not None:
        lst = result["last_start_time"]
        mins, secs = divmod(lst // 1000, 60)
        hrs, mins = divmod(mins, 60)
        print(f"  游标位置       : {lst} ms ({hrs:02d}:{mins:02d}:{secs:02d})")
    print(f"  最后同步时间   : {result.get('last_sync') or '—'}")
    print(f"  落盘目录       : {result['materials_dir']}")
    print(f"───────────────────────────────────────")
    print(f"  文件状态:")
    for fname, exists in result.get("files", {}).items():
        mark = "✅" if exists else "  "
        print(f"    {mark} {fname}")
    if result["files"].get(".stop"):
        print(f"  ⚠️  .stop 标记存在（pull 进程将在下次检测时退出）")
    print(f"═══════════════════════════════════════")


if __name__ == "__main__":
    main()
