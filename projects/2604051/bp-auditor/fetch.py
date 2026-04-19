#!/usr/bin/env python3
"""
bp-auditor data fetcher.

Fetches complete BP data and outputs structured JSON.
Handles the BP system hierarchy:
- BP Goal: use get_goal_detail
- KR (KeyResult): use get_key_result_detail
- Initiative (Action): use get_action_detail

Usage:
    python3 skills/bp-auditor/fetch.py --goal-code G-1 -o /tmp/bp-g1.json
    python3 skills/bp-auditor/fetch.py --bp-id 2000831992328945666
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import bp_client from bp-manager skill
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "bp-manager" / "scripts"))
    from bp_client import BPClient
except ImportError as exc:
    print(f"Error: cannot import bp_client: {exc}", file=sys.stderr)
    print("Hint: bp-manager skill must be installed at skills/bp-manager/", file=sys.stderr)
    sys.exit(1)

# Known group ID for 玄关健康 (G)
_XUANJIAN_GUARD_GROUP_ID = "1998216739737055234"


def collect_people(task_users: Optional[List[Dict]]) -> List[str]:
    """Extract people names from taskUsers field."""
    if not task_users:
        return []
    names = []
    for tu in task_users:
        for emp in tu.get("empList", []):
            names.append(emp.get("name", ""))
    return [n for n in names if n]


def resolve_goal_code(client: BPClient, goal_code: str) -> str:
    """
    Resolve a goal code like G-1 to a goal ID.

    Strategy: search the G group simple_tree and call get_goal_detail on each goal
    to check fullLevelNumber.
    """
    tree = client.get_simple_tree(_XUANJIAN_GUARD_GROUP_ID)
    for item in tree.get("data", []):
        if item.get("type") != "目标":
            continue
        goal_id = item["id"]
        detail = client.get_goal_detail(goal_id)
        data = detail.get("data", {}) if isinstance(detail, dict) else detail
        full_code = data.get("fullLevelNumber", "") if isinstance(data, dict) else ""
        if full_code == goal_code:
            return goal_id
        # Also check children (KRs under the goal)
        for child in item.get("children", []):
            child_id = child.get("id", "")
            child_detail = client.get_goal_detail(child_id)
            child_data = child_detail.get("data", {}) if isinstance(child_detail, dict) else child_detail
            child_code = child_data.get("fullLevelNumber", "") if isinstance(child_data, dict) else ""
            if child_code == goal_code:
                return child_id

    raise ValueError(f"Cannot resolve goal code '{goal_code}'")


def fetch_kr_detail(client: BPClient, kr_id: str) -> Dict[str, Any]:
    """
    Fetch KR (KeyResult) detail using get_key_result_detail.
    KR has measureStandard and is the only node that should have it.
    """
    raw = client.get_key_result_detail(kr_id)
    data = raw.get("data", {}) if isinstance(raw, dict) else raw
    if not isinstance(data, dict):
        return {}

    # Fetch actions (initiatives) under this KR
    raw_actions = client.list_actions(kr_id)
    actions_data = raw_actions.get("data", []) if isinstance(raw_actions, dict) else []
    actions = []
    for act in actions_data:
        act_id = act.get("id", "")
        if not act_id:
            continue
        act_detail_raw = client.get_action_detail(act_id)
        act_detail = act_detail_raw.get("data", {}) if isinstance(act_detail_raw, dict) else act_detail_raw
        if not isinstance(act_detail, dict):
            continue
        actions.append({
            "id": act_id,
            "code": act_detail.get("fullLevelNumber", ""),
            "name": act_detail.get("name", ""),
            "measureStandard": act_detail.get("measureStandard"),  # initiatives may not have ms
            "status": act_detail.get("statusDesc", ""),
            "planDateRange": act_detail.get("planDateRange", ""),
            "people": collect_people(act_detail.get("taskUsers")),
            "upstream": [
                {"id": t.get("id", ""), "name": t.get("name", ""),
                 "groupName": t.get("groupInfo", {}).get("name", "")}
                for t in act_detail.get("upwardTaskList", [])
            ],
        })

    return {
        "id": kr_id,
        "code": data.get("fullLevelNumber", ""),
        "name": data.get("name", ""),
        "measureStandard": data.get("measureStandard"),  # KR ONLY - this is the critical field
        "status": data.get("statusDesc", ""),
        "planDateRange": data.get("planDateRange", ""),
        "people": collect_people(data.get("taskUsers")),
        "upstream": [
            {"id": t.get("id", ""), "name": t.get("name", ""),
             "groupName": t.get("groupInfo", {}).get("name", "")}
            for t in data.get("upwardTaskList", [])
        ],
        "downstream": [
            {"id": t.get("id", ""), "name": t.get("name", ""),
             "groupName": t.get("groupInfo", {}).get("name", "")}
            for t in data.get("downTaskList", [])
        ],
        "actions": actions,
    }


def fetch_bp_full(client: BPClient, goal_id: str) -> Dict[str, Any]:
    """Fetch complete BP data: goal + KRs + actions."""
    # 1. Goal detail (BP node)
    raw_goal = client.get_goal_detail(goal_id)
    goal_data = raw_goal.get("data", {}) if isinstance(raw_goal, dict) else raw_goal
    if not isinstance(goal_data, dict):
        goal_data = {}

    # 2. Direct children (KRs or actions depending on level)
    children = client.get_task_children(goal_id)
    raw_children = children.get("data", []) if isinstance(children, dict) else (children or [])
    child_tasks = raw_children if isinstance(raw_children, list) else []

    # 3. For each child (KR), fetch detail using get_key_result_detail
    kr_list = []
    for child in child_tasks:
        child_id = child.get("id", "")
        if not child_id:
            continue
        # Determine if this is a KR or an Initiative by checking type
        child_type = child.get("type", "")
        if child_type == "关键成果":
            kr_detail = fetch_kr_detail(client, child_id)
            kr_list.append(kr_detail)
        elif child_type == "关键举措":
            # Direct initiative under BP (rare but possible)
            raw_init = client.get_action_detail(child_id)
            init_data = raw_init.get("data", {}) if isinstance(raw_init, dict) else raw_init
            if isinstance(init_data, dict):
                kr_list.append({
                    "id": child_id,
                    "code": init_data.get("fullLevelNumber", ""),
                    "name": init_data.get("name", ""),
                    "measureStandard": None,  # initiatives don't have measureStandard
                    "status": init_data.get("statusDesc", ""),
                    "planDateRange": init_data.get("planDateRange", ""),
                    "people": collect_people(init_data.get("taskUsers")),
                    "upstream": [
                        {"id": t.get("id", ""), "name": t.get("name", ""),
                         "groupName": t.get("groupInfo", {}).get("name", "")}
                        for t in init_data.get("upwardTaskList", [])
                    ],
                    "downstream": [
                        {"id": t.get("id", ""), "name": t.get("name", ""),
                         "groupName": t.get("groupInfo", {}).get("name", "")}
                        for t in init_data.get("downTaskList", [])
                    ],
                    "actions": [],
                })

    # 4. Upstream links (what this BP承接)
    upstream = [
        {"id": t.get("id", ""), "name": t.get("name", ""),
         "groupName": t.get("groupInfo", {}).get("name", "")}
        for t in goal_data.get("upwardTaskList", [])
    ]

    # 5. Downstream links (what this BP养)
    downstream = [
        {"id": t.get("id", ""), "name": t.get("name", ""),
         "groupName": t.get("groupInfo", {}).get("name", "")}
        for t in goal_data.get("downTaskList", [])
    ]

    return {
        "goal": {
            "id": goal_id,
            "code": goal_data.get("fullLevelNumber", goal_id),
            "name": goal_data.get("name", ""),
            "status": goal_data.get("statusDesc", ""),
            "planDateRange": goal_data.get("planDateRange", ""),
            "people": collect_people(goal_data.get("taskUsers")),
            "upstream": upstream,
            "downstream": downstream,
        },
        "keyResults": kr_list,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="bp-auditor data fetcher")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bp-id", help="BP goal ID")
    group.add_argument("--goal-code", help="BP goal code, e.g. G-1")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    client = BPClient()

    # Resolve goal_id
    if args.goal_code:
        try:
            goal_id = resolve_goal_code(client, args.goal_code)
            print(f"Resolved {args.goal_code} -> {goal_id}", file=sys.stderr)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        goal_id = args.bp_id

    # Fetch full BP data
    data = fetch_bp_full(client, goal_id)

    # Output
    output = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
