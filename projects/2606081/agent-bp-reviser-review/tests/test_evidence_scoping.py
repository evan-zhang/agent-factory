#!/usr/bin/env python3
"""
可执行测试：证据语义分层（对应 test_evidence_scoping.md 规格）
"""

import sys
import os
import unittest

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from bp_reviser import TargetStandard, EvidenceBundle, EvidenceLevelEnum


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


class TestEvidenceScoping(unittest.TestCase):

    def setUp(self):
        self.standard = _standard()

    def test_case1_primary(self):
        """用例1：goal_report + 责任人张三 → primary（US-01, US-10）"""
        eb = EvidenceBundle({
            "evidence_id": "ev_001",
            "evidence_type": "goal_report",
            "responsibility_chain": ["公司", "研发部", "张三"],
            "evidence_content": {"summary": "已完成2个新品种注册"},
        })
        self.assertEqual(eb.classify(self.standard), EvidenceLevelEnum.PRIMARY)

    def test_case2_secondary(self):
        """用例2：result_report + 协作方（责任链中但非末尾责任人）→ secondary"""
        eb = EvidenceBundle({
            "evidence_id": "ev_002",
            "evidence_type": "result_report",
            "responsibility_chain": ["研发部"],  # 在责任链中，但非末尾责任人
            "evidence_content": {"summary": "协作佐证"},
        })
        self.assertEqual(eb.classify(self.standard), EvidenceLevelEnum.SECONDARY)

    def test_case3_background(self):
        """用例3：document_record + 责任链匹配 → background（法务/泛背景材料）"""
        eb = EvidenceBundle({
            "evidence_id": "ev_003",
            "evidence_type": "document_record",
            "responsibility_chain": ["研发部"],
            "evidence_content": {"summary": "法务文档"},
        })
        self.assertEqual(eb.classify(self.standard), EvidenceLevelEnum.BACKGROUND)

    def test_case4_insufficient(self):
        """用例4：无责任链 → insufficient"""
        eb = EvidenceBundle({
            "evidence_id": "ev_004",
            "evidence_type": "manual_confirmation",
            "responsibility_chain": [],
            "evidence_content": {"summary": "无责任人"},
        })
        self.assertEqual(eb.classify(self.standard), EvidenceLevelEnum.INSUFFICIENT)

    def test_case5_legal_not_progress(self):
        """用例5：法务证据≠注册进展，document_record 不能自动当主证据（US-01,10,15）"""
        eb = EvidenceBundle({
            "evidence_id": "ev_005",
            "evidence_type": "document_record",
            "responsibility_chain": ["公司", "研发部", "张三"],  # 即使责任人完整
            "evidence_content": {"summary": "投资法务文档"},
        })
        # document_record 即使责任人匹配也只能是 background，不能是 primary
        self.assertEqual(eb.classify(self.standard), EvidenceLevelEnum.BACKGROUND)

    def test_case6_out_of_chain_insufficient(self):
        """用例6：责任链不匹配（财务部）→ insufficient"""
        eb = EvidenceBundle({
            "evidence_id": "ev_006",
            "evidence_type": "goal_report",
            "responsibility_chain": ["财务部"],
            "evidence_content": {"summary": "不相关部门"},
        })
        self.assertEqual(eb.classify(self.standard), EvidenceLevelEnum.INSUFFICIENT)

    def test_case7_auto_defect_detection(self):
        """用例7：证据内容含缺陷关键词 → 自动标记 risk_flag（P3修复, ER-07）"""
        eb = EvidenceBundle({
            "evidence_id": "ev_007",
            "evidence_type": "goal_report",
            "responsibility_chain": ["公司", "研发部", "张三"],
            "evidence_content": {"summary": "数据不一致，存在明显错误"},
        })
        eb.classify(self.standard)
        self.assertTrue(eb.risk_flag, "含缺陷关键词应自动标记 risk_flag")


if __name__ == "__main__":
    unittest.main(verbosity=2)
