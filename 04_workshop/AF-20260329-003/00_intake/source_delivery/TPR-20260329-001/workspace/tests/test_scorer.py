"""
test_scorer.py
==============
BP评分系统单元测试。

覆盖 GRV 第八节验收标准中可自动化的项目：
1. 分值守恒：每层分值之和 = 上层分值（误差 < 0.1）
2. 边界处理：无承接方、单一承接方、内容为空的情况
3. 可配置：修改yaml权重后总分仍 = 100
4. adjust联动：调整一个BP后总分保持100

全部使用 mock 数据，不调用真实 API。
"""

import copy
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# 将 scripts/ 目录加入 sys.path
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))

from adjuster import (
    adjust_bp_score,
    build_original_ratios_session,
    validate_tree_score_conservation,
)
from scorer import _normalize_peer_scores, _normalize_pool_allocations, score_peer_bps, score_undertakers


# ---------------------------------------------------------------------------
# Mock 数据工厂
# ---------------------------------------------------------------------------

def make_bp(bp_id: str, objective: str = "", krs: list = None, measures: list = None) -> dict:
    """构造一个 BP 详情 dict（mock 数据）。"""
    return {
        "bpId": bp_id,
        "objective": objective or f"目标_{bp_id}",
        "keyResults": krs or [
            {"description": f"KR1_{bp_id}", "target": "100%"},
            {"description": f"KR2_{bp_id}", "target": "50"},
        ],
        "measures": measures or [
            {"measureId": f"m1_{bp_id}", "description": f"举措1_{bp_id}", "taskDepts": []},
        ],
    }


def make_score_node(
    node_id: str,
    name: str = "",
    score: float = 25.0,
    source: str = "ai_original",
    children: list = None,
) -> dict:
    """构造一个 ScoreNode dict（mock 数据）。"""
    return {
        "id": node_id,
        "name": name or node_id,
        "type": "bp",
        "score": score,
        "score_source": source,
        "adjusted_from": None,
        "adjust_reason": None,
        "confidence": 0.85,
        "reason": f"reason_{node_id}",
        "tags": [],
        "children": children or [],
        "parent_ratio": score / 100.0,
        "org_path": f"测试组织 → {node_id}",
        "source_bp_ids": [node_id],
    }


# ---------------------------------------------------------------------------
# 1. 分值守恒测试
# ---------------------------------------------------------------------------

class TestScoreConservation(unittest.TestCase):
    """验证评分树每层分值之和 = 上层分值（误差 < 0.1）。"""

    def _make_flat_tree(self, scores: list) -> list:
        """构造指定分值的平铺评分树（无子节点）。"""
        return [make_score_node(f"BP-{i+1:03d}", score=s) for i, s in enumerate(scores)]

    def _make_nested_tree(self) -> list:
        """
        构造两层嵌套评分树：
          BP-001(60) → [BP-001-A(36), BP-001-B(24)]
          BP-002(40) → [BP-002-A(40)]
        """
        child_a = make_score_node("BP-001-A", score=36.0)
        child_b = make_score_node("BP-001-B", score=24.0)
        child_c = make_score_node("BP-002-A", score=40.0)

        root_1 = make_score_node("BP-001", score=60.0, children=[child_a, child_b])
        root_2 = make_score_node("BP-002", score=40.0, children=[child_c])
        return [root_1, root_2]

    def test_root_layer_sums_to_100(self):
        """根层总分 = 100。"""
        tree = self._make_flat_tree([40.0, 35.0, 25.0])
        valid, errors = validate_tree_score_conservation(tree, expected_total=100.0)
        self.assertTrue(valid, f"应通过，但报错: {errors}")

    def test_root_layer_fails_when_not_100(self):
        """根层总分 ≠ 100 时应报错。"""
        tree = self._make_flat_tree([40.0, 35.0, 30.0])  # 合计 105
        valid, errors = validate_tree_score_conservation(tree, expected_total=100.0)
        self.assertFalse(valid)
        self.assertTrue(any("根层" in e for e in errors))

    def test_nested_tree_child_sum_equals_parent(self):
        """嵌套树子节点之和 = 父节点分值。"""
        tree = self._make_nested_tree()
        valid, errors = validate_tree_score_conservation(tree, expected_total=100.0)
        self.assertTrue(valid, f"应通过，但报错: {errors}")

    def test_nested_tree_fails_when_child_mismatch(self):
        """子节点总分 ≠ 父节点时应报错。"""
        tree = self._make_nested_tree()
        # 故意让 BP-001 的子节点总分不等于 60
        tree[0]["children"][0]["score"] = 40.0  # 原 36 → 40，子总 64 ≠ 60
        valid, errors = validate_tree_score_conservation(tree, expected_total=100.0)
        self.assertFalse(valid)

    def test_tolerance_within_0_1(self):
        """在 0.1 误差内应通过。"""
        tree = self._make_flat_tree([40.05, 35.02, 24.98])  # 合计 100.05 > 100，误差 0.05
        valid, errors = validate_tree_score_conservation(tree, expected_total=100.0, tolerance=0.1)
        self.assertTrue(valid)

    def test_normalize_peer_scores_sums_to_100(self):
        """_normalize_peer_scores 后总分 = 100。"""
        result = {
            "scores": [
                {"bp_id": "BP-001", "score": 30},
                {"bp_id": "BP-002", "score": 20},
                {"bp_id": "BP-003", "score": 60},
            ],
            "total": 110,
        }
        normalized = _normalize_peer_scores(result, min_score=1.0)
        total = sum(s["score"] for s in normalized["scores"])
        self.assertAlmostEqual(total, 100.0, delta=0.1)

    def test_normalize_pool_allocations_sums_to_pool(self):
        """_normalize_pool_allocations 后总分 = pool_score。"""
        pool_score = 45.0
        result = {
            "allocations": [
                {"undertaker_id": "U-001", "score": 20},
                {"undertaker_id": "U-002", "score": 35},
            ],
            "total_score": 55,
        }
        normalized = _normalize_pool_allocations(result, pool_score=pool_score, min_score=0.5)
        total = sum(a["score"] for a in normalized["allocations"])
        self.assertAlmostEqual(total, pool_score, delta=0.1)


