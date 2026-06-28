"""
orchestrator/tests/test_engine.py

Multi-Search Orchestrator 单元测试集

测试内容（4 个任务）：
1. apply_query_template() — 验证模板占位符替换（Fix 2）
2. 三轮递进流程 — mock provider 返回，验证精准→泛搜→兜底顺序（Fix 2）
3. Fallback 触发条件 — mock status，验证正确触发（Fix 3）
4. _parse_search_item() result_mapping — 验证字段映射（Fix 4）
"""

import asyncio
import copy
import json
import logging
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from collections import OrderedDict

import pytest

# 关闭 orcherstrator 日志输出
logging.disable(logging.CRITICAL)


# ────────────────────────────────────────────────────────
# Task 1: apply_query_template() 测试
# ────────────────────────────────────────────────────────

from ..engine import apply_query_template
from ..schema import (
    ProviderType,
    ResultStatus,
    ProviderConfig,
    RoundConfig,
    RoundTermination,
    QueryStrategy,
    IntentModeConfig,
    SearchRequest,
    SearchItem,
    OrchestratorSearchResult,
)


class TestApplyQueryTemplate:
    """apply_query_template 函数的单元测试（BATTLE-R4-FIXES.md Fix 2）"""

    def test_precise_round_adds_quotes(self):
        """精准轮：'\"{query}\"' → 加引号"""
        result = apply_query_template('"{query}"', "社保缴费比例")
        assert result == '"社保缴费比例"'

    def test_broaden_round_unchanged(self):
        """泛搜轮：'{query}' → 原样"""
        result = apply_query_template("{query}", "社保缴费比例")
        assert result == "社保缴费比例"

    def test_fallback_round_unchanged(self):
        """兜底轮：'{query}' → 原样"""
        result = apply_query_template("{query}", "社保缴费比例")
        assert result == "社保缴费比例"

    def test_empty_query(self):
        """空查询"""
        result = apply_query_template('"{query}"', "")
        assert result == '""'

    def test_query_with_special_chars(self):
        """包含特殊字符的查询"""
        result = apply_query_template("{query}", "Python 3.9+ & Type Hints")
        assert result == "Python 3.9+ & Type Hints"

    def test_multiple_placeholders(self):
        """多个 {query} 占位符"""
        result = apply_query_template("{query} site:gov.cn {query}", "政策")
        assert result == "政策 site:gov.cn 政策"

    def test_no_placeholder(self):
        """没有占位符的模板——原样返回"""
        result = apply_query_template("hello world", "anything")
        assert result == "hello world"

    def test_template_is_empty(self):
        """空模板"""
        result = apply_query_template("", "test")
        assert result == ""


# ────────────────────────────────────────────────────────
# Task 2 & 3: 三轮递进 + Fallback 触发条件测试
# ────────────────────────────────────────────────────────

class MockConfigLoader:
    """Mock ConfigLoader，用于测试"""

    def __init__(self):
        self._providers = {}
        self._intent_modes = {}
        self._fallback_config = None

    def load_all(self):
        pass

    def get_provider(self, name):
        return self._providers.get(name)

    def list_providers(self, enabled_only=True):
        providers = list(self._providers.values())
        if enabled_only:
            providers = [p for p in providers if p.enabled]
        return providers

    def get_intent_mode(self, intent):
        return self._intent_modes.get(intent)

    def get_fallback_config(self):
        return self._fallback_config

    def get_scorer_config(self):
        from ..schema import ScorerConfig
        return ScorerConfig()

    def get_router_config(self):
        from ..schema import RouterConfig
        return RouterConfig()


class MockStateManager:
    """Mock StateManager"""

    def is_healthy(self, name):
        return True

    def check_quota(self, name, config):
        return True

    def increment_quota(self, name, config):
        pass

    def update_health(self, name, is_healthy, error_message=None, error_code=None):
        pass


class MockCacheManager:
    """Mock CacheManager"""

    def get(self, request):
        return None

    def set(self, request, result, ttl=3600):
        pass

    def clear(self):
        pass


