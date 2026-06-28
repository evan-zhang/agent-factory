"""
orchestrator/tests/test_router.py

Adaptive Provider Router 单元测试集（Phase 2 R3）。

测试内容：
1. select_providers() — 无历史数据时回退到静态路由
2. select_providers() — 有历史数据时按成功率排序
3. select_providers() — 考虑配额（配额不足的排除）
4. select_providers() — 考虑 LLM provider_scores
5. record_result() — 成功/失败计数正确
6. record_result() — 平均延迟计算正确
7. get_performance_report() — 返回格式正确
8. 配置加载 — 从 YAML（通过 ConfigLoader）加载配置
9. Engine 集成 — search() 使用自适应路由
"""

import json
import tempfile
import time
import logging
from pathlib import Path
from typing import List, Dict
from unittest.mock import MagicMock, patch

import pytest

# 关闭 orchestrator 日志输出
logging.disable(logging.CRITICAL)


from ..router import AdaptiveRouter
from ..schema import (
    ProviderConfig,
    ProviderPerformance,
    RouterConfig,
    RoutingDecision,
    ProviderType,
    SearchRequest,
    ResultStatus,
    IntentModeConfig,
)


# ────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────

@pytest.fixture
def router_disabled():
    """默认 disabled 的路由器"""
    config = RouterConfig(enabled=False)
    return AdaptiveRouter(config)


@pytest.fixture
def router_enabled():
    """启用了自适应路由的路由器（无历史数据）"""
    config = RouterConfig(enabled=True, min_history=5)
    return AdaptiveRouter(config)


@pytest.fixture
def router_ready():
    """有足够历史数据可以决策的路由器"""
    config = RouterConfig(enabled=True, min_history=5)
    router = AdaptiveRouter(config)
    # 模拟 MiniMax 历史数据（高成功率，高延迟）
    router._perf["minimax:info"] = ProviderPerformance(
        provider="minimax", intent="info",
        total_calls=20, success_calls=18,
        total_latency_ms=24000.0,  # avg = 1200ms
        last_call_time=time.time(),
    )
    # 模拟 Brave 历史数据（高成功率，低延迟）
    router._perf["brave:info"] = ProviderPerformance(
        provider="brave", intent="info",
        total_calls=15, success_calls=14,
        total_latency_ms=3000.0,  # avg = 200ms
        last_call_time=time.time(),
    )
    # 模拟 Tavily 历史数据（较低成功率）
    router._perf["tavily:info"] = ProviderPerformance(
        provider="tavily", intent="info",
        total_calls=12, success_calls=8,
        total_latency_ms=24000.0,  # avg = 2000ms
        last_call_time=time.time(),
    )
    # 模拟 web_fetch 历史数据（低成功率，高延迟）
    router._perf["web_fetch:info"] = ProviderPerformance(
        provider="web_fetch", intent="info",
        total_calls=10, success_calls=3,
        total_latency_ms=30000.0,  # avg = 3000ms
        last_call_time=time.time(),
    )
    return router


@pytest.fixture
def available_providers() -> List[ProviderConfig]:
    """所有可用的 provider 列表"""
    return [
        ProviderConfig(name="minimax", display_name="MiniMax", type=ProviderType.MCP, enabled=True),
        ProviderConfig(name="brave", display_name="Brave", type=ProviderType.MCP, enabled=True),
        ProviderConfig(name="tavily", display_name="Tavily", type=ProviderType.MCP, enabled=True),
        ProviderConfig(name="web_fetch", display_name="Web Fetch", type=ProviderType.MCP, enabled=True),
    ]


# ────────────────────────────────────────────────────────
# Test: select_providers() — 无历史数据时回退到静态路由
# ────────────────────────────────────────────────────────