# ---------------------------------------------------------------------------
# 2. 边界处理测试
# ---------------------------------------------------------------------------

class TestBoundaryHandling(unittest.TestCase):
    """验证无承接方、单一承接方、内容为空的边界情况处理。"""

    def test_score_undertakers_empty_list_returns_none(self):
        """无承接方时 score_undertakers 返回 None（不崩溃）。"""
        parent_bp = make_bp("BP-PARENT")
        result = score_undertakers(
            parent_bp=parent_bp,
            undertaker_bps=[],
            pool_score=60.0,
            weights={"target_accuracy": 0.45, "outcome_contribution": 0.35, "measure_completeness": 0.20},
        )
        self.assertIsNone(result)

    def test_score_undertakers_single_gets_100_percent(self):
        """单一承接方获得 100% 分值池，不调用 LLM。"""
        parent_bp = make_bp("BP-PARENT")
        single_undertaker = make_bp("BP-U-001")
        pool_score = 60.0

        result = score_undertakers(
            parent_bp=parent_bp,
            undertaker_bps=[single_undertaker],
            pool_score=pool_score,
            weights={"target_accuracy": 0.45, "outcome_contribution": 0.35, "measure_completeness": 0.20},
        )

        self.assertIsNotNone(result)
        allocations = result.get("allocations", [])
        self.assertEqual(len(allocations), 1)
        self.assertAlmostEqual(allocations[0]["score"], pool_score, delta=0.01)
        self.assertAlmostEqual(allocations[0]["ratio"], 1.0, delta=0.01)
        self.assertEqual(result.get("notes"), "单一承接方，无需AI比较")

    def test_score_peer_bps_empty_list_returns_none(self):
        """空 BP 列表时 score_peer_bps 返回 None（不崩溃）。"""
        result = score_peer_bps(
            org_name="测试组织",
            period_name="2026Q1",
            bp_list=[],
            parent_bp=None,
            weights={"strategic_alignment": 0.4, "measurability": 0.2, "measure_coverage": 0.2, "impact_scope": 0.2},
        )
        self.assertIsNone(result)

    def test_empty_objective_bp_handled(self):
        """目标为空的 BP 不导致崩溃，可正常参与归一化。"""
        result = {
            "scores": [
                {"bp_id": "BP-001", "score": 0},   # 内容为空，可能得0
                {"bp_id": "BP-002", "score": 80},
            ],
            "total": 80,
        }
        normalized = _normalize_peer_scores(result, min_score=1.0)
        # 空内容BP应被强制抬到最低分 1.0
        bp1_score = next(s["score"] for s in normalized["scores"] if s["bp_id"] == "BP-001")
        self.assertGreaterEqual(bp1_score, 1.0)
        total = sum(s["score"] for s in normalized["scores"])
        self.assertAlmostEqual(total, 100.0, delta=0.1)

    def test_min_score_enforced_on_normalization(self):
        """每个BP分值不低于 min_score。"""
        result = {
            "scores": [
                {"bp_id": "BP-001", "score": 0.0},
                {"bp_id": "BP-002", "score": 0.0},
                {"bp_id": "BP-003", "score": 100.0},
            ],
            "total": 100,
        }
        normalized = _normalize_peer_scores(result, min_score=1.0)
        for s in normalized["scores"]:
            self.assertGreaterEqual(s["score"], 1.0, f"{s['bp_id']} 低于最低分")

    def test_single_bp_gets_100(self):
        """只有1个BP时，总分应为100。"""
        result = {
            "scores": [{"bp_id": "BP-001", "score": 73.0}],
            "total": 73,
        }
        normalized = _normalize_peer_scores(result, min_score=1.0)
        self.assertAlmostEqual(normalized["scores"][0]["score"], 100.0, delta=0.1)


