"""
创建院外检索 RUN_ROOT：渲染 search_spec.json、初始化 run_meta 与空 evidence.jsonl。
鉴权：nologin（仅本地落盘）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_SKILLCODE = "pharma-outpatient-orchestrator"
# 合同默认执行通道：国内与 Global 检索均以 OpenClaw acpx 注入的 MiniMax MCP 优先（见 channel_bindings）。
DEFAULT_SEARCH_MCP = "minmax_web_search_mcp"


def _normalize_channel_bindings(spec: dict[str, Any]) -> None:
    """Ensure minmax_web_search_mcp is the first hop for CN_SEARCH and GLOBAL_SEARCH (when non-empty)."""
    cb = spec.get("channel_bindings")
    if not isinstance(cb, dict):
        cb = {}
        spec["channel_bindings"] = cb

    cn = cb.get("CN_SEARCH")
    if not isinstance(cn, list):
        cn = []
    tail = [x for x in cn if x != DEFAULT_SEARCH_MCP]
    cb["CN_SEARCH"] = [DEFAULT_SEARCH_MCP, *tail]

    gl = cb.get("GLOBAL_SEARCH")
    if isinstance(gl, list) and gl:
        tail_g = [x for x in gl if x != DEFAULT_SEARCH_MCP]
        cb["GLOBAL_SEARCH"] = [DEFAULT_SEARCH_MCP, *tail_g]


def _log(msg: str, skillcode: str) -> None:
    base = Path.cwd() / ".cms-log" / "log" / skillcode
    try:
        base.mkdir(parents=True, exist_ok=True)
        line = datetime.now(timezone.utc).isoformat() + " " + msg + "\n"
        (base / "init_run.log").open("a", encoding="utf-8").write(line)
    except OSError:
        pass


def slug_city_or_topic(value: str) -> str:
    s = value.strip()
    s = re.sub(r"\s+", "-", s)
    return s


def _safe_segment(name: str, label: str) -> str:
    if not name or not str(name).strip():
        raise SystemExit(f"missing {label}")
    s = str(name).strip()
    if ".." in s or "/" in s or "\\" in s:
        raise SystemExit(f"{label} must not contain path separators or '..'")
    return s


def find_default_template() -> Path | None:
    skill_root = Path(__file__).resolve().parents[2]
    for base in [skill_root, *skill_root.parents]:
        cand = base / "网络搜索" / "pharma-city-outpatient-search-spec.template.json"
        if cand.is_file():
            return cand
    return None


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def render_template_text(raw: str, mapping: dict[str, str]) -> str:
    out = raw
    for k, v in mapping.items():
        out = out.replace(k, v)
    return out


def main() -> None:
    p = argparse.ArgumentParser(
        description="Initialize pharma outpatient search RUN_ROOT.",
        epilog=(
            "Creates the full directory tree for RUN_ROOT (mkdir parents=True). "
            "Writes search_spec.json, run_meta.json, and an empty evidence.jsonl. "
            "Exits with error if RUN_ROOT already exists (no overwrite)."
        ),
    )
    p.add_argument("--task-id", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--city", required=True, help="Replaces {{CITY}} in template.")
    p.add_argument(
        "--template",
        default=None,
        help="Path to pharma-city-outpatient-search-spec.template.json",
    )
    p.add_argument(
        "--base-dir",
        default="./network-search-runs",
        help="output_policy.base_dir equivalent (relative to cwd unless absolute).",
    )
    p.add_argument(
        "--generated-at",
        default=None,
        help="ISO-8601 UTC; default now.",
    )
    p.add_argument(
        "--domain-append-json",
        default=None,
        help="Path to JSON array of extra hostnames to merge into source_policy.include_domains.",
    )
    p.add_argument(
        "--skillcode",
        default=DEFAULT_SKILLCODE,
        help="For .cms-log subdirectory name.",
    )
    args = p.parse_args()
    log_code = args.skillcode

    task_id = _safe_segment(args.task_id, "task_id")
    run_id = _safe_segment(args.run_id, "run_id")
    city = args.city.strip()
    if not city:
        raise SystemExit("city must be non-empty")

    gen_at = args.generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    tpl_path = Path(args.template).expanduser() if args.template else find_default_template()
    if tpl_path is None or not tpl_path.is_file():
        raise SystemExit(
            "template not found; pass --template explicitly "
            "(e.g. path to 网络搜索/pharma-city-outpatient-search-spec.template.json)."
        )

    raw = tpl_path.read_text(encoding="utf-8")
    mapping = {
        "{{TASK_ID}}": task_id,
        "{{RUN_ID}}": run_id,
        "{{GENERATED_AT}}": gen_at,
        "{{CITY}}": city,
    }
    rendered = render_template_text(raw, mapping)
    try:
        spec: dict[str, Any] = json.loads(rendered)
    except json.JSONDecodeError as e:
        raise SystemExit(f"invalid JSON after placeholder replace: {e}") from e

    _normalize_channel_bindings(spec)

    city_or_topic = str(spec.get("city_or_topic") or f"{city}-院外全景")
    mid = slug_city_or_topic(city_or_topic)
    base_dir = Path(args.base_dir).expanduser()
    run_root = (base_dir / task_id / mid / run_id).resolve()

    extra_domains: list[str] = []
    if args.domain_append_json:
        pth = Path(args.domain_append_json).expanduser()
        extra_domains = json.loads(pth.read_text(encoding="utf-8"))
        if not isinstance(extra_domains, list):
            raise SystemExit("domain-append-json must be a JSON array of strings")
        extra_domains = [str(x).strip() for x in extra_domains if str(x).strip()]

    sp = spec.setdefault("source_policy", {})
    inc = list(sp.get("include_domains") or [])
    seen = {x.lower() for x in inc}
    for d in extra_domains:
        if d.lower() not in seen:
            inc.append(d)
            seen.add(d.lower())
    sp["include_domains"] = inc

    run_root.mkdir(parents=True, exist_ok=False)

    spec_path = run_root / "search_spec.json"
    atomic_write_json(spec_path, spec)

    resolution = None
    if extra_domains:
        resolution = {
            "city_input": city,
            "appended_domains": extra_domains,
            "final_include_domains": inc,
        }

    run_meta: dict[str, Any] = {
        "task_id": task_id,
        "run_id": run_id,
        "evidence_id_strategy": "caller_provided",
        "started_at": gen_at,
        "spec_template_path": str(tpl_path.resolve()),
        "run_root": str(run_root),
        "spec_version": spec.get("spec_version"),
    }
    if resolution is not None:
        run_meta["include_domains_resolution"] = resolution

    atomic_write_json(run_root / "run_meta.json", run_meta)
    (run_root / "evidence.jsonl").write_text("", encoding="utf-8")

    _log(f"init ok run_root={run_root}", log_code)
    out = {
        "success": True,
        "run_root": str(run_root),
        "search_spec": str(spec_path),
        "city_or_topic": city_or_topic,
        "city_or_topic_slug": mid,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
