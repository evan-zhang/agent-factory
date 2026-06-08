#!/usr/bin/env python3
"""
可执行测试：修订闸门决策（对应 test_revision_gating.md 规格）
"""

import sys
import os
import unittest

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from bp_reviser import (
    gate_decision, downgrade_user_feedback,
    RevisionStatusEnum,
)


class TestRevisionGating(unittest.TestCase):

    def test_case1_black_to_green_hold(self):
        """用例1：黑→绿 高风险 → hold + review_flag（US-05, US-11）"""
        r = gate_decision("black", "green")
        self.assertEqual(r["revision_status"], RevisionStatusEnum.HOLD)
        self.assertTrue(r["review_flag"])

    def test_case2_red_to_green_hold(self):
        """用例2：红→绿 高风险 → hold + review_flag（US-05, US-11）"""
        r = gate_decision("red", "green")
        self.assertEqual(r["revision_status"], RevisionStatusEnum.HOLD)
        self.assertTrue(r["review_flag"])

    def test_case3_yellow_to_green_approved(self):
        """用例3：黄→绿 非高风险 → approved（黄绿不在高风险名单）"""
        r = gate_decision("yellow", "green")
        self.assertEqual(r["revision_status"], RevisionStatusEnum.APPROVED)
        self.assertFalse(r["review_flag"])

    def test_case4_green_to_green_keep(self):
        """用例4：绿→绿 同色 → approved（保持不变）"""
        r = gate_decision("green", "green")
        self.assertEqual(r["revision_status"], RevisionStatusEnum.APPROVED)
        self.assertFalse(r["review_flag"])

    def test_case5_green_to_yellow_approved(self):
        """用例5：绿→黄 降级（回退类）→ approved"""
        r = gate_decision("green", "yellow")
        self.assertEqual(r["revision_status"], RevisionStatusEnum.APPROVED)
        self.assertFalse(r["review_flag"])

    def test_case6_black_to_yellow_approved(self):
        """用例6：黑→黄 非高风险（只有黑→绿/红→绿是高风险）→ approved"""
        r = gate_decision("black", "yellow")
        self.assertEqual(r["revision_status"], RevisionStatusEnum.APPROVED)
        self.assertFalse(r["review_flag"])

    def test_case7_feedback_downgrade(self):
        """用例7：用户反馈降级为 hypothesis（US-05, US-11）"""
        result = downgrade_user_feedback("把目标改成绿色")
        self.assertEqual(result["status"], "pending_verification")
        self.assertEqual(result["hypothesis"], "把目标改成绿色")
        self.assertTrue(len(result["search_tasks"]) > 0)

    def test_case8_high_risk_only_to_green(self):
        """用例8：高风险仅限 →绿，红→黄不触发 review_flag"""
        r = gate_decision("red", "yellow")
        self.assertEqual(r["revision_status"], RevisionStatusEnum.APPROVED)
        self.assertFalse(r["review_flag"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
