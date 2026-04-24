"""
校验院外检索 RUN 必落文件并补全 run_meta 完成时间戳。
鉴权：nologin。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILLCODE = "pharma-outpatient-orchestrator"

REQUIRED = [
    "search_spec.json",
    "evidence.jsonl",
    "audit_report.json",
    "gap_report.md",
    "summary.md",
    "run_meta.json",
]


def _log(msg: str) -> None:
    base = Path.cwd() / ".cms-log" / "log" / SKILLCODE
    try:
        base.mkdir(parents=True, exist_ok=True)
        line = datetime.now(timezone.utc).isoformat() + " " + msg + "\n"
        (base / "finalize_run.log").open("a", encoding="utf-8").write(line)
    except OSError:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Finalize pharma outpatient RUN_ROOT.")
    ap.add_argument("--run-root", required=True, help="Absolute or cwd-relative RUN_ROOT path.")
    ap.add_argument(
        "--require-summary",
        action="store_true",
        default=True,
        help="Require summary.md to exist (default: true).",
    )
    ap.add_argument(
        "--no-require-summary",
        action="store_true",
        help="Allow missing summary.md (e.g. mid-pipeline debug).",
    )
    args = ap.parse_args()
    require_summary = args.require_summary and not args.no_require_summary

    root = Path(args.run_root).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"run-root is not a directory: {root}")

    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if not require_summary and "summary.md" in missing:
        missing = [m for m in missing if m != "summary.md"]

    if missing:
        raise SystemExit(f"missing files: {missing}")

    meta_path = root / "run_meta.json"
    meta: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["completed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta["finalize_checklist"] = {"required_files": REQUIRED, "all_present": True}
    tmp = meta_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, meta_path)

    _log(f"finalize ok run_root={root}")
    print(json.dumps({"success": True, "run_root": str(root), "completed_at": meta["completed_at"]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code not in (0, None):
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        raise