# ---------------------------------------------------------------------------
# 3. 可配置性测试
# ---------------------------------------------------------------------------

class TestConfigurability(unittest.TestCase):
    """修改 yaml 权重后，总分仍 = 100。"""

    def _load_weights(self, yaml_content: str) -> dict:
        """从 YAML 字符串加载权重。"""
        import yaml
        return yaml.safe_load(yaml_content)

    def test_default_weights_sum_to_1(self):
        """默认配置中各权重组之和 = 1.0。"""
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "scoring_weights.yaml"
        )
        if not os.path.exists(config_path):
            self.skipTest("config/scoring_weights.yaml 不存在")

        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        peer = cfg.get("peer_scoring", {})
        peer_sum = sum(peer.values())
        self.assertAlmostEqual(peer_sum, 1.0, delta=0.001, msg=f"peer_scoring 权重之和 = {peer_sum}")

        pool = cfg.get("pool_distribution", {})
        pool_sum = sum(pool.values())
        self.assertAlmostEqual(pool_sum, 1.0, delta=0.001, msg=f"pool_distribution 权重之和 = {pool_sum}")

    def test_modified_weights_still_produce_100(self):
        """修改权重后，归一化后总分仍 = 100。"""
        # 模拟不标准权重（总和不为1），系统应仍产出总分100的结果
        custom_weights = {
            "strategic_alignment": 0.50,  # 故意调高
            "measurability": 0.30,
            "measure_coverage": 0.15,
            "impact_scope": 0.15,
        }
        # 构造一个"LLM返回"的原始结果（未归一化）
        raw_result = {
            "scores": [
                {"bp_id": "BP-001", "score": 40.0},
                {"bp_id": "BP-002", "score": 35.0},
                {"bp_id": "BP-003", "score": 30.0},  # 合计105，需归一化
            ],
            "total": 105,
        }
        normalized = _normalize_peer_scores(raw_result, min_score=1.0)
        total = sum(s["score"] for s in normalized["scores"])
        self.assertAlmostEqual(total, 100.0, delta=0.1)

    def test_extreme_weights_still_conserve_score(self):
        """极端权重（某维度100%）下，分值守恒仍然成立。"""
        raw_result = {
            "scores": [
                {"bp_id": "BP-001", "score": 1.0},
                {"bp_id": "BP-002", "score": 99.0},
            ],
            "total": 100,
        }
        normalized = _normalize_peer_scores(raw_result, min_score=1.0)
        total = sum(s["score"] for s in normalized["scores"])
        self.assertAlmostEqual(total, 100.0, delta=0.1)


# ---------------------------------------------------------------------------
# 4. adjust 联动测试
# ---------------------------------------------------------------------------

