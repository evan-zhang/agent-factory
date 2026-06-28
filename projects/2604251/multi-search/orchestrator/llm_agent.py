"""
orchestrator/llm_agent.py

LLM Query Agent — 智能查询理解与改写模块。

核心职责：
  接收原始搜索 query，通过 LLM 理解意图并生成多版本优化查询。

Architecture:
  SearchRequest → LLMQueryAgent.preprocess() → EnhancedQueryIntent
    ↓ 成功                      ↓ 失败 (降级)
  engine 使用增强查询            engine 使用原始查询（不影响主流程）

Phase 2 R1 引入。
"""

import asyncio
import hashlib
import json
import logging
import os
from typing import Dict, List, Optional, Any

import aiohttp

from .schema import SuggestedQuery, QueryIntent, LLMConfig

logger = logging.getLogger("orchestrator.llm_agent")

# ────────────────────────────────────────────────────────
# LLM Prompt 模板
# ────────────────────────────────────────────────────────

LLM_SYSTEM_PROMPT = """你是一个搜索查询分析师。分析用户的搜索查询，输出 JSON。

输入：{query}

输出 JSON 格式：
{{
  "intent": "policy|info|news|navigation|general",
  "entities": {{"city": "", "department": "", "year": "", "topic": ""}},
  "suggested_queries": [
    {{"query": "...", "target_providers": [...], "rationale": "..."}},
    {{"query": "...", "target_providers": [...], "rationale": "..."}},
    {{"query": "...", "target_providers": [...], "rationale": "..."}}
  ],
  "provider_scores": {{"minimax": 0.0-1.0, "brave": 0.0-1.0, "tavily": 0.0-1.0, "web_fetch": 0.0-1.0}},
  "site_restrictions": ["domain1", "domain2"]
}}

规则：
- intent: policy=政策法规, info=概念/知识, news=新闻/动态, navigation=导航/网站
- suggested_queries: 生成 2-3 条不同角度的优化查询（精准、泛搜、兜底）
- provider_scores: 哪个 provider 最适合这个查询（0-1）
- site_restrictions: 如果搜索政策类，建议 site:gov.cn 等
- 中文查询保持中文优化，英文查询保持英文"""


