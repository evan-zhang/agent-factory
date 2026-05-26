#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from instinct_lib import ensure_dirs, list_instinct_files, rank_instincts, read_config, read_instinct


def main() -> int:
    parser = argparse.ArgumentParser(description="从 instincts/ 选 Top-K active instinct 并输出可注入摘要。")
    parser.add_argument("--base-dir", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument(
        "--data-dir",
        default=None,
        help="instinct 数据目录（默认 <base-dir>/instincts；推荐在 hook 中传 <workspace>/instincts）",
    )
    parser.add_argument("--query", default="", help="当前用户消息（用于相关性排序）")
    parser.add_argument("--config", default=None, help="config.json 路径（可选）")
    parser.add_argument("--k", type=int, default=None, help="覆盖 config.max_instincts_load")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    ensure_dirs(base_dir, args.data_dir)
    cfg = read_config(base_dir, args.config)
    k = args.k if args.k is not None else int(cfg.get("max_instincts_load", 5))
    k = max(0, min(10, k))
    max_inject_tokens = int(cfg.get("max_inject_tokens", 500) or 500)
    max_chars = max(200, min(8000, max_inject_tokens * 4))

    instincts = [read_instinct(p) for p in list_instinct_files(base_dir, args.data_dir)]
    active = [i for i in instincts if i.status == "active"]
    ranked = rank_instincts(args.query, active)
    selected = ranked[:k]

    payload = {
        "ok": True,
        "k": k,
        "query": args.query,
        "items": [
            {
                "id": inst.id,
                "title": inst.title,
                "confidence": inst.confidence,
                "times_used": int(inst.frontmatter.get("times_used", 0) or 0),
                "tags": inst.tags,
            }
            for inst in selected
        ],
    }

    if args.format == "json":
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        return 0

    if not selected:
        sys.stdout.write("## 🧠 Active Instincts (相关度最高的 0 条)\n\n（暂无可用 instinct）\n")
        return 0

    tmp_lines = ["## 🧠 Active Instincts (相关度最高的 N 条)", ""]
    for idx, inst in enumerate(selected, start=1):
        title = inst.title or inst.id
        conf = f"{inst.confidence:.2f}"
        used = str(int(inst.frontmatter.get("times_used", 0) or 0))
        action = (inst.action or "").strip().replace("\n", " ")
        action_short = action[:120] + ("…" if len(action) > 120 else "")
        tmp_lines.append(
            f'{idx}. **[{title}]** {action_short}（置信度 {conf}，使用 {used} 次，id `{inst.id}`）'
        )
        if len("\n".join(tmp_lines)) > max_chars:
            tmp_lines.pop()
            break

    actual = max(0, len(tmp_lines) - 2)
    tmp_lines[0] = f"## 🧠 Active Instincts (相关度最高的 {actual} 条)"
    tmp_lines.append("")
    sys.stdout.write("\n".join(tmp_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

