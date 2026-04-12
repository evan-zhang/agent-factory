#!/usr/bin/env python3
"""
CWork 工作汇报发送（带发送前确认单）

核心目标：
1) 先生成“发送前确认单”JSON（标题/正文/接收人/抄送人/附件）
2) 人工确认后再发送
3) 附件采用稳定路径：uploadWholeFile -> fileVOList(fileId,name,type)

用法：
  # 1) 生成确认单
  python3 send_report_with_confirm.py prepare \
    --title "玄关健康BP 月度及季度各部门填报模板" \
    --content "附件压缩包内为各部门按月及按季..." \
    --to "张成鹏,侯桐" \
    --cc "屈军利,李广智,成伟" \
    --attachments "./UAT-附件清单-20260327.txt,./CWORK-UAT-Report-20260327.md,./AF-20260327-001-UAT-Bundle-20260327.zip" \
    --out ./report-confirmation.json

  # 2) 人工确认后发送
  python3 send_report_with_confirm.py send \
    --confirm-json ./report-confirmation.json \
    --confirm-token CONFIRM_SEND
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional

import requests

BASE_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api"


@dataclass
class PersonCandidate:
    name: str
    empId: int
    personId: Optional[int]
    dept: str


@dataclass
class ResolvedPerson:
    inputName: str
    resolvedName: str
    empId: int
    personId: Optional[int]
    dept: str
    matchType: str  # exact|alias|single|contains


@dataclass
class AttachmentInfo:
    path: str
    name: str
    exists: bool
    size: int


def _split_csv(text: str) -> List[str]:
    if not text:
        return []
    for sep in ["，", "、", ";", "；"]:
        text = text.replace(sep, ",")
    return [x.strip() for x in text.split(",") if x.strip()]


def get_app_key(cli_app_key: Optional[str]) -> str:
    key = (cli_app_key or os.getenv("BP_APP_KEY") or os.getenv("COMPANY_APP_KEY") or "").strip()
    if not key:
        raise SystemExit("缺少 appKey：请使用 --app-key 或设置 BP_APP_KEY/COMPANY_APP_KEY")
    return key


def _headers(app_key: str) -> Dict[str, str]:
    return {"appKey": app_key}


def _name_aliases(name: str) -> List[str]:
    """姓名纠错候选（常见同音/误写字）。"""
    aliases = [name]
    replacements = {
        "陈": "成",
        "成": "陈",
        "丽": "利",
        "利": "丽",
        "军": "俊",
        "俊": "军",
    }
    for i, ch in enumerate(name):
        if ch in replacements:
            aliases.append(name[:i] + replacements[ch] + name[i + 1 :])

    # 再补一个末字检索，提升候选召回（如“陈伟”->“伟”）
    if len(name) >= 2:
        aliases.append(name[-1])

    # 去重保持顺序
    out: List[str] = []
    seen = set()
    for a in aliases:
        if a and a not in seen:
            seen.add(a)
            out.append(a)
    return out


def query_target_user_groups(app_key: str, check_emp_id: Optional[int] = None) -> List[Dict]:
    payload = {}
    if check_emp_id is not None:
        payload["checkEmpId"] = int(check_emp_id)
    r = requests.post(
        f"{BASE_URL}/cwork-user/group/queryTargetUserGroups",
        headers={**_headers(app_key), "Content-Type": "application/json"},
        json=payload,
        timeout=20,
    )
    j = r.json()
    if j.get("resultCode") != 1:
        return []
    data = j.get("data")
    return data if isinstance(data, list) else []


def resolve_groups(app_key: str, input_group_names: List[str]) -> Tuple[List[Dict], List[Dict], List[int]]:
    all_groups = query_target_user_groups(app_key)
    resolved: List[Dict] = []
    unresolved: List[Dict] = []
    member_ids: List[int] = []

    for name in input_group_names:
        exact = [g for g in all_groups if str(g.get("groupName", "")).strip() == name]
        cands = exact
        if not cands:
            cands = [g for g in all_groups if name in str(g.get("groupName", ""))]

        if len(cands) == 1:
            g = cands[0]
            mids = []
            for m in g.get("members") or []:
                try:
                    mids.append(int(m.get("id")))
                except Exception:
                    continue
            member_ids.extend(mids)
            resolved.append(
                {
                    "inputGroupName": name,
                    "groupId": str(g.get("groupId", "")),
                    "groupName": str(g.get("groupName", "")),
                    "memberCount": len(mids),
                }
            )
        else:
            unresolved.append(
                {
                    "inputGroupName": name,
                    "scope": "to_groups",
                    "candidates": [
                        {
                            "groupId": str(g.get("groupId", "")),
                            "groupName": str(g.get("groupName", "")),
                            "memberCount": len(g.get("members") or []),
                        }
                        for g in cands[:8]
                    ],
                }
            )

    # 去重
    uniq_member_ids = []
    seen = set()
    for x in member_ids:
        if x not in seen:
            seen.add(x)
            uniq_member_ids.append(x)

    return resolved, unresolved, uniq_member_ids


def search_inside_employees(app_key: str, name: str) -> List[PersonCandidate]:
    r = requests.get(
        f"{BASE_URL}/cwork-user/searchEmpByName",
        params={"searchKey": name},
        headers=_headers(app_key),
        timeout=20,
    )
    j = r.json()
    if j.get("resultCode") != 1:
        return []

    inside = (((j.get("data") or {}).get("inside") or {}).get("empList") or [])
    out: List[PersonCandidate] = []
    for e in inside:
        try:
            out.append(
                PersonCandidate(
                    name=str(e.get("name") or "").strip(),
                    empId=int(e.get("id")),
                    personId=(int(e.get("personId")) if e.get("personId") is not None else None),
                    dept=str(e.get("mainDept") or ""),
                )
            )
        except Exception:
            continue
    return out


def resolve_person(app_key: str, input_name: str) -> Tuple[Optional[ResolvedPerson], List[PersonCandidate]]:
    # 先查原名，再查纠错别名
    aliases = _name_aliases(input_name)
    merged: List[PersonCandidate] = []
    seen = set()
    for q in aliases:
        for c in search_inside_employees(app_key, q):
            key = (c.empId, c.name)
            if key in seen:
                continue
            seen.add(key)
            merged.append(c)

    cands = merged
    if not cands:
        return None, []

    exact = [c for c in cands if c.name == input_name]
    if len(exact) == 1:
        c = exact[0]
        return (
            ResolvedPerson(input_name, c.name, c.empId, c.personId, c.dept, "exact"),
            cands,
        )

    # 如果别名中（长度>1）存在唯一精确命中，按纠错命中处理
    alias_exact = [c for c in cands if c.name in [a for a in aliases if len(a) > 1]]
    uniq_alias = {(c.empId, c.name): c for c in alias_exact}
    if len(uniq_alias) == 1:
        c = list(uniq_alias.values())[0]
        return (
            ResolvedPerson(input_name, c.name, c.empId, c.personId, c.dept, "alias"),
            cands,
        )

    if len(cands) == 1:
        c = cands[0]
        return (
            ResolvedPerson(input_name, c.name, c.empId, c.personId, c.dept, "single"),
            cands,
        )

    contains = [c for c in cands if input_name in c.name or c.name in input_name]
    if len(contains) == 1:
        c = contains[0]
        return (
            ResolvedPerson(input_name, c.name, c.empId, c.personId, c.dept, "contains"),
            cands,
        )

    return None, cands


def collect_attachments(paths: List[str]) -> List[AttachmentInfo]:
    infos: List[AttachmentInfo] = []
    for p in paths:
        path = pathlib.Path(p).expanduser().resolve()
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
        infos.append(AttachmentInfo(path=str(path), name=path.name, exists=exists, size=size))
    return infos


def cmd_prepare(args: argparse.Namespace) -> None:
    app_key = get_app_key(args.app_key)

    to_names = _split_csv(args.to)
    to_group_names = _split_csv(args.to_groups)
    cc_names = _split_csv(args.cc)
    advisor_names = _split_csv(args.advisors)
    approver_names = _split_csv(args.approvers)

    unresolved: List[Dict] = []
    to_resolved: List[ResolvedPerson] = []
    to_group_resolved: List[Dict] = []
    to_group_emp_ids: List[int] = []
    cc_resolved: List[ResolvedPerson] = []
    advisor_resolved: List[ResolvedPerson] = []
    approver_resolved: List[ResolvedPerson] = []

    for name in to_names:
        p, cands = resolve_person(app_key, name)
        if p:
            to_resolved.append(p)
        else:
            unresolved.append({"inputName": name, "scope": "to", "candidates": [asdict(c) for c in cands[:8]]})

    if to_group_names:
        gr, gu, gids = resolve_groups(app_key, to_group_names)
        to_group_resolved.extend(gr)
        unresolved.extend(gu)
        to_group_emp_ids.extend(gids)

    for name in cc_names:
        p, cands = resolve_person(app_key, name)
        if p:
            cc_resolved.append(p)
        else:
            unresolved.append({"inputName": name, "scope": "cc", "candidates": [asdict(c) for c in cands[:8]]})

    for name in advisor_names:
        p, cands = resolve_person(app_key, name)
        if p:
            advisor_resolved.append(p)
        else:
            unresolved.append({"inputName": name, "scope": "advisors", "candidates": [asdict(c) for c in cands[:8]]})

    for name in approver_names:
        p, cands = resolve_person(app_key, name)
        if p:
            approver_resolved.append(p)
        else:
            unresolved.append({"inputName": name, "scope": "approvers", "candidates": [asdict(c) for c in cands[:8]]})

    atts = collect_attachments(_split_csv(args.attachments))
    missing = [asdict(a) for a in atts if not a.exists]

    report_level_list: List[Dict] = []
    if advisor_resolved:
        report_level_list.append(
            {
                "level": 1,
                "type": "suggest",
                "nodeCode": "startNode",
                "nodeName": "建议",
                "levelUserList": [{"empId": x.empId, "requirement": ""} for x in advisor_resolved],
            }
        )
    if approver_resolved:
        report_level_list.append(
            {
                "level": 2,
                "type": "decide",
                "nodeCode": "startNode",
                "nodeName": "决策",
                "levelUserList": [{"empId": x.empId, "requirement": ""} for x in approver_resolved],
            }
        )

    accept_emp_ids = [x.empId for x in to_resolved] + to_group_emp_ids
    dedup_accept = []
    seen = set()
    for x in accept_emp_ids:
        if x not in seen:
            seen.add(x)
            dedup_accept.append(x)

    preview = {
        "title": args.title,
        "content": args.content,
        "to": [asdict(x) for x in to_resolved],
        "toGroups": to_group_resolved,
        "cc": [asdict(x) for x in cc_resolved],
        "advisors": [asdict(x) for x in advisor_resolved],
        "approvers": [asdict(x) for x in approver_resolved],
        "attachments": [asdict(x) for x in atts],
        "acceptEmpIdList": dedup_accept,
        "copyEmpIdList": [x.empId for x in cc_resolved],
        "advisorEmpIdList": [x.empId for x in advisor_resolved],
        "approverEmpIdList": [x.empId for x in approver_resolved],
        "reportLevelList": report_level_list,
        "readyToSend": len(unresolved) == 0 and len(missing) == 0 and len(dedup_accept) > 0,
        "unresolved": unresolved,
        "missingAttachments": missing,
        "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sendPolicy": "必须人工确认后发送；发送时需 --confirm-token CONFIRM_SEND",
    }

    out = pathlib.Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"确认单已生成: {out}")
    print(f"readyToSend={preview['readyToSend']}")
    if unresolved:
        print(f"未解析姓名: {len(unresolved)}")
    if missing:
        print(f"缺失附件: {len(missing)}")


def upload_attachment(app_key: str, path: str) -> Dict[str, str]:
    p = pathlib.Path(path)
    with open(p, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/cwork-file/uploadWholeFile",
            headers=_headers(app_key),
            files={"file": (p.name, f)},
            timeout=60,
        )
    j = r.json()
    if j.get("resultCode") != 1:
        raise RuntimeError(f"上传失败: {p.name} -> {j}")

    file_id = str(j.get("data"))
    # 成功经验：fileVOList 使用 fileId+name+type 最稳（不强依赖 url/fsize）
    return {"fileId": file_id, "name": p.name, "type": "file"}


def cmd_send(args: argparse.Namespace) -> None:
    if args.confirm_token != "CONFIRM_SEND":
        raise SystemExit("拒绝发送：缺少确认口令 --confirm-token CONFIRM_SEND")

    app_key = get_app_key(args.app_key)
    cfg_path = pathlib.Path(args.confirm_json).expanduser().resolve()
    if not cfg_path.is_file():
        raise SystemExit(f"确认单不存在: {cfg_path}")

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if not cfg.get("readyToSend"):
        raise SystemExit("确认单未就绪（readyToSend=false），请先修复姓名/附件问题")

    file_vo = []
    for a in cfg.get("attachments", []):
        if not a.get("exists"):
            raise SystemExit(f"附件不存在: {a.get('path')}")
        file_vo.append(upload_attachment(app_key, a["path"]))

    payload = {
        "main": cfg["title"],
        "contentHtml": cfg["content"],
        "contentType": "markdown",
        "acceptEmpIdList": cfg.get("acceptEmpIdList", []),
        "copyEmpIdList": cfg.get("copyEmpIdList", []),
        "reportLevelList": cfg.get("reportLevelList", []),
        "grade": "一般",
        "privacyLevel": "非涉密",
        "typeId": 9999,
        "fileVOList": file_vo,
    }

    headers = {**_headers(app_key), "Content-Type": "application/json"}
    result = None
    for _ in range(6):
        r = requests.post(f"{BASE_URL}/work-report/report/record/submit", headers=headers, json=payload, timeout=60)
        result = r.json()
        if result.get("resultCode") == 1:
            break
        if result.get("resultCode") == 200000:
            time.sleep(2)
            continue
        break

    print(json.dumps({"submit": result, "fileVOList": file_vo}, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CWork 工作汇报发送（带发送前确认单）")
    sub = p.add_subparsers(dest="command", required=True)

    pp = sub.add_parser("prepare", help="生成发送前确认单")
    pp.add_argument("--title", required=True, help="汇报标题")
    pp.add_argument("--content", required=True, help="汇报正文")
    pp.add_argument("--to", required=True, help="接收人姓名，逗号分隔（可留空字符串，仅使用 --to-groups）")
    pp.add_argument("--to-groups", default="", help="接收人分组名，逗号分隔（自动展开成员并去重）")
    pp.add_argument("--cc", default="", help="抄送人姓名，逗号分隔")
    pp.add_argument("--advisors", default="", help="建议人姓名，逗号分隔（写入 reportLevelList:suggest）")
    pp.add_argument("--approvers", default="", help="决策/审批人姓名，逗号分隔（写入 reportLevelList:decide）")
    pp.add_argument("--attachments", default="", help="附件路径，逗号分隔")
    pp.add_argument("--out", required=True, help="确认单 JSON 输出路径")
    pp.add_argument("--app-key", default="", help="可选，覆盖环境变量 appKey")
    pp.set_defaults(func=cmd_prepare)

    ps = sub.add_parser("send", help="根据确认单执行发送")
    ps.add_argument("--confirm-json", required=True, help="prepare 阶段产出的确认单 JSON")
    ps.add_argument("--confirm-token", required=True, help="发送确认口令，必须为 CONFIRM_SEND")
    ps.add_argument("--app-key", default="", help="可选，覆盖环境变量 appKey")
    ps.set_defaults(func=cmd_send)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
