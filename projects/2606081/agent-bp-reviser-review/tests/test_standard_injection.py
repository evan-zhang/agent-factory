#!/usr/bin/env python3
"""
可执行测试：标准注入（对应 test_standard_injection.md 规格）
用 unittest，零外部依赖，可直接 python3 tests/test_standard_injection.py 运行
"""

import sys
import os
import unittest

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from bp_reviser import TargetStandard


def _full_standard():
    return {
        "target_code": "ORG_2026_Q1_REG_001",
        "target_name": "完成3个新品种注册",
        "layer": "goal",
        "bp_type": "organization",
        "period": {"start": "2026-01-01", "end": "2026-03-31"},
        "measurements": [{"metric": "注册数量", "target": 3, "current": 1}],
        "source": "BP_System",
        "scope": "全公司",
        "effective_from": "2026-01-01",
        "version": "1.0.0",
        "conflict_policy": "prefer_latest",
        "owner": "张三",
        "responsibility_chain": ["公司", "研发部", "张三"],
        "evidence_hint": [],
        "status_rule": {},
        "writeback_rule": {},
    }


class TestStandardInjection(unittest.TestCase):

    def test_case1_full_fields_valid(self):
        """用例1：标准完整字段注入 → 通过"""
        ok, errors = TargetStandard(_full_standard()).validate()
        self.assertTrue(ok, f"完整字段应通过: {errors}")
        self.assertEqual(errors, [])

    def test_case2_missing_required_fields(self):
        """用例2：缺少必填字段 → 失败并列出缺失字段（16字段校验）"""
        data = {
            "target_code": "ORG_2026_Q1_REG_001",
            "target_name": "完成3个新品种注册",
            "layer": "goal",
            "bp_type": "organization",
            "period": {"start": "2026-01-01", "end": "2026-03-31"},
        }
        ok, errors = TargetStandard(data).validate()
        self.assertFalse(ok)
        # 缺失字段应至少包含 source / scope / effective_from / version / conflict_policy / owner
        for field in ["source", "scope", "effective_from", "version", "conflict_policy", "owner"]:
            self.assertTrue(any(field in e for e in errors), f"应检测到缺失字段 {field}: {errors}")

    def test_case3_invalid_layer(self):
        """用例3：无效 layer 值 → 失败"""
        data = _full_standard()
        data["layer"] = "invalid_layer"
        ok, errors = TargetStandard(data).validate()
        self.assertFalse(ok)
        self.assertTrue(any("layer" in e for e in errors))

    def test_case4_empty_responsibility_chain(self):
        """用例4：空责任链 → 失败"""
        data = _full_standard()
        data["responsibility_chain"] = []
        ok, errors = TargetStandard(data).validate()
        self.assertFalse(ok)
        self.assertTrue(any("责任链" in e for e in errors))

    def test_case5_invalid_bp_type(self):
        """用例5：无效 bp_type → 失败（P1修复新增）"""
        data = _full_standard()
        data["bp_type"] = "wrong_type"
        ok, errors = TargetStandard(data).validate()
        self.assertFalse(ok)
        self.assertTrue(any("bp_type" in e for e in errors))

    def test_case6_invalid_conflict_policy(self):
        """用例6：无效 conflict_policy → 失败（P1修复新增）"""
        data = _full_standard()
        data["conflict_policy"] = "bad_policy"
        ok, errors = TargetStandard(data).validate()
        self.assertFalse(ok)
        self.assertTrue(any("conflict_policy" in e for e in errors))

    def test_case7_owner_must_be_chain_tail(self):
        """用例7：owner 必须是责任链末尾元素 → 失败（P1修复新增）"""
        data = _full_standard()
        data["owner"] = "李四"  # 责任链末尾是张三
        ok, errors = TargetStandard(data).validate()
        self.assertFalse(ok)
        self.assertTrue(any("owner" in e for e in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