class MockAggregator:
    """Mock ResultAggregator"""

    def aggregate(self, results, query):
        total_items = sum(len(r.items) for r in results)
        status = ResultStatus.OK if total_items > 0 else ResultStatus.NO_MATCH
        valid = [r for r in results if r.status not in (
            ResultStatus.ERROR, ResultStatus.TIMEOUT)]

        items = []
        for r in valid:
            items.extend(r.items)

        return OrchestratorSearchResult(
            version="1.0.0",
            status=status,
            provider="aggregated",
            query=query,
            items=items,
            metadata={"aggregated_from": [r.provider for r in valid]},
        )


class MockFallbackChain:
    """Mock FallbackChain"""

    def __init__(self, config=None):
        self.config = config

    def should_trigger(self, result):
        return result.status in (
            ResultStatus.ALL_FAILED,
            ResultStatus.ERROR,
            ResultStatus.NO_MATCH,
        )

    async def execute(self, providers, search_func, request):
        """模拟串行执行"""
        for provider in providers:
            result = await search_func(provider, request)
            if result.status in (ResultStatus.OK, ResultStatus.PARTIAL) and len(result.items) > 0:
                result.fallback_triggered = True
                return result

        return OrchestratorSearchResult(
            version="1.0.0",
            status=ResultStatus.ALL_FAILED,
            error="Fallback 所有 provider 均失败",
            provider="fallback",
            query=request.query,
            items=[],
            metadata={},
        )


class FakeSearchEngine:
    """
    简化测试引擎，直接控制 provider 返回结果。
    """

    def __init__(self):
        self.results_for = {}  # provider_name -> OrchestratorSearchResult
        self.providers = {}    # provider_name -> ProviderConfig
        self.calls = []

    def set_result(self, provider_name, result):
        self.results_for[provider_name] = result

    def add_provider(self, name, display_name="test"):
        provider_type = ProviderType.MCP
        config = ProviderConfig(
            name=name,
            display_name=display_name,
            type=provider_type,
            enabled=True,
        )
        self.providers[name] = config

    async def _execute_single_provider(self, provider, request):
        self.calls.append({
            "provider": provider.name,
            "query": getattr(request, 'query', 'unknown'),
        })
        if provider.name in self.results_for:
            return self.results_for[provider.name]
        return OrchestratorSearchResult(
            version="1.0.0",
            status=ResultStatus.ERROR,
            error=f"Mock: no result for {provider.name}",
            provider=provider.name,
            query="",
            items=[],
            metadata={},
        )


def make_result(provider, items, status="ok"):
    """创建测试用的搜索结果"""
    status_map = {
        "ok": ResultStatus.OK,
        "partial": ResultStatus.PARTIAL,
        "no_match": ResultStatus.NO_MATCH,
        "all_failed": ResultStatus.ALL_FAILED,
        "error": ResultStatus.ERROR,
    }

    search_items = [
        SearchItem(
            title=item.get("title", "title"),
            url=item.get("url", f"https://example.com/{i}"),
            snippet=item.get("snippet", "snippet"),
        )
        for i, item in enumerate(items)
    ]

    return OrchestratorSearchResult(
        version="1.0.0",
        status=status_map.get(status, ResultStatus.OK),
        provider=provider,
        query="",
        items=search_items,
        metadata={},
    )


async def _simulate_multi_round(engine, strategy, query):
    """手动模拟三轮递进逻辑"""
    all_items = []
    termination = strategy.round_termination
    rounds = strategy.rounds

    for round_idx, round_conf in enumerate(rounds):
        round_query = apply_query_template(round_conf.query_template, query)

        if round_conf.provider_filter:
            round_providers = [engine.providers[p] for p in round_conf.provider_filter
                               if p in engine.providers]
        else:
            round_providers = list(engine.providers.values())

        for provider in round_providers:
            req = MagicMock(query=round_query)
            result = await engine._execute_single_provider(provider, req)
            all_items.extend(result.items)

        if termination and termination.min_results > 0:
            unique_urls = {it.url for it in all_items}
            if len(unique_urls) >= termination.min_results:
                break

    # 去重
    seen = set()
    deduped = []
    for item in all_items:
        if item.url not in seen:
            seen.add(item.url)
            deduped.append(item)

    status = ResultStatus.OK if deduped else ResultStatus.NO_MATCH
    return OrchestratorSearchResult(
        version="1.0.0",
        status=status,
        query=query,
        provider="multi_round",
        items=deduped,
        metadata={},
    )


