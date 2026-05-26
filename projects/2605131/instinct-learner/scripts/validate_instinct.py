#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from instinct_lib import (
    ensure_dirs,
    load_index,
    read_instinct,
    upsert_frontmatter_md,
    utc_now_iso,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="根据本轮是否参考 instinct 更新置信度（stdin JSON）。")
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
    if not isinstance(payload, dict):
        sys.stdout.write(json.dumps({"ok": False, "reason": "invalid_payload"}, ensure_ascii=False))
        return 0

    used_ids = payload.get("used_ids")
    outcome = str(payload.get("outcome") or "").lower().strip()
    if not isinstance(used_ids, list) or not used_ids:
        sys.stdout.write(json.dumps({"ok": True, "updated": 0, "reason": "no_used_ids"}, ensure_ascii=False))
        return 0
    if outcome not in ("success", "corrected", "neutral"):
        outcome = "neutral"

    idx = load_index(base_dir, args.data_dir)
    by_id = idx.get("by_id") if isinstance(idx.get("by_id"), dict) else {}
    updated = 0
    missing: list[str] = []

    for raw_id in used_ids:
        inst_id = str(raw_id)
        p = by_id.get(inst_id)
        if not isinstance(p, str):
            missing.append(inst_id)
            continue
        path = Path(p)
        if not path.exists():
            missing.append(inst_id)
            continue
        text = path.read_text("utf-8", errors="replace")
        inst = read_instinct(path)
        times_used = int(inst.frontmatter.get("times_used", 0) or 0) + 1
        times_validated = int(inst.frontmatter.get("times_validated", 0) or 0)
        conf = float(inst.frontmatter.get("confidence", 0.6) or 0.6)
        if outcome == "success":
            times_validated += 1
            conf = min(1.0, conf + 0.05)
        elif outcome == "corrected":
            conf = max(0.0, conf - 0.1)
        patched = {
            "times_used": times_used,
            "times_validated": times_validated,
            "confidence": round(conf, 4),
            "last_used": utc_now_iso(),
            "status": inst.frontmatter.get("status", "active"),
        }
        new_text = upsert_frontmatter_md(text, patched)
        path.write_text(new_text, "utf-8")
        updated += 1

    sys.stdout.write(
        json.dumps({"ok": True, "updated": updated, "missing": missing, "outcome": outcome}, ensure_ascii=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

