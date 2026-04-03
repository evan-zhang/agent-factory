#!/usr/bin/env python3
"""
CWork Create Task - Agent-First

Usage:
  python3 scripts/cwork-create-task.py --task-main "name" --content "desc" --assignee "person" --deadline 2026-04-10
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cwork_client import make_client, CWorkError, parse_deadline, resolve_names_to_empids

_DEFAULT_MS = int(__import__("datetime").datetime.now().timestamp() * 1000) + 7 * 86400000


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="CWork create task (Agent-First)")
    p.add_argument("--task-main", required=True, help="Task name")
    p.add_argument("--deadline", help="Deadline YYYY-MM-DD or ms timestamp (default 7d)")
    p.add_argument("--content", required=True, help="Task description")
    p.add_argument("--target", help="Target description")
    p.add_argument("--assignee", help="Owner name")
    p.add_argument("--assistant", help="Assistant names (comma-separated)")
    p.add_argument("--supervisor", help="Supervisor name")
    p.add_argument("--copy", help="CC names (comma-separated)")
    p.add_argument("--observer", help="Observer names (comma-separated)")
    p.add_argument("--report-to", help="Report-to name")
    p.add_argument("--push-now", type=lambda x: x.lower() == "true", default=True)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def _comma(val):
    if not val:
        return None
    return [v.strip() for v in val.split(",") if v.strip()]


def _die(msg):
    print(json.dumps({"success": False, "error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


def main():
    args = parse_args()
    try:
        client = make_client()
    except CWorkError as e:
        _die(str(e))

    def _resolve(name_or_list):
        names = _comma(name_or_list) if isinstance(name_or_list, str) else name_or_list
        if not names:
            return None
        return resolve_names_to_empids(client, names)

    dl = parse_deadline(args.deadline) if args.deadline else _DEFAULT_MS
    info = dict(assignee=args.assignee, assistant=args.assistant, supervisor=args.supervisor,
                copy=args.copy, observer=args.observer, reportTo=args.report_to, deadlineMs=dl)

    if args.dry_run:
        print(json.dumps({"success": True, "dryRun": True,
            "task": dict(main=args.task_main, content=args.content, target=args.target or args.content,
                         deadline=args.deadline, deadlineMs=dl, pushNow=args.push_now),
            "resolved": info}, ensure_ascii=False, indent=2))
        return

    try:
        pid = client.create_plan(
            main=args.task_main, needful=args.content, target=args.target or "", end_time=dl,
            owner_emp_id_list=_resolve(args.assignee), assist_emp_id_list=_resolve(args.assistant),
            supervisor_emp_id_list=_resolve(args.supervisor), copy_emp_id_list=_resolve(args.copy),
            observer_emp_id_list=_resolve(args.observer), report_emp_id_list=_resolve(args.report_to),
            push_now=args.push_now)
        print(json.dumps({"success": True, "planId": pid,
            "task": dict(main=args.task_main, deadline=args.deadline, deadlineMs=dl),
            "resolved": info}, ensure_ascii=False, indent=2))
    except CWorkError as e:
        _die(str(e))


if __name__ == "__main__":
    main()