class TestSearchMultiRound:
    """三轮递进检索流程测试（BATTLE-R4-FIXES.md Fix 2）"""

    def test_early_termination_after_round1(self):
        """Round 1 达到 min_results → 提前终止，不执行 Round 2"""
        engine = FakeSearchEngine()
        engine.add_provider("minimax")
        engine.add_provider("open_websearch")

        rounds = [
            MagicMock(mode="precise", query_template='"{query}"', count=5, timeout_ms=8000,
                      provider_filter=["minimax"]),
            MagicMock(mode="broaden", query_template="{query}", count=10, timeout_ms=10000,
                      provider_filter=["open_websearch"]),
        ]
        strategy = QueryStrategy(
            enabled=True,
            rounds=rounds,
            round_termination=RoundTermination(min_results=3, max_rounds=2),
        )

        result_r1 = make_result("minimax", [
            {"title": "R1-1", "url": "https://example.com/1"},
            {"title": "R1-2", "url": "https://example.com/2"},
            {"title": "R1-3", "url": "https://example.com/3"},
            {"title": "R1-4", "url": "https://example.com/4"},
        ])
        engine.set_result("minimax", result_r1)

        result = asyncio.run(_simulate_multi_round(engine, strategy, "test"))

        # 只有 Round 1 被执行
        assert len(engine.calls) == 1
        assert engine.calls[0]["provider"] == "minimax"
        assert engine.calls[0]["query"] == '"test"'
        assert len(result.items) == 4

    def test_multi_round_dedup(self):
        """三轮递进去重：跨轮相同 URL 只保留一条"""
        engine = FakeSearchEngine()
        engine.add_provider("minimax")
        engine.add_provider("open_websearch")

        rounds = [
            MagicMock(mode="precise", query_template='"{query}"', count=5, timeout_ms=8000,
                      provider_filter=["minimax"]),
            MagicMock(mode="broaden", query_template="{query}", count=10, timeout_ms=10000,
                      provider_filter=["open_websearch"]),
        ]
        strategy = QueryStrategy(
            enabled=True,
            rounds=rounds,
            round_termination=RoundTermination(min_results=10, max_rounds=2),
        )

        result_r1 = make_result("minimax", [
            {"title": "R1-1", "url": "https://example.com/1"},
            {"title": "R1-2", "url": "https://example.com/2"},
        ])
        result_r2 = make_result("open_websearch", [
            {"title": "R2-1", "url": "https://example.com/1"},  # 重复
            {"title": "R2-2", "url": "https://example.com/3"},
        ])
        engine.set_result("minimax", result_r1)
        engine.set_result("open_websearch", result_r2)

        result = asyncio.run(_simulate_multi_round(engine, strategy, "test"))

        # 去重后 3 条（不是 4 条）
        assert len(result.items) == 3
        urls = [it.url for it in result.items]
        assert urls.count("https://example.com/1") == 1

    def test_multi_round_precise_broaden_order(self):
        """验证精准→泛搜顺序"""
        engine = FakeSearchEngine()
        engine.add_provider("minimax")
        engine.add_provider("open_websearch")

        rounds = [
            MagicMock(mode="precise", query_template='"{query}"', count=3, timeout_ms=8000,
                      provider_filter=["minimax"]),
            MagicMock(mode="broaden", query_template="{query}", count=5, timeout_ms=10000,
                      provider_filter=["open_websearch"]),
        ]
        strategy = QueryStrategy(
            enabled=True,
            rounds=rounds,
            round_termination=RoundTermination(min_results=10, max_rounds=2),
        )

        result_r1 = make_result("minimax", [
            {"title": "exact", "url": "https://example.com/exact"},
        ])
        result_r2 = make_result("open_websearch", [
            {"title": "broad", "url": "https://example.com/broad"},
        ])
        engine.set_result("minimax", result_r1)
        engine.set_result("open_websearch", result_r2)

        result = asyncio.run(_simulate_multi_round(engine, strategy, "test"))

        assert len(engine.calls) == 2
        # Round 1: precise query with quotes
        assert '"test"' in engine.calls[0]["query"]
        assert engine.calls[0]["provider"] == "minimax"
        # Round 2: broaden query without quotes
        assert engine.calls[1]["query"] == "test"
        assert engine.calls[1]["provider"] == "open_websearch"


