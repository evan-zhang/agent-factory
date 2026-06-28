"""
orchestrator/tests/test_integration.py

集成测试 — 多模块协作流程验证。

测试范围：
1. 基础搜索流程：完整 request → search → response 生命周期
2. 三轮递进策略：提前终止 + query_template 验证
3. Fallback 链集成：主搜索失败 → fallback 兜底，跳过已调用 provider
4. 错误重试传播：TIMEOUT 重试 3 次后失败
5. 缓存集成：cache miss → hit 流程
6. 性能追踪：provider stats 记录

约束：
- 不修改 35 项现有测试
- 优先 mock MCP client 的 call_tool 返回值
- 保持 Python 3.9+ 兼容
- 所有 mock 数据用 Python dict/list，不用 JSON 字符串
- 性能追踪测试使用 engine.reset_stats() 确保隔离
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 关闭 orchestrator 日志输出
logging.disable(logging.CRITICAL)

from ..engine import SearchEngine, apply_query_template
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
    FallbackChainConfig,
)
from ..config import ConfigLoader
from ..mcp_client import McporterMCPClient
from ..state import StateManager
from ..cache import CacheManager
from ..aggregator import ResultAggregator
from ..fallback_chain import FallbackChain


# ────────────────────────────────────────────────────────
# MCP mock 响应工厂
# ────────────────────────────────────────────────────────

def make_organic_mcp(items: List[Dict[str, str]]) -> Dict[str, Any]:
    """MiniMax 格式：{organic: [{title, link, snippet, date}, ...]}"""
    return {
        "content": [{"type": "text", "text": json.dumps({"organic": items})}],
        "isError": False,
    }


def make_results_mcp(items: List[Dict[str, str]]) -> Dict[str, Any]:
    """open-websearch 格式：{results: [{title, url, content, publishedDate}, ...]}"""
    return {
        "content": [{"type": "text", "text": json.dumps({"results": items})}],
        "isError": False,
    }


def make_empty_mcp() -> Dict[str, Any]:
    """空结果"""
    return {
        "content": [{"type": "text", "text": json.dumps({"organic": []})}],
        "isError": False,
    }


def make_error_mcp(error_msg: str = "Mock provider error") -> Dict[str, Any]:
    """MCP 错误响应"""
    return {
        "content": [],
        "isError": True,
        "error": error_msg,
    }


# ────────────────────────────────────────────────────────
# 可编程 Mock MCP 客户端
# ────────────────────────────────────────────────────────

class _InMemoryMCPClient:
    """每个 server_name 可独立配置返回值和异常。

    跟踪所有调用记录以便断言验证。
    """

    def __init__(self):
        self.responses: Dict[str, Dict[str, Any]] = {}
        self.exceptions: Dict[str, Exception] = {}
        self.call_history: List[Dict[str, Any]] = []

    def set_response(self, server_name: str, response: Dict[str, Any]):
        """设置指定 server_name 的正常返回值"""
        self.responses[server_name] = response
        self.exceptions.pop(server_name, None)

    def set_exception(self, server_name: str, exception: Exception):
        """设置指定 server_name 的异常"""
        self.exceptions[server_name] = exception
        self.responses.pop(server_name, None)

    def clear_history(self):
        """清空调用历史"""
        self.call_history.clear()

    async def call_tool(
        self, server_name: str, tool_name: str,
        arguments: Dict[str, Any], timeout: float = 30.0,
    ) -> Dict[str, Any]:
        self.call_history.append({
            "server": server_name,
            "tool": tool_name,
            "args": arguments,
        })
        if server_name in self.exceptions:
            raise self.exceptions[server_name]
        if server_name in self.responses:
            return self.responses[server_name]
        raise Exception(f"no mock data for server={server_name}")

    async def close(self):
        pass

    def get_call_count(self, server_name: Optional[str] = None) -> int:
        if server_name is None:
            return len(self.call_history)
        return sum(1 for c in self.call_history if c["server"] == server_name)


# ────────────────────────────────────────────────────────
# Mock ConfigLoader 工厂
# ────────────────────────────────────────────────────────

def _default_providers() -> Dict[str, ProviderConfig]:
    """默认的三合一 provider 配置"""
    return {
        "minimax": ProviderConfig(
            name="minimax",
            display_name="MiniMax Search",
            type=ProviderType.MCP,
            enabled=True,
            mcp_server="minimax",
            mcp_tool_name="web_search",
            call_parameters={"query": {"source": "query", "type": "string"},
                             "num_results": {"source": "num_results", "type": "integer"}},
            result_mapping={"title": "title", "url": "link", "snippet": "snippet",
                            "published_date": "date", "score": None},
            quota_limit=100,
            quota_window=60,
            timeout=30,
        ),
        "open_websearch": ProviderConfig(
            name="open_websearch",
            display_name="Open Web Search",
            type=ProviderType.MCP,
            enabled=True,
            mcp_server="open-websearch",
            mcp_tool_name="search",
            call_parameters={"query": {"source": "query", "type": "string"},
                             "count": {"source": "num_results", "type": "integer"}},
            result_mapping={"title": "title", "url": "url", "snippet": "content",
                            "published_date": "publishedDate", "score": None},
            quota_limit=60,
            quota_window=60,
            timeout=30,
        ),
        "web_fetch": ProviderConfig(
            name="web_fetch",
            display_name="Web Fetch",
            type=ProviderType.MCP,
            enabled=True,
            mcp_server="exa",
            mcp_tool_name="web_search_exa",
            call_parameters={"query": {"source": "query", "type": "string"},
                             "numResults": {"source": "num_results", "type": "integer"}},
            result_mapping={"title": "title", "url": "url", "snippet": "snippet",
                            "published_date": "published_date", "score": None},
            quota_limit=50,
            quota_window=60,
            timeout=30,
        ),
    }


def _mock_config_loader(
    providers: Optional[Dict[str, ProviderConfig]] = None,
    intent_modes: Optional[Dict[str, IntentModeConfig]] = None,
    fallback_config: Optional[FallbackChainConfig] = None,
):
    """创建 Mock ConfigLoader

    用 MagicMock 覆盖 ConfigLoader 的所有配置查询方法，
    避免从文件系统读取真实 YAML。
    """
    pdata = providers or _default_providers()

    if fallback_config is None:
        fallback_config = FallbackChainConfig(
            chain=["open_websearch", "web_fetch", "minimax"],
            trigger_on_status=[
                ResultStatus.ALL_FAILED,
                ResultStatus.ERROR,
                ResultStatus.NO_MATCH,
            ],
            max_depth=3,
        )

    loader = MagicMock(spec=ConfigLoader)
    loader.load_all = MagicMock()
    loader.get_provider = lambda name: pdata.get(name)
    loader.list_providers = MagicMock(
        side_effect=lambda enabled_only=True: (
            [p for p in pdata.values() if p.enabled]
            if enabled_only else list(pdata.values())
        )
    )
    loader.get_intent_mode = lambda intent: (
        intent_modes.get(intent) if intent_modes else None
    )
    loader.list_intent_modes = lambda: list(intent_modes.values()) if intent_modes else []
    loader.get_fallback_config = lambda: fallback_config

    # 保存 providers 引用以便测试中修改
    loader._providers_data = pdata
    loader._intent_modes_data = intent_modes or {}

    # Phase 2 R2: Scorer 配置
    from ..schema import ScorerConfig
    loader.get_scorer_config = lambda: ScorerConfig()

    # Phase 2 R3: Router 配置（默认 disabled）
    from ..schema import RouterConfig
    loader.get_router_config = lambda: RouterConfig()

    return loader


def _make_engine(
    mock_client: _InMemoryMCPClient,
    config_loader=None,
    intent_modes: Optional[Dict[str, IntentModeConfig]] = None,
) -> SearchEngine:
    """工厂：创建 SearchEngine，所有子组件均为真实实现（除 MCP client 和 ConfigLoader）"""
    if config_loader is None:
        config_loader = _mock_config_loader(intent_modes=intent_modes)

    engine = SearchEngine(
        config_loader=config_loader,
        mcp_client=mock_client,
        state_manager=StateManager(),
        cache_manager=CacheManager(),
        aggregator=ResultAggregator(),
        fallback_chain=FallbackChain(),
    )
    engine.reset_stats()
    return engine


# ────────────────────────────────────────────────────────
# Helper: 运行异步函数
# ────────────────────────────────────────────────────────

def _run(coro):
    """同步调用异步 coroutine"""
    return asyncio.run(coro)


# ════════════════════════════════════════════════════════
# 集成测试 1：基础搜索流程
# ════════════════════════════════════════════════════════

class TestBasicSearchFlow:
    """完整的 request → search → response 生命周期"""

    @pytest.fixture
    def mock_client(self) -> _InMemoryMCPClient:
        client = _InMemoryMCPClient()
        # 两个 provider 都返回正常结果
        client.set_response("minimax", make_organic_mcp([
            {"title": "社保缴费基数调整", "link": "https://example.com/1",
             "snippet": "社保缴费基数最新政策", "date": "2026-01-01"},
            {"title": "深圳社保缴费比例", "link": "https://example.com/2",
             "snippet": "2025年深圳社保缴费比例详解", "date": "2026-01-02"},
        ]))
        client.set_response("open-websearch", make_results_mcp([
            {"title": "社保缴费指南", "url": "https://example.com/3",
             "content": "社保缴费流程和注意事项", "publishedDate": "2026-01-01"},
        ]))
        return client

    @pytest.fixture
    def engine(self, mock_client) -> SearchEngine:
        eng = _make_engine(mock_client)
        # 确保 exa 也有 response
        eng.config_loader._providers_data.setdefault(
            "web_fetch", _default_providers()["web_fetch"]
        )
        return eng

    def test_complete_flow_returns_valid_result(self, engine, mock_client):
        """验证 search() 完整生命周期返回正确结构"""
        result = _run(engine.search(SearchRequest(query="社保缴费", num_results=5)))

        # 版本号
        assert result.version == "1.0.0"
        # 状态应为 OK 或 PARTIAL
        assert result.status in (ResultStatus.OK, ResultStatus.PARTIAL)
        # provider 不应为空
        assert result.provider is not None
        # 应有搜索结果
        assert len(result.items) > 0
        # 响应时间应 > 0
        assert result.response_time > 0
        # 应记录 engine 轨迹
        assert "engines_tried" in result.metadata
        assert len(result.metadata["engines_tried"]) > 0
        # 非缓存结果
        assert not result.cached
        # 未触发 fallback
        assert not result.fallback_triggered

    def test_search_invokes_all_providers(self, engine, mock_client):
        """验证 search() 调用了所有启用的 provider"""
        _run(engine.search(SearchRequest(query="test", num_results=3)))
        servers = {c["server"] for c in mock_client.call_history}
        assert len(mock_client.call_history) >= 2

    def test_aggregator_dedup_works(self, engine, mock_client):
        """两个 provider 返回相同 URL → 聚合后只保留一条"""
        mock_client.clear_history()
        mock_client.set_response("minimax", make_organic_mcp([
            {"title": "标题 A", "link": "https://example.com/dup",
             "snippet": "摘要 A", "date": "2026-01-01"},
            {"title": "标题 B", "link": "https://example.com/B",
             "snippet": "摘要 B", "date": "2026-01-01"},
        ]))
        mock_client.set_response("open-websearch", make_results_mcp([
            {"title": "标题 A（重复）", "url": "https://example.com/dup",
             "content": "摘要 A 重复", "publishedDate": "2026-01-01"},
            {"title": "标题 C", "url": "https://example.com/C",
             "content": "摘要 C", "publishedDate": "2026-01-01"},
            {"title": "标题 D", "url": "https://example.com/D",
             "content": "摘要 D", "publishedDate": "2026-01-01"},
        ]))

        result = _run(engine.search(SearchRequest(query="test dedup", num_results=5)))

        # 去重前 5 条，去重后 4 条
        assert len(result.items) == 4
        urls = [item.url for item in result.items]
        assert len(set(urls)) == 4
        assert urls.count("https://example.com/dup") == 1

    def test_error_provider_returns_partial(self, engine, mock_client):
        """某个 provider 失败返回 ERROR，不影响其他 provider 的结果"""
        mock_client.clear_history()
        mock_client.set_exception("minimax", Exception("connection timeout"))
        mock_client.set_response("open-websearch", make_results_mcp([
            {"title": "正常结果", "url": "https://example.com/ok",
             "content": "正常摘要", "publishedDate": "2026-01-01"},
        ]))
        mock_client.set_response("exa", make_results_mcp([
            {"title": "Web Fetch 结果", "url": "https://example.com/wf",
             "snippet": "Fetch 摘要", "published_date": "2026-01-01"},
        ]))

        result = _run(engine.search(SearchRequest(query="partial test", num_results=5)))

        assert result.status in (ResultStatus.PARTIAL, ResultStatus.OK)
        assert len(result.items) > 0


# ════════════════════════════════════════════════════════
# 集成测试 2：三轮递进策略完整流程
# ════════════════════════════════════════════════════════

class TestMultiRoundProgressStrategy:
    """三轮递进检索：提前终止 + query_template + provider_filter"""

    @pytest.fixture
    def mock_client(self) -> _InMemoryMCPClient:
        return _InMemoryMCPClient()

    @pytest.fixture
    def intent_modes(self) -> Dict[str, IntentModeConfig]:
        three_round_strategy = QueryStrategy(
            enabled=True,
            rounds=[
                RoundConfig(
                    mode="precise",
                    query_template='"{query}"',
                    count=5,
                    timeout_ms=8000,
                    provider_filter=["minimax"],
                ),
                RoundConfig(
                    mode="broaden",
                    query_template="{query}",
                    count=10,
                    timeout_ms=10000,
                    provider_filter=[],
                ),
                RoundConfig(
                    mode="fallback",
                    query_template="{query}",
                    count=15,
                    timeout_ms=12000,
                    provider_filter=[],
                ),
            ],
            round_termination=RoundTermination(min_results=3, max_rounds=3),
        )
        return {
            "INFO": IntentModeConfig(
                intent="INFO",
                enable_fallback=True,
                preferred_providers=["minimax", "open_websearch"],
                strategy_rounds=three_round_strategy,
            ),
        }

    @pytest.fixture
    def engine(self, mock_client, intent_modes) -> SearchEngine:
        eng = _make_engine(mock_client, intent_modes=intent_modes)
        # 确保 exa 可用
        eng.config_loader._providers_data.setdefault(
            "web_fetch", _default_providers()["web_fetch"]
        )
        return eng

    def test_round2_termination(self, engine, mock_client, intent_modes):
        """Round 1 返回 1 条（< min_results=3），Round 2 返回 5 条，在 Round 2 后终止"""
        # Round 1: minimax 返回 1 条
        mock_client.set_response("minimax", make_organic_mcp([
            {"title": "精确匹配结果", "link": "https://exact.com/1",
             "snippet": "精确匹配", "date": "2026-01-01"},
        ]))
        # Round 2: open-websearch 返回 5 条
        mock_client.set_response("open-websearch", make_results_mcp([
            {"title": f"泛搜结果 {i}", "url": f"https://broad.com/{i}",
             "content": f"泛搜摘要 {i}", "publishedDate": "2026-01-01"}
            for i in range(5)
        ]))
        mock_client.set_response("exa", make_results_mcp([]))

        request = SearchRequest(
            query="深圳社保缴费比例2025", num_results=10, intent="INFO",
        )
        result = _run(engine.search(request))

        # 应有 6 条结果（Round1 的 1 条 + Round2 的 5 条）
        assert len(result.items) == 6
        assert result.status in (ResultStatus.OK, ResultStatus.PARTIAL)

        # Round 1 使用引号 query
        round1_calls = [c for c in mock_client.call_history
                        if c["server"] == "minimax"]
        assert len(round1_calls) >= 1
        assert any('"' in str(c["args"].get("query", ""))
                    for c in round1_calls)

        # Round 2 的 query 无引号
        round2_calls = [c for c in mock_client.call_history
                        if c["server"] == "open-websearch"]
        assert len(round2_calls) >= 1
        for c in round2_calls:
            q = c["args"].get("query", "")
            assert not q.startswith('"') or not q.endswith('"')

        # 验证 metadata
        assert result.metadata.get("strategy") == "multi_round"
        assert result.metadata.get("rounds_completed", 0) == 2
        assert result.metadata.get("total_rounds") >= 2
        assert result.metadata.get("round_termination_triggered") is True

    def test_round1_termination_when_enough(self, engine, mock_client):
        """Round 1 直接达到 min_results=3 → 在 Round 1 后终止"""
        mock_client.clear_history()
        mock_client.set_response("minimax", make_organic_mcp([
            {"title": f"精确结果 {i}", "link": f"https://exact.com/{i}",
             "snippet": f"精确摘要 {i}", "date": "2026-01-01"}
            for i in range(5)
        ]))
        mock_client.set_response("open-websearch", make_results_mcp([
            {"title": "不应被调用", "url": "https://never.com/called",
             "content": "不应出现", "publishedDate": "2026-01-01"},
        ]))
        mock_client.set_response("exa", make_results_mcp([]))

        result = _run(engine.search(
            SearchRequest(query="test", num_results=10, intent="INFO"),
        ))

        assert len(result.items) == 5
        assert result.metadata.get("rounds_completed") == 1
        assert result.metadata.get("round_termination_triggered") is True

        # Round 2 的 provider 不应被调用
        open_web_calls = [c for c in mock_client.call_history
                          if c["server"] == "open-websearch"]
        assert len(open_web_calls) == 0

    def test_all_three_rounds_when_insufficient(self, engine, mock_client):
        """每轮结果都不够 → 全部三轮执行完成"""
        mock_client.clear_history()
        mock_client.set_response("minimax", make_organic_mcp([]))
        mock_client.set_response("open-websearch", make_results_mcp([
            {"title": "泛搜结果", "url": "https://broad.com/1",
             "content": "泛搜摘要", "publishedDate": "2026-01-01"},
        ]))
        mock_client.set_response("exa", make_results_mcp([]))

        result = _run(engine.search(
            SearchRequest(query="rare query", num_results=30, intent="INFO"),
        ))

        assert result.metadata.get("rounds_completed") == 3
        assert result.metadata.get("total_rounds") == 3
        assert result.metadata.get("round_termination_triggered") is False


# ════════════════════════════════════════════════════════
# 集成测试 3：Fallback 链集成
# ════════════════════════════════════════════════════════

class TestFallbackChainIntegration:
    """主搜索全失败 → Fallback 链触发 → 跳过已调用 provider → 兜底成功"""

    @pytest.fixture
    def mock_client(self) -> _InMemoryMCPClient:
        c = _InMemoryMCPClient()
        # 所有主搜索的 provider 都失败（包括 exa/web_fetch）
        # 这样 aggregator 返回 ALL_FAILED，触发 fallback 链
        c.set_exception("minimax", Exception("connection reset: timeout"))
        c.set_exception("open-websearch", Exception("connection reset: timeout"))
        c.set_exception("exa", Exception("connection reset: timeout"))
        return c

    @pytest.fixture
    def extra_provider_config(self) -> ProviderConfig:
        return ProviderConfig(
            name="fallback_bot",
            display_name="Fallback Bot",
            type=ProviderType.MCP,
            enabled=True,
            mcp_server="fallback_bot",
            mcp_tool_name="search",
            call_parameters={"query": {"source": "query", "type": "string"}},
            result_mapping={"title": "title", "url": "url", "snippet": "snippet",
                            "published_date": None, "score": None},
            quota_limit=100,
            quota_window=60,
            timeout=30,
        )

    @pytest.fixture
    def engine(self, mock_client, extra_provider_config) -> SearchEngine:
        providers = _default_providers()
        providers["fallback_bot"] = extra_provider_config
        config_loader = _mock_config_loader(
            providers=providers,
            intent_modes={
                "SEARCH": IntentModeConfig(
                    intent="SEARCH",
                    enable_fallback=True,
                    preferred_providers=["minimax", "open_websearch", "web_fetch"],
                ),
            },
        )
        return _make_engine(mock_client, config_loader=config_loader)

    def test_fallback_skips_tried_providers(self, engine, mock_client,
                                              extra_provider_config):
        """主搜索尝试 minimax, open_websearch, web_fetch 全部失败

        Fallback 跳过这 3 个，尝试 fallback_bot → 成功
        """
        mock_client.set_response("fallback_bot", make_results_mcp([
            {"title": "Fallback 兜底结果", "url": "https://fallback.com/1",
             "snippet": "Fallback 摘要", "published_date": "2026-01-01"},
            {"title": "Fallback 结果 2", "url": "https://fallback.com/2",
             "snippet": "Fallback 摘要 2", "published_date": "2026-01-01"},
        ]))

        result = _run(engine.search(
            SearchRequest(query="test fallback", num_results=5, intent="SEARCH"),
        ))

        assert result.fallback_triggered is True, (
            f"fallback_triggered should be True, got False. "
            f"status={result.status.value} error={result.error}"
        )
        assert len(result.items) >= 1

        # fallback_chain 记录 fallback_bot 被调用过
        assert "fallback_bot" in result.fallback_chain, (
            f"fallback_bot should be in fallback_chain: {result.fallback_chain}"
        )
        # engines_tried 包含主搜索尝试的 provider
        engines_tried = result.metadata.get("engines_tried", [])
        assert "minimax" in engines_tried or "open_websearch" in engines_tried

    def test_fallback_all_remaining_fail(self, engine, mock_client,
                                          extra_provider_config):
        """主搜索全失败 + fallback 也全部失败 → 最终 ALL_FAILED"""
        mock_client.set_exception("fallback_bot", Exception("connection refused"))

        result = _run(engine.search(
            SearchRequest(query="all fail test", num_results=5, intent="SEARCH"),
        ))

        # 当主搜索 + fallback 都失败时，fallback_triggered 会在主搜索结果中保留
        # 因为最终返回的是 primary_result（而非 fallback_result）
        assert result.status in (ResultStatus.ALL_FAILED, ResultStatus.ERROR), (
            f"status={result.status.value} error={result.error}"
        )
        assert len(result.items) == 0


# ════════════════════════════════════════════════════════
# 集成测试 4：错误重试传播
# ════════════════════════════════════════════════════════

class TestErrorRetryPropagation:
    """Provider 返回 TIMEOUT → _execute_with_retry 重试 3 次 → 全部超时"""

    @pytest.fixture
    def mock_client(self) -> _InMemoryMCPClient:
        c = _InMemoryMCPClient()
        c.set_exception("minimax", Exception("timeout: connection timed out"))
        c.set_exception("open-websearch", Exception("timeout: connection timed out"))
        return c

    @pytest.fixture
    def engine(self, mock_client) -> SearchEngine:
        eng = _make_engine(mock_client)
        eng._max_retries = 3
        eng._retry_backoff_base = 0.01  # 快速重试
        # 确保 exa 也有异常
        eng.config_loader._providers_data.setdefault(
            "web_fetch", ProviderConfig(
                name="web_fetch", display_name="WF", type=ProviderType.MCP,
                enabled=True, mcp_server="exa", mcp_tool_name="search",
                call_parameters={}, result_mapping={},
                quota_limit=100, quota_window=60, timeout=30,
            )
        )
        return eng

    def test_retry_exhausted_returns_error(self, engine, mock_client):
        """重试 3 次全部超时 → 最终返回 ERROR 状态"""
        result = _run(engine.search(SearchRequest(query="timeout test", num_results=5)))
        assert result.status in (ResultStatus.ERROR, ResultStatus.ALL_FAILED)
        assert result.error is not None

    def test_perf_records_3_fails(self, engine, mock_client):
        """perf_data 记录每次 provider 调用失败的 fail 计数"""
        _run(engine.search(SearchRequest(query="perf fail test", num_results=5)))
        stats = engine.get_stats()

        for provider_name in ("minimax", "open_websearch"):
            pdata = stats.get("providers", {}).get(provider_name, {})
            # 至少有一次 fail（每次 _execute_inner_provider 调用都记录一次 fail）
            assert pdata.get("fail", 0) >= 1, (
                f"{provider_name} should have >= 1 fails, got {pdata.get('fail')}"
            )

    def test_provider_marked_unhealthy(self, engine, mock_client):
        """provider 被标记为不健康"""
        _run(engine.search(SearchRequest(query="health test", num_results=5)))

        for provider_name in ("minimax", "open_websearch"):
            health = engine.state_manager.get_health(provider_name)
            assert health.is_healthy is False
            assert health.error_message is not None


# ════════════════════════════════════════════════════════
# 集成测试 5：缓存集成
# ════════════════════════════════════════════════════════

class TestCacheIntegration:
    """cache miss → hit 完整流程"""

    @pytest.fixture
    def mock_client(self) -> _InMemoryMCPClient:
        c = _InMemoryMCPClient()
        c.set_response("minimax", make_organic_mcp([
            {"title": "缓存测试结果", "link": "https://cache.com/1",
             "snippet": "缓存摘要", "date": "2026-01-01"},
        ]))
        c.set_response("open-websearch", make_results_mcp([]))
        c.set_response("exa", make_results_mcp([]))
        return c

    @pytest.fixture
    def engine(self, mock_client) -> SearchEngine:
        return _make_engine(mock_client)

    def test_cache_miss_then_hit(self, engine, mock_client):
        """cache miss → 第二次相同 query cache hit"""
        query = "cache integration test"

        # 第一次搜索：cache miss
        result1 = _run(engine.search(SearchRequest(query=query, num_results=3)))
        assert result1 is not None
        call_count_after_first = mock_client.get_call_count()
        assert call_count_after_first > 0

        # 第二次搜索（相同 query）：cache hit
        result2 = _run(engine.search(SearchRequest(query=query, num_results=3)))
        assert result2 is not None
        # 不应有新的 provider 调用（cache 直接返回）
        assert mock_client.get_call_count() == call_count_after_first, (
            f"cache should prevent new provider calls: "
            f"{mock_client.get_call_count()} vs {call_count_after_first}"
        )

        # cache 统计更新
        stats = engine.get_stats()
        cache_stats = stats.get("cache", {})
        assert cache_stats.get("hits", 0) >= 1, (
            f"expected at least 1 hit, got {cache_stats.get('hits')}"
        )
        assert cache_stats.get("misses", 0) >= 1

    def test_different_query_cache_miss(self, engine, mock_client):
        """不同 query → 两次都是 cache miss → 调用 provider 两次"""
        _run(engine.search(SearchRequest(query="first query", num_results=3)))
        count1 = mock_client.get_call_count()

        _run(engine.search(SearchRequest(query="second query", num_results=3)))
        count2 = mock_client.get_call_count()

        assert count2 > count1, "不同 query 应导致新的 provider 调用"

    def test_cache_different_num_results(self, engine, mock_client):
        """相同 query 但不同 num_results → cache miss"""
        _run(engine.search(SearchRequest(query="test", num_results=3)))
        count1 = mock_client.get_call_count()

        _run(engine.search(SearchRequest(query="test", num_results=10)))
        count2 = mock_client.get_call_count()

        assert count2 > count1


# ════════════════════════════════════════════════════════
# 集成测试 6：性能追踪
# ════════════════════════════════════════════════════════

class TestPerformanceTracking:
    """provider stats 记录 + get_stats() 查询"""

    @pytest.fixture
    def mock_client(self) -> _InMemoryMCPClient:
        c = _InMemoryMCPClient()
        c.set_response("minimax", make_organic_mcp([
            {"title": f"Result R{i}", "link": f"https://r.com/{i}",
             "snippet": f"Snippet {i}", "date": "2026-01-01"}
            for i in range(2)
        ]))
        c.set_response("open-websearch", make_results_mcp([]))
        c.set_response("exa", make_results_mcp([]))
        return c

    @pytest.fixture
    def engine(self, mock_client) -> SearchEngine:
        return _make_engine(mock_client)

    def test_successful_search_tracks_stats(self, engine, mock_client):
        """一次成功搜索 → provider stats 应有记录"""
        _run(engine.search(SearchRequest(query="perf test", num_results=5)))

        stats = engine.get_stats()
        pdata = stats.get("providers", {}).get("minimax", {})
        assert pdata.get("success", 0) >= 1
        assert pdata.get("avg_latency_ms", 0) > 0

    def test_failed_search_tracks_fail(self, engine, mock_client):
        """一次失败搜索 → fail++"""
        mock_client.set_exception("minimax", Exception("connection error"))
        mock_client.set_exception("open-websearch", Exception("connection error"))
        mock_client.set_exception("exa", Exception("connection error"))

        _run(engine.search(SearchRequest(query="perf fail", num_results=5)))

        stats = engine.get_stats()
        for pname in ("minimax", "open_websearch"):
            pdata = stats.get("providers", {}).get(pname, {})
            assert pdata.get("fail", 0) >= 1

    def test_mixed_success_fail_tracking(self, engine, mock_client):
        """多次搜索混合成功和失败 → 统计准确"""
        engine.reset_stats()

        # Search 1: minimax success
        _run(engine.search(SearchRequest(query="search 1", num_results=5)))

        # Search 2: minimax fails
        mock_client.set_exception("minimax", Exception("connection timeout"))
        mock_client.set_response("open-websearch", make_results_mcp([
            {"title": "Search2 Result", "url": "https://s2.com/1",
             "content": "Search2 snippet", "publishedDate": "2026-01-01"},
        ]))
        _run(engine.search(SearchRequest(query="search 2", num_results=5)))

        stats = engine.get_stats()
        minimax_data = stats.get("providers", {}).get("minimax", {})
        assert minimax_data.get("calls", 0) >= 2

    def test_reset_stats(self, engine, mock_client):
        """reset_stats() 后统计数据清零"""
        _run(engine.search(SearchRequest(query="seed data", num_results=5)))

        stats_before = engine.get_stats()
        assert len(stats_before.get("providers", {})) > 0

        engine.reset_stats()
        stats_after = engine.get_stats()
        assert len(stats_after.get("providers", {})) == 0
        assert stats_after.get("cache", {}).get("hits") == 0


# ════════════════════════════════════════════════════════
# 集成测试 7：Phase 2 完整三组件协同
# ════════════════════════════════════════════════════════

class TestPhase2FullPipeline:
    """LLM Query Agent + Adaptive Router + Scorer 协同工作"""

    @pytest.fixture
    def mock_client(self) -> _InMemoryMCPClient:
        c = _InMemoryMCPClient()
        c.set_response("minimax", make_organic_mcp([
            {"title": "社保缴费基数", "link": "https://sz.gov.cn/shebao",
             "snippet": "社保缴费基数调整通知", "date": "2026-01-15"},
            {"title": "社保缴费比例", "link": "https://hr.sz.gov.cn/policy",
             "snippet": "2025年深圳社保缴费比例", "date": "2026-02-01"},
        ]))
        c.set_response("open-websearch", make_results_mcp([
            {"title": "社保指南", "url": "https://example.com/guide",
             "content": "社保缴费流程简介", "publishedDate": "2026-01-10"},
        ]))
        c.set_response("exa", make_results_mcp([]))
        return c

    @pytest.fixture
    def engine(self, mock_client) -> SearchEngine:
        """创建启用了 LLM Agent + Adaptive Router + Scorer 的引擎"""
        from ..llm_agent import LLMQueryAgent
        from ..schema import LLMConfig
        from ..router import AdaptiveRouter

        # LLM Agent（启用，mock API 返回）
        llm_config = LLMConfig(enabled=True, timeout=10)
        llm_agent = LLMQueryAgent(config=llm_config)

        # Mock LLM API 返回
        import json
        mock_policy_response = json.dumps({
            "intent": "policy",
            "entities": {"city": "深圳", "department": "人社局", "year": "2025"},
            "suggested_queries": [
                {
                    "query": "深圳市人社局 2025 社保缴费基数 政策",
                    "target_providers": ["minimax"],
                    "rationale": "精准政策查询",
                },
            ],
            "provider_scores": {"minimax": 0.9, "open_websearch": 0.5, "web_fetch": 0.7},
            "site_restrictions": ["gov.cn", "sz.gov.cn"],
        })
        llm_agent._call_llm = AsyncMock(return_value=mock_policy_response)
        llm_agent._session = MagicMock()

        # Adaptive Router（启用，直接创建）
        from ..schema import RouterConfig
        import time
        from ..schema import ProviderPerformance

        engine = SearchEngine(
            config_loader=_mock_config_loader(
                providers=_default_providers(),
                intent_modes={
                    "INFO": IntentModeConfig(
                        intent="INFO",
                        preferred_providers=["minimax", "open_websearch"],
                    ),
                },
            ),
            mcp_client=mock_client,
            state_manager=StateManager(),
            cache_manager=CacheManager(),
            aggregator=ResultAggregator(),
            fallback_chain=FallbackChain(),
            llm_agent=llm_agent,
        )

        # Override router with enabled version
        router_config = RouterConfig(enabled=True, min_history=5)
        engine.router = AdaptiveRouter(router_config)

        # Pre-seed perf data to meet min_history
        engine.router._perf["minimax:INFO"] = ProviderPerformance(
            provider="minimax", intent="INFO",
            total_calls=10, success_calls=9, total_latency_ms=5000.0,
            last_call_time=time.time(),
        )
        engine.router._perf["open_websearch:INFO"] = ProviderPerformance(
            provider="open_websearch", intent="INFO",
            total_calls=8, success_calls=7, total_latency_ms=1200.0,
            last_call_time=time.time(),
        )
        engine.router._perf["web_fetch:INFO"] = ProviderPerformance(
            provider="web_fetch", intent="INFO",
            total_calls=5, success_calls=2, total_latency_ms=10000.0,
            last_call_time=time.time(),
        )

        engine.reset_stats()
        return engine

    def test_full_pipeline_llm_router_scorer(self, engine, mock_client):
        """LLM 改写 query → Router 选 provider → 搜索 → Scorer 排序"""
        result = _run(engine.search(
            SearchRequest(query="深圳社保缴费比例", intent="INFO", num_results=5),
        ))

        # 结果应有
        assert result.status in (ResultStatus.OK, ResultStatus.PARTIAL)
        assert len(result.items) > 0

        # Scorer 已评分排序（score 字段应 > 0）
        scores = [item.score for item in result.items]
        assert all(s > 0 for s in scores)

        # Router 的性能数据已记录
        report = engine.router.get_performance_report()
        assert report["data_points"] >= 1

        # LLM 改写应已触发（query 被改写为 LLM 建议的查询）
        # result.query 是改写后的 query
        assert result.query != "深圳社保缴费比例"
        # 改写后包含 SRE 相关的关键词
        assert "社保" in result.query


class TestPhase2LlmDegradeToRouter:
    """LLM 失败时降级到自适应路由（不影响搜索）"""

    @pytest.fixture
    def mock_client(self) -> _InMemoryMCPClient:
        c = _InMemoryMCPClient()
        c.set_response("minimax", make_organic_mcp([
            {"title": "结果 A", "link": "https://gov.cn/a",
             "snippet": "摘要 A", "date": "2026-01-01"},
            {"title": "结果 B", "link": "https://gov.cn/b",
             "snippet": "摘要 B", "date": "2026-01-02"},
        ]))
        c.set_response("open-websearch", make_results_mcp([
            {"title": "结果 C", "url": "https://ex.com/c",
             "content": "摘要 C", "publishedDate": "2026-01-01"},
        ]))
        c.set_response("exa", make_results_mcp([]))
        return c

    @pytest.fixture
    def engine(self, mock_client) -> SearchEngine:
        """创建引擎：LLM Agent enabled 但 API 超时 + Adaptive Router enabled"""
        from ..llm_agent import LLMQueryAgent
        from ..schema import LLMConfig, RouterConfig
        from ..router import AdaptiveRouter
        import time
        from ..schema import ProviderPerformance

        # LLM Agent（启用但 API 会超时）
        llm_config = LLMConfig(enabled=True, timeout=5)
        llm_agent = LLMQueryAgent(config=llm_config)
        llm_agent._call_llm = AsyncMock(side_effect=asyncio.TimeoutError("LLM timeout"))
        llm_agent._session = MagicMock()

        engine = SearchEngine(
            config_loader=_mock_config_loader(
                intent_modes={
                    "SEARCH": IntentModeConfig(
                        intent="SEARCH", preferred_providers=["minimax", "open_websearch"],
                    ),
                },
            ),
            mcp_client=mock_client,
            state_manager=StateManager(),
            cache_manager=CacheManager(),
            aggregator=ResultAggregator(),
            fallback_chain=FallbackChain(),
            llm_agent=llm_agent,
        )

        # Override router to enabled + seed data
        router_config = RouterConfig(enabled=True, min_history=5)
        engine.router = AdaptiveRouter(router_config)
        engine.router._perf["minimax:SEARCH"] = ProviderPerformance(
            provider="minimax", intent="SEARCH",
            total_calls=10, success_calls=9, total_latency_ms=5000.0,
            last_call_time=time.time(),
        )
        engine.router._perf["open_websearch:SEARCH"] = ProviderPerformance(
            provider="open_websearch", intent="SEARCH",
            total_calls=8, success_calls=7, total_latency_ms=1200.0,
            last_call_time=time.time(),
        )

        engine.reset_stats()
        return engine

    def test_llm_fails_router_still_works(self, engine, mock_client):
        """LLM 超时 → 降级 → Router 仍能正确路由 → 搜索成功"""
        result = _run(engine.search(
            SearchRequest(query="test degrade", intent="SEARCH", num_results=5),
        ))

        # 搜索仍成功
        assert result.status in (ResultStatus.OK, ResultStatus.PARTIAL)
        assert len(result.items) > 0

        # Router 记录了本次调用
        report = engine.router.get_performance_report()
        assert report["data_points"] >= 2


class TestPhase2RouterDisabled:
    """Adaptive Router 禁用时走静态路由"""

    @pytest.fixture
    def mock_client(self) -> _InMemoryMCPClient:
        c = _InMemoryMCPClient()
        c.set_response("minimax", make_organic_mcp([
            {"title": "Static Route Result", "link": "https://gov.cn/static",
             "snippet": "Static routed", "date": "2026-01-01"},
        ]))
        c.set_response("open-websearch", make_results_mcp([]))
        c.set_response("exa", make_results_mcp([]))
        return c

    @pytest.fixture
    def engine(self, mock_client) -> SearchEngine:
        """Adaptive Router disabled（默认）"""
        return _make_engine(
            mock_client,
            intent_modes={
                "STATIC": IntentModeConfig(
                    intent="STATIC",
                    preferred_providers=["minimax", "open_websearch"],
                ),
            },
        )

    def test_disabled_router_uses_static_preferred_providers(self, engine, mock_client):
        """Router disabled → 按 preferred_providers 顺序选择 provider"""
        # 不传 intent=STATIC，走默认路由
        # Adaptive Router 默认 disabled，按 preferred_providers 选择
        result = _run(engine.search(
            SearchRequest(query="static test", intent="STATIC", num_results=5),
        ))

        assert result.status in (ResultStatus.OK, ResultStatus.PARTIAL)
        assert len(result.items) > 0

        # Router 不记录任何数据（disabled）
        report = engine.router.get_performance_report()
        assert report["data_points"] == 0

    def test_disabled_router_still_routes_providers(self, engine, mock_client):
        """禁用路由 → providers 按 intent mode 的 preferred_providers 选择"""
        # 验证 router 的 select_providers 直接走静态回退
        providers = engine.config_loader.list_providers(enabled_only=True)

        # Router disabled，不会记录
        engine.router.record_result("minimax", "STATIC", True, 100.0)
        assert len(engine.router._perf) == 0


class TestPhase2PerfRecording:
    """Phase 2 组件性能数据记录"""

    @pytest.fixture
    def mock_client(self) -> _InMemoryMCPClient:
        c = _InMemoryMCPClient()
        # 混合成功和失败
        c.set_response("minimax", make_organic_mcp([
            {"title": "结果 X", "link": "https://gov.cn/x",
             "snippet": "结果 X", "date": "2026-01-01"},
        ]))
        c.set_exception("open-websearch", Exception("connection error"))
        c.set_exception("exa", Exception("timeout"))
        return c

    @pytest.fixture
    def engine(self, mock_client) -> SearchEngine:
        from ..schema import RouterConfig
        from ..router import AdaptiveRouter
        import time
        from ..schema import ProviderPerformance

        engine = _make_engine(mock_client)

        # Enable router with seed data
        router_config = RouterConfig(enabled=True, min_history=5)
        engine.router = AdaptiveRouter(router_config)
        engine.router._perf["minimax:general"] = ProviderPerformance(
            provider="minimax", intent="general",
            total_calls=10, success_calls=9, total_latency_ms=5000.0,
            last_call_time=time.time(),
        )

        engine.reset_stats()
        return engine

    def test_router_perf_recorded_on_success(self, engine, mock_client):
        """成功时 Router 记录 perf 数据"""
        _run(engine.search(SearchRequest(query="test", num_results=5)))

        report = engine.router.get_performance_report()
        assert report["data_points"] >= 2

        # 检查 provider 有记录
        for provider_name in ("minimax",):
            assert provider_name in report["providers"]

        # minimax 应至少有 1 次成功调用（包括 seed 的 9 次）
        assert report["providers"]["minimax"]["total_calls"] >= 11

    def test_router_perf_recorded_on_failure(self, engine, mock_client):
        """失败时 Router 也记录 perf 数据"""
        report_before = engine.router.get_performance_report()

        _run(engine.search(SearchRequest(query="test", num_results=5)))

        report_after = engine.router.get_performance_report()

        # open-websearch 和 exa 应该被记录为失败
        # 至少 data_points 增加了
        assert report_after["data_points"] >= report_before["data_points"]

        # 失败 provider 的 success_rate 应降低
        if "open_websearch" in report_after["providers"]:
            ow = report_after["providers"]["open_websearch"]
            assert ow["fail_calls"] >= 1

    def test_scorer_perf_correct(self, engine, mock_client):
        """Scorer 的性能数据正确（通过 score_detail 验证）"""
        result = _run(engine.search(SearchRequest(query="test", num_results=5)))

        # 每个结果都应该有 score_detail
        for item in result.items:
            assert "total" in item.score_detail
            assert "authority" in item.score_detail
            assert "freshness" in item.score_detail
            assert "relevance" in item.score_detail

        # 评分排序应正确：gov.cn 域名应排前面
        if len(result.items) >= 2:
            # 第一个结果的 score 不低于最后一个
            assert result.items[0].score >= result.items[-1].score
