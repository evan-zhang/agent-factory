#!/usr/bin/env python3
"""meeting-status.py — 查询会议素材镜像状态（含锁/熔断/空跑计数）"""

import argparse
import json
import os
from pathlib import Path


def resolve_gateway_name() -> str:
    for key in ("OPENCLAW_GATEWAY", "OPENCLAW_GATEWAY_NAME", "GATEWAY", "GATEWAY_NAME"):
        val = os.environ.get(key)
        if val:
            return str(val).strip()
    return "default"


def resolve_materials_root() -> Path:
    explicit = os.environ.get("CMS_MEETING_MATERIALS_ROOT")
    if explicit:
        base = Path(explicit).expanduser().resolve()
    else:
        base = (Path.home() / ".openclaw" / "cms-meeting-materials").resolve()
    root = base / resolve_gateway_name()
    root.mkdir(parents=True, exist_ok=True)
    return root


def count_fragments(fragments_path: Path) -> int:
    if not fragments_path.exists():
        return 0
    c = 0
    with open(fragments_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c += 1
    return c


def main():
    parser = argparse.ArgumentParser(description="查询会议素材镜像器落盘状态")
    parser.add_argument("meeting_chat_id")
    parser.add_argument("--json", dest="as_json", action="store_true")
    args = parser.parse_args()

    mat_dir = resolve_materials_root() / args.meeting_chat_id
    manifest_path = mat_dir / "manifest.json"
    checkpoint_path = mat_dir / "checkpoint.json"
    fragments_path = mat_dir / "fragments.ndjson"
    lock_path = mat_dir / ".pull.lock"

    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    checkpoint = {}
    if checkpoint_path.exists():
        try:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except Exception:
            checkpoint = {}

    result = {
        "meeting_chat_id": args.meeting_chat_id,
        "materials_dir": str(mat_dir),
        "status": manifest.get("status", "not_found" if not mat_dir.exists() else "unknown"),
        "is_fully_pulled": manifest.get("is_fully_pulled", False),
        "fragment_count": count_fragments(fragments_path),
        "fragment_count_manifest": manifest.get("fragment_count", 0),
        "last_sync": manifest.get("last_sync"),
        "last_start_time": checkpoint.get("last_start_time"),
        "checkpoint_updated_at": checkpoint.get("updated_at"),
        "started_at": manifest.get("started_at"),
        "stopped_at": manifest.get("stopped_at"),
        "stopped_reason": manifest.get("stopped_reason"),
        "consecutive_empty_polls": manifest.get("consecutive_empty_polls", 0),
        "consecutive_failures": manifest.get("consecutive_failures", 0),
        "circuit_open_until": manifest.get("circuit_open_until"),
        "next_retry_after": manifest.get("next_retry_after"),
        "last_error": manifest.get("last_error"),
        "lock": {
            "file_exists": lock_path.exists(),
            **(manifest.get("lock") or {}),
        },
        "files": {
            "manifest.json": manifest_path.exists(),
            "checkpoint.json": checkpoint_path.exists(),
            "fragments.ndjson": fragments_path.exists(),
            "transcript.txt": (mat_dir / "transcript.txt").exists(),
            "pull.log": (mat_dir / "pull.log").exists(),
            ".stop": (mat_dir / ".stop").exists(),
            ".pull.lock": lock_path.exists(),
        },
    }

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