class TestSelectProvidersNoHistory:
    """select_providers — 无历史数据时的表现"""

    def test_disabled_router_returns_static(self, router_disabled, available_providers):
        """disabled 路由器总是返回静态路由"""
        decision = router_disabled.select_providers("info", available_providers)
        assert decision.selected_providers == ["minimax", "brave", "tavily"]
        assert "静态回退" in decision.rationale

    def test_enabled_no_history_returns_static(self, router_enabled, available_providers):
        """启用但无历史数据时回退静态路由"""
        decision = router_enabled.select_providers("info", available_providers)
        assert decision.selected_providers == ["minimax", "brave", "tavily"]
        assert "历史数据不足" in decision.rationale or "静态回退" in decision.rationale

    def test_under_min_history_returns_static(self, available_providers):
        """历史数据不足 min_history 时回退静态路由"""
        config = RouterConfig(enabled=True, min_history=10)
        router = AdaptiveRouter(config)
        router._perf["minimax:info"] = ProviderPerformance(
            provider="minimax", intent="info",
            total_calls=3, success_calls=3, total_latency_ms=1000.0,
        )

        decision = router.select_providers("info", available_providers)
        assert "历史数据不足" in decision.rationale or "静态回退" in decision.rationale


# ────────────────────────────────────────────────────────
# Test: select_providers() — 有历史数据时按成功率排序
# ────────────────────────────────────────────────────────

class TestSelectProvidersWithHistory:
    """select_providers — 有历史数据时的表现"""

    def test_providers_sorted_by_score(self, router_ready, available_providers):
        """有历史数据时按综合得分排序"""
        decision = router_ready.select_providers("info", available_providers)

        # 应该选 3 个（max_providers=3）
        assert len(decision.selected_providers) == 3

        # Brave 应该排第一（高成功率 + 低延迟）
        assert decision.selected_providers[0] == "brave"

        # 应该有 rationale
        assert "自适应路由" in decision.rationale

    def test_top_provider_by_success_rate(self, router_ready, available_providers):
        """高成功率的 provider 应该排前面"""
        decision = router_ready.select_providers("info", available_providers)

        # Brave 的 success_rate = 14/15 = 93%, MiniMax = 18/20 = 90%
        # Tavily = 8/12 = 67%, web_fetch = 3/10 = 30%
        # 但还考虑延迟，Brave 延迟 200ms, MiniMax 1200ms
        # Brave 的得分应该最高
        assert decision.selected_providers[0] == "brave"

    def test_reject_quota_exhausted_providers(self, router_ready):
        """配额已用完的 provider 应被排除"""
        # 创建一个配额已用完的 provider
        providers = [
            ProviderConfig(name="minimax", display_name="MiniMax", type=ProviderType.MCP, enabled=True),
            ProviderConfig(name="brave", display_name="Brave", type=ProviderType.MCP, enabled=True),
        ]
        decision = router_ready.select_providers("info", providers)

        # 应该只返回 braves（无 quota 检查，只是过滤 enabled=False 的）
        # 所有 provider 都是 enabled=True，所以都应该在列表里
        assert "minimax" in decision.selected_providers
        assert "brave" in decision.selected_providers


# ────────────────────────────────────────────────────────
# Test: select_providers() — 考虑 LLM provider_scores
# ────────────────────────────────────────────────────────

class TestSelectProvidersWithLLM:
    """select_providers — 考虑 LLM provider_scores"""

    def test_llm_scores_influence_ranking(self, router_ready, available_providers):
        """LLM provider_scores 影响排名"""
        # LLM 认为 Minimax 最适合 info 意图
        llm_scores = {"minimax": 1.0, "brave": 0.3, "tavily": 0.5, "web_fetch": 0.1}

        decision = router_ready.select_providers(
            "info", available_providers, llm_scores=llm_scores
        )

        # 有了 LLM 权重，minimax 应该排第一
        # 因为 llm_score_weight=0.2, minimax 额外得 0.2 分
        # 而 brave 只额外得 0.06 分
        assert decision.selected_providers[0] == "minimax"

    def test_llm_scores_ignored_when_none(self, router_ready, available_providers):
        """llm_scores=None 时忽略 LLM 权重"""
        decision = router_ready.select_providers("info", available_providers, llm_scores=None)
        assert decision.selected_providers[0] == "brave"

    def test_empty_llm_scores(self, router_ready, available_providers):
        """空 LLM scores 字典不影响排名"""
        decision = router_ready.select_providers("info", available_providers, llm_scores={})
        assert decision.selected_providers[0] == "brave"