class LLMQueryAgent:
    """
    LLM 查询理解代理。

    可选组件：失败自动降级，不影响现有搜索流程。

    Architecture:
      SearchRequest → LLMQueryAgent.preprocess() → EnhancedQueryIntent
        ↓ 成功                      ↓ 失败
      engine 使用增强查询            engine 使用原始查询

    默认 disabled，需用户显式启用。
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        初始化 LLM Query Agent。

        Args:
            config: LLM 配置。如果为 None，从环境变量 + 默认值自动构建。
        """
        self.config = config or self._build_config_from_env()
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, QueryIntent] = {}

        logger.debug(
            f"LLMQueryAgent 初始化完成 "
            f"enabled={self.config.enabled} "
            f"model={self.config.model} "
            f"endpoint={self.config.endpoint}"
        )

    @staticmethod
    def _build_config_from_env() -> LLMConfig:
        """从环境变量构建 LLMConfig。"""
        api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        endpoint = (
            os.environ.get("LLM_API_ENDPOINT")
            or "https://api.evan-zhang.com/v1/chat/completions"
        )
        model = os.environ.get("LLM_MODEL") or "deepseek-v4-flash"

        return LLMConfig(
            enabled=False,  # 默认关闭
            cache_ttl=3600,
            timeout=10,
            endpoint=endpoint,
            model=model,
            max_tokens=512,
            temperature=0.3,
        )

    # ────────────────────────────────────────────────────
    # 公开接口
    # ────────────────────────────────────────────────────

    async def preprocess(self, query: str) -> QueryIntent:
        """
        对 query 做 LLM 意图理解，返回优化查询方案。

        缓存：相同 query 在 cache_ttl 内命中缓存。
        降级：LLM 调用失败时返回默认 QueryIntent（intent="general"）。

        Args:
            query: 用户原始搜索查询。

        Returns:
            QueryIntent 对象，包含意图分析和优化查询建议。
        """
        cache_key = self._cache_key(query)

        # 1. 检查缓存
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug(f"LLM 缓存命中 query='{query[:60]}'")
            return cached

        # 2. 调用 LLM API
        try:
            prompt = self._build_prompt(query)
            raw_response = await self._call_llm(prompt)
            intent = self._parse_llm_response(raw_response)
        except Exception as e:
            logger.warning(
                f"LLM Query Agent 调用失败 query='{query[:60]}' error={e}"
            )
            intent = self._default_intent()

        # 3. 缓存结果（即使失败也缓存默认意图，避免重复调用）
        self._cache[cache_key] = intent

        logger.debug(f"LLM preprocess 完成 intent={intent.intent} query='{query[:60]}'")
        return intent

    def clear_cache(self) -> None:
        """清空 LLM 查询缓存。"""
        self._cache.clear()
        logger.debug("LLM 缓存已清空")

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    # ────────────────────────────────────────────────────
    # LLM 调用
    # ────────────────────────────────────────────────────

    async def _call_llm(self, prompt: str) -> str:
        """
        调用 OpenAI 兼容 API。

        API 地址、model name、API key 从 config / 环境变量读取。

        Returns:
            LLM 返回的原始文本（markdown JSON 代码块或裸 JSON）。

        Raises:
            asyncio.TimeoutError: API 超时
            aiohttp.ClientError: 网络错误
            ValueError: 返回格式异常
        """
        api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("LLM_API_KEY 或 OPENAI_API_KEY 未设置")

        # 延迟初始化 HTTP session
        if self._session is None:
            self._session = aiohttp.ClientSession()

        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with self._session.post(
            self.config.endpoint,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise ValueError(
                    f"LLM API 返回 {response.status}: {error_text[:200]}"
                )

            data = await response.json()

        # 提取 message content
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("LLM API 返回空 choices")

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise ValueError("LLM API 返回空 content")

        return content

    # ────────────────────────────────────────────────────
    # Prompt 构建
    # ────────────────────────────────────────────────────

    def _build_prompt(self, query: str) -> str:
        """
        构造 LLM 提示词。

        Args:
            query: 用户原始搜索查询。

        Returns:
            完整的 prompt 字符串。
        """
        return LLM_SYSTEM_PROMPT.format(query=query)

    # ────────────────────────────────────────────────────
    # 响应解析
    # ────────────────────────────────────────────────────

    def _parse_llm_response(self, raw: str) -> QueryIntent:
        """
        解析 LLM JSON 响应为 QueryIntent。

        兼容输入格式：
        - 裸 JSON: {"intent": "policy", ...}
        - Markdown JSON 代码块: ```json {"intent": "policy", ...} ```
        - Markdown 代码块: ``` {"intent": "policy", ...} ```
        - 代码块前后有额外文本

        Args:
            raw: LLM 返回的原始文本。

        Returns:
            QueryIntent 对象。

        Raises:
            json.JSONDecodeError: JSON 解析失败。
        """
        cleaned = raw.strip()

        # 处理 markdown 代码块（无论是开头还是中间出现）
        # 查找 ``` 代码块标记
        if "```" in cleaned:
            lines = cleaned.splitlines()
            # 找到第一个 ``` 开头的行
            start = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    start = i + 1
                    break
            # 找到 ``` 结束标记（从后往前找）
            end = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == "```":
                    end = i
                    break
            cleaned = "\n".join(lines[start:end]).strip()

        # 解析 JSON
        data = json.loads(cleaned)

        # 构建 QueryIntent
        intent_str = data.get("intent", "general")
        if intent_str not in ("policy", "info", "news", "navigation", "general"):
            intent_str = "general"

        entities = data.get("entities", {})

        # 解析 suggested_queries
        suggested_queries_raw = data.get("suggested_queries", [])
        suggested_queries = []
        for sq in suggested_queries_raw:
            if isinstance(sq, dict):
                suggested_queries.append(
                    SuggestedQuery(
                        query=sq.get("query", ""),
                        target_providers=sq.get("target_providers", []),
                        rationale=sq.get("rationale", ""),
                    )
                )

        # 解析 provider_scores
        provider_scores = data.get("provider_scores", {})

        # 解析 site_restrictions
        site_restrictions = data.get("site_restrictions", [])

        return QueryIntent(
            intent=intent_str,
            entities=entities,
            suggested_queries=suggested_queries,
            provider_scores=provider_scores,
            site_restrictions=site_restrictions,
        )

    # ────────────────────────────────────────────────────
    # 缓存
    # ────────────────────────────────────────────────────

    def _cache_key(self, query: str) -> str:
        """
        缓存键（normalized query 的 hash）。

        Args:
            query: 搜索查询。

        Returns:
            MD5 hash 字符串。
        """
        normalized = query.strip().lower()
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def _default_intent(self) -> QueryIntent:
        """
        降级时使用的默认 QueryIntent。
        """
        return QueryIntent(
            intent="general",
            entities={},
            suggested_queries=[],
            provider_scores={},
            site_restrictions=[],
        )

    # ────────────────────────────────────────────────────
    # 资源管理
    # ────────────────────────────────────────────────────

    async def close(self) -> None:
        """关闭 HTTP 会话。"""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None
        logger.debug("LLMQueryAgent 已关闭")


__all__ = ["LLMQueryAgent", "LLM_SYSTEM_PROMPT"]
