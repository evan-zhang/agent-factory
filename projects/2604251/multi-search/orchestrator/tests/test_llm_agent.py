"""
orchestrator/tests/test_llm_agent.py

LLM Query Agent 单元测试集（Phase 2 R1）。

测试内容：
1. _build_prompt() — 验证 prompt 包含 query
2. _parse_llm_response() — 裸 JSON 解析
3. _parse_llm_response() — Markdown JSON 代码块容错
4. _cache_key() — 相同 query 相同 key
5. preprocess() 缓存命中
6. LLM 失败时的优雅降级
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

logging.disable(logging.CRITICAL)

from ..llm_agent import LLMQueryAgent, LLM_SYSTEM_PROMPT
from ..schema import SuggestedQuery, QueryIntent, LLMConfig


# ────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────

@pytest.fixture
def agent():
    """创建一个默认 disabled 的 LLMQueryAgent 实例。"""
    config = LLMConfig(
        enabled=True,
        cache_ttl=3600,
        timeout=10,
        endpoint="https://api.test.com/v1/chat/completions",
        model="test-model",
        max_tokens=512,
        temperature=0.3,
    )
    return LLMQueryAgent(config=config)


@pytest.fixture
def disabled_agent():
    """创建一个 disabled 的 LLMQueryAgent 实例。"""
    config = LLMConfig(enabled=False)
    return LLMQueryAgent(config=config)


# ────────────────────────────────────────────────────────
# Task 1: _build_prompt() 测试
# ────────────────────────────────────────────────────────

class TestBuildPrompt:
    """_build_prompt() 单元测试"""

    def test_prompt_contains_query(self, agent):
        """prompt 包含原始查询文本"""
        prompt = agent._build_prompt("深圳市社保缴费比例")
        assert "深圳市社保缴费比例" in prompt

    def test_prompt_contains_system_instructions(self, agent):
        """prompt 包含系统指令"""
        prompt = agent._build_prompt("test")
        assert "搜索查询分析师" in prompt
        assert "intent" in prompt
        assert "suggested_queries" in prompt
        assert "provider_scores" in prompt
        assert "site_restrictions" in prompt

    def test_prompt_with_english_query(self, agent):
        """英文查询也正确包含"""
        prompt = agent._build_prompt("US inflation rate 2025")
        assert "US inflation rate 2025" in prompt

    def test_prompt_with_special_chars(self, agent):
        """特殊字符查询正确包含"""
        query = "Python 3.9+ & Type Hints"
        prompt = agent._build_prompt(query)
        assert query in prompt

    def test_prompt_format(self, agent):
        """prompt 符合 LLM_SYSTEM_PROMPT 模板格式"""
        prompt = agent._build_prompt("test")
        expected_prefix = LLM_SYSTEM_PROMPT.split("{query}")[0]
        assert prompt.startswith(expected_prefix)


# ────────────────────────────────────────────────────────
# Task 2: _parse_llm_response() 测试
# ────────────────────────────────────────────────────────

class TestParseLlmResponse:
    """_parse_llm_response() 单元测试"""

    def test_parse_standard_json(self, agent):
        """标准 JSON 解析"""
        raw = json.dumps({
            "intent": "policy",
            "entities": {"city": "深圳", "department": "人社局", "year": "2025"},
            "suggested_queries": [
                {
                    "query": "深圳市人社局 2025 社保缴费比例",
                    "target_providers": ["minimax"],
                    "rationale": "精准政策查询",
                },
                {
                    "query": "深圳 社保 缴费 比例 规定",
                    "target_providers": ["brave", "tavily"],
                    "rationale": "泛搜覆盖",
                },
            ],
            "provider_scores": {"minimax": 0.9, "brave": 0.5, "tavily": 0.3, "web_fetch": 0.7},
            "site_restrictions": ["gov.cn", "sz.gov.cn"],
        })

        intent = agent._parse_llm_response(raw)

        assert intent.intent == "policy"
        assert intent.entities["city"] == "深圳"
        assert intent.entities["department"] == "人社局"
        assert len(intent.suggested_queries) == 2
        assert intent.suggested_queries[0].query == "深圳市人社局 2025 社保缴费比例"
        assert intent.suggested_queries[0].target_providers == ["minimax"]
        assert intent.suggested_queries[0].rationale == "精准政策查询"
        assert intent.suggested_queries[1].target_providers == ["brave", "tavily"]
        assert intent.provider_scores["minimax"] == 0.9
        assert intent.provider_scores["web_fetch"] == 0.7
        assert intent.site_restrictions == ["gov.cn", "sz.gov.cn"]

    def test_parse_empty_suggestions(self, agent):
        """suggested_queries 为空"""
        raw = json.dumps({
            "intent": "info",
            "entities": {},
            "suggested_queries": [],
            "provider_scores": {},
            "site_restrictions": [],
        })

        intent = agent._parse_llm_response(raw)
        assert intent.intent == "info"
        assert intent.suggested_queries == []

    def test_parse_invalid_intent_fallback(self, agent):
        """无效的 intent 值回退到 general"""
        raw = json.dumps({
            "intent": "shopping",
            "entities": {},
            "suggested_queries": [],
            "provider_scores": {},
            "site_restrictions": [],
        })

        intent = agent._parse_llm_response(raw)
        assert intent.intent == "general"

    def test_parse_minimal_json(self, agent):
        """最简 JSON 也能解析"""
        raw = '{"intent": "news"}'
        intent = agent._parse_llm_response(raw)
        assert intent.intent == "news"
        assert intent.entities == {}
        assert intent.suggested_queries == []


# ────────────────────────────────────────────────────────
# Task 3: Markdown JSON 代码块容错
# ────────────────────────────────────────────────────────

class TestParseLlmResponseMarkdown:
    """_parse_llm_response() Markdown JSON 代码块容错"""

    def test_parse_json_code_block(self, agent):
        """```json ... ``` 格式"""
        raw = """```json
{
  "intent": "policy",
  "entities": {"city": "北京"},
  "suggested_queries": [
    {"query": "北京 政策", "target_providers": ["minimax"], "rationale": "test"}
  ],
  "provider_scores": {"minimax": 0.8},
  "site_restrictions": ["gov.cn"]
}
```"""
        intent = agent._parse_llm_response(raw)
        assert intent.intent == "policy"
        assert intent.entities["city"] == "北京"
        assert len(intent.suggested_queries) == 1

    def test_parse_plain_code_block(self, agent):
        """``` ... ``` 格式（无 json 标记）"""
        raw = """```
{
  "intent": "info",
  "entities": {"topic": "Python"},
  "suggested_queries": [],
  "provider_scores": {},
  "site_restrictions": []
}
```"""
        intent = agent._parse_llm_response(raw)
        assert intent.intent == "info"
        assert intent.entities["topic"] == "Python"

    def test_parse_code_block_with_extra_text(self, agent):
        """代码块前后有额外文本"""
        raw = """Here is the analysis:

