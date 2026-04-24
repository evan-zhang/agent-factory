"""
追加 Global 维度证据：校验 query 属于 search_spec 中该 field 的 global_queries 后写入 evidence.jsonl。
鉴权：nologin。
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
    ap = argparse.ArgumentParser(description="Append one GLOBAL evidence line.")
    ap.add_argument("--run-root", required=True)
    ap.add_argument("--evidence-json", default=None)
    ap.add_argument("--evidence-json-stdin", action="store_true")
    args = ap.parse_args()

    root = Path(args.run_root).expanduser().resolve()
    spec_path = root / "search_spec.json"
    ev_path = root / "evidence.jsonl"
    if not spec_path.is_file():
        raise SystemExit(f"search_spec.json not found: {spec_path}")
    if not ev_path.is_file():
        raise SystemExit(f"evidence.jsonl not found: {ev_path}")

    spec: dict[str, Any] = json.loads(spec_path.read_text(encoding="utf-8"))
    fields = spec.get("field_specs") or []
    by_name = {str(fs.get("field_name")): fs for fs in fields if fs.get("field_name")}

    if args.evidence_json_stdin:
        row = json.loads(sys.stdin.read())
    elif args.evidence_json:
        row = json.loads(Path(args.evidence_json).expanduser().read_text(encoding="utf-8"))
    else:
        raise SystemExit("provide --evidence-json or --evidence-json-stdin")

    if not isinstance(row, dict):
        raise SystemExit("evidence must be a JSON object")

    missing = [k for k in REQUIRED_KEYS if k not in row or row[k] in (None, "")]
    if missing:
        raise SystemExit(f"missing or empty keys: {missing}")

    fname = str(row["field_name"])
    if fname not in by_name:
        raise SystemExit(f"unknown field_name: {fname}")

    gq = by_name[fname].get("global_queries") or []
    if not isinstance(gq, list) or len(gq) == 0:
        raise SystemExit(f"global_queries empty for field {fname}; do not use this script")

    q = str(row["query"]).strip()
    allowed = {str(x).strip() for x in gq if str(x).strip()}
    if q not in allowed:
        raise SystemExit(f"query not in global_queries for this field. allowed={sorted(allowed)!r} got={q!r}")

    if row.get("query_kind") != "positive":
        raise SystemExit("global evidence lines must use query_kind='positive' per contract")

    line = json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
    with ev_path.open("a", encoding="utf-8") as f:
        f.write(line)

    print(json.dumps({"success": True, "evidence_id": row.get("evidence_id")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
