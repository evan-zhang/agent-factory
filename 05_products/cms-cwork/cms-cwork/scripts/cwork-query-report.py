#!/usr/bin/env python3
"""
CWork Query Reports - Agent-First

Modes: inbox / outbox / unread / detail / node-detail / sender-history / keyword-search / pending / my-sent

Usage:
  python3 scripts/cwork-query-report.py --mode inbox [--page-size 20]
  python3 scripts/cwork-query-report.py --mode detail --report-id <id>
  python3 scripts/cwork-query-report.py --mode node-detail --report-id <id>
  python3 scripts/cwork-query-report.py --mode sender-history --sender-emp-id <empId>
  python3 scripts/cwork-query-report.py --mode keyword-search --keyword "公章"
  python3 scripts/cwork-query-report.py --mode pending
  python3 scripts/cwork-query-report.py --mode unread
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cwork_client import CWorkClient, make_client, CWorkError


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="CWork query reports (Agent-First)")
    parser.add_argument("--mode", required=True,
                        choices=["inbox", "outbox", "unread", "detail", "node-detail", "sender-history", "keyword-search", "pending", "my-sent"])
    parser.add_argument("--page-index", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--report-id", help="Report ID (required for detail/node-detail)")
    parser.add_argument("--sender-emp-id", help="Sender employee ID (required for sender-history)")
    parser.add_argument("--keyword", help="Search keyword (required for keyword-search)")
    parser.add_argument("--days", type=int, default=90, help="Days to look back (default 90)")
    parser.add_argument("--report-type", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--status", type=int, help="Read status: 0=unread 1=read")
    parser.add_argument("--keyword-filter", help="Legacy: Keyword filter")
    parser.add_argument("--start-date", help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", help="End date YYYY-MM-DD")
    return parser.parse_args(argv)


def _parse_date(value):
    if value is None:
        return None
    from datetime import datetime
    try:
        return int(datetime.strptime(value, "%Y-%m-%d").timestamp() * 1000)
    except ValueError:
        return None


def _die(msg):
    print(json.dumps({"success": False, "error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


def main():
    args = parse_args()
    try:
        client = make_client()
    except CWorkError as e:
        _die(str(e))

    try:
        if args.mode == "detail":
            if not args.report_id:
                _die("--report-id is required for detail mode")
            data = client.get_report_info(args.report_id)
            print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))
            return

        if args.mode == "node-detail":
            if not args.report_id:
                _die("--report-id is required for node-detail mode")
            data = client.get_report_node_detail(args.report_id)
            print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))
            return

        if args.mode == "sender-history":
            if not args.sender_emp_id:
                _die("--sender-emp-id is required for sender-history mode")
            data = client.get_sender_history(
                sender_emp_id=args.sender_emp_id,
                days=args.days,
                max_count=args.page_size
            )
            print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))
            return

        if args.mode == "keyword-search":
            if not args.keyword:
                _die("--keyword is required for keyword-search mode")
            data = client.search_reports_by_keyword(
                keyword=args.keyword,
                days=args.days,
                max_count=args.page_size
            )
            print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))
            return

        if args.mode == "unread":
            data = client.get_unread_list(args.page_index, args.page_size)
            print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))
            return

        read_status = args.status
        if args.mode == "pending":
            read_status = 0

        if args.mode in ("inbox", "pending"):
            data = client.get_inbox_list(
                page_size=args.page_size, page_index=args.page_index,
                report_record_type=args.report_type, read_status=read_status,
                begin_time=_parse_date(args.start_date), end_time=_parse_date(args.end_date))
        else:
            data = client.get_outbox_list(
                page_size=args.page_size, page_index=args.page_index,
                report_record_type=args.report_type,
                begin_time=_parse_date(args.start_date), end_time=_parse_date(args.end_date))

        print(json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2))

    except CWorkError as e:
        _die(str(e))


if __name__ == "__main__":
    main()
