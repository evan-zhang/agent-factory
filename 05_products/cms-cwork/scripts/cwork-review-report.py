#!/usr/bin/env python3
"""
CWork Review Report — 审阅/回复汇报脚本

Modes:
  reply     — 回复/点评汇报
  mark-read — 标记已读
  pending   — 查询待审汇报

Usage:
  python cwork-review-report.py --mode reply --report-id <id> --reply "内容"
  python cwork-review-report.py --mode reply --report-id <id> --reply "内容" --at "张三"
  python cwork-review-report.py --mode mark-read --report-id <id>
  python cwork-review-report.py --mode pending [--page-size 20]

Output: JSON to stdout, error JSON to stderr + exit 1
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cwork_client import CWorkClient, make_client, CWorkError, output_json, output_error, resolve_names_to_empids


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="CWork 审阅汇报")
    parser.add_argument("--mode", required=True,
                        choices=["reply", "mark-read", "pending"],
                        help="操作模式")
    parser.add_argument("--report-id", help="汇报ID（reply/mark-read模式必填）")
    parser.add_argument("--reply", help="回复内容（reply模式必填）")
    parser.add_argument("--at", help="被@人的姓名（reply模式可选）")
    parser.add_argument("--page-index", type=int, default=1, help="页码（默认1）")
    parser.add_argument("--page-size", type=int, default=20, help="每页大小（默认20）")
    parser.add_argument("--report-type", type=int, choices=[1, 2, 3, 4, 5],
                        help="汇报类型筛选")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    parser.add_argument("--dry-run", action="store_true", help="干跑模式")
    return parser.parse_args(argv)


def main():
    args = parse_args()

    if args.dry_run:
        preview = {
            "mode": args.mode,
            "reportId": args.report_id,
            "reply": args.reply,
            "at": args.at,
        }
        print("=== DRY RUN PREVIEW ===", file=sys.stderr)
        print(json.dumps(preview, ensure_ascii=False, indent=2), file=sys.stderr)
        output_json({"success": True, "message": "Dry run — no actual API call made"})
        return

    if args.interactive:
        from cwork_client import interactive_confirm
        desc = f"{args.mode} 汇报 (report_id={args.report_id})"
        if not interactive_confirm(f"review_{args.mode}", desc):
            output_json({"success": True, "message": "Skipped by user"})
            return

    try:
        client = make_client()
    except CWorkError as e:
        output_error(str(e))

    try:
        if args.mode == "reply":
            if not args.report_id:
                output_error("--report-id is required for reply mode")
            if not args.reply:
                output_error("--reply is required for reply mode")

            at_emp_ids = None
            if args.at:
                at_emp_ids = resolve_names_to_empids(client, [args.at])

            reply_id = client.reply_report(
                report_record_id=args.report_id,
                content_html=f"<p>{args.reply}</p>",
                add_emp_id_list=at_emp_ids,
                send_msg=True,
            )
            output_json({"success": True, "replyId": reply_id, "message": "Reply submitted successfully"})

        elif args.mode == "mark-read":
            if not args.report_id:
                output_error("--report-id is required for mark-read mode")
            client.mark_report_read(args.report_id)
            output_json({"success": True, "message": f"Report {args.report_id} marked as read"})

        elif args.mode == "pending":
            result = client.get_inbox_list(
                page_size=args.page_size,
                page_index=args.page_index,
                report_record_type=args.report_type,
                read_status=0,
            )
            output_json({"success": True, "data": result})

    except CWorkError as e:
        output_error(str(e))
    except Exception as e:
        output_error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
