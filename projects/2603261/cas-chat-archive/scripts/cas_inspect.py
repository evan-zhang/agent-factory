#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


def parse_day(day: str | None) -> str:
    return day or dt.datetime.now().strftime("%Y-%m-%d")


def list_gateways(base: Path, gateway: str) -> list[str]:
    if gateway != "all":
        return [gateway]
    if not base.exists():
        return []
    return sorted([p.name for p in base.iterdir() if p.is_dir()])


def scope_targets(base: Path, gateway: str, scope_mode: str, agent: str) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for gw in list_gateways(base, gateway):
        gw_root = base / gw
        if scope_mode == "gateway":
            out.append((f"{gw}", gw_root))
            continue

        agents_root = gw_root / "agents"
        if not agents_root.exists():
            if agent != "all":
                out.append((f"{gw}/agents/{agent}", agents_root / agent))
            continue

        if agent == "all":
            for ap in sorted([p for p in agents_root.iterdir() if p.is_dir()]):
                out.append((f"{gw}/agents/{ap.name}", ap))
        else:
            out.append((f"{gw}/agents/{agent}", agents_root / agent))

    return out


def count_log_metrics(log_path: Path) -> dict:
    if not log_path.exists():
        return {
            "exists": False,
            "sessions": 0,
            "inbound": 0,
            "outbound": 0,
            "assets": 0,
            "lines": 0,
            "bytes": 0,
        }

    text = log_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    return {
        "exists": True,
        "sessions": sum(1 for l in lines if l.startswith("## Session #")),
        "inbound": sum(1 for l in lines if l.startswith("**[INBOUND]**")),
        "outbound": sum(1 for l in lines if l.startswith("**[OUTBOUND]**")),
        "assets": sum(1 for l in lines if l.startswith("**[ASSET]**")),
        "lines": len(lines),
        "bytes": log_path.stat().st_size,
    }


def folder_size_bytes(root: Path) -> int:
    if not root.exists():
        return 0
    total = 0
    for p in root.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total


def cmd_report(args: argparse.Namespace) -> None:
    archive_root = Path(args.archive_root).expanduser()
    day = parse_day(args.day)

    result = {
        "day": day,
        "archiveRoot": str(archive_root),
        "scopeMode": args.scope_mode,
        "targets": {},
        "summary": {
            "sessions": 0,
            "inbound": 0,
            "outbound": 0,
            "assets": 0,
            "logBytes": 0,
            "assetBytes": 0,
        },
    }

    targets = scope_targets(archive_root, args.gateway, args.scope_mode, args.agent)
    for scope_key, root in targets:
        log_path = root / "logs" / f"{day}.md"
        m = count_log_metrics(log_path)
        in_dir = root / "assets" / day / "inbound"
        out_dir = root / "assets" / day / "outbound"
        asset_bytes = folder_size_bytes(in_dir) + folder_size_bytes(out_dir)

        m["assetBytes"] = asset_bytes
        m["logPath"] = str(log_path)
        m["inboundAssetCount"] = len(list(in_dir.glob("*"))) if in_dir.exists() else 0
        m["outboundAssetCount"] = len(list(out_dir.glob("*"))) if out_dir.exists() else 0

        result["targets"][scope_key] = m
        result["summary"]["sessions"] += m["sessions"]
        result["summary"]["inbound"] += m["inbound"]
        result["summary"]["outbound"] += m["outbound"]
        result["summary"]["assets"] += m["assets"]
        result["summary"]["logBytes"] += m["bytes"]
        result["summary"]["assetBytes"] += asset_bytes

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"CAS Report | day={day} | scope={args.scope_mode}")
    print(f"archiveRoot: {archive_root}")
    if not result["targets"]:
        print("(no targets)")
    for key, m in result["targets"].items():
        print(
            f"- {key}: sessions={m['sessions']} inbound={m['inbound']} outbound={m['outbound']} assets={m['assets']} "
            f"log={m['bytes']}B asset={m['assetBytes']}B"
        )
    s = result["summary"]
    print(
        f"SUMMARY: sessions={s['sessions']} inbound={s['inbound']} outbound={s['outbound']} assets={s['assets']} "
        f"log={s['logBytes']}B asset={s['assetBytes']}B"
    )


def cmd_search(args: argparse.Namespace) -> None:
    archive_root = Path(args.archive_root).expanduser()
    day = parse_day(args.day)
    pattern = re.compile(args.query, re.IGNORECASE if args.ignore_case else 0)

    hits = []
    for scope_key, root in scope_targets(archive_root, args.gateway, args.scope_mode, args.agent):
        log_path = root / "logs" / f"{day}.md"
        if not log_path.exists():
            continue
        for i, line in enumerate(log_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if pattern.search(line):
                hits.append({"scope": scope_key, "line": i, "text": line, "path": str(log_path)})
                if len(hits) >= args.limit:
                    break
        if len(hits) >= args.limit:
            break

    if args.format == "json":
        print(json.dumps({"day": day, "query": args.query, "hits": hits}, ensure_ascii=False, indent=2))
        return

    print(f"CAS Search | day={day} | scope={args.scope_mode} | query={args.query}")
    if not hits:
        print("(no hits)")
        return
    for h in hits:
        print(f"- [{h['scope']}] {h['path']}#{h['line']}: {h['text']}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CAS inspect/report/search helper")
    p.add_argument("--archive-root", default="~/.openclaw/chat-archive")

    sub = p.add_subparsers(dest="cmd", required=True)

    p_report = sub.add_parser("report", help="daily backup/report summary")
    p_report.add_argument("--day", help="YYYY-MM-DD, default today")
    p_report.add_argument("--gateway", default="all", help="gateway name or all")
    p_report.add_argument("--scope-mode", choices=["gateway", "agent"], default="gateway")
    p_report.add_argument("--agent", default="all", help="agent id or all (when scope-mode=agent)")
    p_report.add_argument("--format", choices=["text", "json"], default="text")
    p_report.set_defaults(func=cmd_report)

    p_search = sub.add_parser("search", help="search daily log lines")
    p_search.add_argument("--day", help="YYYY-MM-DD, default today")
    p_search.add_argument("--gateway", default="all", help="gateway name or all")
    p_search.add_argument("--scope-mode", choices=["gateway", "agent"], default="gateway")
    p_search.add_argument("--agent", default="all", help="agent id or all (when scope-mode=agent)")
    p_search.add_argument("--query", required=True, help="regex query")
    p_search.add_argument("--ignore-case", action="store_true")
    p_search.add_argument("--limit", type=int, default=50)
    p_search.add_argument("--format", choices=["text", "json"], default="text")
    p_search.set_defaults(func=cmd_search)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