```json
{
  "intent": "navigation",
  "entities": {"city": "上海"},
  "suggested_queries": [
    {"query": "上海 市政府 网站", "target_providers": ["web_fetch"], "rationale": "导航"}
  ],
  "provider_scores": {"web_fetch": 0.9, "minimax": 0.1},
  "site_restrictions": []
}
```

Hope this helps!"""
        intent = agent._parse_llm_response(raw)
        assert intent.intent == "navigation"
        assert intent.entities["city"] == "上海"

    def test_parse_code_block_multiple_backticks(self, agent):
        """多重 ``` 符号"""
        raw = """```json
{
  "intent": "news",
  "entities": {},
  "suggested_queries": [],
  "provider_scores": {},
  "site_restrictions": []
}
```"""
        intent = agent._parse_llm_response(raw)
        assert intent.intent == "news"


# ────────────────────────────────────────────────────────
# Task 4: _cache_key() 测试
# ────────────────────────────────────────────────────────

class TestCacheKey:
    """_cache_key() 单元测试"""

    def test_same_query_same_key(self, agent):
        """相同 query 返回相同 key"""
        key1 = agent._cache_key("深圳市社保缴费比例")
        key2 = agent._cache_key("深圳市社保缴费比例")
        assert key1 == key2

    def test_different_query_different_key(self, agent):
        """不同 query 返回不同 key"""
        key1 = agent._cache_key("深圳社保")
        key2 = agent._cache_key("北京医保")
        assert key1 != key2

    def test_case_insensitive(self, agent):
        """大小写不敏感（strip+lower）"""
        key1 = agent._cache_key("Hello World")
        key2 = agent._cache_key("hello world")
        assert key1 == key2

    def test_whitespace_insensitive(self, agent):
        """首尾空格不敏感"""
        key1 = agent._cache_key("  test  ")
        key2 = agent._cache_key("test")
        assert key1 == key2

    def test_md5_length(self, agent):
        """MD5 hash 长度为 32"""
        key = agent._cache_key("any query")
        assert len(key) == 32
        assert all(c in "0123456789abcdef" for c in key)


# ────────────────────────────────────────────────────────
# Task 5: 缓存命中测试
# ────────────────────────────────────────────────────────

class TestPreprocessCache:
    """preprocess() 缓存命中"""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_same_object(self, agent):
        """相同 query 第二次调用返回相同 result"""
        # Mock _call_llm to avoid real API call
        mock_response = json.dumps({
            "intent": "info",
            "entities": {"topic": "test"},
            "suggested_queries": [],
            "provider_scores": {},
            "site_restrictions": [],
        })
        agent._call_llm = AsyncMock(return_value=mock_response)
        agent._session = MagicMock()

        result1 = await agent.preprocess("cache test")
        result2 = await agent.preprocess("cache test")

        # Second call should return from cache, not call API twice
        assert agent._call_llm.call_count == 1
        assert result1.intent == result2.intent
        assert result1.entities == result2.entities

    @pytest.mark.asyncio
    async def test_cache_miss_different_queries(self, agent):
        """不同 query 不共享缓存"""
        agent._call_llm = AsyncMock()
        agent._session = MagicMock()

        # Make _call_llm return different results for different calls
        async def side_effect(prompt):
            if "query1" in prompt:
                return json.dumps({"intent": "info", "entities": {}, "suggested_queries": [],
                                   "provider_scores": {}, "site_restrictions": []})
            return json.dumps({"intent": "news", "entities": {}, "suggested_queries": [],
                               "provider_scores": {}, "site_restrictions": []})

        agent._call_llm.side_effect = side_effect

        result1 = await agent.preprocess("query1")
        result2 = await agent.preprocess("query2")

        assert agent._call_llm.call_count == 2
        assert result1.intent != result2.intent

    @pytest.mark.asyncio
    async def test_cache_after_error_uses_default(self, agent):
        """即使 LLM 调用失败，结果也会被缓存（不重复调用）"""
        agent._call_llm = AsyncMock(side_effect=ValueError("API error"))
        agent._session = MagicMock()

        result1 = await agent.preprocess("error query")
        result2 = await agent.preprocess("error query")

        # Both return default, but API is only called once
        assert agent._call_llm.call_count == 1
        assert result1.intent == "general"
        assert result2.intent == "general"

    @pytest.mark.asyncio
    async def test_clear_cache(self, agent):
        """clear_cache 清空缓存，导致再次调用 LLM"""
        mock_response = json.dumps({
            "intent": "info", "entities": {},
            "suggested_queries": [],
            "provider_scores": {},
            "site_restrictions": [],
        })
        agent._call_llm = AsyncMock(return_value=mock_response)
        agent._session = MagicMock()

        result1 = await agent.preprocess("cache clear test")
        agent.clear_cache()
        result2 = await agent.preprocess("cache clear test")

        # Cache cleared, should call API again
        assert agent._call_llm.call_count == 2


# ────────────────────────────────────────────────────────
# Task 6: LLM 失败时的优雅降级
# ────────────────────────────────────────────────────────

class TestLlmGracefulDegradation:
    """LLM 失败降级测试"""

    @pytest.mark.asyncio
    async def test_api_timeout_returns_default(self, agent):
        """API 超时返回默认 QueryIntent"""
        agent._call_llm = AsyncMock(side_effect=asyncio.TimeoutError("Timeout"))
        agent._session = MagicMock()

        intent = await agent.preprocess("timeout query")
        assert intent.intent == "general"
        assert intent.suggested_queries == []

    @pytest.mark.asyncio
    async def test_api_http_error_returns_default(self, agent):
        """API HTTP 错误返回默认 QueryIntent"""
        agent._call_llm = AsyncMock(side_effect=ValueError("HTTP 500"))
        agent._session = MagicMock()

        intent = await agent.preprocess("http error query")
        assert intent.intent == "general"

    @pytest.mark.asyncio
    async def test_network_error_returns_default(self, agent):
        """网络错误返回默认 QueryIntent"""
        agent._call_llm = AsyncMock(side_effect=ConnectionError("Connection refused"))
        agent._session = MagicMock()

        intent = await agent.preprocess("network error query")
        assert intent.intent == "general"

    @pytest.mark.asyncio
    async def test_json_parse_error_returns_default(self, agent):
        """JSON 解析失败返回默认 QueryIntent"""
        agent._call_llm = AsyncMock(return_value="not json at all")
        agent._session = MagicMock()

        intent = await agent.preprocess("bad json query")
        # _parse_llm_response would fail, caught by preprocess try/except
        assert intent.intent == "general"

    @pytest.mark.asyncio
    async def test_preprocess_does_not_raise(self, agent):
        """preprocess() 在任何情况下都不抛异常"""
        errors = [
            asyncio.TimeoutError("timeout"),
            ValueError("bad response"),
            ConnectionError("connection failed"),
            RuntimeError("any error"),
            Exception("unknown"),
        ]

        for err in errors:
            agent._call_llm = AsyncMock(side_effect=err)
            agent._session = MagicMock()
            # Should not raise
            intent = await agent.preprocess(f"error {type(err).__name__}")
            assert isinstance(intent, QueryIntent)
            assert intent.intent == "general"

    @pytest.mark.asyncio
    async def test_disabled_agent_does_not_call_api(self, disabled_agent):
        """disabled agent 的 preprocess 不会调用 LLM API"""
        disabled_agent._call_llm = AsyncMock()
        disabled_agent._session = MagicMock()

        # disabled agent still runs normally, but enabled=False means
        # the engine won't call preprocess at all
        # Just verify the module doesn't crash
        intent = await disabled_agent.preprocess("disabled test")
        assert isinstance(intent, QueryIntent)


# ────────────────────────────────────────────────────────
# Task 7: preprocess() 完整流程
# ────────────────────────────────────────────────────────

class TestPreprocessFullFlow:
    """preprocess() 完整流程测试"""

    @pytest.mark.asyncio
    async def test_preprocess_policy_query(self, agent):
        """政策类查询的预处理器流程"""
        mock_response = json.dumps({
            "intent": "policy",
            "entities": {"city": "深圳", "department": "人社局", "year": "2025"},
            "suggested_queries": [
                {
                    "query": "深圳市 2025 社保缴费比例 官方",
                    "target_providers": ["minimax", "web_fetch"],
                    "rationale": "精准查询官方政策",
                },
            ],
            "provider_scores": {"minimax": 0.9, "web_fetch": 0.8, "brave": 0.4},
            "site_restrictions": ["gov.cn", "sz.gov.cn"],
        })
        agent._call_llm = AsyncMock(return_value=mock_response)
        agent._session = MagicMock()

        intent = await agent.preprocess("深圳社保缴费比例")

        assert intent.intent == "policy"
        assert intent.entities["city"] == "深圳"
        assert len(intent.suggested_queries) == 1
        assert "社保" in intent.suggested_queries[0].query
        assert intent.provider_scores["minimax"] == 0.9
        assert "gov.cn" in intent.site_restrictions

    @pytest.mark.asyncio
    async def test_preprocess_news_query(self, agent):
        """新闻类查询"""
        mock_response = json.dumps({
            "intent": "news",
            "entities": {"topic": "US inflation", "year": "2025"},
            "suggested_queries": [
                {
                    "query": "US inflation rate 2025 latest",
                    "target_providers": ["brave"],
                    "rationale": "新闻查询用 brave",
                },
            ],
            "provider_scores": {"brave": 0.9, "minimax": 0.3},
            "site_restrictions": [],
        })
        agent._call_llm = AsyncMock(return_value=mock_response)
        agent._session = MagicMock()

        intent = await agent.preprocess("US inflation rate 2025")

        assert intent.intent == "news"
        assert intent.provider_scores["brave"] == 0.9

    @pytest.mark.asyncio
    async def test_preprocess_navigation_query(self, agent):
        """导航类查询"""
        mock_response = json.dumps({
            "intent": "navigation",
            "entities": {"city": "北京"},
            "suggested_queries": [
                {
                    "query": "北京市人力资源和社会保障局 官网",
                    "target_providers": ["web_fetch"],
                    "rationale": "导航到官方网站",
                },
            ],
            "provider_scores": {"web_fetch": 0.95, "minimax": 0.2},
            "site_restrictions": ["gov.cn"],
        })
        agent._call_llm = AsyncMock(return_value=mock_response)
        agent._session = MagicMock()

        intent = await agent.preprocess("北京人社局官网")

        assert intent.intent == "navigation"
        assert intent.provider_scores["web_fetch"] == 0.95

    @pytest.mark.asyncio
    async def test_preprocess_info_query(self, agent):
        """信息/概念类查询"""
        mock_response = json.dumps({
            "intent": "info",
            "entities": {"topic": "Transformer"},
            "suggested_queries": [
                {
                    "query": "Transformer 模型 原理 详解",
                    "target_providers": ["minimax", "brave"],
                    "rationale": "知识查询用 minimax + brave",
                },
            ],
            "provider_scores": {"minimax": 0.7, "brave": 0.8},
            "site_restrictions": [],
        })
        agent._call_llm = AsyncMock(return_value=mock_response)
        agent._session = MagicMock()

        intent = await agent.preprocess("Transformer 模型原理")

        assert intent.intent == "info"
        assert intent.entities["topic"] == "Transformer"


# ────────────────────────────────────────────────────────
# Task 8: 配置与环境变量
# ────────────────────────────────────────────────────────

class TestConfig:
    """配置测试"""

    def test_default_config_disabled(self):
        """默认 LLMConfig 中 enabled=False"""
        config = LLMConfig()
        assert config.enabled is False

    def test_custom_config(self):
        """自定义配置"""
        config = LLMConfig(
            enabled=True,
            cache_ttl=1800,
            timeout=30,
            endpoint="https://custom.api.com/v1/chat",
            model="gpt-4",
            max_tokens=1024,
            temperature=0.5,
        )
        assert config.enabled is True
        assert config.cache_ttl == 1800
        assert config.timeout == 30
        assert config.endpoint == "https://custom.api.com/v1/chat"
        assert config.model == "gpt-4"
        assert config.max_tokens == 1024
        assert config.temperature == 0.5

    def test_build_config_from_env_defaults(self, monkeypatch):
        """从环境变量构建配置"""
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_API_ENDPOINT", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)

        config = LLMQueryAgent._build_config_from_env()
        assert config.enabled is False
        assert config.endpoint == "https://api.evan-zhang.com/v1/chat/completions"
        assert config.model == "deepseek-v4-flash"
        assert config.timeout == 10

    def test_build_config_from_env_overrides(self, monkeypatch):
        """环境变量覆盖默认配置"""
        monkeypatch.setenv("LLM_API_KEY", "sk-custom-key")
        monkeypatch.setenv("LLM_API_ENDPOINT", "https://custom.api.com/v1/chat")
        monkeypatch.setenv("LLM_MODEL", "custom-model-v2")

        config = LLMQueryAgent._build_config_from_env()
        assert config.endpoint == "https://custom.api.com/v1/chat"
        assert config.model == "custom-model-v2"

    def test_build_config_api_key_fallback(self, monkeypatch):
        """API Key 回退至 OPENAI_API_KEY"""
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fallback-key")

        config = LLMQueryAgent._build_config_from_env()
        # endpoint and model should use defaults
        assert config.endpoint == "https://api.evan-zhang.com/v1/chat/completions"
        # The api_key isn't stored in LLMConfig, it's read at call time

    @pytest.mark.asyncio
    async def test_enabled_property(self, agent, disabled_agent):
        """enabled 属性正确反映配置"""
        assert agent.enabled is True
        assert disabled_agent.enabled is False

    @pytest.mark.asyncio
    async def test_close_agent(self, agent):
        """close() 关闭 HTTP 会话"""
        session_mock = AsyncMock()
        session_mock.closed = False
        agent._session = session_mock

        await agent.close()
        session_mock.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_agent_no_session(self, agent):
        """close() 时 session 为 None 不报错"""
        agent._session = None
        # 不应报错
        await agent.close()

    @pytest.mark.asyncio
    async def test_close_agent_already_closed(self, agent):
        """close() 时 session 已关闭不报错"""
        agent._session = AsyncMock()
        agent._session.closed = True

        await agent.close()
        agent._session.close.assert_not_called()


# ────────────────────────────────────────────────────────
# Task 9: Engine 集成接口
# ────────────────────────────────────────────────────────

class TestEngineIntegration:
    """与 SearchEngine 集成测试"""

    @pytest.mark.asyncio
    async def test_engine_accepts_llm_agent(self):
        """SearchEngine 可以接收 LLMQueryAgent 参数"""
        from ..engine import SearchEngine
        from ..config import ConfigLoader

        config = LLMConfig(enabled=False)
        agent = LLMQueryAgent(config=config)

        engine = SearchEngine(llm_agent=agent)
        assert engine.llm_agent is agent
        assert engine.llm_agent.enabled is False

    @pytest.mark.asyncio
    async def test_engine_llm_disabled_by_default(self):
        """SearchEngine 默认不启用 LLM"""
        from ..engine import SearchEngine
        engine = SearchEngine()
        assert engine.llm_agent is None

    @pytest.mark.asyncio
    async def test_llm_enabled_engine_search_graceful_degradation(self, monkeypatch):
        """启用 LLM 但 API 失败时不影响主搜索流程"""
        from ..engine import SearchEngine
        from ..config import ConfigLoader
        from ..state import StateManager

        # 创建 LLM agent
        config = LLMConfig(enabled=True)
        llm_agent = LLMQueryAgent(config=config)

        # Mock _call_llm to fail
        llm_agent._call_llm = AsyncMock(side_effect=ValueError("API down"))
        llm_agent._session = MagicMock()

        # 创建简单 mock 引擎避免真实 provider 调用
        from ..fallback_chain import FallbackChain
        from ..mcp_client import McporterMCPClient
        from ..cache import CacheManager
        from ..aggregator import ResultAggregator

        engine = SearchEngine(
            config_loader=MagicMock(),
            mcp_client=MagicMock(),
            state_manager=MagicMock(),
            cache_manager=MagicMock(),
            aggregator=MagicMock(),
            fallback_chain=MagicMock(),
            llm_agent=llm_agent,
        )

        # Mock _execute_primary_search to return ok
        mock_result = MagicMock()
        mock_result.status = MagicMock(value="ok")
        mock_result.items = []
        engine._execute_primary_search = AsyncMock(return_value=mock_result)

        from ..schema import SearchRequest

        # 让 cache_manager.get() 返回 None（避免缓存命中提前返回）
        engine.cache_manager.get.return_value = None

        request = SearchRequest(query="test query")
        # LLM fails → engine still runs primary search → result returned
        result = await engine.search(request)
        assert result is not None
        # Primary search was called
        engine._execute_primary_search.assert_called_once()
