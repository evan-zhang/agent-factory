#!/usr/bin/env python3
"""Run discovery and render a report only when this run wrote a draft."""

from __future__ import annotations

import json
import sys

from discovery_report import render_report
from dry_run_orchestrator import build_parser, run_discovery
from event_store import JsonlEventStore


def wrote_draft(result: dict) -> bool:
    return any(item.get("schema") == "draft_candidates.v1" for item in result.get("written", []))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "discovery":
        print("discovery_job only supports discovery")
        return 2
    result = run_discovery(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("calendar_skip"):
        print("\nHEARTBEAT_OK")
        print(f"calendar_skip: {result.get('calendar_status')} {result.get('calendar_skip_reason')}")
    elif result.get("ok") and wrote_draft(result):
        print("\n" + render_report(JsonlEventStore(args.event_root), args.market))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
