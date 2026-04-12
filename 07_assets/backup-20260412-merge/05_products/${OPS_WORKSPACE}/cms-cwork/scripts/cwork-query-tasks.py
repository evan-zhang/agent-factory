#!/usr/bin/env python3
"""
CWork Query Tasks — 任务查询脚本

Modes:
  my       — 查询我负责的任务（进行中 status=1）
  created  — 查询我创建的任务（未启动 status=0）
  team     — 查询团队任务（进行中 status=1）
  assigned — 查询分配给我的任务
  detail   — 查看任务详情（需 --task-id）
  chain    — 查看任务→汇报链路（需 --task-id）
  blocked  — 识别卡点/逾期任务
  unclosed — 识别未闭环事项
  manager  — 管理者仪表盘（需 --subordinate-ids）

Usage:
  python cwork-query-tasks.py --mode my [--page-index 1] [--page-size 20]
  python cwork-query-tasks.py --mode detail --task-id <id>
  python cwork-query-tasks.py --mode blocked [--days-threshold 7]
  python cwork-query-tasks.py --mode manager --subordinate-ids emp001,emp002

Output: JSON to stdout, error JSON to stderr + exit 1
"""

import sys
import os
import json
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cwork_client import CWorkClient, make_client, CWorkError, output_json, output_error, resolve_names_to_empids


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="CWork 任务查询")
    parser.add_argument("--mode", required=True,
                        choices=["my", "created", "team", "assigned", "detail", "chain",
                                 "blocked", "unclosed", "manager", "nudge"],
                        help="查询模式")
    parser.add_argument("--task-id", help="任务ID（detail/chain模式必填）")
    parser.add_argument("--page-index", type=int, default=1, help="页码（默认1）")
    parser.add_argument("--page-size", type=int, default=20, help="每页大小（默认20）")
    parser.add_argument("--status", type=int, choices=[0, 1, 2],
                        help="任务状态: 0=已关闭, 1=进行中, 2=未启动")
    parser.add_argument("--task-status", type=int, choices=[1, 2],
                        help="汇报状态: 1=已逾期, 2=未逾期")
    parser.add_argument("--report-status", type=int, choices=[1, 2],
                        help="汇报状态（同task-status）")
    parser.add_argument("--key-word", help="关键词搜索")
    parser.add_argument("--assignee", help="责任人姓名")
    parser.add_argument("--subordinate-ids", help="下属empId列表（逗号分隔，manager模式用）")
    parser.add_argument("--days-threshold", type=int, default=7,
                        help="未闭环天数阈值（默认7）")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    parser.add_argument("--dry-run", action="store_true", help="干跑模式")
    return parser.parse_args(argv)


def main():
    args = parse_args()

    if args.dry_run:
        preview = {
            "mode": args.mode,
            "params": {
                "pageIndex": args.page_index,
                "pageSize": args.page_size,
                "status": args.status,
                "taskStatus": args.task_status,
                "reportStatus": args.report_status,
                "keyWord": args.key_word,
                "assignee": args.assignee,
                "subordinateIds": args.subordinate_ids,
                "daysThreshold": args.days_threshold,
            }
        }
        print("=== DRY RUN PREVIEW ===", file=sys.stderr)
        print(json.dumps(preview, ensure_ascii=False, indent=2), file=sys.stderr)
        output_json({"success": True, "message": "Dry run — no actual API call made"})
        return

    if args.interactive:
        from cwork_client import interactive_confirm
        desc = f"查询任务 (mode={args.mode}, page={args.page_index})"
        if not interactive_confirm(f"query_task_{args.mode}", desc):
            output_json({"success": True, "message": "Skipped by user"})
            return

    try:
        client = make_client()
    except CWorkError as e:
        output_error(str(e))

    try:
        if args.mode in ("detail", "chain"):
            if not args.task_id:
                output_error("--task-id is required for detail/chain mode")
            result = client.get_simple_plan_and_report_info(args.task_id)
            output_json({"success": True, "data": result})

        elif args.mode == "blocked":
            threshold_ms = args.days_threshold * 24 * 60 * 60 * 1000
            now_ms = int(datetime.now().timestamp() * 1000)
            result = client.search_task_page(
                page_size=args.page_size,
                page_index=args.page_index,
                report_status=1,
                key_word=args.key_word,
            )
            items = result if isinstance(result, list) else result.get("list", [])
            blocked = [
                item for item in items
                if item.get("endTime") and (now_ms - item.get("endTime", 0)) > threshold_ms
            ]
            output_json({"success": True, "data": blocked, "total": len(blocked)})

        elif args.mode == "unclosed":
            result = client.search_task_page(
                page_size=args.page_size,
                page_index=args.page_index,
                report_status=2,
                key_word=args.key_word,
            )
            output_json({"success": True, "data": result})

        elif args.mode == "manager":
            if not args.subordinate_ids:
                output_error("--subordinate-ids is required for manager mode")
            emp_ids = [e.strip() for e in args.subordinate_ids.split(",") if e.strip()]
            result = client.search_task_page(
                page_size=args.page_size,
                page_index=args.page_index,
                emp_id_list=emp_ids,
                status=args.status,
                key_word=args.key_word,
            )
            output_json({"success": True, "data": result})

        elif args.mode in ("my", "assigned"):
            status = args.status if args.status is not None else 1
            if args.assignee:
                emp_ids = resolve_names_to_empids(client, [args.assignee])
            else:
                emp_ids = None
            result = client.search_task_page(
                page_size=args.page_size,
                page_index=args.page_index,
                status=status,
                emp_id_list=emp_ids,
                key_word=args.key_word,
            )
            output_json({"success": True, "data": result})

        elif args.mode == "created":
            status = args.status if args.status is not None else 0
            result = client.search_task_page(
                page_size=args.page_size,
                page_index=args.page_index,
                status=status,
                key_word=args.key_word,
            )
            output_json({"success": True, "data": result})

        elif args.mode == "team":
            status = args.status if args.status is not None else 1
            result = client.search_task_page(
                page_size=args.page_size,
                page_index=args.page_index,
                status=status,
                key_word=args.key_word,
            )
            output_json({"success": True, "data": result})

        elif args.mode == "nudge":
            result = client.search_task_page(
                page_size=args.page_size,
                page_index=args.page_index,
                report_status=1,
                key_word=args.key_word,
            )
            output_json({"success": True, "data": result, "message": "Use --emp-id with cwork-nudge-report.py to send nudge"})

    except CWorkError as e:
        output_error(str(e))
    except Exception as e:
        output_error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