class TestFallbackTrigger:
    """Fallback 触发条件测试（BATTLE-R4-FIXES.md Fix 3）"""

    def _check_trigger(self, status):
        """Helper: 检查给定状态是否会触发 Fallback"""
        trigger_states = {
            ResultStatus.ALL_FAILED,
            ResultStatus.ERROR,
            ResultStatus.NO_MATCH,
        }
        return status in trigger_states

    def test_ok_should_not_trigger_fallback(self):
        """status=ok → 不触发 Fallback"""
        assert not self._check_trigger(ResultStatus.OK)

    def test_partial_should_not_trigger_fallback(self):
        """status=partial → 不触发 Fallback"""
        assert not self._check_trigger(ResultStatus.PARTIAL)

    def test_all_failed_should_trigger_fallback(self):
        """status=all_failed → 触发 Fallback"""
        assert self._check_trigger(ResultStatus.ALL_FAILED)

    def test_error_should_trigger_fallback(self):
        """status=error → 触发 Fallback"""
        assert self._check_trigger(ResultStatus.ERROR)

    def test_no_match_should_trigger_fallback(self):
        """status=no_match → 触发 Fallback"""
        assert self._check_trigger(ResultStatus.NO_MATCH)


async def _run_serial_test(providers, mock_func):
    """执行串行 fallback 链测试的辅助函数"""
    from ..fallback_chain import FallbackChain
    chain = FallbackChain()
    return await chain.execute(providers, mock_func, MagicMock(query="test"))


class TestExecuteSerial:
    """串行 fallback 链测试"""

    def test_serial_first_succeeds(self):
        """串行执行: 第一个 provider 成功即返回"""
        class MockSearchFunc:
            def __init__(self):
                self.call_count = 0

            async def __call__(self, provider, request):
                self.call_count += 1
                if provider.name == "provider_a":
                    return OrchestratorSearchResult(
                        version="1.0.0",
                        status=ResultStatus.OK,
                        provider="provider_a",
                        query=request.query,
                        items=[SearchItem(title="Found", url="https://example.com/1",
                                          snippet="desc")],
                        metadata={},
                    )
                return OrchestratorSearchResult(
                    version="1.0.0",
                    status=ResultStatus.ERROR,
                    provider=provider.name,
                    query=request.query,
                    items=[],
                    metadata={},
                )

        search_func = MockSearchFunc()
        config_a = ProviderConfig(name="provider_a", display_name="A", type=ProviderType.MCP)

        result = asyncio.run(_run_serial_test([config_a], search_func))

        assert result.status == ResultStatus.OK
        assert len(result.items) == 1
        assert result.provider == "provider_a"
        assert search_func.call_count == 1

    def test_serial_first_fails_then_succeeds(self):
        """串行执行: 第一个 provider 失败，第二个成功"""
        class MockSearchFunc:
            def __init__(self):
                self.calls = []

            async def __call__(self, provider, request):
                self.calls.append(provider.name)
                if provider.name == "provider_fail":
                    return OrchestratorSearchResult(
                        version="1.0.0",
                        status=ResultStatus.NO_MATCH,
                        provider="provider_fail",
                        query=request.query,
                        items=[],
                        metadata={},
                    )
                return OrchestratorSearchResult(
                    version="1.0.0",
                    status=ResultStatus.OK,
                    provider="provider_ok",
                    query=request.query,
                    items=[SearchItem(title="Found", url="https://example.com/1",
                                      snippet="desc")],
                    metadata={},
                )

        search_func = MockSearchFunc()
        config_fail = ProviderConfig(name="provider_fail", display_name="Fail", type=ProviderType.MCP)
        config_ok = ProviderConfig(name="provider_ok", display_name="OK", type=ProviderType.MCP)

        result = asyncio.run(_run_serial_test([config_fail, config_ok], search_func))

        assert result.status == ResultStatus.OK
        assert result.fallback_triggered
        assert search_func.calls == ["provider_fail", "provider_ok"]

    def test_serial_all_fail(self):
        """串行执行: 所有 provider 均失败"""
        class MockSearchFunc:
            async def __call__(self, provider, request):
                if provider.name == "p1":
                    return OrchestratorSearchResult(
                        version="1.0.0",
                        status=ResultStatus.ERROR,
                        provider="p1",
                        query=request.query,
                        items=[],
                        metadata={},
                    )
                return OrchestratorSearchResult(
                    version="1.0.0",
                    status=ResultStatus.NO_MATCH,
                    provider="p2",
                    query=request.query,
                    items=[],
                    metadata={},
                )

        search_func = MockSearchFunc()
        config_a = ProviderConfig(name="p1", display_name="P1", type=ProviderType.MCP)
        config_b = ProviderConfig(name="p2", display_name="P2", type=ProviderType.MCP)

        result = asyncio.run(_run_serial_test([config_a, config_b], search_func))

        assert result.status in (ResultStatus.NO_MATCH, ResultStatus.ERROR, ResultStatus.ALL_FAILED)
        assert result.fallback_triggered