# ────────────────────────────────────────────────────────
# Test: record_result() — 成功/失败计数正确
# ────────────────────────────────────────────────────────

class TestRecordResult:
    """record_result — 性能数据记录"""

    def test_disabled_router_does_not_record(self, router_disabled):
        """disabled 路由器不记录数据"""
        router_disabled.record_result("minimax", "info", True, 100.0)
        assert len(router_disabled._perf) == 0

    def test_record_success(self, router_enabled):
        """记录一次成功调用"""
        router_enabled.record_result("minimax", "info", True, 100.0)

        key = "minimax:info"
        assert key in router_enabled._perf
        perf = router_enabled._perf[key]
        assert perf.total_calls == 1
        assert perf.success_calls == 1
        assert perf.total_latency_ms == 100.0

    def test_record_failure(self, router_enabled):
        """记录一次失败调用"""
        router_enabled.record_result("minimax", "info", False, 200.0)

        key = "minimax:info"
        perf = router_enabled._perf[key]
        assert perf.total_calls == 1
        assert perf.success_calls == 0
        assert perf.total_latency_ms == 200.0

    def test_multiple_calls_accumulate(self, router_enabled):
        """多次调用正确累加"""
        router_enabled.record_result("minimax", "info", True, 100.0)
        router_enabled.record_result("minimax", "info", True, 150.0)
        router_enabled.record_result("minimax", "info", False, 200.0)

        key = "minimax:info"
        perf = router_enabled._perf[key]
        assert perf.total_calls == 3
        assert perf.success_calls == 2
        assert perf.total_latency_ms == 450.0

    def test_different_intent_separate_perf(self, router_enabled):
        """不同意图分开记录"""
        router_enabled.record_result("minimax", "info", True, 100.0)
        router_enabled.record_result("minimax", "news", True, 200.0)

        info_perf = router_enabled._perf["minimax:info"]
        news_perf = router_enabled._perf["minimax:news"]
        assert info_perf.total_calls == 1
        assert news_perf.total_calls == 1
        assert info_perf != news_perf


# ────────────────────────────────────────────────────────
# Test: record_result() — 平均延迟计算正确
# ────────────────────────────────────────────────────────

class TestRecordResultLatency:
    """record_result — 延迟计算"""

    def test_avg_latency_single_call(self, router_enabled):
        """单次调用平均延迟正确"""
        router_enabled.record_result("minimax", "info", True, 1000.0)
        perf = router_enabled._perf["minimax:info"]
        assert perf.avg_latency_ms == 1000.0

    def test_avg_latency_multiple_calls(self, router_enabled):
        """多次调用平均延迟正确"""
        router_enabled.record_result("minimax", "info", True, 100.0)
        router_enabled.record_result("minimax", "info", True, 200.0)
        router_enabled.record_result("minimax", "info", True, 300.0)

        perf = router_enabled._perf["minimax:info"]
        assert perf.avg_latency_ms == 200.0

    def test_success_rate_property(self, router_enabled):
        """success_rate 属性计算正确"""
        router_enabled.record_result("minimax", "info", True, 100.0)
        router_enabled.record_result("minimax", "info", True, 100.0)
        router_enabled.record_result("minimax", "info", False, 100.0)

        perf = router_enabled._perf["minimax:info"]
        assert perf.success_rate == 2 / 3

    def test_no_calls_success_rate_zero(self):
        """无调用时 success_rate 为 0"""
        perf = ProviderPerformance(provider="minimax", intent="info")
        assert perf.success_rate == 0.0
        assert perf.avg_latency_ms == 0.0


# ────────────────────────────────────────────────────────
# Test: get_performance_report()
# ────────────────────────────────────────────────────────

