"""
API 客户端模块

封装玄关开发者平台 BP 相关 API 调用
"""

import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class BPGoal:
    """BP 目标数据结构"""
    id: str
    code: str
    name: str
    type: str  # "personal" | "org"
    measure_standard: Optional[str] = None
    number_anchors: List[str] = None
    key_results: List[Dict] = None
    status: Optional[str] = None


class BPAPIClient:
    """BP API 客户端"""
    
    def __init__(self, base_url: str, app_key: str):
        self.base_url = base_url.rstrip("/")
        self.app_key = app_key
        self.headers = {"appKey": app_key}
    
    def _call_api(self, path: str, params: dict = None) -> dict:
        """调用 API"""
        url = f"{self.base_url}{path}"
        response = requests.get(url, params=params, headers=self.headers)
        
        if response.status_code == 401:
            raise PermissionError(f"API 权限不足: {path}")
        
        data = response.json()
        if data.get("resultCode") != 1:
            raise Exception(f"API 错误: {data.get('resultMsg')}")
        
        return data.get("data")
    
    def get_org_tree(self, period_id: str) -> List[Dict]:
        """API 4.2: 获取组织架构树"""
        return self._call_api("/bp/group/getTree", {"periodId": period_id})
    
    def get_bp_tree(self, group_id: str) -> List[Dict]:
        """API 4.4: 获取 BP 树（简化）"""
        return self._call_api("/bp/task/v2/getSimpleTree", {"groupId": group_id})
    
    def get_goal_detail(self, goal_id: str) -> Dict:
        """API 4.5: 获取目标详情"""
        return self._call_api("/bp/task/v2/getGoalAndKeyResult", {"id": goal_id})
    
    def find_group_id(self, org_tree: List[Dict], org_name: str) -> Optional[str]:
        """在组织树中查找 groupId"""
        for node in org_tree:
            if org_name in node.get("name", ""):
                return node.get("id")
            if node.get("children"):
                result = self.find_group_id(node["children"], org_name)
                if result:
                    return result
        return None
    
    def fetch_bp_data(
        self,
        org_name: str,
        person_name: Optional[str] = None,
        period_id: str = None
    ) -> Dict:
        """
        获取完整 BP 数据
        
        返回：
        {
            "org_name": str,
            "person_name": Optional[str],
            "period": str,
            "goals": List[BPGoal]
        }
        """
        # 1. 获取组织架构
        org_tree = self.get_org_tree(period_id)
        
        # 2. 查找组织 ID
        group_id = self.find_group_id(org_tree, org_name)
        if not group_id:
            raise ValueError(f"未找到组织: {org_name}")
        
        # 3. 获取 BP 树
        bp_tree = self.get_bp_tree(group_id)
        
        # 4. 获取每个目标的详情
        goals = []
        for goal_node in bp_tree:
            if goal_node.get("type") != "目标":
                continue
            
            detail = self.get_goal_detail(goal_node["id"])
            
            goal = BPGoal(
                id=goal_node["id"],
                code=goal_node.get("levelNumber", ""),
                name=goal_node.get("name", ""),
                type="personal" if goal_node.get("levelNumber", "").startswith("P") else "org",
                measure_standard=detail.get("measureStandard"),
                number_anchors=extract_number_anchors(detail.get("measureStandard", "")),
                key_results=detail.get("keyResults", []),
                status=goal_node.get("status")
            )
            goals.append(goal)
        
        return {
            "org_name": org_name,
            "person_name": person_name,
            "period": "2026年度计划BP",
            "goals": goals
        }


def extract_number_anchors(text: str) -> List[str]:
    """从文本中提取数字锚点"""
    import re
    
    if not text:
        return []
    
    # 匹配模式：≥90%, ≤5%, 100%, 3月31日 等
    patterns = [
        r"[≥<>≤]\s*\d+\.?\d*%?",  # 百分比
        r"\d+月\d+日",              # 日期
        r"\d+个",                   # 数量
    ]
    
    anchors = []
    for pattern in patterns:
        anchors.extend(re.findall(pattern, text))
    
    return anchors


# 使用示例
if __name__ == "__main__":
    client = BPAPIClient(
        base_url="https://sg-al-cwork-web.mediportal.com.cn/open-api",
        app_key="TsFhRR7OywNULeHPqudePf85STc4EpHI"
    )
    
    data = client.fetch_bp_data("产品中心", period_id="1994002024299085826")
    print(f"获取到 {len(data['goals'])} 个目标")
    for goal in data["goals"]:
        print(f"  - {goal.code}: {goal.name}")
