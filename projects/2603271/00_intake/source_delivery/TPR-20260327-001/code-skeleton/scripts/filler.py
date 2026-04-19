"""
模板填充模块

将 BP 数据填充到模板中
"""

import re
from typing import Dict, List, Optional
from datetime import datetime


def fill_template(template: str, bp_data: Dict, template_type: str) -> str:
    """
    填充模板主函数
    
    Args:
        template: 模板内容（Markdown）
        bp_data: BP 数据
        template_type: 模板类型（月报/季报/半年报/年报）
    
    Returns:
        填充后的 Markdown 内容
    """
    content = template
    
    # 元数据填充
    content = fill_metadata(content, bp_data)
    
    # 第1章：汇报综述
    content = fill_chapter_1(content, bp_data, template_type)
    
    # 第2章：BP目标承接
    content = fill_chapter_2(content, bp_data, template_type)
    
    # 第3-8章（简化处理）
    content = fill_remaining_chapters(content, bp_data, template_type)
    
    return content


def fill_metadata(content: str, bp_data: Dict) -> str:
    """填充元数据"""
    now = datetime.now().strftime("%Y-%m-%d")
    
    replacements = {
        "[项目编号]": f"TPR-{datetime.now().strftime('%Y%m%d')}-001",
        "[节点编号]": "NODE-001",
        "[模板编号]": "TPL-001",
        "[日期]": now,
        "DRAFT": "DRAFT"
    }
    
    for key, value in replacements.items():
        content = content.replace(key, value)
    
    return content


def fill_chapter_1(content: str, bp_data: Dict, template_type: str) -> str:
    """填充第1章：汇报综述"""
    
    org_name = bp_data.get("org_name", "")
    person_name = bp_data.get("person_name", "")
    goals = bp_data.get("goals", [])
    
    # 时间维度描述
    time_desc = {
        "月报": "本月",
        "季报": "本季度",
        "半年报": "半年度",
        "年报": "年度"
    }
    
    # 填充总体判断（默认值）
    overall_judgment = f"[待填写：{time_desc.get(template_type, '')}总体判断]"
    content = replace_placeholder(content, f"{time_desc.get(template_type, '')}总体判断", overall_judgment)
    content = replace_placeholder(content, f"{time_desc.get(template_type, '')}总体评价", overall_judgment)
    
    # 提取关键成果
    key_results = []
    for goal in goals[:3]:  # 取前3个
        if goal.key_results:
            for kr in goal.key_results[:1]:
                key_results.append(f"- {goal.name}：{kr.get('name', '')}")
    
    if key_results:
        key_results_text = "\n".join(key_results)
        content = replace_placeholder(content, "1-3项关键成果", key_results_text)
        content = replace_placeholder(content, "3-5项，每项一句话", key_results_text)
    
    return content


def fill_chapter_2(content: str, bp_data: Dict, template_type: str) -> str:
    """填充第2章：BP目标承接"""
    
    goals = bp_data.get("goals", [])
    
    # 时间维度描述
    time_desc = {
        "月报": "本月",
        "季报": "本季度",
        "半年报": "半年",
        "年报": "年度"
    }
    
    # 生成每个 BP 维度的章节
    bp_sections = []
    for i, goal in enumerate(goals, 1):
        section = generate_bp_section(goal, i, time_desc.get(template_type, ""))
        bp_sections.append(section)
    
    # 替换模板中的 BP 维度占位符
    if bp_sections:
        # 找到第2章的位置
        chapter_2_match = re.search(r"## 2\..*?(?=## 3\.|$)", content, re.DOTALL)
        if chapter_2_match:
            # 构建新的第2章内容
            new_chapter_2 = f"## 2. BP目标承接与对齐情况\n\n" + "\n".join(bp_sections)
            content = content[:chapter_2_match.start()] + new_chapter_2 + content[chapter_2_match.end():]
    
    return content


def generate_bp_section(goal, index: int, time_prefix: str) -> str:
    """生成单个 BP 维度的章节"""
    
    code = goal.code or "[待确认编码]"
    name = goal.name or "[待确认名称]"
    measure_standard = goal.measure_standard or "[待确认衡量标准]"
    number_anchors = goal.number_anchors or []
    
    # 判断编码类型
    if code.startswith("P"):
        personal_code = code
        org_code = "[对应组织BP编码]"
    else:
        personal_code = "[对应个人BP编码]"
        org_code = code
    
    section = f"""### 2.{index} [{name}]

**对标BP：** {personal_code}（个人）/ {org_code}（组织）

**{time_prefix}承接重点：**
- {measure_standard}

**当前状态：**
- 量化指标：{', '.join(number_anchors) if number_anchors else '[待填写]'}
- 偏离判断：[红/黄/绿]

**是否偏离预期：**
- [是/否]，[偏离率]
"""
    
    return section


def fill_remaining_chapters(content: str, bp_data: Dict, template_type: str) -> str:
    """填充第3-8章（简化处理）"""
    
    # 这些章节需要实际数据支撑，这里只做基础替换
    # 实际实现时需要根据 BP 数据填充
    
    return content


def replace_placeholder(content: str, placeholder: str, value: str) -> str:
    """替换占位符"""
    # 尝试多种格式
    patterns = [
        f"[{placeholder}]",
        f"[填写：{placeholder}]",
        f"[填写:{placeholder}]",
        placeholder
    ]
    
    for pattern in patterns:
        content = content.replace(pattern, value)
    
    return content


if __name__ == "__main__":
    # 测试
    from api_client import BPAPIClient, extract_number_anchors
    
    # 模拟 BP 数据
    bp_data = {
        "org_name": "产品中心",
        "person_name": "林刚",
        "period": "2026年度计划BP",
        "goals": [
            {
                "id": "1",
                "code": "A3-1",
                "name": "上市得分",
                "type": "org",
                "measure_standard": "年度上市得分≥7分",
                "number_anchors": ["≥7分"],
                "key_results": [{"name": "完成2个产品上市"}]
            }
        ]
    }
    
    template = """
## 1. 汇报综述

- **本月总体判断：**
  [填写：正常 / 承压 / 预警]

## 2. BP目标承接与对齐情况

### 2.1 [BP维度1]
- 对应个人 BP：[编码]
"""
    
    filled = fill_template(template, bp_data, "月报")
    print(filled)
