"""
BP 解析模块

从 BP 数据中提取结构化信息
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class BPGoal:
    """BP 目标"""
    id: str
    code: str
    name: str
    type: str
    measure_standard: Optional[str] = None
    number_anchors: List[str] = None
    key_results: List[Dict] = None
    status: Optional[str] = None


@dataclass
class BPData:
    """BP 数据容器"""
    org_name: str
    person_name: str
    period: str
    goals: List[BPGoal]


def parse_bp_from_api(api_data: dict) -> BPData:
    """从 API 返回数据解析为 BPData"""
    
    if not api_data:
        return BPData(goals=[], org_name="", person_name="", period="")
    
    org_name = api_data.get("org_name", "")
    person_name = api_data.get("person_name", "")
    period = api_data.get("period", "")
    
    goals = []
    for g in api_data.get("goals", []):
        goal = BPGoal(
            id=g.get("id", ""),
            code=g.get("levelNumber", ""),
            name=g.get("name", ""),
            type="personal" if g.get("levelNumber", "").startswith("P") else "org",
            measure_standard=g.get("measureStandard"),
            number_anchors=extract_number_anchors(g.get("measureStandard") or ""),
            key_results=g.get("keyResults", []),
            status=g.get("status")
        )
        goals.append(goal)
    
    return BPData(
        org_name=org_name,
        person_name=person_name,
        period=period,
        goals=goals
    )


def parse_bp_from_file(file_path: str) -> BPData:
    """从 Markdown 文件解析 BP 数据"""
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 简化处理
    return BPData(
        org_name="从文件名解析",
        person_name="",
        period="",
        goals=[]
    )


def extract_number_anchors(text: str) -> List[str]:
    """从文本中提取数字锚点"""
    if not text:
        return []
    
    anchors = []
    
    # 匹配模式
    patterns = [
        r"[≥<>≤]\s*\d+\.?\d*%?",  # 百分比
        r"\d+月\d+日",              # 日期
        r"\d+个",                   # 数量
        r"\d+亿",                  # 金额
    ]
    
    for pattern in patterns:
        anchors.extend(re.findall(pattern, text))
    
    return anchors


if __name__ == "__main__":
    # 测试
    bp_data = {
        "org_name": "产品中心",
        "person_name": "林刚",
        "period": "2026年度计划BP",
        "goals": [
            {
                "id": "1",
                "levelNumber": "A3-1",
                "name": "上市得分",
                "measureStandard": "年度上市得分≥7分",
                "keyResults": [{"name": "完成2个产品上市"}],
                "status": "green"
            }
        ]
    }
    
    result = parse_bp_from_api(bp_data)
    print(f"组织: {result.org_name}")
    print(f"目标数: {len(result.goals)}")
    for goal in result.goals:
        print(f"  - {goal.code}: {goal.name}")