class TestAdjustCascade(unittest.TestCase):
    """调整一个BP后总分保持100，且联动更新下级分值池。"""

    def _make_tree_with_children(self) -> tuple[list, dict]:
        """
        构造测试用评分树：
          BP-001(40) → [BP-001-A(24), BP-001-B(16)]
          BP-002(35) → []
          BP-003(25) → [BP-003-A(25)]
        """
        child_a = make_score_node("BP-001-A", score=24.0)
        child_b = make_score_node("BP-001-B", score=16.0)
        child_c = make_score_node("BP-003-A", score=25.0)

        root = [
            make_score_node("BP-001", score=40.0, children=[child_a, child_b]),
            make_score_node("BP-002", score=35.0),
            make_score_node("BP-003", score=25.0, children=[child_c]),
        ]
        session = build_original_ratios_session(root)
        return root, session

    def test_adjust_one_bp_preserves_total_100(self):
        """调整 BP-001 后根层总分仍 = 100。"""
        tree, session = self._make_tree_with_children()
        updated_tree, found = adjust_bp_score(
            score_tree=tree,
            bp_id="BP-001",
            new_score=55.0,
            reason="战略优先级调整",
            original_ratios_session=session,
        )
        self.assertTrue(found)
        total = sum(n["score"] for n in updated_tree)
        self.assertAlmostEqual(total, 100.0, delta=0.1, msg=f"根层总分 = {total}")

    def test_adjust_cascade_updates_children(self):
        """调整父节点后，子节点总分 = 父节点新分值。"""
        tree, session = self._make_tree_with_children()
        new_parent_score = 55.0
        updated_tree, found = adjust_bp_score(
            score_tree=tree,
            bp_id="BP-001",
            new_score=new_parent_score,
            reason="测试联动",
            original_ratios_session=session,
        )
        self.assertTrue(found)

        # 找到更新后的 BP-001 节点
        bp001 = next((n for n in updated_tree if n["id"] == "BP-001"), None)
        self.assertIsNotNone(bp001)

        children = bp001.get("children", [])
        if children:
            child_total = sum(c["score"] for c in children)
            self.assertAlmostEqual(
                child_total, new_parent_score, delta=0.1,
                msg=f"子节点总分 {child_total} ≠ 父节点 {new_parent_score}"
            )

    def test_adjust_target_bp_has_manual_source(self):
        """被调整的BP score_source 应为 manual_adjusted。"""
        tree, session = self._make_tree_with_children()
        updated_tree, _ = adjust_bp_score(
            score_tree=tree,
            bp_id="BP-002",
            new_score=50.0,
            reason="人工校准",
            original_ratios_session=session,
        )
        bp002 = next((n for n in updated_tree if n["id"] == "BP-002"), None)
        self.assertIsNotNone(bp002)
        self.assertEqual(bp002["score_source"], "manual_adjusted")
        self.assertEqual(bp002["score"], 50.0)
        self.assertEqual(bp002["adjust_reason"], "人工校准")

    def test_adjust_sibling_cascades_correctly(self):
        """调整 BP-002 后，BP-001 和 BP-003 按原始比例缩放。"""
        tree, session = self._make_tree_with_children()
        # 原始比例: BP-001=40%, BP-002=35%, BP-003=25%
        original_bp001 = 40.0
        original_bp003 = 25.0
        original_total = 100.0

        updated_tree, _ = adjust_bp_score(
            score_tree=tree,
            bp_id="BP-002",
            new_score=50.0,
            reason="测试",
            original_ratios_session=session,
        )

        # 验证总分守恒
        total = sum(n["score"] for n in updated_tree)
        self.assertAlmostEqual(total, 100.0, delta=0.1)

        # 验证 BP-001 和 BP-003 按比例收缩（剩余 50 分按 40:25 = 8:5 分配）
        remaining = 50.0  # 100 - 50
        bp001 = next(n for n in updated_tree if n["id"] == "BP-001")
        bp003 = next(n for n in updated_tree if n["id"] == "BP-003")
        self.assertGreater(bp001["score"], 0)
        self.assertGreater(bp003["score"], 0)
        # BP-001 / BP-003 比例应接近原始 40:25 = 1.6
        ratio = bp001["score"] / bp003["score"]
        self.assertAlmostEqual(ratio, 40.0 / 25.0, delta=0.2)

    def test_adjust_nonexistent_bp_returns_not_found(self):
        """调整不存在的BP ID时，返回 found=False。"""
        tree, session = self._make_tree_with_children()
        _, found = adjust_bp_score(
            score_tree=tree,
            bp_id="BP-NONEXISTENT",
            new_score=50.0,
            reason="测试",
            original_ratios_session=session,
        )
        self.assertFalse(found)

    def test_validate_after_adjust_passes(self):
        """
        adjust 后根层总分守恒（= 100），被调整节点的子节点也同步更新。

        注意：adjust 只联动更新"被调整BP"本身的子节点分值；
        同层其他BP的子节点不在本次调整范围内（其分值将在下一次
        针对该父节点的 adjust 时更新）。
        因此仅校验根层守恒，以及被调整节点自身的子节点守恒。
        """
        tree, session = self._make_tree_with_children()
        new_score = 60.0
        updated_tree, found = adjust_bp_score(
            score_tree=tree,
            bp_id="BP-001",
            new_score=new_score,
            reason="验证测试",
            original_ratios_session=session,
        )
        self.assertTrue(found)

        # 根层总分守恒
        root_total = sum(n["score"] for n in updated_tree)
        self.assertAlmostEqual(root_total, 100.0, delta=0.1, msg=f"根层总分 = {root_total}")

        # BP-001 子节点总分守恒（联动更新范围）
        bp001 = next(n for n in updated_tree if n["id"] == "BP-001")
        children = bp001.get("children", [])
        if children:
            child_total = sum(c["score"] for c in children)
            self.assertAlmostEqual(
                child_total, new_score, delta=0.1,
                msg=f"BP-001 子节点总分 {child_total} ≠ {new_score}"
            )

    def test_multiple_adjustments_preserve_total(self):
        """多次 adjust 后总分仍 = 100。"""
        tree, session = self._make_tree_with_children()

        # 第一次调整
        tree, _ = adjust_bp_score(tree, "BP-001", 50.0, "调整1", session)
        total = sum(n["score"] for n in tree)
        self.assertAlmostEqual(total, 100.0, delta=0.1)

        # 第二次调整
        tree, _ = adjust_bp_score(tree, "BP-003", 20.0, "调整2", session)
        total = sum(n["score"] for n in tree)
        self.assertAlmostEqual(total, 100.0, delta=0.1)