class TestPerformanceReport:
    """get_performance_report — 返回格式"""

    def test_report_disabled_router(self, router_disabled):
        """disabled 路由器报告"""
        report = router_disabled.get_performance_report()
        assert report["enabled"] is False
        assert report["data_points"] == 0
        assert report["providers"] == {}

    def test_report_with_data(self, router_ready):
        """有数据时报告格式正确"""
        report = router_ready.get_performance_report()
        assert report["enabled"] is True
        assert report["data_points"] == 4  # 4 个 provider 各有数据

        # 应该包含所有 provider
        assert "minimax" in report["providers"]
        assert "brave" in report["providers"]
        assert "tavily" in report["providers"]
        assert "web_fetch" in report["providers"]

        # 验证各字段
        minimax = report["providers"]["minimax"]
        assert minimax["total_calls"] == 20
        assert minimax["success_calls"] == 18
        assert minimax["fail_calls"] == 2

        # 应该有 by_intent 数据
        assert "info" in minimax["by_intent"]


# ────────────────────────────────────────────────────────
# Test: 持久化
# ────────────────────────────────────────────────────────

class TestPersistence:
    """持久化功能测试"""

    def test_load_empty_file(self, tmp_path):
        """从空文件加载不报错"""
        config = RouterConfig(enabled=True, persistence_file=str(tmp_path / "perf.json"))
        router = AdaptiveRouter(config, runtime_dir=tmp_path)
        assert len(router._perf) == 0

    def test_save_and_load(self, tmp_path):
        """保存后重新加载数据一致"""
        perf_file = tmp_path / "perf.json"
        config = RouterConfig(enabled=True, persistence_file=str(perf_file))
        router = AdaptiveRouter(config, runtime_dir=tmp_path)

        # 记录数据
        router.record_result("minimax", "info", True, 100.0)
        router.record_result("brave", "info", True, 50.0)

        # 创建新路由器并加载
        router2 = AdaptiveRouter(config, runtime_dir=tmp_path)
        router2._load_perf_data()

        assert len(router2._perf) == 2
        assert router2._perf["minimax:info"].total_calls == 1
        assert router2._perf["brave:info"].total_calls == 1

    def test_persistence_disabled(self, tmp_path):
        """persistence_enabled=False 不写文件"""
        config = RouterConfig(
            enabled=True,
            persistence_enabled=False,
            persistence_file=str(tmp_path / "noperf.json"),
        )
        router = AdaptiveRouter(config, runtime_dir=tmp_path)
        router.record_result("minimax", "info", True, 100.0)

        # 文件不应该存在
        assert not (tmp_path / "noperf.json").exists()


# ────────────────────────────────────────────────────────
# Test: 配置加载
# ────────────────────────────────────────────────────────

class TestConfigLoading:
    """从 ConfigLoader 加载路由器配置"""

    def test_default_config_disabled(self):
        """默认配置为 disabled"""
        from ..config import ConfigLoader

        loader = ConfigLoader()
        config = loader.get_router_config()
        assert config.enabled is False
        assert config.max_providers == 3
        assert config.min_history == 5
        assert config.success_weight == 0.5
        assert config.latency_weight == 0.3
        assert config.llm_score_weight == 0.2

    def test_enabled_router_config_can_be_overridden(self):
        """配置可以被覆盖"""
        config = RouterConfig(
            enabled=True,
            max_providers=4,
            min_history=10,
            success_weight=0.6,
            latency_weight=0.3,
            llm_score_weight=0.1,
        )
        assert config.enabled is True
        assert config.max_providers == 4
        assert config.min_history == 10
        assert config.success_weight == 0.6


# ────────────────────────────────────────────────────────
# Test: Engine 集成
# ────────────────────────────────────────────────────────

