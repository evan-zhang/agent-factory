#!/usr/bin/env python3
"""
tbs-scene-create.py

Call POST /scene/createScene with prepared scene draft.
"""

import argparse
import json
import os
import sys
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def http_post_json(url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def pick_list(data: Any) -> List[Dict[str, Any]]:
    """
    Normalize various response shapes into a list of dict items.
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

    name_keys = ("name", "title", "drugName", "departmentName", "businessDomainName")
    for it in items:
        for k in name_keys:
            if norm(it.get(k)) == t:
                return it

    for it in items:
        for k in name_keys:
            v = norm(it.get(k))
            if v and (t in v or v in t):
                return it

    return None


def resolve_one_list(items: List[Dict[str, Any]], target_name: str) -> Tuple[Optional[str], Optional[str]]:
    hit = match_by_name(items, target_name)
    if not hit:
        return None, None

    for id_key in ("id", "code", "drugId", "departmentId", "businessDomainId"):
        v = hit.get(id_key)
        if v is not None and str(v).strip() != "":
            return str(v), hit.get("name") or hit.get("title") or hit.get(id_key)
    return None, None


def is_numeric_id(v: Any) -> bool:
    if v is None:
        return False
    s = str(v).strip()
    return s.isdigit()


def fetch_list(base: str, path: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    url = base + path
    bodies_to_try = [{}, {"pageNum": 1, "pageSize": 50}, {"pageIndex": 1, "pageSize": 50}]
    last_err: Optional[Exception] = None
    for body in bodies_to_try:
        try:
            res = http_post_json(url, headers, body)
            return pick_list(res.get("data"))
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"fetch_list failed for {path}: {last_err}")


def maybe_resolve_ids(scene: Dict[str, Any], headers: Dict[str, str], base_url: str) -> Dict[str, Any]:
    """
    If departmentId/drugId/businessDomainId are not numeric IDs, treat them as names
    and resolve to IDs before calling POST /scene/createScene.
    """
    base = base_url.rstrip("/")
    dept_val = scene.get("departmentId")
    drug_val = scene.get("drugId")
    domain_val = scene.get("businessDomainId")

    need_resolve = (not is_numeric_id(dept_val)) or (not is_numeric_id(drug_val)) or (not is_numeric_id(domain_val))
    if not need_resolve:
        return scene

    domains = fetch_list(base, "/businessDomain/listBusinessDomains", headers)
    depts = fetch_list(base, "/department/listDepartments", headers)
    drugs = fetch_list(base, "/drug/listDrugs", headers)

    domainId, _ = resolve_one_list(domains, domain_val) if not is_numeric_id(domain_val) else (str(domain_val), None)
    departmentId, _ = resolve_one_list(depts, dept_val) if not is_numeric_id(dept_val) else (str(dept_val), None)
    drugId, _ = resolve_one_list(drugs, drug_val) if not is_numeric_id(drug_val) else (str(drug_val), None)

    if not domainId or not departmentId or not drugId:
        raise RuntimeError(
            f"resolve ids failed (domainId={domainId}, departmentId={departmentId}, drugId={drugId}) "
            f"from (domain='{domain_val}', dept='{dept_val}', drug='{drug_val}')"
        )

    scene["businessDomainId"] = domainId
    scene["departmentId"] = departmentId
    scene["drugId"] = drugId
    return scene


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params-file", required=False, help="Path to draft.json")
    ap.add_argument("--params-json", required=False, help="Draft JSON string (optional)")
    ap.add_argument("--access-token", required=True, help="TBS access-token")
    ap.add_argument("--base-url", default=os.getenv("TBS_BASE_URL", "https://cwork-web-test.xgjktech.com.cn/tbs-admin"))
    args = ap.parse_args()

    try:
        if args.params_json:
            payload = json.loads(args.params_json)
        else:
            if not args.params_file:
                raise ValueError("either --params-file or --params-json is required")
            payload = load_json(args.params_file)
    except Exception as e:
        print(json.dumps({"success": False, "error": f"load_json failed: {e}"}), file=sys.stderr)
        return 2

    scene = payload.get("scene") or payload.get("draft") or payload
    if not isinstance(scene, dict):
        print(json.dumps({"success": False, "error": "scene must be an object"}), file=sys.stderr)
        return 2

    # Prepare request body according to TBS接口.md
    headers = {
        "access-token": args.access_token,
        "Content-Type": "application/json",
    }

    # Best-effort name -> id resolve (because Step1 may only capture names)
    try:
        scene = maybe_resolve_ids(scene, headers, args.base_url)
    except Exception as e:
        print(json.dumps({"success": False, "error": f"resolve ids failed: {e}"}), file=sys.stderr)
        return 1

    body: Dict[str, Any] = {
        "title": scene.get("title"),
        "departmentId": scene.get("departmentId"),
        "drugId": scene.get("drugId"),
        "businessDomainId": scene.get("businessDomainId"),
        "location": scene.get("location"),
        "doctorOnlyContext": scene.get("doctorOnlyContext"),
        "coachOnlyContext": scene.get("coachOnlyContext"),
        "repBriefing": scene.get("repBriefing"),
        "personaIds": scene.get("personaIds", []),
        "knowledgeIds": scene.get("knowledgeIds", []),
        "status": scene.get("status", 1),
    }

    url = args.base_url.rstrip("/") + "/scene/createScene"

    try:
        res = http_post_json(url, headers=headers, body=body)
    except Exception as e:
        print(json.dumps({"success": False, "error": f"request failed: {e}"}), file=sys.stderr)
        return 1

    # Expected response: { resultCode, resultMsg, data }
    scene_id = res.get("data")
    out = {
        "success": True,
        "sceneDbId": scene_id,
        "apiRaw": res,
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

