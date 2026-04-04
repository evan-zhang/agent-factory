#!/usr/bin/env python3
"""
cwork-send-report.py
Send a work report: search recipients → validate → save draft → show preview → send → cleanup

Usage:
  python3 scripts/cwork-send-report.py --title "汇报标题" \
    --content-html "<p>汇报内容</p>" \
    --receivers "张三,李四" \
    --grade "一般"

Environment:
  CWORK_APP_KEY  (required)
  CWORK_BASE_URL (optional, default: https://sg-al-cwork-web.mediportal.com.cn)
"""

import sys
import json
import argparse
from pathlib import Path

# Allow running as `python3 scripts/send-report.py` from skill root
sys.path.insert(0, str(Path(__file__).parent))
from cwork_api import make_client, CWorkError


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Send a CWork report")
    p.add_argument("--title", "-t", required=True, help="Report title")
    p.add_argument("--content-html", "-c", required=True, help="Report body HTML")
    p.add_argument(
        "--receivers", "-r", default="",
        help="Comma-separated receiver names (will be resolved to empId)"
    )
    p.add_argument(
        "--cc", dest="cc_names", default="",
        help="Comma-separated CC recipient names"
    )
    p.add_argument(
        "--grade", "-g", default="一般",
        choices=["一般", "紧急"],
        help="Report urgency"
    )
    p.add_argument(
        "--type-id", dest="type_id", type=int, default=9999,
        help="Report type ID (default 9999)"
    )
    p.add_argument(
        "--file-paths", nargs="*", dest="file_paths", default=[],
        help="Local file paths to attach (up to 10)"
    )
    p.add_argument(
        "--file-names", nargs="*", dest="file_names", default=[],
        help="File names for attachments (same order as --file-paths)"
    )
    p.add_argument(
        "--plan-id", dest="plan_id", default=None,
        help="Linked plan/task ID"
    )
    p.add_argument(
        "--preview-only", dest="preview_only", action="store_true",
        help="Save draft and print preview JSON, do not send"
    )
    p.add_argument(
        "--draft-id", dest="draft_id", default=None,
        help="Existing draft ID to update (omit to create new draft)"
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Step 1 — Resolve names → empIds
# ---------------------------------------------------------------------------

def resolve_receivers(client, names: list[str]) -> dict:
    """Search each name; return {name: {status, empId, title, dept}}"""
    results = {}
    for name in names:
        if not name.strip():
            continue
        try:
            data = client.search_emp_by_name(name.strip())
        except CWorkError as e:
            results[name] = {"status": "error", "message": str(e)}
            continue

        inside = data.get("inside", {}).get("empList", [])
        outside = data.get("outside", {}).get("empList", [])
        all_emps = inside + outside

        if len(all_emps) == 0:
            results[name] = {"status": "not_found"}
        elif len(all_emps) == 1:
            emp = all_emps[0]
            results[name] = {
                "status": "found",
                "empId": emp["id"],
                "name": emp["name"],
                "title": emp.get("title", ""),
                "dept": emp.get("mainDept", ""),
            }
        else:
            results[name] = {
                "status": "multiple",
                "employees": [
                    {"empId": e["id"], "name": e["name"],
                     "title": e.get("title", ""), "dept": e.get("mainDept", "")}
                    for e in all_emps
                ],
            }
    return results


def validate_receivers(resolved: dict) -> tuple[list[dict], list[str]]:
    """Return (confirmed list, error messages). Fails if any name ambiguous or missing."""
    confirmed = []
    errors = []
    for name, info in resolved.items():
        if info["status"] == "not_found":
            errors.append(f'"{name}" 未找到对应员工')
        elif info["status"] == "multiple":
            opts = "\n".join(
                f'  - {e["name"]}（{e["title"]}，{e["dept"]}）'
                for e in info["employees"]
            )
            errors.append(
                f'"{name}" 匹配到多人，请输入更精确的姓名：\n{opts}'
            )
        elif info["status"] == "found":
            confirmed.append({"empId": info["empId"], "name": info["name"]})
    return confirmed, errors


# ---------------------------------------------------------------------------
# Step 2 — Upload files
# ---------------------------------------------------------------------------

def upload_files(client, file_paths: list[str], file_names: list[str]) -> list[dict]:
    """Upload files; return fileVO list for submit."""
    if not file_paths:
        return []
    file_vos = []
    for i, path in enumerate(file_paths):
        fname = file_names[i] if i < len(file_names) else Path(path).name
        try:
            result = client.upload_file(path)
            file_id = result.get("fileId", "")
            file_vos.append({
                "fileId": file_id,
                "name": fname,
                "type": "file",
            })
        except CWorkError as e:
            print(json.dumps({
                "step": "upload",
                "file": fname,
                "error": str(e)
            }, ensure_ascii=False), file=sys.stderr)
    return file_vos


# ---------------------------------------------------------------------------
# Step 3 — Save draft
# ---------------------------------------------------------------------------

def save_draft(client, args, accept_emp_ids: list[str], copy_emp_ids: list[str],
               file_vos: list[dict]) -> str | None:
    """Save or update draft; return draft ID."""
    params = {
        "main": args.title,
        "contentHtml": args.content_html,
        "contentType": "html",
        "typeId": args.type_id,
        "grade": args.grade,
        "acceptEmpIdList": accept_emp_ids or None,
        "copyEmpIdList": copy_emp_ids or None,
        "fileVOList": file_vos or None,
        "planId": args.plan_id,
    }
    if args.draft_id:
        params["id"] = args.draft_id
    try:
        result = client.save_draft(**{k: v for k, v in params.items() if v is not None})
        return result.get("id")
    except CWorkError as e:
        print(json.dumps({"step": "save_draft", "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Step 4 — Preview
# ---------------------------------------------------------------------------

def build_preview(args, confirmed: list[dict], cc_confirmed: list[dict],
                  file_vos: list[dict]) -> dict:
    accept_names = [e["name"] for e in confirmed]
    cc_names = [e["name"] for e in cc_confirmed]
    import re
    plain = re.sub(r"<[^>]+>", "", args.content_html)

    return {
        "report": {
            "title": args.title,
            "grade": args.grade,
            "typeId": args.type_id,
            "planId": args.plan_id,
        },
        "receivers": {
            "count": len(accept_names),
            "names": accept_names,
            "confirmed": confirmed,
        },
        "cc": {
            "count": len(cc_names),
            "names": cc_names,
        },
        "attachments": {
            "count": len(file_vos),
            "files": [{"name": f["name"]} for f in file_vos],
        },
        "contentPreview": plain[:300] + ("..." if len(plain) > 300 else ""),
        "confirmPrompt": (
            f"【汇报预览】\n"
            f"标题：{args.title}\n"
            f"优先级：{args.grade}\n"
            f"接收人：{', '.join(accept_names) or '（无）'}\n"
            f"抄送：{', '.join(cc_names) or '（无）'}\n"
            f"附件：{', '.join(f['name'] for f in file_vos) or '无附件'}\n"
            f"正文预览：{plain[:200]}...\n"
            f"\n回复「是」确认发送，或告诉我需要修改的内容。"
        ),
    }


# ---------------------------------------------------------------------------
# Step 5 — Send
# ---------------------------------------------------------------------------

def submit_report(client, args, accept_emp_ids: list[str], copy_emp_ids: list[str],
                  file_vos: list[dict]) -> str | None:
    params = {
        "main": args.title,
        "contentHtml": args.content_html,
        "contentType": "html",
        "typeId": args.type_id,
        "grade": args.grade,
        "acceptEmpIdList": accept_emp_ids or None,
        "copyEmpIdList": copy_emp_ids or None,
        "fileVOList": file_vos or None,
        "planId": args.plan_id,
    }
    try:
        result = client.submit_report(**{k: v for k, v in params.items() if v is not None})
        return result.get("id")
    except CWorkError as e:
        print(json.dumps({"step": "submit", "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Step 6 — Cleanup draft
# ---------------------------------------------------------------------------

def cleanup_draft(client, draft_id: str):
    try:
        client.delete_draft(draft_id)
    except CWorkError as e:
        print(json.dumps({"step": "cleanup_draft", "draftId": draft_id, "error": str(e)}, ensure_ascii=False), file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()
    client = make_client()

    # ---- Step 1: Resolve receiver names ----
    receiver_names = [n.strip() for n in args.receivers.split(",") if n.strip()]
    cc_names = [n.strip() for n in args.cc_names.split(",") if n.strip()]

    resolved = resolve_receivers(client, receiver_names)
    confirmed, errors = validate_receivers(resolved)
    if errors:
        print(json.dumps({"success": False, "step": "validate_receivers", "errors": errors}, ensure_ascii=False, indent=2))
        sys.exit(1)

    cc_resolved = resolve_receivers(client, cc_names)
    cc_confirmed, cc_errors = validate_receivers(cc_resolved)
    # CC errors are non-fatal — just warn
    if cc_errors:
        print(json.dumps({"step": "cc_validate_warnings", "errors": cc_errors}, ensure_ascii=False), file=sys.stderr)

    accept_emp_ids = [e["empId"] for e in confirmed]
    cc_emp_ids = [e["empId"] for e in cc_confirmed]

    # ---- Step 2: Upload files ----
    file_vos = upload_files(client, args.file_paths, args.file_names)

    # ---- Step 3: Save draft ----
    draft_id = save_draft(client, args, accept_emp_ids, cc_emp_ids, file_vos)

    # ---- Step 4: Build preview ----
    preview = build_preview(args, confirmed, cc_confirmed, file_vos)
    preview["draftId"] = draft_id

    if args.preview_only:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return

    # Send confirmation loop would happen at the Agent layer.
    # Here we just proceed to send.
    report_id = submit_report(client, args, accept_emp_ids, cc_emp_ids, file_vos)

    if report_id:
        # ---- Step 6: Cleanup ----
        if draft_id:
            cleanup_draft(client, draft_id)
        result = {
            "success": True,
            "reportId": report_id,
            "receivers": accept_emp_ids,
            "cc": cc_emp_ids,
            "attachments": len(file_vos),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = {
            "success": False,
            "step": "submit",
            "draftId": draft_id,
            "message": "汇报发送失败，请检查草稿是否已保存",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
