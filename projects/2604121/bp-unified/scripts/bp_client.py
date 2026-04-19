#!/usr/bin/env python3
"""
BP API 客户端封装

提供 BP 系统所有 API 接口的封装，支持只读和写操作。
"""

import os
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any

class BPClient:
    """BP API 客户端"""
    
    def __init__(self, app_key: str = None, base_url: str = None):
        self.app_key = app_key or os.getenv("BP_APP_KEY")
        self.base_url = base_url or "https://sg-al-cwork-web.mediportal.com.cn/open-api"
        
        if not self.app_key:
            raise ValueError("缺少 app_key，请设置 BP_APP_KEY 环境变量")
    
    def _request(self, method: str, path: str, params: Dict = None, data: Dict = None) -> Dict:
        """发送 HTTP 请求"""
        url = f"{self.base_url}{path}"
        headers = {
            "appKey": self.app_key,
            "Content-Type": "application/json"
        }
        
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        
        try:
            if method == "GET":
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    body = response.read().decode('utf-8')
                    return json.loads(body)
            elif method == "POST":
                req_data = json.dumps(data).encode('utf-8') if data else None
                req = urllib.request.Request(url, headers=headers, data=req_data, method='POST')
                with urllib.request.urlopen(req) as response:
                    body = response.read().decode('utf-8')
                    return json.loads(body)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")
        except Exception as e:
            return {"resultCode": 0, "resultMsg": str(e), "data": None}
    
    # ==================== 周期管理 ====================
    
    def list_periods(self, name: str = None) -> Dict:
        """查询周期列表"""
        params = {"name": name} if name else None
        return self._request("GET", "/bp/period/list", params=params)
    
    # ==================== 分组管理 ====================
    
    def list_groups(self, period_id: str, only_personal: bool = False) -> Dict:
        """获取分组树"""
        params = {
            "periodId": period_id,
            "onlyPersonal": str(only_personal).lower()
        }
        return self._request("GET", "/bp/group/list", params=params)
    
    def get_personal_group_ids(self, employee_ids: List[str]) -> Dict:
        """批量查询员工个人类型分组 ID"""
        return self._request("POST", "/bp/group/getPersonalGroupIds", data=employee_ids)
    
    def search_groups(self, period_id: str, name: str) -> Dict:
        """按名称搜索分组"""
        params = {
            "periodId": period_id,
            "name": name
        }
        return self._request("GET", "/bp/group/searchByName", params=params)
    
    def get_group_markdown(self, group_id: str) -> Dict:
        """获取分组完整 BP 的 Markdown"""
        params = {"groupId": group_id}
        return self._request("GET", "/bp/group/markdown", params=params)
    
    def batch_get_key_position_markdown(self, group_ids: List[str]) -> Dict:
        """批量获取关键岗位详情 Markdown"""
        return self._request("POST", "/bp/group/batchGetKeyPositionMarkdown", data=group_ids)
    
    # ==================== 任务管理 ====================
    
    def get_simple_tree(self, group_id: str) -> Dict:
        """查询 BP 任务树（简要信息）"""
        params = {"groupId": group_id}
        return self._request("GET", "/bp/task/v2/getSimpleTree", params=params)
    
    def search_tasks(self, group_id: str, name: str) -> Dict:
        """按名称搜索任务"""
        params = {
            "groupId": group_id,
            "name": name
        }
        return self._request("GET", "/bp/task/v2/searchByName", params=params)
    
    def get_task_children(self, parent_id: str) -> Dict:
        """获取任务子树骨架"""
        params = {"parentId": parent_id}
        return self._request("GET", "/bp/task/children", params=params)
    
    # ==================== 目标管理 ====================
    
    def list_goals(self, group_id: str) -> Dict:
        """获取目标列表"""
        params = {"groupId": group_id}
        return self._request("GET", "/bp/goal/list", params=params)
    
    def get_goal_detail(self, goal_id: str) -> Dict:
        """获取目标详情"""
        return self._request("GET", f"/bp/goal/{goal_id}/detail")
    
    # ==================== 关键成果管理 ====================
    
    def list_key_results(self, goal_id: str) -> Dict:
        """获取关键成果列表"""
        params = {"goalId": goal_id}
        return self._request("GET", "/bp/keyResult/list", params=params)
    
    def get_key_result_detail(self, key_result_id: str) -> Dict:
        """获取关键成果详情"""
        return self._request("GET", f"/bp/keyResult/{key_result_id}/detail")
    
    def add_key_result(self, goal_id: str, name: str, **kwargs) -> Dict:
        """新增关键成果"""
        data = {
            "goalId": goal_id,
            "name": name,
            **kwargs
        }
        return self._request("POST", "/bp/task/v2/addKeyResult", data=data)
    
    # ==================== 关键举措管理 ====================
    
    def list_actions(self, key_result_id: str) -> Dict:
        """获取关键举措列表"""
        params = {"keyResultId": key_result_id}
        return self._request("GET", "/bp/action/list", params=params)
    
    def get_action_detail(self, action_id: str) -> Dict:
        """获取关键举措详情"""
        return self._request("GET", f"/bp/action/{action_id}/detail")
    
    def add_action(self, key_result_id: str, name: str, **kwargs) -> Dict:
        """新增关键举措"""
        data = {
            "keyResultId": key_result_id,
            "name": name,
            **kwargs
        }
        return self._request("POST", "/bp/task/v2/addAction", data=data)
    
    # ==================== 汇报管理 ====================
    
    def list_task_reports(self, task_id: str, page_index: int = 1, page_size: int = 10, 
                          keyword: str = None, sort_by: str = "relation_time", 
                          sort_order: str = "desc") -> Dict:
        """分页查询所有汇报"""
        data = {
            "taskId": task_id,
            "keyword": keyword,
            "sortBy": sort_by,
            "sortOrder": sort_order,
            "pageIndex": page_index,
            "pageSize": page_size
        }
        return self._request("POST", "/bp/task/relation/pageAllReports", data=data)
    
    # ==================== 延期提醒 ====================
    
    def send_delay_report(self, receiver_emp_id: str, report_name: str, content: str) -> Dict:
        """发送延期提醒汇报"""
        data = {
            "receiverEmpId": receiver_emp_id,
            "reportName": report_name,
            "content": content
        }
        return self._request("POST", "/bp/delayReport/send", data=data)
    
    def list_delay_reports(self, receiver_emp_id: str) -> Dict:
        """查询延期提醒汇报历史"""
        params = {"receiverEmpId": receiver_emp_id}
        return self._request("GET", "/bp/delayReport/list", params=params)


# 便捷函数
def get_current_period(client: BPClient) -> Optional[Dict]:
    """获取当前启用的周期"""
    result = client.list_periods()
    if result.get("resultCode") == 1 and result.get("data"):
        for period in result["data"]:
            if period.get("status") == 1:  # status=1 表示启用
                return period
    return None


def find_my_group(client: BPClient, period_id: str, employee_id: str) -> Optional[Dict]:
    """找到员工在指定周期下的个人分组"""
    result = client.get_personal_group_ids([employee_id])
    if result.get("resultCode") == 1 and result.get("data"):
        return result["data"].get(employee_id)
    return None


if __name__ == "__main__":
    # 测试连接
    client = BPClient()
    print("测试周期列表:")
    result = client.list_periods()
    print(json.dumps(result, indent=2, ensure_ascii=False))
