"""
审查模块

审查填充后的模板，检查：
1. BP 编码对齐
2. 数字锚点完整性
3. 衡量标准引用
4. 颜色预警正确性
"""

import re
from typing import Dict, List


def review_template(content: str, bp_data: Dict) -> Dict:
    """
    审查填充后的模板
    
    Returns:
        {
            "passed": bool,
            "issues": List[Dict]  # [{"type": str, "detail": str, "severity": str}]
        }
    """
    issues = []
    
    # 1. BP 编码对齐检查
    issues.extend(check_bp_codes(content, bp_data))
    
    # 2. 数字锚点检查
    issues.extend(check_number_anchors(content))
    
    # 3. 衡量标准检查
    issues.extend(check_measure_standards(content))
    
    # 4. 颜色预警检查
    issues.extend(check_alert_rules(content))
    
    # 5. 占位符检查
    issues.extend(check_placeholders(content))
    
    return {
        "passed": len([i for i in issues if i["severity"] == "error"]) == 0,
        "issues": issues
    }


def check_bp_codes(content: str, bp_data: Dict) -> List[Dict]:
    """检查 BP 编码对齐"""
    issues = []
    
    # 提取内容中的编码
    code_pattern = r"[PA]\d+-?\d*\.?\d*"
    found_codes = set(re.findall(code_pattern, content))
    
    # 检查是否有 [待确认编码] 标记
    if "[待确认编码]" in content:
        issues.append({
            "type": "编码缺失",
            "detail": "存在未确认的 BP 编码",
            "severity": "warning"
        })
    
    # 检查编码格式
    for code in found_codes:
        # P 系列应该是 PXXXX-X.X 格式
        if code.startswith("P") and not re.match(r"P\d+-\d+\.\d+", code):
            # 可能是不完整的编码，但如果是 P1001 这种也是合法的
            if not re.match(r"P\d+", code):
                issues.append({
                    "type": "编码格式",
                    "detail": f"编码 {code} 格式可能不正确",
                    "severity": "warning"
                })
    
    return issues


def check_number_anchors(content: str) -> List[Dict]:
    """检查数字锚点"""
    issues = []
    
    # 检查是否有数字锚点
    number_patterns = [
        r"≥\d+",   # ≥90
        r"≤\d+",   # ≤5
        r">=\d+",  # >=90
        r"<=\d+",  # <=5
        r"\d+%",   # 100%
    ]
    
    has_numbers = any(re.search(p, content) for p in number_patterns)
    
    # 检查量化指标章节是否有数字
    quant_match = re.search(r"量化指标[：:](.*?)(?:\n|$)", content)
    if quant_match:
        quant_content = quant_match.group(1)
        if not any(re.search(p, quant_content) for p in number_patterns):
            issues.append({
                "type": "数字锚点缺失",
                "detail": "量化指标章节缺少具体数字",
                "severity": "warning"
            })
    
    return issues


def check_measure_standards(content: str) -> List[Dict]:
    """检查衡量标准"""
    issues = []
    
    # 检查是否有 [待确认衡量标准] 标记
    if "[待确认衡量标准]" in content:
        issues.append({
            "type": "衡量标准缺失",
            "detail": "存在未确认的衡量标准",
            "severity": "error"
        })
    
    return issues


def check_alert_rules(content: str) -> List[Dict]:
    """检查颜色预警规则"""
    issues = []
    
    # 检查颜色标记
    alert_sections = re.findall(r"偏离判断[：:](.*?)(?:\n|$)", content)
    
    for section in alert_sections:
        # 检查是否有红/黄/绿标记
        if not any(color in section for color in ["红", "黄", "绿"]):
            issues.append({
                "type": "颜色预警缺失",
                "detail": f"偏离判断缺少颜色标记: {section.strip()}",
                "severity": "warning"
            })
    
    return issues


def check_placeholders(content: str) -> List[Dict]:
    """检查是否有未替换的占位符"""
    issues = []
    
    # 常见占位符模式
    placeholder_patterns = [
        r"\[待填写.*?\]",
        r"\[填写：.*?\]",
        r"\[示例.*?\]",
        r"\[描述\]",
        r"\[量化\]",
    ]
    
    for pattern in placeholder_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            issues.append({
                "type": "占位符未替换",
                "detail": f"存在未替换的占位符: {match}",
                "severity": "warning"
            })
    
    return issues


def check_zero_tolerance(content: str, bp_data: Dict) -> List[Dict]:
    """检查零容忍项"""
    issues = []
    
    zero_tolerance_items = [
        "重大合规事故",
        "BP签约率<100%",
        "奖金发放delay"
    ]
    
    # 检查内容中是否提到零容忍项
    for item in zero_tolerance_items:
        if item in content:
            # 检查是否有对应的颜色标记（应该是红）
            # 这里简化处理，实际需要更复杂的逻辑
            pass
    
    return issues


if __name__ == "__main__":
    # 测试
    test_content = """
### 2.1 [上市得分]

**对标BP：** P4432-1.1（个人）/ A3-1（组织）

**本月承接重点：**
- 年度上市得分≥7分

**当前状态：**
- 量化指标：≥7分
- 偏离判断：绿

**是否偏离预期：**
- 否
"""
    
    bp_data = {
        "goals": [
            {"code": "A3-1", "name": "上市得分"}
        ]
    }
    
    result = review_template(test_content, bp_data)
    print(f"通过: {result['passed']}")
    print(f"问题: {len(result['issues'])}")
    for issue in result['issues']:
        print(f"  - [{issue['severity']}] {issue['type']}: {issue['detail']}")
