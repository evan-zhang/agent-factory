#!/usr/bin/env python3
"""
CWork API Client — 共享 API 封装
由所有编排脚本 import 使用

环境变量:
  CWORK_BASE_URL  (default: https://sg-al-cwork-web.mediportal.com.cn)
  CWORK_APP_KEY   (required)
"""

import os
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import argparse
from datetime import datetime

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CWorkError(Exception):
    """Raised on API errors (non-1 resultCode or HTTP non-OK)."""
    pass


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class CWorkClient:
    BASE_URL = os.environ.get(
        "CWORK_BASE_URL",
        "https://sg-al-cwork-web.mediportal.com.cn"
    )

    def __init__(self, app_key: str | None = None):
        self.app_key = app_key or os.environ.get("CWORK_APP_KEY")
        if not self.app_key:
            raise CWorkError("CWORK_APP_KEY environment variable is required")

    # ---- HTTP helpers -------------------------------------------------------

    def _headers(self, json_body: bool = False) -> dict:
        h = {"appKey": self.app_key}
        if json_body:
            h["Content-Type"] = "application/json"
        return h

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        if params:
            q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{q}&appKey={self.app_key}"
        else:
            url = f"{url}?appKey={self.app_key}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        return self._request(req)

    def _post(self, path: str, body: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url,
            data=data,
            headers=self._headers(json_body=body is not None),
            method="POST",
        )
        return self._request(req)

    def _request(self, req: urllib.request.Request) -> dict:
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise CWorkError(f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise CWorkError(f"URL error: {e.reason}")

        if result.get("resultCode", -1) != 1:
            raise CWorkError(
                f"API Error ({result.get('resultCode')}): {result.get('resultMsg', 'unknown')}"
            )
        return result.get("data", {})

    # -------------------------------------------------------------------------
    # Employee
    # -------------------------------------------------------------------------

    def search_emp_by_name(self, search_key: str) -> dict:
        """Returns {inside: {empList:[]}, outside: {empList:[]}}"""
        return self._get("/open-api/cwork-user/searchEmpByName", {"searchKey": search_key})

    # -------------------------------------------------------------------------
    # Reports — inbox / outbox / detail
    # -------------------------------------------------------------------------

    def get_inbox_list(
        self,
        page_size: int,
        page_index: int = 1,
        *,
        report_record_type: int | None = None,
        emp_id_list: list[str] | None = None,
        begin_time: int | None = None,
        end_time: int | None = None,
        read_status: int | None = None,
        order_column: str | None = None,
        grade: str | None = None,
        template_id: int | None = None,
    ) -> dict:
        """PaginatedResult<ReportListItem>"""
        params = {
            "pageSize": page_size,
            "pageIndex": page_index,
            "reportRecordType": report_record_type,
            "empIdList": emp_id_list,
            "beginTime": begin_time,
            "endTime": end_time,
            "readStatus": read_status,
            "orderColumn": order_column,
            "grade": grade,
            "templateId": template_id,
        }
        return self._post("/open-api/work-report/report/record/inbox", params)

    def get_outbox_list(
        self,
        page_size: int,
        page_index: int = 1,
        *,
        report_record_type: int | None = None,
        emp_id_list: list[str] | None = None,
        begin_time: int | None = None,
        end_time: int | None = None,
        grade: str | None = None,
        template_id: int | None = None,
    ) -> dict:
        params = {
            "pageSize": page_size,
            "pageIndex": page_index,
            "reportRecordType": report_record_type,
            "empIdList": emp_id_list,
            "beginTime": begin_time,
            "endTime": end_time,
            "grade": grade,
            "templateId": template_id,
        }
        return self._post("/open-api/work-report/report/record/outbox", params)

    def get_report_info(self, report_id: str) -> dict:
        """ReportDetail"""
        return self._get("/open-api/work-report/report/info", {"reportId": report_id})

    def get_report_node_detail(self, report_id: str | int) -> dict:
        """
        获取汇报详情（含节点与处理意见）
        API: 5.33 /work-report/report/getReportNodeDetail

        Returns:
          {
            "id": 汇报ID,
            "main": 标题,
            "content": 正文,
            "writeEmpId": 汇报人ID,
            "writeEmpName": 汇报人姓名,
            "createTime": 发起时间,
            "nodeList": [
              {
                "nodeName": "建议人",
                "type": "建议/决策/传阅",
                "status": "未开始/已完成/进行中/已取消",
                "level": 1,
                "userList": [
                  {
                    "empId": 员工ID,
                    "name": 姓名,
                    "status": "待处理/已处理",
                    "operate": "同意/不同意/建议",
                    "content": "处理意见",
                    "finishTime": "完成时间"
                  }
                ]
              }
            ]
          }
        """
        return self._get("/open-api/work-report/report/getReportNodeDetail", {"reportId": report_id})

    def get_unread_list(self, page_index: int, page_size: int) -> dict:
        return self._post("/open-api/work-report/reportInfoOpenQuery/unreadList", {
            "pageIndex": page_index,
            "pageSize": page_size,
        })

    def is_report_read(self, report_id: str | int, employee_id: str | int) -> bool:
        return self._get(
            f"/open-api/work-report/reportInfoOpenQuery/isReportRead"
            f"?reportId={report_id}&employeeId={employee_id}"
        )

    def mark_report_read(self, report_id: str | int) -> None:
        self._get(f"/open-api/work-report/open-platform/report/readReport?reportId={report_id}")

    # -------------------------------------------------------------------------
    # Report — reply / submit / remind
    # -------------------------------------------------------------------------

    def submit_report(
        self,
        main: str,
        content_html: str,
        *,
        content_type: str = "html",
        type_id: int = 9999,
        grade: str = "一般",
        privacy_level: str = "非涉密",
        plan_id: str | None = None,
        template_id: int | None = None,
        accept_emp_id_list: list[str] | None = None,
        copy_emp_id_list: list[str] | None = None,
        report_level_list: list[dict] | None = None,
        file_vo_list: list[dict] | None = None,
    ) -> dict:
        """Returns {id: string}"""
        return self._post("/open-api/work-report/report/record/submit", {
            "appKey": self.app_key,
            "main": main,
            "contentHtml": content_html,
            "contentType": content_type,
            "typeId": type_id,
            "grade": grade,
            "privacyLevel": privacy_level,
            "planId": plan_id,
            "templateId": template_id,
            "acceptEmpIdList": accept_emp_id_list,
            "copyEmpIdList": copy_emp_id_list,
            "reportLevelList": report_level_list,
            "fileVOList": file_vo_list,
        })

    def reply_report(
        self,
        report_record_id: str,
        content_html: str,
        *,
        add_emp_id_list: list[str] | None = None,
        send_msg: bool = True,
    ) -> int:
        """Returns reply ID"""
        return self._post("/open-api/work-report/report/record/reply", {
            "appKey": self.app_key,
            "reportRecordId": report_record_id,
            "contentHtml": content_html,
            "addEmpIdList": add_emp_id_list,
            "sendMsg": send_msg,
        })

    # -------------------------------------------------------------------------
    # Draft box
    # -------------------------------------------------------------------------

    def save_draft(
        self,
        main: str,
        content_html: str,
        *,
        draft_id: str | None = None,
        content_type: str = "markdown",
        type_id: int = 9999,
        grade: str = "一般",
        privacy_level: str = "非涉密",
        plan_id: str | None = None,
        template_id: str | None = None,
        accept_emp_id_list: list[str] | None = None,
        copy_emp_id_list: list[str] | None = None,
        report_level_list: list[dict] | None = None,
        file_vo_list: list[dict] | None = None,
    ) -> dict:
        payload = {
            "appKey": self.app_key,
            "main": main,
            "contentHtml": content_html,
            "contentType": content_type,
            "typeId": type_id,
            "grade": grade,
            "privacyLevel": privacy_level,
            "planId": plan_id,
            "templateId": template_id,
            "acceptEmpIdList": accept_emp_id_list,
            "copyEmpIdList": copy_emp_id_list,
            "reportLevelList": report_level_list,
            "fileVOList": file_vo_list,
        }
        if draft_id is not None:
            payload["id"] = draft_id
        return self._post("/open-api/work-report/draftBox/saveOrUpdate", payload)

    def list_drafts(self, page_index: int, page_size: int) -> dict:
        return self._post("/open-api/work-report/draftBox/listByPage", {
            "pageIndex": page_index,
            "pageSize": page_size,
        })

    def get_draft_detail(self, report_record_id: str) -> dict:
        return self._get(f"/open-api/work-report/draftBox/detail/{report_record_id}")

    def delete_draft(self, draft_id: str) -> bool:
        return self._post(f"/open-api/work-report/draftBox/delete/{draft_id}")

    # -------------------------------------------------------------------------
    # Tasks
    # -------------------------------------------------------------------------

    def search_task_page(
        self,
        page_size: int,
        page_index: int = 1,
        *,
        key_word: str | None = None,
        status: int | None = None,
        report_status: int | None = None,
        emp_id_list: list[str] | None = None,
        grades: list[str] | None = None,
        label_list: list[str] | None = None,
        is_read: int | None = None,
    ) -> dict:
        params = {
            "pageSize": page_size,
            "pageIndex": page_index,
            "keyWord": key_word,
            "status": status,
            "reportStatus": report_status,
            "empIdList": emp_id_list,
            "grades": grades,
            "labelList": label_list,
            "isRead": is_read,
        }
        return self._post("/open-api/work-report/report/plan/searchPage", params)

    def get_simple_plan_and_report_info(self, plan_id: str) -> dict:
        return self._get(
            "/open-api/work-report/report/plan/getSimplePlanAndReportInfo",
            {"planId": plan_id},
        )

    def create_plan(
        self,
        main: str,
        needful: str,
        target: str,
        end_time: int,
        type_id: int = 9999,
        *,
        report_emp_id_list: list[str] | None = None,
        owner_emp_id_list: list[str] | None = None,
        assist_emp_id_list: list[str] | None = None,
        supervisor_emp_id_list: list[str] | None = None,
        copy_emp_id_list: list[str] | None = None,
        observer_emp_id_list: list[str] | None = None,
        push_now: bool = True,
    ) -> str:
        """Returns plan ID string."""
        result = self._post("/open-api/work-report/open-platform/report/plan/create", {
            "appKey": self.app_key,
            "main": main,
            "needful": needful,
            "target": target,
            "typeId": type_id,
            "reportEmpIdList": report_emp_id_list,
            "ownerEmpIdList": owner_emp_id_list,
            "assistEmpIdList": assist_emp_id_list,
            "supervisorEmpIdList": supervisor_emp_id_list,
            "copyEmpIdList": copy_emp_id_list,
            "observerEmpIdList": observer_emp_id_list,
            "pushNow": 1 if push_now else 0,
            "endTime": end_time,
        })
        return str(result)

    # -------------------------------------------------------------------------
    # Todo / feedback
    # -------------------------------------------------------------------------

    def list_created_feedbacks(self, page_num: int, page_size: int) -> dict:
        return self._post("/open-api/work-report/todoTask/listCreatedFeedbacks", {
            "pageNum": page_num,
            "pageSize": page_size,
        })

    def get_todo_list(self, page_index: int, page_size: int, *, status: str | None = None) -> dict:
        params = {"pageIndex": page_index, "pageSize": page_size}
        if status:
            params["status"] = status
        return self._post("/open-api/work-report/reportInfoOpenQuery/todoList", params)

    def complete_todo(
        self, todo_id: str, content: str, *, operate: str | None = None
    ) -> bool:
        return self._post("/open-api/work-report/open-platform/todo/completeTodo", {
            "appKey": self.app_key,
            "todoId": todo_id,
            "content": content,
            "operate": operate,
        })

    # -------------------------------------------------------------------------
    # File upload
    # -------------------------------------------------------------------------

    def upload_file(self, file_path: str) -> dict:
        import mimetypes
        boundary = "----FormBoundary7MA4YWxkTrZu0gW"
        filename = os.path.basename(file_path)
        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            file_data = f.read()
        body_parts = [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            file_data,
            f"\r\n--{boundary}--\r\n".encode(),
        ]
        body = b"".join(body_parts)
        req = urllib.request.Request(
            f"{self.BASE_URL}/open-api/cwork-file/uploadWholeFile",
            data=body,
            headers={
                "appKey": self.app_key,
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        result = self._request(req)
        if isinstance(result, str):
            return {"fileId": result}
        return result

    # -------------------------------------------------------------------------
    # Templates
    # -------------------------------------------------------------------------

    def list_templates(
        self, begin_time: int | None = None, end_time: int | None = None, limit: int | None = None
    ) -> dict:
        return self._post("/open-api/work-report/template/listTemplates", {
            "appKey": self.app_key,
            "beginTime": begin_time,
            "endTime": end_time,
            "limit": limit,
        })


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def make_client() -> CWorkClient:
    app_key = os.environ.get("CWORK_APP_KEY")
    if not app_key:
        raise CWorkError(
            "CWORK_APP_KEY environment variable is not set. "
            "Run:  export CWORK_APP_KEY='your-key'"
        )
    return CWorkClient(app_key)


# ---------------------------------------------------------------------------
# CLI argument helpers
# ---------------------------------------------------------------------------

def parse_deadline(value: str | None) -> int | None:
    """Parse deadline string to milliseconds timestamp."""
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return int(dt.timestamp() * 1000)
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(f"Invalid deadline format: {value}. Use YYYY-MM-DD or milliseconds.")


def resolve_names_to_empids(client: CWorkClient, names: list[str]) -> list[str]:
    """Resolve a list of names to empIds via search API."""
    empids = []
    for name in names:
        result = client.search_emp_by_name(name)
        inside_list = result.get("inside", {}).get("empList", [])
        outside_list = result.get("outside", {}).get("empList", [])
        all_emps = inside_list + outside_list
        if not all_emps:
            raise CWorkError(f"No employee found with name: {name}")
        empids.append(all_emps[0].get("empId") or all_emps[0].get("empid"))
    return empids


def output_json(data: dict) -> None:
    """Output JSON to stdout."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def output_error(message: str) -> None:
    """Output error JSON and exit."""
    print(json.dumps({"success": False, "message": message}, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(1)


def interactive_confirm(step_name: str, description: str) -> bool:
    """Print step description and wait for 'confirm' from stdin."""
    print(f"\n[STEP] {step_name}: {description}", file=sys.stderr)
    print("Type 'confirm' to proceed (or press Enter to skip): ", file=sys.stderr, end="")
    sys.stderr.flush()
    try:
        user_input = input().strip().lower()
        return user_input == "confirm"
    except (EOFError, KeyboardInterrupt):
        return False
