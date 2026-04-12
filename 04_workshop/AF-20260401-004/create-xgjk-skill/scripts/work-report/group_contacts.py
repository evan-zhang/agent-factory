#!/usr/bin/env python3
"""
CWork 个人联系人分组管理

功能：
- list: 列出分组及成员
- create: 新建分组
- rename: 重命名分组
- members: 分组增删成员（按姓名解析 empId）
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List, Optional

import requests

BASE_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api"


def get_app_key(cli_app_key: Optional[str]) -> str:
    key = (cli_app_key or os.getenv("BP_APP_KEY") or os.getenv("COMPANY_APP_KEY") or "").strip()
    if not key:
        raise SystemExit("缺少 appKey：请使用 --app-key 或设置 BP_APP_KEY/COMPANY_APP_KEY")
    return key


def _headers(app_key: str) -> Dict[str, str]:
    return {"appKey": app_key, "Content-Type": "application/json"}


def _split_csv(text: str) -> List[str]:
    if not text:
        return []
    for sep in ["，", "、", ";", "；"]:
        text = text.replace(sep, ",")
    return [x.strip() for x in text.split(",") if x.strip()]


def query_groups(app_key: str, check_emp_id: Optional[int] = None) -> List[Dict]:
    payload = {}
    if check_emp_id is not None:
        payload["checkEmpId"] = int(check_emp_id)
    r = requests.post(f"{BASE_URL}/cwork-user/group/queryTargetUserGroups", headers=_headers(app_key), json=payload, timeout=20)
    j = r.json()
    if j.get("resultCode") != 1:
        raise SystemExit(f"查询分组失败: {j}")
    return j.get("data") or []


def search_emp(app_key: str, name: str) -> List[int]:
    r = requests.get(
        f"{BASE_URL}/cwork-user/searchEmpByName",
        params={"searchKey": name},
        headers={"appKey": app_key},
        timeout=20,
    )
    j = r.json()
    if j.get("resultCode") != 1:
        return []
    inside = (((j.get("data") or {}).get("inside") or {}).get("empList") or [])
    exact = [x for x in inside if str(x.get("name", "")).strip() == name]
    rows = exact if exact else inside
    out = []
    for x in rows:
        try:
            out.append(int(x.get("id")))
        except Exception:
            pass
    # 去重
    return list(dict.fromkeys(out))


def resolve_group_id(app_key: str, group_name: str) -> int:
    groups = query_groups(app_key)
    exact = [g for g in groups if str(g.get("groupName", "")).strip() == group_name]
    cands = exact if exact else [g for g in groups if group_name in str(g.get("groupName", ""))]
    if len(cands) != 1:
        brief = [{"groupId": g.get("groupId"), "groupName": g.get("groupName")} for g in cands[:8]]
        raise SystemExit(f"分组匹配不唯一: {group_name}, candidates={brief}")
    return int(cands[0].get("groupId"))


def cmd_list(args: argparse.Namespace) -> None:
    app_key = get_app_key(args.app_key)
    groups = query_groups(app_key)
    print(json.dumps(groups, ensure_ascii=False, indent=2))


def cmd_create(args: argparse.Namespace) -> None:
    app_key = get_app_key(args.app_key)
    r = requests.post(
        f"{BASE_URL}/cwork-user/group/saveOrUpdatePersonalGroup",
        headers=_headers(app_key),
        json={"name": args.name},
        timeout=20,
    )
    print(r.text)


def cmd_rename(args: argparse.Namespace) -> None:
    app_key = get_app_key(args.app_key)
    gid = resolve_group_id(app_key, args.group)
    r = requests.post(
        f"{BASE_URL}/cwork-user/group/saveOrUpdatePersonalGroup",
        headers=_headers(app_key),
        json={"id": gid, "name": args.new_name},
        timeout=20,
    )
    print(r.text)


def cmd_members(args: argparse.Namespace) -> None:
    app_key = get_app_key(args.app_key)
    gid = resolve_group_id(app_key, args.group)

    add_ids = []
    for n in _split_csv(args.add):
        ids = search_emp(app_key, n)
        if len(ids) == 1:
            add_ids.extend(ids)
        elif len(ids) == 0:
            raise SystemExit(f"成员未找到: {n}")
        else:
            raise SystemExit(f"成员匹配不唯一: {n}, empIds={ids[:8]}")

    remove_ids = []
    for n in _split_csv(args.remove):
        ids = search_emp(app_key, n)
        if len(ids) == 1:
            remove_ids.extend(ids)
        elif len(ids) == 0:
            raise SystemExit(f"成员未找到: {n}")
        else:
            raise SystemExit(f"成员匹配不唯一: {n}, empIds={ids[:8]}")

    payload = {"groupId": gid, "addEmpIds": list(dict.fromkeys(add_ids)), "removeEmpIds": list(dict.fromkeys(remove_ids))}
    r = requests.post(f"{BASE_URL}/cwork-user/group/manageGroupMembers", headers=_headers(app_key), json=payload, timeout=20)
    print(r.text)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CWork 个人联系人分组管理")
    sub = p.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("list", help="列出分组")
    p1.add_argument("--app-key", default="")
    p1.set_defaults(func=cmd_list)

    p2 = sub.add_parser("create", help="新建分组")
    p2.add_argument("--name", required=True)
    p2.add_argument("--app-key", default="")
    p2.set_defaults(func=cmd_create)

    p3 = sub.add_parser("rename", help="重命名分组")
    p3.add_argument("--group", required=True, help="原分组名")
    p3.add_argument("--new-name", required=True)
    p3.add_argument("--app-key", default="")
    p3.set_defaults(func=cmd_rename)

    p4 = sub.add_parser("members", help="增删成员")
    p4.add_argument("--group", required=True)
    p4.add_argument("--add", default="", help="新增姓名，逗号分隔")
    p4.add_argument("--remove", default="", help="移除姓名，逗号分隔")
    p4.add_argument("--app-key", default="")
    p4.set_defaults(func=cmd_members)

    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