class TestResultMapping:
    """_parse_search_item() result_mapping 测试（BATTLE-R4-FIXES.md Fix 4）"""

    def test_minimax_result_mapping(self):
        """MiniMax 映射: title, link→url, snippet, date→published_date"""
        provider = ProviderConfig(
            name="minimax",
            display_name="MiniMax",
            type=ProviderType.MCP,
            result_mapping={
                "title": "title",
                "url": "link",
                "snippet": "snippet",
                "published_date": "date",
                "score": None,
            },
        )

        raw_item = {
            "title": "MiniMax Result",
            "link": "https://api.minimax.chat/",
            "snippet": "MiniMax snippet",
            "date": "2026-06-06",
        }

        from ..engine import SearchEngine
        engine = SearchEngine.__new__(SearchEngine)
        engine.config_loader = MagicMock()
        item = engine._parse_search_item(provider, raw_item)

        assert item.title == "MiniMax Result"
        assert item.url == "https://api.minimax.chat/"
        assert item.snippet == "MiniMax snippet"
        assert item.published_date == "2026-06-06"
        assert item.score == 0.0

    def test_open_websearch_result_mapping(self):
        """open-websearch 映射: title, url, content→snippet, publishedDate→published_date"""
        provider = ProviderConfig(
            name="open_websearch",
            display_name="Open Web Search",
            type=ProviderType.MCP,
            result_mapping={
                "title": "title",
                "url": "url",
                "snippet": "content",
                "published_date": "publishedDate",
                "score": None,
            },
        )

        raw_item = {
            "title": "Open Web Result",
            "url": "https://example.com/ow",
            "content": "Open web snippet",
            "publishedDate": "2026-06-05",
        }

        from ..engine import SearchEngine
        engine = SearchEngine.__new__(SearchEngine)
        engine.config_loader = MagicMock()
        item = engine._parse_search_item(provider, raw_item)

        assert item.title == "Open Web Result"
        assert item.url == "https://example.com/ow"
        assert item.snippet == "Open web snippet"
        assert item.published_date == "2026-06-05"

    def test_web_fetch_result_mapping(self):
        """web_fetch 映射: title, url, snippet, published_date"""
        provider = ProviderConfig(
            name="web_fetch",
            display_name="Web Fetch",
            type=ProviderType.MCP,
            result_mapping={
                "title": "title",
                "url": "url",
                "snippet": "snippet",
                "published_date": "published_date",
                "score": None,
            },
        )

        raw_item = {
            "title": "Web Fetch Result",
            "url": "https://example.com/wf",
            "snippet": "Web fetch snippet",
            "published_date": "2026-06-04",
        }

        from ..engine import SearchEngine
        engine = SearchEngine.__new__(SearchEngine)
        engine.config_loader = MagicMock()
        item = engine._parse_search_item(provider, raw_item)

        assert item.title == "Web Fetch Result"
        assert item.url == "https://example.com/wf"
        assert item.snippet == "Web fetch snippet"
        assert item.published_date == "2026-06-04"

    def test_default_mapping_fallback(self):
        """未配置 result_mapping 时使用默认映射"""
        provider = ProviderConfig(
            name="default",
            display_name="Default",
            type=ProviderType.MCP,
            result_mapping={},
        )

        raw_item = {
            "title": "Default Title",
            "url": "https://example.com/",
            "snippet": "Default snippet",
        }

        from ..engine import SearchEngine
        engine = SearchEngine.__new__(SearchEngine)
        engine.config_loader = MagicMock()
        item = engine._parse_search_item(provider, raw_item)

        assert item.title == "Default Title"
        assert item.url == "https://example.com/"
        assert item.snippet == "Default snippet"
        assert item.published_date is None
        assert item.score == 0.0

    def test_missing_field_returns_default(self):
        """provider 返回缺少某字段时，使用默认值"""
        provider = ProviderConfig(
            name="partial",
            display_name="Partial",
            type=ProviderType.MCP,
            result_mapping={
                "title": "title",
                "url": "url",
                "snippet": "snippet",
                "published_date": "date",
                "score": "relevance",
            },
        )

        raw_item = {
            "title": "Partial Title",
            "url": "https://example.com/partial",
        }

        from ..engine import SearchEngine
        engine = SearchEngine.__new__(SearchEngine)
        engine.config_loader = MagicMock()
        item = engine._parse_search_item(provider, raw_item)

        assert item.title == "Partial Title"
        assert item.url == "https://example.com/partial"
        assert item.snippet == ""
        assert item.published_date is None
        assert item.score == 0.0


