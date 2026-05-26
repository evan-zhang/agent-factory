#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from instinct_lib import (
    archived_dir,
    days_since_iso,
    ensure_dirs,
    index_path,
    list_instinct_files,
    read_config,
    read_instinct,
    save_index,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="清理/归档过期 Instinct（按 config.json）。")
    parser.add_argument("--base-dir", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument(
        "--data-dir",
        default=None,
        help="instinct 数据目录（默认 <base-dir>/instincts；推荐在 hook 中传 <workspace>/instincts）",
    )
    parser.add_argument("--config", default=None, help="config.json 路径（可选）")
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    ensure_dirs(base_dir, args.data_dir)
    cfg = read_config(base_dir, args.config)
    dormant_days = int(cfg.get("dormant_days", 30))
    expired_days = int(cfg.get("expired_days", 60))
    confidence_threshold = float(cfg.get("confidence_threshold", 0.3))
    max_active_instincts = int(cfg.get("max_active_instincts", 50) or 50)

    moved = 0
    marked_dormant = 0
    marked_expired = 0
    capped_active = 0

    for p in list_instinct_files(base_dir, args.data_dir):
        inst = read_instinct(p)
        last_used_days = days_since_iso(inst.last_used)
        status = inst.status
        conf = inst.confidence
        times_used = int(inst.frontmatter.get("times_used", 0) or 0)

        new_status = status
        if last_used_days is not None:
            if last_used_days >= expired_days:
                new_status = "expired"
            elif last_used_days >= dormant_days:
                new_status = "dormant"
        if conf < confidence_threshold and times_used > 5:
            new_status = "expired"

        if new_status != status:
            text = p.read_text("utf-8", errors="replace")
            from instinct_lib import upsert_frontmatter_md

            new_text = upsert_frontmatter_md(text, {"status": new_status})
            if not args.dry_run:
                p.write_text(new_text, "utf-8")
            if new_status == "dormant":
                marked_dormant += 1
            if new_status == "expired":
                marked_expired += 1

        if new_status == "expired":
            dest = archived_dir(base_dir, args.data_dir) / p.name
            if not args.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                p.replace(dest)
            moved += 1

    # Enforce max_active_instincts by demoting lowest-confidence active instincts to dormant.
    if max_active_instincts > 0:
        active_records: list[tuple[Path, float, int]] = []
        for p in list_instinct_files(base_dir, args.data_dir):
            inst = read_instinct(p)
            if inst.status != "active":
                continue
            last_used_days = days_since_iso(inst.last_used)
            age = last_used_days if last_used_days is not None else 999999
            active_records.append((p, inst.confidence, age))

        if len(active_records) > max_active_instincts:
            active_records.sort(key=lambda x: (x[1], -x[2]))
            to_demote = active_records[: max(0, len(active_records) - max_active_instincts)]
            from instinct_lib import upsert_frontmatter_md

            for p, _, _ in to_demote:
                text = p.read_text("utf-8", errors="replace")
                new_text = upsert_frontmatter_md(text, {"status": "dormant"})
                if not args.dry_run:
                    p.write_text(new_text, "utf-8")
                capped_active += 1
                marked_dormant += 1

    if not args.dry_run:
        new_idx = {"by_fingerprint": {}, "by_id": {}}
        for p in list_instinct_files(base_dir, args.data_dir):
            inst = read_instinct(p)
            fp = inst.frontmatter.get("fingerprint")
            if fp:
                new_idx["by_fingerprint"][str(fp)] = str(p)
            new_idx["by_id"][inst.id] = str(p)
        save_index(base_dir, new_idx, args.data_dir)

    out = {
        "ok": True,
        "dry_run": args.dry_run,
        "moved": moved,
        "marked_dormant": marked_dormant,
        "marked_expired": marked_expired,
        "capped_active": capped_active,
        "index": str(index_path(base_dir, args.data_dir)),
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

