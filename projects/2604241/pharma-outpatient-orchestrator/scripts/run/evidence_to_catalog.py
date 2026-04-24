#!/usr/bin/env python3
"""从 evidence.jsonl 生成可浏览的 Markdown 目录（机械汇总，不替代 summary.md / 审计结论）。"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _esc_cell(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def main() -> None:
    p = argparse.ArgumentParser(description="Render evidence.jsonl as a grouped Markdown catalog.")
    p.add_argument(
        "--run-root",
        required=True,
        help="RUN_ROOT directory containing evidence.jsonl",
    )
    p.add_argument(
        "--output",
        default=None,
        help="Output .md path (default: <run-root>/evidence_catalog.md)",
    )
    args = p.parse_args()
    run_root = Path(args.run_root).expanduser().resolve()
    ev_path = run_root / "evidence.jsonl"
    if not ev_path.is_file():
        raise SystemExit(f"missing {ev_path}")

    out_path = Path(args.output).expanduser() if args.output else run_root / "evidence_catalog.md"

    rows: list[dict[str, Any]] = []
    with ev_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    by_field: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_field[str(r.get("field_name") or "?")].append(r)

    lines: list[str] = [
        "# 证据目录（由 evidence.jsonl 机械生成）",
        "",
        f"- **run_root**: `{run_root}`",
        f"- **条数**: {len(rows)}",
        "",
        "> 人读结论请以 **`summary.md`**（院外 §4.1）为准；缺口与动作以 **`gap_report.md`** / **`audit_report.json`** 为准。本文件仅便于浏览原始引用。",
        "",
    ]
    for fname in sorted(by_field.keys(), key=lambda x: (x or "")):
        lines.append(f"## {fname}")
        lines.append("")
        lines.append("| query_kind | query | source_url |")
        lines.append("|------------|-------|------------|")
        for r in by_field[fname]:
            q = _esc_cell(str(r.get("query") or ""))[:200]
            lines.append(
                f"| {_esc_cell(str(r.get('query_kind') or ''))} | {q} | {_esc_cell(str(r.get('source_url') or ''))} |"
            )
        lines.append("")
        lines.append("**摘录**（前 5 条，节选）：")
        lines.append("")
        for r in by_field[fname][:5]:
            quote = _esc_cell(str(r.get("evidence_quote") or ""))[:500]
            lines.append(f"- `{r.get('evidence_id')}`: {quote}")
        if len(by_field[fname]) > 5:
            lines.append(f"- … 共 {len(by_field[fname])} 条，其余见上表")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"success": True, "output": str(out_path), "rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
