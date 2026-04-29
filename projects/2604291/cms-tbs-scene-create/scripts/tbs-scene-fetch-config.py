#!/usr/bin/env python3
"""
tbs-scene-fetch-config.py

Best-effort resolver for Step1:
Resolve businessDomainId/departmentId/drugId from names by calling:
 - POST /businessDomain/listBusinessDomains
 - POST /department/listDepartments
 - POST /drug/listDrugs

Because TBS list endpoints request/response payloads may differ by backend,
this script tries a few common request bodies and response shapes.
"""

import argparse
import json
import os
import sys
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


def http_post_json(url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def pick_list(data: Any) -> List[Dict[str, Any]]:
    """
    Try to normalize various response shapes into a list of objects.
    Common shapes:
    - data: [{...}]
    - data: { list/records/items: [{...}] }
    """
    if data is None:
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("records", "list", "items", "data"):
            v = data.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    return []


def norm(s: Any) -> str:
    if s is None:
        return ""
    return str(s).strip().lower()


def match_by_name(items: List[Dict[str, Any]], target_name: str) -> Optional[Dict[str, Any]]:
    t = norm(target_name)
    if not t:
        return None

    # 1) exact match on common name keys
    name_keys = ("name", "title", "drugName", "departmentName", "businessDomainName")
    for it in items:
        for k in name_keys:
            if norm(it.get(k)) == t:
                return it

    # 2) contains match
    for it in items:
        for k in name_keys:
            v = norm(it.get(k))
            if v and (t in v or v in t):
                return it

    return None


def resolve_one_list(
    url: str,
    headers: Dict[str, str],
    items: List[Dict[str, Any]],
    target_name: str,
) -> Tuple[Optional[str], Optional[str]]:
    hit = match_by_name(items, target_name)
    if not hit:
        return None, None

    # Common id keys
    for id_key in ("id", "code", "drugId", "departmentId", "businessDomainId"):
        v = hit.get(id_key)
        if v is not None and str(v).strip() != "":
            return str(v), hit.get("name") or hit.get("title") or hit.get(id_key)
    return None, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--access-token", required=True, help="TBS access-token")
    ap.add_argument("--base-url", default=os.getenv("TBS_BASE_URL", "https://cwork-web-test.xgjktech.com.cn/tbs-admin"))
    ap.add_argument("--business-domain-name", required=False, default="")
    ap.add_argument("--department-name", required=False, default="")
    ap.add_argument("--drug-name", required=False, default="")
    ap.add_argument("--params-json", required=False, help="Optional JSON for names")
    args = ap.parse_args()

    names = {
        "businessDomainName": args.business_domain_name,
        "departmentName": args.department_name,
        "drugName": args.drug_name,
    }
    if args.params_json:
        try:
            pj = json.loads(args.params_json)
            names.update(pj)
        except Exception:
            print(json.dumps({"success": False, "error": "params-json is not valid json"}), file=sys.stderr)
            return 2

    business_name = names.get("businessDomainName", "")
    dept_name = names.get("departmentName", "")
    drug_name = names.get("drugName", "")

    headers = {
        "access-token": args.access_token,
        "Content-Type": "application/json",
    }
    base = args.base_url.rstrip("/")

    # Common request body candidates
    bodies_to_try = [{}, {"pageNum": 1, "pageSize": 50}, {"pageIndex": 1, "pageSize": 50}]

    def fetch_list(path: str) -> List[Dict[str, Any]]:
        url = base + path
        last_err = None
        for body in bodies_to_try:
            try:
                res = http_post_json(url, headers, body)
                # admin list APIs usually wrap: {resultCode,resultMsg,data}
                data = res.get("data")
                return pick_list(data)
            except Exception as e:
                last_err = e
                continue
        raise RuntimeError(f"fetch_list failed for {path}: {last_err}")

    try:
        domains = fetch_list("/businessDomain/listBusinessDomains")
        depts = fetch_list("/department/listDepartments")
        drugs = fetch_list("/drug/listDrugs")
    except Exception as e:
        print(json.dumps({"success": False, "error": f"fetch config failed: {e}"}), file=sys.stderr)
        return 1

    businessDomainId, _ = resolve_one_list("", headers, domains, business_name)
    departmentId, _ = resolve_one_list("", headers, depts, dept_name)
    drugId, _ = resolve_one_list("", headers, drugs, drug_name)

    out = {
        "success": True,
        "resolved": {
            "businessDomainId": businessDomainId,
            "departmentId": departmentId,
            "drugId": drugId,
        },
        "debug": {
            "matchedNames": {
                "businessDomainName": business_name,
                "departmentName": dept_name,
                "drugName": drug_name,
            },
            "counts": {
                "domains": len(domains),
                "departments": len(depts),
                "drugs": len(drugs),
            },
        },
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