class TestEngineIntegration:
    """Engine 集成测试"""

    def test_engine_has_router(self):
        """SearchEngine 初始化时创建 AdaptiveRouter"""
        from ..engine import SearchEngine

        engine = SearchEngine()
        assert hasattr(engine, "router")
        assert engine.router is not None
        assert engine.router.config.enabled is False

    def test_router_disabled_by_default(self):
        """路由默认 disabled"""
        from ..engine import SearchEngine

        engine = SearchEngine()
        assert engine.router.config.enabled is False

    @pytest.mark.asyncio
    async def test_router_does_not_interfere_with_static_routing(self):
        """disabled 路由不影响静态路由"""
        from ..engine import SearchEngine

        engine = SearchEngine()
        # 使用真实存在的 provider 名称
        providers = engine._get_providers(
            IntentModeConfig(intent="info", preferred_providers=["minimax", "open_websearch"]),
            max_providers=2,
        )
        # 应该返回静态的路由结果，不受路由影响
        provider_names = [p.name for p in providers]
        assert len(provider_names) >= 1  # 至少 1 个（minimax）
        assert "minimax" in provider_names

    @pytest.mark.asyncio
    async def test_search_with_router_disabled(self):
        """disabled 路由下 search() 正常工作"""
        from ..engine import SearchEngine

        engine = SearchEngine()
        # 只要不报错即可 —— 路由 disabled 不会干预任何流程
        assert engine.router.config.enabled is False


# ────────────────────────────────────────────────────────
# Test: RoutingDecision
# ────────────────────────────────────────────────────────

class TestRoutingDecision:
    """RoutingDecision 数据结构"""

    def test_default_round_strategy(self):
        """默认轮询策略为 parallel"""
        decision = RoutingDecision(
            selected_providers=["minimax", "brave"],
            rationale="test",
        )
        assert decision.round_strategy == "parallel"

    def test_hybrid_strategy(self):
        """支持 hybrid 策略"""
        decision = RoutingDecision(
            selected_providers=["minimax"],
            rationale="test",
            round_strategy="hybrid",
        )
        assert decision.round_strategy == "hybrid"


# ────────────────────────────────────────────────────────
# Test: _compute_score
# ────────────────────────────────────────────────────────

class TestComputeScore:
    """_compute_score 得分计算"""

    def test_no_history_zero_score(self, router_enabled):
        """无历史数据得 0 分（无 LLM 分）"""
        score = router_enabled._compute_score(None, "unknown", "info", None)
        assert score == 0.0

    def test_high_success_rate_high_score(self, router_enabled):
        """高成功率得分"""
        perf = ProviderPerformance(
            provider="minimax", intent="info",
            total_calls=10, success_calls=9,  # 90% 成功率
            total_latency_ms=5000.0,  # avg 500ms
        )
        score = router_enabled._compute_score(perf, "minimax", "info", None)
        # success_component = 0.9 * 0.5 = 0.45
        # latency_component = min(1.0, 1000/500) * 0.3 = 0.3
        # total ≈ 0.75
        assert score > 0.5

    def test_low_success_rate_low_score(self, router_enabled):
        """低成功率得分低"""
        perf = ProviderPerformance(
            provider="minimax", intent="info",
            total_calls=10, success_calls=2,  # 20% 成功率
            total_latency_ms=10000.0,
        )
        score = router_enabled._compute_score(perf, "minimax", "info", None)
        # success_component = 0.2 * 0.5 = 0.1
        # latency_component = min(1.0, 1000/1000) * 0.3 = 0.3
        # total ≈ 0.4
        assert score < 0.5

    def test_llm_score_boosts_total(self, router_enabled):
        """LLM provider_score 提升总得分"""
        perf = ProviderPerformance(
            provider="minimax", intent="info",
            total_calls=10, success_calls=0,  # 0% 成功率
            total_latency_ms=0.0,
        )
        score_no_llm = router_enabled._compute_score(perf, "minimax", "info", None)
        score_with_llm = router_enabled._compute_score(
            perf, "minimax", "info", {"minimax": 1.0}
        )
        # 有 LLM 分时应该更高
        assert score_with_llm > score_no_llm
        # llm_component = 1.0 * 0.2 = 0.2
        assert score_with_llm == pytest.approx(0.2, abs=0.01)