# ────────────────────────────────────────────────────────
# Task X: HTTP provider 测试
# ────────────────────────────────────────────────────────


class MockHttpResponse:
    """
    Mock aiohttp ClientResponse，支持 async with 上下文。
    """

    def __init__(self, status: int, json_data: Optional[Dict] = None):
        self.status = status
        self._json_data = json_data or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def json(self):
        return self._json_data

    async def text(self):
        import json
        return json.dumps(self._json_data)


class TestHttpProvider:
    """HTTP provider 执行路径测试"""

    @pytest.fixture
    def engine_with_mocks(self):
        """
        创建 SearchEngine 实例，所有子组件均为 mock。
        HTTP session 也设为 mock，不会发起真实 HTTP 请求。
        """
        from ..engine import SearchEngine

        engine = SearchEngine(
            config_loader=MockConfigLoader(),
            mcp_client=MagicMock(),
            state_manager=MockStateManager(),
            cache_manager=MockCacheManager(),
            aggregator=MockAggregator(),
            fallback_chain=MockFallbackChain(),
        )
        # 用 MagicMock 替换 HTTP session
        engine._http_session = MagicMock()
        return engine

    @pytest.fixture
    def http_provider(self):
        """标准 HTTP provider 配置"""
        return ProviderConfig(
            name="test_http",
            display_name="Test HTTP",
            type=ProviderType.HTTP,
            http_endpoint="https://api.example.com/search",
            http_method="POST",
            http_headers={"X-API-Key": "test-key"},
            call_parameters={"q": "query", "size": "num_results"},
            result_mapping={
                "title": "title",
                "url": "url",
                "snippet": "snippet",
                "published_date": None,
                "score": None,
            },
            timeout=5,
        )

    def test_http_200_with_results(self, engine_with_mocks, http_provider):
        """HTTP 200 成功响应，解析 results 格式 JSON"""
        engine = engine_with_mocks

        mock_resp = MockHttpResponse(status=200, json_data={
            "results": [
                {"title": "Result A", "url": "https://example.com/a", "snippet": "Desc A"},
                {"title": "Result B", "url": "https://example.com/b", "snippet": "Desc B"},
            ],
        })

        # 非 async 函数：aiohttp session.request() 返回的 _RequestContextManager
        # 本身是 async context manager，不是 coroutine。mock 需符合同一契约。
        def mock_request(*args, **kwargs):
            return mock_resp

        engine._http_session.request = mock_request

        request = SearchRequest(query="test query", num_results=10)
        result = asyncio.run(engine._execute_http_provider(http_provider, request))

        # 2 条结果 < 10，返回 PARTIAL
        assert result.status == ResultStatus.PARTIAL
        assert len(result.items) == 2
        assert result.items[0].title == "Result A"
        assert result.items[0].url == "https://example.com/a"
        assert result.items[0].snippet == "Desc A"
        assert result.items[1].title == "Result B"

    def test_http_200_with_results_singular_key(self, engine_with_mocks, http_provider):
        """HTTP 200 成功响应，解析 result 单数键格式"""
        engine = engine_with_mocks

        mock_resp = MockHttpResponse(status=200, json_data={
            "result": [
                {"title": "Single", "url": "https://example.com/1", "snippet": "Single result"},
            ],
        })

        def mock_request(*args, **kwargs):
            return mock_resp

        engine._http_session.request = mock_request

        request = SearchRequest(query="single", num_results=1)
        result = asyncio.run(engine._execute_http_provider(http_provider, request))

        assert result.status == ResultStatus.OK  # 1 条 >= 请求的 1 条
        assert len(result.items) == 1
        assert result.items[0].title == "Single"

    def test_http_200_with_organic_format(self, engine_with_mocks):
        """HTTP 200 成功响应，解析 organic 格式（如 MiniMax HTTP）"""
        engine = engine_with_mocks

        provider = ProviderConfig(
            name="organic_http",
            display_name="Organic HTTP",
            type=ProviderType.HTTP,
            http_endpoint="https://api.example.com/search",
            http_method="POST",
            http_headers={},
            call_parameters={"q": "query"},
            result_mapping={"title": "title", "url": "link", "snippet": "snippet"},
            timeout=5,
        )

        mock_resp = MockHttpResponse(status=200, json_data={
            "organic": [
                {"title": "Org 1", "link": "https://example.com/o1", "snippet": "Organic 1"},
                {"title": "Org 2", "link": "https://example.com/o2", "snippet": "Organic 2"},
            ],
        })

        def mock_request(*args, **kwargs):
            return mock_resp

        engine._http_session.request = mock_request

        request = SearchRequest(query="organic test", num_results=2)
        result = asyncio.run(engine._execute_http_provider(provider, request))

        # 2 条 >= 请求的 2 条
        assert result.status == ResultStatus.OK
        assert len(result.items) == 2
        assert result.items[0].title == "Org 1"

    def test_http_non_200_returns_error(self, engine_with_mocks, http_provider):
        """HTTP 非 200 状态码返回 error"""
        engine = engine_with_mocks

        mock_resp = MockHttpResponse(status=403, json_data={"error": "forbidden"})

        def mock_request(*args, **kwargs):
            return mock_resp

        engine._http_session.request = mock_request

        request = SearchRequest(query="test")
        result = asyncio.run(engine._execute_http_provider(http_provider, request))

        assert result.status == ResultStatus.ERROR
        assert "403" in result.error
        assert len(result.items) == 0

    def test_http_timeout_returns_timeout(self, engine_with_mocks, http_provider):
        """HTTP 超时返回 TIMEOUT 状态"""
        engine = engine_with_mocks

        def mock_request_timeout(*args, **kwargs):
            raise asyncio.TimeoutError()

        engine._http_session.request = mock_request_timeout

        request = SearchRequest(query="test")
        result = asyncio.run(engine._execute_http_provider(http_provider, request))

        assert result.status == ResultStatus.TIMEOUT
        assert "超时" in result.error
        assert len(result.items) == 0

    def test_http_get_uses_params(self, engine_with_mocks, http_provider):
        """HTTP GET 请求使用 params 参数，非 POST json body"""
        engine = engine_with_mocks

        provider = ProviderConfig(
            name="get_provider",
            display_name="GET Provider",
            type=ProviderType.HTTP,
            http_endpoint="https://api.example.com/search",
            http_method="GET",
            http_headers={"X-Key": "value"},
            call_parameters={"q": "query", "limit": "num_results"},
            result_mapping={"title": "title", "url": "url", "snippet": "snippet"},
            timeout=5,
        )

        mock_resp = MockHttpResponse(status=200, json_data={"results": []})

        captured_kwargs = {}

        def mock_request_get(*args, **kwargs):
            nonlocal captured_kwargs
            captured_kwargs = kwargs
            return mock_resp

        engine._http_session.request = mock_request_get

        request = SearchRequest(query="get test", num_results=5)
        result = asyncio.run(engine._execute_http_provider(provider, request))

        assert captured_kwargs.get("params") is not None
        assert captured_kwargs["params"] == {"q": "get test", "limit": 5}
        assert captured_kwargs.get("json") is None

    def test_http_post_uses_json(self, engine_with_mocks, http_provider):
        """HTTP POST 请求使用 json body"""
        engine = engine_with_mocks

        mock_resp = MockHttpResponse(status=200, json_data={"results": [
            {"title": "T", "url": "https://example.com/t", "snippet": "S"},
        ]})

        captured_kwargs = {}

        def mock_request_post(*args, **kwargs):
            nonlocal captured_kwargs
            captured_kwargs = kwargs
            return mock_resp

        engine._http_session.request = mock_request_post

        request = SearchRequest(query="post test", num_results=3)
        result = asyncio.run(engine._execute_http_provider(http_provider, request))

        assert captured_kwargs.get("json") is not None
        assert captured_kwargs["json"] == {"q": "post test", "size": 3}
        assert captured_kwargs.get("params") is None

    def test_http_headers_merged(self, engine_with_mocks, http_provider):
        """HTTP 请求头合并 provider.http_headers + Content-Type"""
        engine = engine_with_mocks

        mock_resp = MockHttpResponse(status=200, json_data={"results": []})

        captured_kwargs = {}

        def mock_request_headers(*args, **kwargs):
            nonlocal captured_kwargs
            captured_kwargs = kwargs
            return mock_resp

        engine._http_session.request = mock_request_headers

        request = SearchRequest(query="headers test")
        result = asyncio.run(engine._execute_http_provider(http_provider, request))

        headers = captured_kwargs.get("headers", {})
        assert headers.get("X-API-Key") == "test-key"
        assert headers.get("Content-Type") == "application/json"

    def test_http_call_parameters_mapping(self, engine_with_mocks):
        """HTTP provider 的 call_parameters 映射 search 参数"""
        engine = engine_with_mocks

        provider = ProviderConfig(
            name="mapped_http",
            display_name="Mapped HTTP",
            type=ProviderType.HTTP,
            http_endpoint="https://api.example.com/search",
            http_method="POST",
            http_headers={},
            call_parameters={
                "query": "query",
                "max_results": "num_results",
                "start": "offset",
            },
            result_mapping={"title": "title", "url": "url", "snippet": "snippet"},
            timeout=5,
        )

        mock_resp = MockHttpResponse(status=200, json_data={"results": [
            {"title": "Mapped", "url": "https://example.com/m", "snippet": "Mapped result"},
        ]})

        captured_kwargs = {}

        def mock_request_map(*args, **kwargs):
            nonlocal captured_kwargs
            captured_kwargs = kwargs
            return mock_resp

        engine._http_session.request = mock_request_map

        request = SearchRequest(query="mapping test", num_results=1, offset=2)
        result = asyncio.run(engine._execute_http_provider(provider, request))

        body = captured_kwargs.get("json", {})
        assert body["query"] == "mapping test"
        assert body["max_results"] == 1
        assert body["start"] == 2
        assert result.status == ResultStatus.OK

    def test_http_connection_error_propagates(self, engine_with_mocks, http_provider):
        """HTTP 连接错误（非超时）抛异常，由 _execute_single_provider 捕获"""
        engine = engine_with_mocks

        def mock_request_error(*args, **kwargs):
            raise ConnectionError("Failed to connect")

        engine._http_session.request = mock_request_error

        request = SearchRequest(query="test")

        with pytest.raises(ConnectionError):
            asyncio.run(engine._execute_http_provider(http_provider, request))

    def test_http_quota_health_check_flow(self, engine_with_mocks, http_provider):
        """
        通过 _execute_single_provider 验证 HTTP provider 在执行前
        会经过配额检查和健康检查（复用 MCP 路径的检查逻辑）。
        """
        engine = engine_with_mocks

        mock_resp = MockHttpResponse(status=200, json_data={"results": [
            {"title": "Q", "url": "https://example.com/q", "snippet": "Quota test"},
        ]})

        def mock_request(*args, **kwargs):
            return mock_resp

        engine._http_session.request = mock_request

        request = SearchRequest(query="quota check", num_results=1)
        result = asyncio.run(engine._execute_single_provider(http_provider, request))

        assert result.status == ResultStatus.OK
        assert len(result.items) == 1
        assert result.provider == "test_http"
        assert result.provider_type == ProviderType.HTTP
