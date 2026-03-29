#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


def today() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d")


def week_of(day: str) -> str:
    d = dt.datetime.fromisoformat(day)
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def month_of(day: str) -> str:
    d = dt.datetime.fromisoformat(day)
    return d.strftime("%Y-%m")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            items.append(json.loads(s))
        except Exception:
            continue
    return items


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def cas_inspect_json(script_dir: Path, archive_root: str, day: str, scope_mode: str, gateway: str, agent: str) -> dict:
    import subprocess, sys

    cmd = [
        sys.executable,
        str(script_dir / "cas_inspect.py"),
        "--archive-root",
        archive_root,
        "report",
        "--day",
        day,
        "--gateway",
        gateway,
        "--scope-mode",
        scope_mode,
        "--agent",
        agent,
        "--format",
        "json",
    ]
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def suggestions_from_summary(summary: dict) -> list[str]:
    s = summary or {}
    inbound = int(s.get("inbound", 0))
    outbound = int(s.get("outbound", 0))
    sessions = int(s.get("sessions", 0))
    assets = int(s.get("assets", 0))

    tips: list[str] = []
    if outbound < inbound:
        tips.append("提升一次响应命中率：减少追问轮次，优先给出可执行结论。")
    if sessions > 5:
        tips.append("优化上下文连续性：减少同主题跨会话碎片化，优先主题化归并。")
    if assets > 20:
        tips.append("优化附件策略：大附件优先摘要化后再深查，控制存储增长。")

    if not tips:
        tips = [
            "继续强化用户偏好命中：默认给建议而非仅列选项。",
            "每次复盘补充 1 条可复用操作规则并写入持久记忆。",
            "对高频问题建立快捷处理模板，减少重复沟通成本。",
        ]

    while len(tips) < 3:
        tips.append("补充 1 条基于今日偏差的可执行改进动作。")

    return tips[:5]


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def cmd_daily(args: argparse.Namespace) -> None:
    day = args.day or today()
    script_dir = Path(__file__).parent
    report = cas_inspect_json(script_dir, args.archive_root, day, args.scope_mode, args.gateway, args.agent)
    tips = suggestions_from_summary(report.get("summary", {}))

    out_path = Path(args.out_dir).expanduser() / "daily" / f"{day}.md"

    lines = [
        f"# Daily Review — {day}",
        "",
        f"- scopeMode: {args.scope_mode}",
        f"- gateway: {args.gateway}",
        f"- agent: {args.agent}",
        "",
        "## 1) 备份概览",
        f"- sessions: {report['summary']['sessions']}",
        f"- inbound: {report['summary']['inbound']}",
        f"- outbound: {report['summary']['outbound']}",
        f"- assets: {report['summary']['assets']}",
        f"- logBytes: {report['summary']['logBytes']}",
        f"- assetBytes: {report['summary']['assetBytes']}",
        "",
        "## 2) 今日关键学习（最重要）",
        "- 问题修复沉淀（Problem -> Rule）：",
        "- 预期偏差校正（Mismatch -> Preference）：",
        "- 用户模式更新（Pattern -> Twin）：",
        "",
        "## 3) AI能力改进建议（至少3条）",
    ]
    for t in tips:
        lines.append(f"- {t}")

    lines.extend([
        "",
        "## 4) 经验分享状态",
        "- 是否已分享：待检查 SHARE-LOG.jsonl",
        "- 默认策略：未分享优先；已分享则跳过，除非强制分享",
        "",
    ])

    write_markdown(out_path, "\n".join(lines))
    print(f"daily review written: {out_path}")


def cmd_weekly(args: argparse.Namespace) -> None:
    key = args.week or week_of(args.day or today())
    out_path = Path(args.out_dir).expanduser() / "weekly" / f"{key}.md"

    text = f"""# Weekly Review — {key}

## 1) 本周主线进展
- 

## 2) 重复问题 Top3
- 

## 3) 本周学习沉淀
- Problem -> Rule:
- Mismatch -> Preference:
- Pattern -> Twin:

## 4) 下周优化动作
- 
"""
    write_markdown(out_path, text)
    print(f"weekly review written: {out_path}")


def cmd_monthly(args: argparse.Namespace) -> None:
    key = args.month or month_of(args.day or today())
    out_path = Path(args.out_dir).expanduser() / "monthly" / f"{key}.md"

    text = f"""# Monthly Review — {key}

## 1) 月度能力进展
- 

## 2) 数字分身逼近度评估
- 

## 3) 系统性问题与优化路线
- 

## 4) 下月计划
- 
"""
    write_markdown(out_path, text)
    print(f"monthly review written: {out_path}")


def cmd_share_status(args: argparse.Namespace) -> None:
    log_path = Path(args.share_log).expanduser()
    items = read_jsonl(log_path)
    found = [x for x in items if x.get("period") == args.period and x.get("key") == args.key]

    if not found:
        print("NOT_SHARED")
        return

    last = found[-1]
    print(json.dumps({"status": "SHARED", "record": last}, ensure_ascii=False, indent=2))


def cmd_mark_shared(args: argparse.Namespace) -> None:
    log_path = Path(args.share_log).expanduser()
    obj = {
        "period": args.period,
        "key": args.key,
        "skill": args.skill,
        "shared": True,
        "channel": args.channel,
        "sharedAt": dt.datetime.now().astimezone().isoformat(),
        "messageId": args.message_id,
        "forced": bool(args.forced),
    }
    append_jsonl(log_path, obj)
    print("OK")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CAS manual review/share helper")

    sub = p.add_subparsers(dest="cmd", required=True)

    common_review = argparse.ArgumentParser(add_help=False)
    common_review.add_argument("--archive-root", default="~/.openclaw/chat-archive")
    common_review.add_argument("--out-dir", default="./design/reviews")
    common_review.add_argument("--scope-mode", choices=["gateway", "agent"], default="agent")
    common_review.add_argument("--gateway", default="all")
    common_review.add_argument("--agent", default="all")
    common_review.add_argument("--day", help="YYYY-MM-DD")

    p_daily = sub.add_parser("daily", parents=[common_review], help="generate daily review markdown")
    p_daily.set_defaults(func=cmd_daily)

    p_week = sub.add_parser("weekly", parents=[common_review], help="generate weekly review markdown")
    p_week.add_argument("--week", help="YYYY-Www")
    p_week.set_defaults(func=cmd_weekly)

    p_month = sub.add_parser("monthly", parents=[common_review], help="generate monthly review markdown")
    p_month.add_argument("--month", help="YYYY-MM")
    p_month.set_defaults(func=cmd_monthly)

    p_status = sub.add_parser("share-status", help="check if period/key already shared")
    p_status.add_argument("--share-log", default="./design/SHARE-LOG.jsonl")
    p_status.add_argument("--period", choices=["daily", "weekly", "monthly"], required=True)
    p_status.add_argument("--key", required=True)
    p_status.set_defaults(func=cmd_share_status)

    p_mark = sub.add_parser("mark-shared", help="record share action")
    p_mark.add_argument("--share-log", default="./design/SHARE-LOG.jsonl")
    p_mark.add_argument("--period", choices=["daily", "weekly", "monthly"], required=True)
    p_mark.add_argument("--key", required=True)
    p_mark.add_argument("--skill", default="cas-chat-archive")
    p_mark.add_argument("--channel", default="")
    p_mark.add_argument("--message-id", default="")
    p_mark.add_argument("--forced", action="store_true")
    p_mark.set_defaults(func=cmd_mark_shared)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
