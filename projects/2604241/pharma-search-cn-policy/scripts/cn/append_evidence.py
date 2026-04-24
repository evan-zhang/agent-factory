"""
校验单条证据 JSON 并追加到 RUN_ROOT/evidence.jsonl。
鉴权：nologin。检索本身由 Agent 调用 minmax_web_search_mcp 等完成后再落盘。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_KEYS = (
    "evidence_id",
    "task_id",
    "subtask_id",
    "field_name",
    "query_kind",
    "query",
    "source_url",
    "evidence_quote",
    "captured_at",
)


def main() -> None:
    ap = argparse.ArgumentParser(description="Append one evidence line to evidence.jsonl.")
    ap.add_argument("--run-root", required=True)
    ap.add_argument("--evidence-json", default=None, help="Path to JSON file with one object.")
    ap.add_argument(
        "--evidence-json-stdin",
        action="store_true",
        help="Read one JSON object from stdin instead of --evidence-json.",
    )
    args = ap.parse_args()

    root = Path(args.run_root).expanduser().resolve()
    ev_path = root / "evidence.jsonl"
    if not ev_path.is_file():
        raise SystemExit(f"evidence.jsonl not found under {root}")

    if args.evidence_json_stdin:
        raw = sys.stdin.read()
        row: dict[str, Any] = json.loads(raw)
    elif args.evidence_json:
        row = json.loads(Path(args.evidence_json).expanduser().read_text(encoding="utf-8"))
    else:
        raise SystemExit("provide --evidence-json or --evidence-json-stdin")

    if not isinstance(row, dict):
        raise SystemExit("evidence must be a JSON object")

    missing = [k for k in REQUIRED_KEYS if k not in row or row[k] in (None, "")]
    if missing:
        raise SystemExit(f"missing or empty keys: {missing}")

    if row["query_kind"] not in ("positive", "counter"):
        raise SystemExit("query_kind must be 'positive' or 'counter'")

    line = json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
    with ev_path.open("a", encoding="utf-8") as f:
        f.write(line)

    print(json.dumps({"success": True, "evidence_id": row.get("evidence_id")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
