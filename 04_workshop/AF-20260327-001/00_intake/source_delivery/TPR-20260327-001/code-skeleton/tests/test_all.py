"""
测试模块
"""

import unittest
from pathlib import Path

from input_handler import parse_user_input
from reviewer import review_template


class TestInputHandler(unittest.TestCase):
    """输入解析测试"""
    
    def test_parse_template_types(self):
        """测试模板类型解析"""
        test_cases = [
            ("生成四套", ["月报", "季报", "半年报", "年报"]),
            ("只做季报", ["季报"]),
            ("月报和年报", ["月报", "年报"]),
            ("把季报和半年报给我", ["季报", "半年报"]),
        ]
        
        for input, expected in test_cases:
            result = parse_user_input(input)
            self.assertEqual(result["template_types"], expected)
    
    def test_parse_org_name(self):
        """测试组织名解析"""
        result = parse_user_input("为产品中心生成四套")
        self.assertEqual(result["org_name"], "产品中心")


class TestReviewer(unittest.TestCase):
    """审查器测试"""
    
    def test_review_template_pass(self):
        """测试审查通过"""
        content = """
### 2.1 [上市得分]

**对标BP：** P4432-1.1（个人）/ A3-1（组织）

**本月承接重点：**
- 年度上市得分≥7分

**当前状态：**
- 量化指标：≥7分
- 偏离判断：绿
"""
        
        bp_data = {
            "goals": [{"code": "A3-1", "name": "上市得分"}]
        }
        
        result = review_template(content, bp_data)
        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()
