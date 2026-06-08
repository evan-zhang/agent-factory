#!/usr/bin/env python3
"""
可执行测试：BP API 集成（C2 — 用 mock 拦截网络，不依赖真实网络）
覆盖 search_tasks_by_name / get_task_tree / search_groups_by_name /
search_product_aliases 的解析逻辑与失败降级。
"""

import sys
import os
import io
import json
import unittest
from unittest.mock import patch, MagicMock

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import helpers


def _mock_response(payload: dict):
    """构造一个模拟 urlopen 返回的上下文管理器"""
    cm = MagicMock()
    resp = MagicMock()
    resp.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__enter__.return_value = resp
    cm.__exit__.return_value = False
    return cm


class TestBPApiIntegration(unittest.TestCase):

    @patch("helpers.urllib.request.urlopen")
    def test_search_tasks_by_name_success(self, mock_urlopen):
        """searchByName 成功 → 返回 data 列表"""
        mock_urlopen.return_value = _mock_response({
            "resultCode": 1,
            "data": [{"id": "T001", "name": "苯加兰他敏注册", "type": "goal"}],
        })
        result = helpers.search_tasks_by_name("苯加兰他敏")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "T001")

    @patch("helpers.urllib.request.urlopen")
    def test_search_tasks_by_name_empty_data(self, mock_urlopen):
        """searchByName resultCode=1 但 data 为空 → 返回空列表"""
        mock_urlopen.return_value = _mock_response({"resultCode": 1, "data": []})
        self.assertEqual(helpers.search_tasks_by_name("不存在"), [])

    @patch("helpers.urllib.request.urlopen")
    def test_search_tasks_by_name_failure_code(self, mock_urlopen):
        """searchByName resultCode=0（失败）→ 返回空列表"""
        mock_urlopen.return_value = _mock_response({"resultCode": 0, "data": None})
        self.assertEqual(helpers.search_tasks_by_name("x"), [])

    @patch("helpers.urllib.request.urlopen")
    def test_network_error_graceful(self, mock_urlopen):
        """网络异常 → 优雅降级返回空列表，不抛出"""
        mock_urlopen.side_effect = OSError("network down")
        # _bp_api_call 内部捕获异常返回 resultCode=0
        self.assertEqual(helpers.search_tasks_by_name("x"), [])
        self.assertEqual(helpers.get_task_tree("g1"), [])
        self.assertEqual(helpers.search_groups_by_name("x"), [])

    @patch("helpers.urllib.request.urlopen")
    def test_get_task_tree_success(self, mock_urlopen):
        """getSimpleTree 成功 → 返回树"""
        mock_urlopen.return_value = _mock_response({
            "resultCode": 1,
            "data": [{"id": "G1", "name": "产品中心", "children": []}],
        })
        tree = helpers.get_task_tree("G1")
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]["name"], "产品中心")

    @patch("helpers.urllib.request.urlopen")
    def test_search_product_aliases_strategy1(self, mock_urlopen):
        """search_product_aliases 策略1（searchByName 命中）→ 直接返回任务"""
        def side_effect(req, timeout=15):
            url = req.full_url if hasattr(req, "full_url") else req.get_full_url()
            if "/task/v2/searchByName" in url:
                return _mock_response({
                    "resultCode": 1,
                    "data": [{"id": "T100", "name": "少女针", "type": "goal"}],
                })
            return _mock_response({"resultCode": 1, "data": []})
        mock_urlopen.side_effect = side_effect

        results = helpers.search_product_aliases(["少女针"])
        self.assertTrue(any(r["target_id"] == "T100" for r in results))
        hit = [r for r in results if r["target_id"] == "T100"][0]
        self.assertEqual(hit["source"], "searchByName")

    @patch("helpers.urllib.request.urlopen")
    def test_search_product_aliases_dedup(self, mock_urlopen):
        """search_product_aliases 多关键词命中同一目标 → 去重"""
        mock_urlopen.return_value = _mock_response({
            "resultCode": 1,
            "data": [{"id": "T200", "name": "ECM复查", "type": "goal"}],
        })
        results = helpers.search_product_aliases(["ECM", "复查"])
        ids = [r["target_id"] for r in results]
        self.assertEqual(len(ids), len(set(ids)), f"应去重，但出现重复: {ids}")

    @patch("helpers.urllib.request.urlopen")
    def test_search_product_aliases_strategy2_group_tree(self, mock_urlopen):
        """策略2：searchByName 无任务 → 走 group + tree walk"""
        def side_effect(req, timeout=15):
            url = req.full_url if hasattr(req, "full_url") else req.get_full_url()
            if "/task/v2/searchByName" in url:
                return _mock_response({"resultCode": 1, "data": []})
            if "/group/searchByName" in url:
                return _mock_response({
                    "resultCode": 1,
                    "data": [{"id": "G9", "name": "产品组"}],
                })
            if "/task/v2/getSimpleTree" in url:
                return _mock_response({
                    "resultCode": 1,
                    "data": [{"id": "TT1", "name": "破伤风单抗", "type": "goal", "children": []}],
                })
            return _mock_response({"resultCode": 0, "data": None})
        mock_urlopen.side_effect = side_effect

        results = helpers.search_product_aliases(["破伤风单抗"])
        self.assertTrue(any(r["target_id"] == "TT1" for r in results))
        hit = [r for r in results if r["target_id"] == "TT1"][0]
        self.assertEqual(hit["source"], "group_tree")

    def test_short_keyword_skipped(self):
        """单字关键词（<2字）被跳过，不发起 API 调用"""
        # 无需 mock，单字直接跳过
        results = helpers.search_product_aliases(["x", ""])
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
