#!/usr/bin/env python3
"""
可执行测试：写回一致性校验（对应 test_writeback_consistency.md 规格）
"""

import sys
import os
import unittest

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from bp_reviser import TargetStandard, EvidenceBundle, RevisionOutput
from helpers import run_consistency_check


def _standard():
    return TargetStandard({
        "target_code": "ORG_2026_Q1_REG_001",
        "target_name": "完成3个新品种注册",
        "layer": "goal",
        "bp_type": "organization",
        "period": {"start": "2026-01-01", "end": "2026-03-31"},
        "measurements": [],
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
    })


def _primary_evidence():
    return EvidenceBundle({
        "evidence_id": "ev_001",
        "evidence_type": "goal_report",
        "evidence_level": "primary",
        "responsibility_chain": ["公司", "研发部", "张三"],
        "evidence_content": {"summary": "ok"},
    })


class TestWritebackConsistency(unittest.TestCase):

    def setUp(self):
        self.standard = _standard()

    def test_case1_green_with_primary_passes(self):
        """用例1：绿灯 + 主要证据 → 通过（US-03）"""
        out = RevisionOutput()
        out.target_code = "ORG_2026_Q1_REG_001"
        out.evidence_bundle_ref = ["ev_001"]
        out.writeback_patch = {
            "text_updates": [],
            "color_updates": [{"target": "ORG_2026_Q1_REG_001", "new_color": "green"}],
            "evidence_updates": [],
        }
        ev = _primary_evidence()
        ev.evidence_level = "primary"
        result = run_consistency_check(out, self.standard, [ev])
        self.assertTrue(result["passed"], f"绿灯+主要证据应通过: {result['issues']}")

    def test_case2_black_with_evidence_fails(self):
        """用例2：黑灯 + 有效证据 → 失败（US-03）"""
        out = RevisionOutput()
        out.target_code = "ORG_2026_Q1_REG_001"
        out.evidence_bundle_ref = ["ev_001"]
        out.writeback_patch = {
            "text_updates": [],
            "color_updates": [{"target": "ORG_2026_Q1_REG_001", "new_color": "black"}],
            "evidence_updates": [],
        }
        result = run_consistency_check(out, self.standard, [_primary_evidence()])
        self.assertFalse(result["passed"])
        self.assertTrue(any("黑灯" in i for i in result["issues"]))

    def test_case3_green_without_primary_fails(self):
        """用例3：绿灯 + 无主要证据 → 失败（US-03）"""
        out = RevisionOutput()
        out.target_code = "ORG_2026_Q1_REG_001"
        out.evidence_bundle_ref = []
        out.writeback_patch = {
            "text_updates": [],
            "color_updates": [{"target": "ORG_2026_Q1_REG_001", "new_color": "green"}],
            "evidence_updates": [],
        }
        result = run_consistency_check(out, self.standard, [])
        self.assertFalse(result["passed"])
        self.assertTrue(any("绿灯" in i for i in result["issues"]))

    def test_case4_cross_target_text_fails(self):
        """用例4：跨目标文字写回 → 失败（US-04）"""
        out = RevisionOutput()
        out.target_code = "ORG_2026_Q1_REG_001"
        out.writeback_patch = {
            "text_updates": [{"target": "OTHER_TARGET", "field": "desc", "new_value": "x"}],
            "color_updates": [],
            "evidence_updates": [],
        }
        result = run_consistency_check(out, self.standard, [])
        self.assertFalse(result["passed"])
        self.assertTrue(any("跨目标文字" in i for i in result["issues"]))

    def test_case5_cross_target_color_fails(self):
        """用例5：跨目标色块写回 → 失败（US-04）"""
        out = RevisionOutput()
        out.target_code = "ORG_2026_Q1_REG_001"
        out.writeback_patch = {
            "text_updates": [],
            "color_updates": [{"target": "OTHER_TARGET", "new_color": "green"}],
            "evidence_updates": [],
        }
        result = run_consistency_check(out, self.standard, [])
        self.assertFalse(result["passed"])
        self.assertTrue(any("跨目标色块" in i for i in result["issues"]))

    def test_case7_no_updates_passes(self):
        """用例7：无更新 → 通过（正常流程）"""
        out = RevisionOutput()
        out.target_code = "ORG_2026_Q1_REG_001"
        out.writeback_patch = {"text_updates": [], "color_updates": [], "evidence_updates": []}
        result = run_consistency_check(out, self.standard, [])
        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
