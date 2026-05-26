#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from instinct_lib import (
    build_instinct_markdown,
    compute_fingerprint,
    ensure_dirs,
    load_index,
    next_instinct_filename,
    save_index,
    simple_extract_candidate,
    utc_now_iso,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="从最近 N 轮会话中提取 0/1 条 Instinct（关键词规则，幂等去重）。"
    )
    parser.add_argument("--base-dir", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument(
        "--data-dir",
        default=None,
        help="instinct 数据目录（默认 <base-dir>/instincts；推荐在 hook 中传 <workspace>/instincts）",
    )
    parser.add_argument("--config", default=None, help="config.json 路径（可选）")
    parser.add_argument("--stdin", action="store_true", default=True, help="从 stdin 读取 JSON")
    args = parser.parse_args()

    raw = sys.stdin.read()
    payload = None
    if raw.strip():
        try:
            payload = json.loads(raw)
        except Exception:
            payload = None

    base_dir = Path(args.base_dir).resolve()
    ensure_dirs(base_dir, args.data_dir)
    messages = (payload or {}).get("messages") if isinstance(payload, dict) else None
    if not isinstance(messages, list) or not messages:
        print(json.dumps({"ok": False, "reason": "missing_messages"}, ensure_ascii=False))
        return 0

    candidate = simple_extract_candidate(messages)
    if not candidate:
        print(json.dumps({"ok": True, "created": False, "reason": "no_candidate"}, ensure_ascii=False))
        return 0

    fingerprint = compute_fingerprint(candidate["trigger"], candidate["action"])
    idx = load_index(base_dir, args.data_dir)
    by_fp = idx.get("by_fingerprint")
    if isinstance(by_fp, dict) and fingerprint in by_fp:
        print(
            json.dumps(
                {"ok": True, "created": False, "reason": "duplicate", "fingerprint": fingerprint},
                ensure_ascii=False,
            )
        )
        return 0

    instinct_id = f"instinct-{utc_now_iso().replace(':', '').replace('-', '')[:15]}-{fingerprint}"
    doc = build_instinct_markdown(
        {
            "id": instinct_id,
            "created": utc_now_iso(),
            "confidence": 0.6,
            "times_used": 0,
            "times_validated": 0,
            "last_used": "",
            "tags": candidate.get("tags", []),
            "status": "active",
            "title": candidate.get("title", instinct_id),
            "fingerprint": fingerprint,
            "trigger": candidate["trigger"],
            "action": candidate["action"],
            "evidence": candidate.get("evidence", "- (自动生成：暂无证据)"),
        }
    )
    target = next_instinct_filename(base_dir, args.data_dir)
    target.write_text(doc, "utf-8")

    idx.setdefault("by_fingerprint", {})[fingerprint] = str(target)
    idx.setdefault("by_id", {})[instinct_id] = str(target)
    save_index(base_dir, idx, args.data_dir)

    out = {"ok": True, "created": True, "id": instinct_id, "path": str(target), "fingerprint": fingerprint}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

