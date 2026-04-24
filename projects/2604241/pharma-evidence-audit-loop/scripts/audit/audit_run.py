"""
根据 search_spec + evidence.jsonl 生成 audit_report.json 与 gap_report.md（启发式首版）。
鉴权：nologin。
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

GRADE_RANK = {"D": 0, "C": 1, "B": 2, "A": 3}


def url_grade(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
    except Exception:
        return "D"
    if not netloc:
        return "D"
    if "nmpa.gov.cn" in netloc or "chp.org.cn" in netloc:
        return "A"
    if netloc.endswith("gov.cn") or ".gov.cn" in netloc:
        return "B"
    return "D"


def meets_min(line_grade: str, min_g: str) -> bool:
    need = (min_g or "B").strip().upper()
    if need not in GRADE_RANK:
        need = "B"
    return GRADE_RANK.get(line_grade, 0) >= GRADE_RANK.get(need, 2)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def atomic_write_json(path: Path, data: Any) -> None:
    atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def load_evidence(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def next_action_for_codes(codes: list[str]) -> str:
    if any(c == "E_COUNTER_CHECK_MISSING" for c in codes):
        return "补检"
    if any(c in ("E_INSUFFICIENT_EVIDENCE", "E_SOURCE_GRADE_LOW", "E_NO_QUOTE", "E_NO_SOURCE_URL") for c in codes):
        return "补检"
    if any(c == "E_DEDUP_COLLISION" for c in codes):
        return "人工"
    return "收口"


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit evidence and write audit_report + gap_report.")
    ap.add_argument("--run-root", required=True)
    args = ap.parse_args()

    root = Path(args.run_root).expanduser().resolve()
    spec_path = root / "search_spec.json"
    ev_path = root / "evidence.jsonl"
    if not spec_path.is_file():
        raise SystemExit(f"missing {spec_path}")
    if not ev_path.is_file():
        raise SystemExit(f"missing {ev_path}")

    spec: dict[str, Any] = json.loads(spec_path.read_text(encoding="utf-8"))
    task_id = str(spec.get("task_id") or "")
    run_id = str((spec.get("output_policy") or {}).get("run_id") or "")
    spec_version = spec.get("spec_version")
    fields: list[dict[str, Any]] = list(spec.get("field_specs") or [])
    evidence = load_evidence(ev_path)

    by_field: dict[str, list[dict[str, Any]]] = {}
    for row in evidence:
        fn = str(row.get("field_name") or "")
        by_field.setdefault(fn, []).append(row)

    verdicts: list[dict[str, Any]] = []
    gap_rows: list[tuple[str, str, str, str]] = []

    for fs in fields:
        fname = str(fs.get("field_name") or "")
        ftype = str(fs.get("field_type") or "fact")
        need = int(fs.get("required_evidence_count") or 0)
        min_g = str(fs.get("min_source_grade") or "B")
        rows = by_field.get(fname, [])

        codes: list[str] = []
        reasons: list[str] = []

        if not rows:
            codes.append("E_INSUFFICIENT_EVIDENCE")
            reasons.append("无证据行")
        else:
            for i, r in enumerate(rows):
                if not str(r.get("evidence_quote", "")).strip():
                    codes.append("E_NO_QUOTE")
                    reasons.append(f"行 {i} 缺 evidence_quote")
                    break
                if not str(r.get("source_url", "")).strip():
                    codes.append("E_NO_SOURCE_URL")
                    reasons.append(f"行 {i} 缺 source_url")
                    break

            good = [
                r
                for r in rows
                if str(r.get("evidence_quote", "")).strip()
                and str(r.get("source_url", "")).strip()
                and meets_min(url_grade(str(r.get("source_url", ""))), min_g)
            ]
            if len(good) < need:
                codes.append("E_INSUFFICIENT_EVIDENCE")
                reasons.append(f"达等级且可引用条数 {len(good)} < 需要 {need}")

        if ftype == "judgment" and not any(str(r.get("query_kind")) == "counter" for r in rows):
            if "E_COUNTER_CHECK_MISSING" not in codes:
                codes.append("E_COUNTER_CHECK_MISSING")
                reasons.append("judgment 维度缺少 counter 证据")

        stance = "support"
        if codes:
            stance = "uncertain"

        verdicts.append(
            {
                "field_name": fname,
                "stance": stance,
                "reasons": reasons or ["规则检查通过"],
                "codes": sorted(set(codes)) if codes else [],
            }
        )

        if stance != "support":
            gap_rows.append(
                (
                    fname,
                    ", ".join(sorted(set(codes))) or "UNKNOWN",
                    next_action_for_codes(codes),
                    "; ".join(reasons[:3]),
                )
            )

    report: dict[str, Any] = {
        "task_id": task_id,
        "run_id": run_id,
        "spec_version": spec_version,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "field_verdicts": verdicts,
        "errors": [],
    }

    atomic_write_json(root / "audit_report.json", report)

    lines = [
        "# gap_report",
        "",
        f"**task_id**={task_id} **run_id**={run_id}",
        "",
        "| 维度（field_name） | 问题类型 / 错误码 | next_action | 备注 |",
        "|---|---|---|---|",
    ]
    if not gap_rows:
        lines += ["| （无） | — | 收口 | 全部维度 support |"]
    else:
        for fn, code, na, note in gap_rows:
            lines.append(f"| {fn} | {code} | {na} | {note} |")
    lines.append("")
    atomic_write_text(root / "gap_report.md", "\n".join(lines))

    print(
        json.dumps(
            {"success": True, "run_root": str(root), "fields": len(verdicts), "gaps": len(gap_rows)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