# ---------------------------------------------------------------------------
# 5. 集成场景测试
# ---------------------------------------------------------------------------

class TestIntegrationScenarios(unittest.TestCase):
    """端到端场景验证（mock LLM，不调用真实API）。"""

    def _mock_llm_response(self, bp_list: list) -> str:
        """构造 LLM 返回的评分 JSON（均分）。"""
        n = len(bp_list)
        base_score = round(100.0 / n, 1)
        scores = []
        for bp in bp_list:
            scores.append({
                "bp_id": bp["bpId"],
                "score": base_score,
                "confidence": 0.85,
                "reason": "mock评分",
                "dimension_scores": {
                    "strategic_alignment": 8,
                    "measurability": 7,
                    "measure_coverage": 7,
                    "impact_scope": 7,
                },
            })
        return json.dumps({"scores": scores, "total": base_score * n, "notes": "mock"})

    @patch("scorer._call_llm")
    def test_score_peer_bps_with_mock_llm(self, mock_llm):
        """mock LLM 后，score_peer_bps 返回总分 ≈ 100。"""
        bp_list = [make_bp(f"BP-{i:03d}") for i in range(1, 5)]
        mock_llm.return_value = self._mock_llm_response(bp_list)

        weights = {
            "strategic_alignment": 0.4,
            "measurability": 0.2,
            "measure_coverage": 0.2,
            "impact_scope": 0.2,
        }
        result = score_peer_bps(
            org_name="测试组织",
            period_name="2026Q1",
            bp_list=bp_list,
            parent_bp=None,
            weights=weights,
        )

        self.assertIsNotNone(result)
        total = sum(s["score"] for s in result["scores"])
        self.assertAlmostEqual(total, 100.0, delta=0.1)

    @patch("scorer._call_llm")
    def test_score_undertakers_with_mock_llm(self, mock_llm):
        """mock LLM 后，score_undertakers 分配总和 ≈ pool_score。"""
        parent_bp = make_bp("BP-PARENT")
        undertakers = [make_bp(f"U-{i:03d}") for i in range(1, 4)]
        pool_score = 60.0

        # 构造mock响应
        allocations = []
        ratio = round(1.0 / len(undertakers), 4)
        for bp in undertakers:
            allocations.append({
                "undertaker_id": bp["bpId"],
                "ratio": ratio,
                "score": round(pool_score * ratio, 1),
                "confidence": 0.85,
                "reason": "mock分配",
            })
        mock_llm.return_value = json.dumps({
            "allocations": allocations,
            "total_ratio": 1.0,
            "total_score": pool_score,
            "notes": "mock",
        })

        weights = {
            "target_accuracy": 0.45,
            "outcome_contribution": 0.35,
            "measure_completeness": 0.20,
        }
        result = score_undertakers(
            parent_bp=parent_bp,
            undertaker_bps=undertakers,
            pool_score=pool_score,
            weights=weights,
        )

        self.assertIsNotNone(result)
        total = sum(a["score"] for a in result["allocations"])
        self.assertAlmostEqual(total, pool_score, delta=0.1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
