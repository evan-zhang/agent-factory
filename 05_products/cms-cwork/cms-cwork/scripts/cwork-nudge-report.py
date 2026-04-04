#!/usr/bin/env python3
"""
CWork Nudge Report — 催办通知脚本

Modes:
  list   — 列出未闭环事项清单（用于催收）
  nudge  — 发送催办通知

Usage:
  python cwork-nudge-report.py --mode list [--days-threshold 7]
  python cwork-nudge-report.py --mode nudge --emp-id <empId> --task-main "任务名" --deadline 2026-04-10 --content "催办内容"

Output: JSON to stdout, error JSON to stderr + exit 1
"""

import sys
import os
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cwork_client import (CWorkClient, make_client, CWorkError,
                           output_json, output_error, parse_deadline, resolve_names_to_empids)


REPORT_TYPE_ID = 12  # 催收汇报


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="CWork 催办通知")
    parser.add_argument("--mode", required=True, choices=["list", "nudge"],
                        help="操作模式: list=列出未闭环, nudge=发送催办")
    parser.add_argument("--emp-id", help="催办对象 empId（nudge模式必填）")
    parser.add_argument("--task-main", help="任务名称（nudge模式必填）")
    parser.add_argument("--deadline", help="截止日期 YYYY-MM-DD 或毫秒时间戳")
    parser.add_argument("--content", help="催办内容描述")
    parser.add_argument("--target", help="目标描述")
    parser.add_argument("--remind-style", choices=["polite", "normal"], default="polite",
                        help="催办风格（默认polite）")
    parser.add_argument("--days-threshold", type=int, default=7,
                        help="未闭环天数阈值（默认7天）")
    parser.add_argument("--assignee", help="责任人姓名（用于解析empId）")
    parser.add_argument("--page-index", type=int, default=1, help="页码（默认1）")
    parser.add_argument("--page-size", type=int, default=50, help="每页大小（默认50）")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    parser.add_argument("--dry-run", action="store_true", help="干跑模式")
    return parser.parse_args(argv)


def build_nudge_content(task_main: str, deadline: str | None, content: str | None,
                        style: str) -> str:
    """Build HTML nudge content based on style."""
    if style == "polite":
        body = f"""<p>您好，您有任务需要关注：</p>
<p><strong>📌 任务名称：</strong>{task_main}</p>"""
        if deadline:
            body += f"<p><strong>⏰ 截止日期：</strong>{deadline}</p>"
        if content:
            body += f"<p><strong>📝 详情：</strong>{content}</p>"
        body += "<p>请及时处理，如有疑问请联系我。谢谢！</p>"
    else:
        body = f"""<p>【催办】任务：{task_main}</p>"""
        if deadline:
            body += f"<p>截止日期：{deadline}</p>"
        if content:
            body += f"<p>详情：{content}</p>"
        body += "<p>请尽快处理。</p>"
    return body


def main():
    args = parse_args()

    if args.dry_run:
        preview = {
            "mode": args.mode,
            "empId": args.emp_id,
            "taskMain": args.task_main,
            "deadline": args.deadline,
            "content": args.content,
            "target": args.target,
            "remindStyle": args.remind_style,
            "daysThreshold": args.days_threshold,
            "assignee": args.assignee,
        }
        print("=== DRY RUN PREVIEW ===", file=sys.stderr)
        print(json.dumps(preview, ensure_ascii=False, indent=2), file=sys.stderr)
        output_json({"success": True, "message": "Dry run — no actual API call made"})
        return

    if args.interactive:
        from cwork_client import interactive_confirm
        desc = f"催办任务 (mode={args.mode}, empId={args.emp_id})"
        if not interactive_confirm(f"nudge_{args.mode}", desc):
            output_json({"success": True, "message": "Skipped by user"})
            return

    try:
        client = make_client()
    except CWorkError as e:
        output_error(str(e))

    try:
        if args.mode == "list":
            threshold_ms = args.days_threshold * 24 * 60 * 60 * 1000
            now_ms = int(datetime.now().timestamp() * 1000)
            result = client.search_task_page(
                page_size=args.page_size,
                page_index=args.page_index,
                report_status=1,
            )
            items = result if isinstance(result, list) else result.get("list", [])
            unclosed = [
                item for item in items
                if item.get("endTime") and (now_ms - item.get("endTime", 0)) > threshold_ms
            ]
            output_json({
                "success": True,
                "data": unclosed,
                "total": len(unclosed),
                "daysThreshold": args.days_threshold,
                "message": f"Found {len(unclosed)} unclosed items older than {args.days_threshold} days"
            })

        elif args.mode == "nudge":
            if not args.emp_id and not args.assignee:
                output_error("--emp-id or --assignee is required for nudge mode")
            if not args.task_main:
                output_error("--task-main is required for nudge mode")

            emp_id = args.emp_id
            if args.assignee and not args.emp_id:
                emp_ids = resolve_names_to_empids(client, [args.assignee])
                emp_id = emp_ids[0]

            deadline_str = args.deadline if args.deadline else None
            nudge_content = build_nudge_content(
                args.task_main,
                deadline_str,
                args.content,
                args.remind_style
            )

            result = client.submit_report(
                main=f"【催办】{args.task_main}",
                content_html=nudge_content,
                type_id=REPORT_TYPE_ID,
                accept_emp_id_list=[emp_id],
                report_level_list=[
                    {
                        "level": 12,
                        "type": "催收汇报",
                        "nodeName": "催收汇报",
                        "levelUserList": [{"empId": emp_id}]
                    }
                ],
            )
            output_json({
                "success": True,
                "reportId": result.get("id"),
                "empId": emp_id,
                "message": f"Nudge sent to empId={emp_id} for task: {args.task_main}"
            })

    except CWorkError as e:
        output_error(str(e))
    except Exception as e:
        output_error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
