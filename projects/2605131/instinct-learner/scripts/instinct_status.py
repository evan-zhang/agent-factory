#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from instinct_lib import FRONTMATTER_RE, ensure_dirs, instincts_dir as _instincts_dir, resolve_data_dir, utc_now_iso


def _parse_frontmatter_md(text: str) -> dict[str, Any]:
    m = FRONTMATTER_RE.search(text)
    if not m:
        return {}
    block = m.group(1)
    out: dict[str, Any] = {}
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        key = k.strip()
        val = v.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                out[key] = []
            else:
                out[key] = [x.strip().strip('"').strip("'") for x in inner.split(",")]
            continue
        if val.lower() in ("true", "false"):
            out[key] = val.lower() == "true"
            continue
        try:
            if "." in val:
                out[key] = float(val)
            else:
                out[key] = int(val)
            continue
        except Exception:
            pass
        out[key] = val.strip('"').strip("'")
    return out


def _read_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text("utf-8"))
    except Exception:
        return {}


@dataclass(frozen=True)
class InstinctRecord:
    path: Path
    id: str | None
    created: str | None
    confidence: float | None
    times_used: int | None
    last_used: str | None
    status: str | None
    tags: list[str]


def _load_instinct(path: Path) -> InstinctRecord:
    text = path.read_text("utf-8", errors="replace")
    fm = _parse_frontmatter_md(text)
    tags = fm.get("tags")
    if not isinstance(tags, list):
        tags = []
    return InstinctRecord(
        path=path,
        id=fm.get("id") if isinstance(fm.get("id"), str) else None,
        created=fm.get("created") if isinstance(fm.get("created"), str) else None,
        confidence=float(fm["confidence"]) if "confidence" in fm else None,
        times_used=int(fm["times_used"]) if "times_used" in fm else None,
        last_used=fm.get("last_used") if isinstance(fm.get("last_used"), str) else None,
        status=fm.get("status") if isinstance(fm.get("status"), str) else None,
        tags=[str(x) for x in tags],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Instinct 状态概览（MVP）。")
    parser.add_argument(
        "--base-dir",
        default=str(Path(__file__).resolve().parents[1]),
        help="skill 根目录（默认：脚本上级目录）",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="instinct 数据目录（默认 <base-dir>/instincts；推荐在 hook 中传 <workspace>/instincts）",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    data_dir = resolve_data_dir(base_dir, args.data_dir)
    instincts_dir = _instincts_dir(base_dir, args.data_dir)
    archived_dir = instincts_dir / "archived"
    _ = _read_config(base_dir / "config.json")

    ensure_dirs(base_dir, args.data_dir)

    active: list[InstinctRecord] = []
    dormant: list[InstinctRecord] = []
    expired: list[InstinctRecord] = []
    archived: list[InstinctRecord] = []

    for p in sorted(instincts_dir.glob("*.md")):
        rec = _load_instinct(p)
        st = (rec.status or "active").strip().lower()
        if st == "dormant":
            dormant.append(rec)
        elif st == "expired":
            expired.append(rec)
        else:
            active.append(rec)

    for p in sorted(archived_dir.glob("*.md")):
        archived.append(_load_instinct(p))

    def by_confidence(rec: InstinctRecord) -> float:
        return rec.confidence if rec.confidence is not None else -1.0

    top = sorted(active, key=by_confidence, reverse=True)[:5]
    recent = sorted(active, key=lambda r: r.created or r.path.name, reverse=True)[:5]

    print("Instinct 状态概览")
    print("=================")
    print(f"总计: {len(active)} 条 active, {len(dormant)} 条 dormant, {len(archived)} 条 archived")
    if expired:
        print(f"（注意：仍有 {len(expired)} 条 status=expired 未归档，建议运行 prune 脚本）")
    print("")

    print("Top 5 高置信度:")
    if not top:
        print("（空）")
    for idx, rec in enumerate(top, start=1):
        conf = f"{rec.confidence:.2f}" if rec.confidence is not None else "?"
        used = str(rec.times_used) if rec.times_used is not None else "?"
        label = rec.id or rec.path.stem
        print(f"{idx}. [{label}] 置信度 {conf} (使用 {used} 次)")

    print("")
    print("最近 5 条:")
    if not recent:
        print("（空）")
    for idx, rec in enumerate(recent, start=1):
        label = rec.id or rec.path.stem
        created = rec.created or "?"
        conf = f"{rec.confidence:.2f}" if rec.confidence is not None else "?"
        print(f"{idx}. [{label}] {created} 置信度 {conf}")

    print("")
    print(f"生成时间: {utc_now_iso()}")
    print(f"目录: {instincts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

