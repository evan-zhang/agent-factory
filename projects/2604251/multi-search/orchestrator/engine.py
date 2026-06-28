"""
orchestrator/engine.py

执行引擎模块。

本模块负责：
- 并行/串行调度多个 provider
- 三轮递进检索策略管理
- query_template 处理（精准轮加引号，泛搜/兜底轮原样）
- asyncio.ALL_COMPLETED 并发控制

变更记录：
- Phase 1: 增加重试逻辑 (_execute_with_retry)、结构化日志、性能监控
"""

import asyncio
import json
import time
import logging
from typing import Optional, List, Dict, Any

import aiohttp

from .schema import (
    OrchestratorSearchResult,
    SearchRequest,
    SearchItem,
    ProviderConfig,
    IntentModeConfig,
    RoundConfig,
    RoundTermination,
    QueryStrategy,
    ResultStatus,
    ProviderType,
    # 异常类
    SearchError,
    RetryableError,
    NonRetryableError,
    ProviderUnavailableError,
    QuotaExhaustedError,
    SearchTimeoutError,
)
from .config import ConfigLoader
from .mcp_client import McporterMCPClient
from .state import StateManager
from .cache import CacheManager
from .aggregator import ResultAggregator
from .fallback_chain import FallbackChain
from .scorer import ResultScorer
from .llm_agent import LLMQueryAgent
from .schema import (  # Phase 2 R1: LLM Query Agent
    SuggestedQuery,
    QueryIntent,
    LLMConfig,
)
from .router import AdaptiveRouter
from .schema import (  # Phase 2 R3: Adaptive Router
    RouterConfig,
    ProviderPerformance,
    RoutingDecision,
)

logger = logging.getLogger("orchestrator.engine")


# ────────────────────────────────────────────────────────
# 性能监控数据（B1 — 进程级内存 dict）
# ────────────────────────────────────────────────────────

_perf_data: Dict[str, Any] = {
    "providers": {},
    "cache": {"hits": 0, "misses": 0, "size": 0},
    "quota": {},
}


def _update_provider_stats(
    name: str,
    success: bool,
    latency_ms: float,
    cache_hit: bool = False,
):
    """更新 provider 性能统计数据"""
    providers = _perf_data.setdefault("providers", {})
    stats = providers.setdefault(name, {
        "calls": 0, "success": 0, "fail": 0,
        "avg_latency_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0,
        "cache_hits": 0,
    })
    stats["calls"] += 1
    if success:
        stats["success"] += 1
        if cache_hit:
            stats["cache_hits"] += 1
    else:
        stats["fail"] += 1

    # 延迟统计
    if stats["min_ms"] == 0 or latency_ms < stats["min_ms"]:
        stats["min_ms"] = latency_ms
    if latency_ms > stats["max_ms"]:
        stats["max_ms"] = latency_ms
    # 滚动平均
    total = stats["avg_latency_ms"] * (stats["success"] - 1) + latency_ms
    stats["avg_latency_ms"] = total / stats["success"] if stats["success"] > 0 else 0.0


def _update_quota_stats(name: str, remaining: int, reset_in: float):
    """更新配额统计数据"""
    quota = _perf_data.setdefault("quota", {})
    quota[name] = {"remaining": remaining, "reset_in": reset_in}


# ────────────────────────────────────────────────────────
# 工具函数
# ────────────────────────────────────────────────────────

def apply_query_template(template: str, original_query: str) -> str:
    """
    将 query_template 中的 {query} 占位符替换为实际搜索词。

    BATTLE-R4-FIXES.md Fix 2 — 模板占位符方案。

    示例：
      template = '"{query}"', query = "社保缴费比例"
      → 结果: '"社保缴费比例"'

      template = '{query}', query = "社保缴费比例"
      → 结果: "社保缴费比例"

    Args:
        template: query_template 字符串，包含 {query} 占位符
        original_query: 用户原始搜索词

    Returns:
        替换后的 query 字符串
    """
    return template.replace("{query}", original_query)


class SearchEngine:
    """
    搜索执行引擎

    核心职责：
    1. 调度多个 provider 执行搜索（并行或串行）
    2. 管理三轮递进检索策略
    3. 处理 query_template（精准轮使用 "{query}"，泛搜/兜底轮使用 {query}）
    4. 完整 fallback 触发条件（BATTLE-R4-FIXES.md Fix 3）
    5. 重试逻辑（_execute_with_retry）
    6. 性能监控（_perf_data）
    7. LLM Query Agent 集成（Phase 2 R1，可选组件，默认关闭）
    """

    def __init__(
        self,
        config_loader: Optional[ConfigLoader] = None,
        mcp_client: Optional[McporterMCPClient] = None,
        state_manager: Optional[StateManager] = None,
        cache_manager: Optional[CacheManager] = None,
        aggregator: Optional[ResultAggregator] = None,
        fallback_chain: Optional[FallbackChain] = None,
        llm_agent: Optional[LLMQueryAgent] = None,
        scorer: Optional[ResultScorer] = None,
    ):
        """
        初始化搜索引擎

        Args:
            config_loader: 配置加载器（如果为 None 则创建新实例）
            mcp_client: MCP 客户端（如果为 None 则创建新实例）
            state_manager: 状态管理器（如果为 None 则创建新实例）
            cache_manager: 缓存管理器（如果为 None 则创建新实例）
            aggregator: 结果聚合器（如果为 None 则创建新实例）
            fallback_chain: Fallback 链（如果为 None 则创建新实例）
            llm_agent: LLM Query Agent（可选，默认关闭 None = 不启用）
            scorer: 结果质量评分器（可选，默认从配置加载器获取配置后创建）
        """
        # 初始化组件
        self.config_loader = config_loader or ConfigLoader()
        self.config_loader.load_all()

        self.mcp_client = mcp_client or McporterMCPClient()
        self.state_manager = state_manager or StateManager()
        self.cache_manager = cache_manager or CacheManager()
        self.aggregator = aggregator or ResultAggregator()
        self.fallback_chain = fallback_chain or FallbackChain(
            self.config_loader.get_fallback_config()
        )

        # Phase 2 R1: LLM Query Agent（可选，默认 None = 不启用）
        self.llm_agent = llm_agent

        # Phase 2 R2: Result Quality Scorer（总是启用）
        if scorer is not None:
            self.scorer = scorer
        else:
            scorer_config = self.config_loader.get_scorer_config()
            self.scorer = ResultScorer(scorer_config)

        # Phase 2 R3: Adaptive Provider Router（可选，默认关闭）
        router_config = self.config_loader.get_router_config()
        self.router = AdaptiveRouter(router_config)

        # HTTP 会话（首次使用时创建）
        self._http_session: Optional[aiohttp.ClientSession] = None
        # 重试配置
        self._max_retries = 3
        self._retry_backoff_base = 1.0

        llm_status = f"llm_agent={'enabled' if llm_agent and llm_agent.enabled else 'disabled'}"
        logger.debug(f"SearchEngine 初始化完成 {llm_status} scorer=always_enabled")

    async def search(
        self,
        request: SearchRequest,
        parallel: bool = True,
        max_providers: int = 3,
    ) -> OrchestratorSearchResult:
        """
        执行搜索（完整生命周期）。

        BATTLE-R4-FIXES.md Fix 3 — 完整执行流程：
        1. 先按 intent 策略执行（含三轮递进）
        2. 如果结果 status 为 ok/partial → 直接返回
        3. 如果结果 status 为 all_failed/error/no_match → 触发 Fallback 链
        4. Fallback 链跳过已经在三轮递进中调用过的 provider
        5. Fallback 链串行尝试剩余 provider，任意成功即返回

        Args:
            request: 搜索请求
            parallel: 是否并行执行（默认 True）
            max_providers: 最大 provider 数量（默认 3）

        Returns:
            搜索结果
        """
        # A5 — 生成请求追踪 ID，通过 request.request_id 传递
        import hashlib
        raw_ts = str(time.time_ns())
        request_id = hashlib.md5(raw_ts.encode()).hexdigest()[:12]
        request.request_id = request_id
        _req_str = f"req={request_id}"

        logger.info(f"开始搜索 query={request.query} parallel={parallel} {_req_str}")

        start_time = time.time()

        # 检查缓存
        cached_result = self.cache_manager.get(request)
        if cached_result:
            logger.info(f"使用缓存结果 {_req_str}")
            return cached_result

        # 获取意图模式配置
        intent_mode = self._get_intent_mode(request)

        # ────────────────────────────────────────────────────────
        # Step 0: LLM Query Agent（Phase 2 R1，可选）
        # ────────────────────────────────────────────────────────
        if self.llm_agent and self.llm_agent.enabled:
            try:
                intent = await self.llm_agent.preprocess(request.query)
                logger.info(
                    f"LLM 查询分析完成 intent={intent.intent} "
                    f"suggestions={len(intent.suggested_queries)} {_req_str}"
                )

                # 使用 LLM 的 provider_scores 更新 intent 模式（如果未配置首选 provider）
                if intent.provider_scores and (
                    intent_mode is None
                    or not intent_mode.preferred_providers
                ):
                    logger.info(
                        f"LLM 更新 provider 选择 scores={intent.provider_scores} {_req_str}"
                    )

                # 应用 site_restrictions
                if intent.site_restrictions and not request.include_domains:
                    request.include_domains = intent.site_restrictions
                    logger.info(
                        f"LLM 应用 site 限制 restrictions={intent.site_restrictions} {_req_str}"
                    )

                # 使用 LLM 改写后的第一个建议查询替换原始 query
                # （仅在 LLM 明确建议改写时使用）
                if intent.suggested_queries:
                    primary_suggestion = intent.suggested_queries[0]
                    # 仅当改写后的查询与原始查询不同时才替换
                    if primary_suggestion.query and primary_suggestion.query != request.query:
                        original_query = request.query
                        request.query = primary_suggestion.query
                        logger.info(
                            f"LLM 改写查询 '{original_query}' → "
                            f"'{request.query}' {_req_str}"
                        )

            except Exception as e:
                logger.warning(
                    f"LLM Query Agent 失败 query={request.query[:80]} "
                    f"error={e} {_req_str}"
                )
                # 降级到默认流程，不中断搜索

        # Step 1: 执行主要搜索策略
        primary_result = await self._execute_primary_search(
            request, intent_mode, parallel, max_providers,
        )

        # Step 2: 检查是否已有可用结果（Fix 3 — 状态检查）
        if primary_result.status in (ResultStatus.OK, ResultStatus.PARTIAL):
            # 已有可用结果，更新元数据后返回
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"主要搜索完成 status={primary_result.status.value} "
                f"items={len(primary_result.items)} {_req_str}"
            )
            primary_result.response_time = time.time() - start_time
            primary_result.original_query = request.query

            # 缓存结果
            cache_ttl = intent_mode.cache_ttl if intent_mode else 3600
            self.cache_manager.set(request, primary_result, cache_ttl)

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"搜索完成 status={primary_result.status.value} "
                f"items={len(primary_result.items)} "
                f"duration_ms={elapsed_ms:.0f} {_req_str}"
            )
            return primary_result

        # 如果启用了 fallback，触发 Fallback 链（Fix 3）
        should_fallback = (
            intent_mode is None or intent_mode.enable_fallback
        )

        if not should_fallback:
            # Fallback 已禁用，直接返回
            primary_result.response_time = time.time() - start_time
            primary_result.original_query = request.query
            return primary_result

        # Step 3: 触发 Fallback 链
        # Fallback 链跳过已经在主要搜索中调用过的 provider
        engines_tried = primary_result.metadata.get("engines_tried", [])
        all_providers = self.config_loader.list_providers(enabled_only=True)
        fallback_providers = [
            p for p in all_providers
            if p.name not in engines_tried
        ]

        if not fallback_providers:
            logger.warning(
                f"Fallback 跳过: 所有 provider 已在主要搜索中尝试过 "
                f"engines_tried={engines_tried} {_req_str}"
            )
            primary_result.response_time = time.time() - start_time
            primary_result.original_query = request.query
            primary_result.status = ResultStatus.ALL_FAILED
            primary_result.error = (
                f"所有 provider 已尝试过，无可用的 fallback provider. "
                f"engines_tried={engines_tried}"
            )
            return primary_result

        logger.info(
            f"触发 Fallback 跳过已调用 {engines_tried} "
            f"剩余 {[p.name for p in fallback_providers]} {_req_str}"
        )

        # Step 4: 串行执行 Fallback 链
        fallback_result = await self.fallback_chain.execute(
            fallback_providers,
            self._execute_single_provider,
            request,
        )

        # 合并 metadata
        fallback_result.metadata["engines_tried"] = (
            engines_tried + fallback_result.metadata.get("engines_tried", [])
        )
        fallback_result.metadata["primary_status"] = primary_result.status.value

        # 确定最终结果
        if fallback_result.status in (ResultStatus.OK, ResultStatus.PARTIAL):
            final_result = fallback_result
        else:
            # Fallback 也失败了，返回主要搜索的结果（保留错误信息）
            primary_result.status = ResultStatus.ALL_FAILED
            primary_result.error = (
                f"主要搜索 + Fallback 均失败. "
                f"主要: {primary_result.status.value}, "
                f"Fallback: {fallback_result.status.value}, "
                f"engines_tried={engines_tried + [p.name for p in fallback_providers]}"
            )
            final_result = primary_result

        # Phase 2 R2: 结果质量评分排序（总是启用）
        if final_result.items:
            final_result.items = self.scorer.score_and_sort(
                final_result.items, final_result.query
            )

        # 更新响应时间
        final_result.response_time = time.time() - start_time
        final_result.original_query = request.query

        # 缓存结果
        cache_ttl = intent_mode.cache_ttl if intent_mode else 3600
        self.cache_manager.set(request, final_result, cache_ttl)

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"搜索完成 status={final_result.status.value} "
            f"items={len(final_result.items)} "
            f"duration_ms={elapsed_ms:.0f} {_req_str}"
        )

        return final_result

    async def _execute_primary_search(
        self,
        request: SearchRequest,
        intent_mode: Optional[IntentModeConfig],
        parallel: bool = True,
        max_providers: int = 3,
    ) -> OrchestratorSearchResult:
        """
        执行主要搜索策略。

        如果 intent 配置了三轮递进（query_strategy_config.rounds），
        则执行 _search_multi_round()。
        否则执行原有的并行/串行搜索。

        Returns:
            搜索结果（可能为 ok/partial/all_failed/error/no_match）
        """
        _req_str = f"req={request.request_id}" if request.request_id else ""

        # 检查是否有三轮递进配置
        if intent_mode and intent_mode.strategy_rounds and intent_mode.strategy_rounds.enabled:
            logger.info(f"执行三轮递进检索 intent={intent_mode.intent} {_req_str}")
            return await self._search_multi_round(
                request, intent_mode, max_providers,
            )

        # 无三轮递进，使用原有的并行/串行逻辑
        providers = self._get_providers(intent_mode, max_providers)

        if not providers:
            return OrchestratorSearchResult(
                version="1.0.0",
                status=ResultStatus.ALL_FAILED,
                error="没有可用的 provider",
                provider="none",
                query=request.query,
                items=[],
                metadata={"engines_tried": [], "engines_succeeded": [], "engines_failed": []},
            )

        if parallel:
            results = await self._search_parallel(providers, request)

            # 聚合结果
            if len(results) > 1:
                aggregated = self.aggregator.aggregate(results, request.query)
            else:
                aggregated = results[0]

            # 记录引擎轨迹
            engines_tried = [r.provider for r in results]
            engines_succeeded = [
                r.provider for r in results
                if r.status in (ResultStatus.OK, ResultStatus.PARTIAL) and len(r.items) > 0
            ]
            engines_failed = [
                {"engine": r.provider, "reason": r.status.value}
                for r in results
                if r.status not in (ResultStatus.OK, ResultStatus.PARTIAL) or len(r.items) == 0
            ]

            aggregated.metadata["engines_tried"] = engines_tried
            aggregated.metadata["engines_succeeded"] = engines_succeeded
            aggregated.metadata["engines_failed"] = engines_failed

            # Phase 2 R2: 结果质量评分排序（总是启用）
            if aggregated.items:
                aggregated.items = self.scorer.score_and_sort(
                    aggregated.items, aggregated.query
                )

            return aggregated
        else:
            # 串行执行（使用 fallback 链）
            result = await self.fallback_chain.execute(
                providers,
                self._execute_single_provider,
                request,
            )

            engines_tried = []
            engines_succeeded = []
            engines_failed = []
            for p in providers:
                engines_tried.append(p.name)
                if result.status in (ResultStatus.OK, ResultStatus.PARTIAL) and result.provider == p.name:
                    engines_succeeded.append(p.name)
                else:
                    engines_failed.append({"engine": p.name, "reason": result.status.value})

            result.metadata["engines_tried"] = engines_tried
            result.metadata["engines_succeeded"] = engines_succeeded
            result.metadata["engines_failed"] = engines_failed

            # Phase 2 R2: 结果质量评分排序（总是启用）
            if result.items:
                result.items = self.scorer.score_and_sort(
                    result.items, result.query
                )

            return result

    async def _search_multi_round(
        self,
        request: SearchRequest,
        intent_mode: IntentModeConfig,
        max_providers: int,
    ) -> OrchestratorSearchResult:
        """
        执行三轮递进检索（BATTLE-R4-FIXES.md Fix 2）。

        流程：
        1. 使用 query_template 改写每轮的 query
        2. 按精准→泛搜→兜底顺序执行
        3. 每轮结果达到 min_results 后提前终止
        4. 三轮结果去重后返回

        Args:
            request: 搜索请求
            intent_mode: 意图模式配置（含 strategy_rounds）
            max_providers: 最大 provider 数量

        Returns:
            聚合后的搜索结果
        """
        _req_str = f"req={request.request_id}" if request.request_id else ""
        strategy = intent_mode.strategy_rounds
        if not strategy or not strategy.rounds:
            # 没有三轮递进配置，降级到并行搜索
            providers = self._get_providers(intent_mode, max_providers)
            results = await self._search_parallel(providers, request)
            aggregated = self.aggregator.aggregate(results, request.query)

            # Phase 2 R2: 结果质量评分排序（总是启用）
            if aggregated.items:
                aggregated.items = self.scorer.score_and_sort(
                    aggregated.items, aggregated.query
                )

            return aggregated

        rounds = strategy.rounds
        termination = strategy.round_termination

        logger.info(
            f"三轮递进检索启动 rounds={[r.mode for r in rounds]} "
            f"min_results={termination.min_results if termination else 'N/A'} {_req_str}"
        )

        all_items: List[SearchItem] = []
        engines_tried: List[str] = []
        engines_succeeded: List[str] = []
        engines_failed: List[Dict[str, str]] = []
        completed_rounds = 0

        for round_idx, round_conf in enumerate(rounds):
            # Step 1: 改写 query
            round_query = apply_query_template(round_conf.query_template, request.query)
            logger.info(
                f"Round {round_idx + 1} ({round_conf.mode}) "
                f"query='{round_query}' "
                f"template='{round_conf.query_template}' {_req_str}"
            )

            # Step 2: 筛选本轮 provider
            if round_conf.provider_filter:
                round_providers = [
                    self.config_loader.get_provider(p_name)
                    for p_name in round_conf.provider_filter
                ]
                round_providers = [
                    p for p in round_providers
                    if p and p.enabled
                ]
            else:
                round_providers = self._get_providers(intent_mode, max_providers)

            if not round_providers:
                logger.warning(f"Round {round_idx + 1}: 没有可用的 provider {_req_str}")
                continue

            # Step 3: 创建本轮 request
            round_request = SearchRequest(
                query=round_query,
                intent=request.intent,
                num_results=round_conf.count,
                offset=request.offset,
            )

            # Step 4: 执行并行搜索
            try:
                round_results = await asyncio.wait_for(
                    self._search_parallel(round_providers, round_request),
                    timeout=round_conf.timeout_ms / 1000,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Round {round_idx + 1} 超时 ({round_conf.timeout_ms}ms) {_req_str}"
                )
                round_results = [
                    OrchestratorSearchResult(
                        version="1.0.0",
                        status=ResultStatus.TIMEOUT,
                        error=f"Round {round_idx + 1} 超时",
                        provider="unknown",
                        query=round_query,
                        items=[],
                        metadata={},
                    )
                ]

            # Step 5: 记录引擎轨迹
            for r in round_results:
                if r.provider not in engines_tried:
                    engines_tried.append(r.provider)
                if r.status in (ResultStatus.OK, ResultStatus.PARTIAL) and len(r.items) > 0:
                    if r.provider not in engines_succeeded:
                        engines_succeeded.append(r.provider)
                else:
                    if not any(
                        ef["engine"] == r.provider for ef in engines_failed
                    ):
                        engines_failed.append({
                            "engine": r.provider,
                            "reason": r.status.value,
                        })

            # Step 6: 聚合本轮结果
            round_items_count = 0
            for r in round_results:
                all_items.extend(r.items)
                round_items_count += len(r.items)

            completed_rounds = round_idx + 1

            # Step 7: 检查提前终止条件
            if termination and termination.min_results > 0:
                unique_urls = set()
                for item in all_items:
                    unique_urls.add(item.url)
                unique_count = len(unique_urls)

                logger.info(
                    f"Round {round_idx + 1} 完成 "
                    f"本轮 {round_items_count} 条 "
                    f"累计去重 {unique_count} 条 {_req_str}"
                )

                if unique_count >= termination.min_results:
                    logger.info(
                        f"提前终止 {unique_count} >= {termination.min_results} "
                        f"跳过 rounds {round_idx + 2}-{len(rounds)} {_req_str}"
                    )
                    break
            else:
                logger.info(
                    f"Round {round_idx + 1} 完成 "
                    f"本轮 {round_items_count} 条 {_req_str}"
                )

        # Step 8: 去重
        unique_urls = set()
        deduplicated_items = []
        for item in all_items:
            if item.url not in unique_urls:
                unique_urls.add(item.url)
                deduplicated_items.append(item)

        # Step 9: 确定状态
        if deduplicated_items:
            if len(deduplicated_items) >= request.num_results:
                status = ResultStatus.OK
            else:
                status = ResultStatus.PARTIAL
        else:
            status = ResultStatus.NO_MATCH

        logger.info(
            f"三轮递进结束 rounds={completed_rounds}/{len(rounds)} "
            f"去重后 {len(deduplicated_items)} 条 "
            f"status={status.value} "
            f"engines_tried={engines_tried} {_req_str}"
        )

        # 构建结果
        metadata = {
            "strategy": "multi_round",
            "rounds_completed": completed_rounds,
            "total_rounds": len(rounds),
            "engines_tried": engines_tried,
            "engines_succeeded": engines_succeeded,
            "engines_failed": engines_failed,
            "round_termination_triggered": (
                termination is not None
                and completed_rounds < len(rounds)
            ),
        }

        # Phase 2 R2: 结果质量评分排序（总是启用）
        if deduplicated_items:
            scorer = self.scorer
            deduplicated_items = scorer.score_and_sort(
                deduplicated_items, request.query
            )

        return OrchestratorSearchResult(
            version="1.0.0",
            status=status,
            query=request.query,
            provider="multi_round",
            items=deduplicated_items,
            metadata=metadata,
        )

    def _get_intent_mode(self, request: SearchRequest) -> Optional[IntentModeConfig]:
        """
        获取意图模式配置

        Args:
            request: 搜索请求

        Returns:
            IntentModeConfig 对象，如果不存在返回 None
        """
        if not request.intent:
            return None

        return self.config_loader.get_intent_mode(request.intent)

    def _get_providers(
        self,
        intent_mode: Optional[IntentModeConfig],
        max_providers: int,
        llm_intent: Optional[QueryIntent] = None,
    ) -> List[ProviderConfig]:
        """
        获取 provider 列表

        Phase 2 R3: 如果启用了自适应路由，使用 AdaptiveRouter 动态选择 provider。
        否则使用静态的 preferred_providers 或排序后的全部 provider。

        Args:
            intent_mode: 意图模式配置
            max_providers: 最大 provider 数量
            llm_intent: LLM 查询意图（可选，包含 provider_scores）

        Returns:
            ProviderConfig 列表（按优先级排序）
        """
        # Phase 2 R3: 如果启用了自适应路由
        if self.router and self.router.config.enabled:
            intent = (
                llm_intent.intent
                if llm_intent
                else (intent_mode.intent if intent_mode else "general")
            )
            llm_scores = llm_intent.provider_scores if llm_intent else None

            all_enabled = self.config_loader.list_providers(enabled_only=True)
            routing = self.router.select_providers(
                intent=intent,
                available_providers=all_enabled,
                llm_scores=llm_scores,
            )

            logger.info(
                f"自适应路由选择 providers={routing.selected_providers} "
                f"rationale={routing.rationale}"
            )

            provider_map = {p.name: p for p in all_enabled}
            return [
                provider_map[name]
                for name in routing.selected_providers
                if name in provider_map
            ]

        # 回退到静态路由
        # 如果有意图模式且配置了首选 provider
        if intent_mode and intent_mode.preferred_providers:
            providers = []
            for provider_name in intent_mode.preferred_providers:
                provider = self.config_loader.get_provider(provider_name)
                if provider and provider.enabled:
                    providers.append(provider)

            # 限制数量
            return providers[:max_providers]

        # 否则使用所有启用的 provider
        all_providers = self.config_loader.list_providers(enabled_only=True)

        # 按名称排序（确保顺序一致）
        all_providers.sort(key=lambda p: p.name)

        return all_providers[:max_providers]

    async def _search_parallel(
        self,
        providers: List[ProviderConfig],
        request: SearchRequest,
    ) -> List[OrchestratorSearchResult]:
        """
        并行执行多个 provider

        Args:
            providers: Provider 配置列表
            request: 搜索请求

        Returns:
            搜索结果列表
        """
        _req_str = f"req={request.request_id}" if request.request_id else ""
        logger.info(f"并行执行 {len(providers)} 个 provider {_req_str}")

        # 创建任务列表
        tasks = []
        for provider in providers:
            task = self._execute_single_provider(provider, request)
            tasks.append(task)

        # 并行执行所有任务（使用 ALL_COMPLETED）
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        final_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Provider {providers[idx].name} 执行失败 "
                    f"error_type=Exception error={result} {_req_str}"
                )

                # 创建错误结果
                error_result = OrchestratorSearchResult(
                    version="1.0.0",
                    status=ResultStatus.ERROR,
                    error=str(result),
                    provider=providers[idx].name,
                    provider_type=providers[idx].type,
                    query=request.query,
                    items=[],
                    metadata={},
                )
                final_results.append(error_result)
            else:
                final_results.append(result)

        return final_results

    async def _execute_with_retry(
        self,
        provider: ProviderConfig,
        request: SearchRequest,
    ) -> OrchestratorSearchResult:
        """
        带重试的执行（A3 — 重试逻辑）

        对 RetryableError 自动重试，最多 3 次，指数退避 1s, 2s, 4s。
        对 NonRetryableError 不重试，直接抛出。

        Returns:
            搜索结果

        Raises:
            NonRetryableError: 不可重试错误
            SearchError: 重试耗尽后的最终错误
        """
        _req_str = f"req={request.request_id}" if request.request_id else ""
        last_exception = None

        for attempt in range(1, self._max_retries + 1):
            try:
                result = await self._execute_inner_provider(provider, request)

                # 成功返回
                return result

            except RetryableError as e:
                last_exception = e
                retry_after = getattr(e, 'retry_after', self._retry_backoff_base * (2 ** (attempt - 1)))

                if attempt < self._max_retries:
                    logger.warning(
                        f"重试 {attempt}/{self._max_retries} "
                        f"provider={provider.name} "
                        f"retry_after={retry_after}s {_req_str}"
                    )
                    await asyncio.sleep(retry_after)
                else:
                    logger.error(
                        f"重试耗尽 provider={provider.name} "
                        f"attempts={self._max_retries} {_req_str}"
                    )
                    raise

            except NonRetryableError:
                # 不重试，直接抛出
                raise

        # 所有重试失败
        raise SearchError(
            f"重试耗尽: provider={provider.name}, attempts={self._max_retries}"
        ) from last_exception

    async def _execute_inner_provider(
        self,
        provider: ProviderConfig,
        request: SearchRequest,
    ) -> OrchestratorSearchResult:
        """
        实际执行单个 provider 的搜索（不包含重试逻辑）。

        Args:
            provider: Provider 配置
            request: 搜索请求

        Returns:
            搜索结果

        Raises:
            RetryableError: 可重试错误
            NonRetryableError: 不可重试错误
        """
        start_time = time.time()
        _req_str = f"req={request.request_id}" if request.request_id else ""

        # 检查健康状态
        if not self.state_manager.is_healthy(provider.name):
            logger.warning(
                f"Provider 不健康 provider={provider.name} "
                f"healthy=false {_req_str}"
            )

            raise ProviderUnavailableError(f"Provider 不健康: {provider.name}")

        # 检查配额
        if not self.state_manager.check_quota(provider.name, provider):
            logger.warning(
                f"Provider 配额不足 provider={provider.name} "
                f"healthy=false {_req_str}"
            )

            self.state_manager.update_health(
                provider.name,
                is_healthy=False,
                error_message="配额不足",
                error_code="RATE_LIMITED",
            )

            # 更新配额监控数据
            quota_state = self.state_manager.get_quota(provider.name, provider)
            remaining = quota_state.quota_limit - quota_state.request_count
            _update_quota_stats(provider.name, max(0, remaining), 30.0)

            raise QuotaExhaustedError(f"Provider 配额不足: {provider.name}")

        # 获取剩余配额用于监控
        quota_remaining = None
        if hasattr(self.state_manager, 'get_quota'):
            try:
                quota_state = self.state_manager.get_quota(provider.name, provider)
                quota_remaining = quota_state.quota_limit - quota_state.request_count
                _update_quota_stats(provider.name, max(0, quota_remaining), float(quota_state.quota_window))
            except Exception:
                quota_remaining = None

        try:
            # 根据 provider 类型执行搜索
            if provider.type == ProviderType.MCP:
                result = await self._execute_mcp_provider(provider, request)
            elif provider.type == ProviderType.HTTP:
                result = await self._execute_http_provider(provider, request)
            else:
                raise NonRetryableError(f"不支持的 provider 类型: {provider.type}")

            # 检查结果状态，决定是否需要重试
            if result.status in (ResultStatus.TIMEOUT,):
                elapsed_ms = (time.time() - start_time) * 1000
                _update_provider_stats(provider.name, False, elapsed_ms)
                raise SearchTimeoutError(
                    f"Provider 超时: {provider.name} ({elapsed_ms:.0f}ms) - {result.error}",
                    retry_after=2.0,
                )

            if result.status == ResultStatus.RATE_LIMITED:
                elapsed_ms = (time.time() - start_time) * 1000
                _update_provider_stats(provider.name, False, elapsed_ms)
                raise QuotaExhaustedError(f"Provider 配额耗尽: {provider.name} - {result.error}")

            if result.status == ResultStatus.ERROR:
                elapsed_ms = (time.time() - start_time) * 1000
                _update_provider_stats(provider.name, False, elapsed_ms)
                err_msg = result.error or "unknown error"
                err_lower = err_msg.lower()
                # 分类错误
                if "connect" in err_lower or "reset" in err_lower or "refused" in err_lower:
                    raise RetryableError(
                        f"Provider 连接失败: {provider.name} - {err_msg}",
                        retry_after=1.0,
                    )
                elif "timeout" in err_lower:
                    raise SearchTimeoutError(
                        f"Provider 超时: {provider.name} - {err_msg}",
                        retry_after=2.0,
                    )
                elif "403" in err_msg or "401" in err_msg or "config" in err_lower:
                    raise NonRetryableError(
                        f"Provider 配置错误: {provider.name} - {err_msg}"
                    )
                elif "quota" in err_lower or "429" in err_msg:
                    raise QuotaExhaustedError(
                        f"Provider 配额耗尽: {provider.name} - {err_msg}"
                    )
                else:
                    raise RetryableError(
                        f"Provider 执行失败: {provider.name} - {err_msg}",
                        retry_after=1.0,
                    )

            # 更新配额计数
            self.state_manager.increment_quota(provider.name, provider)

            # 更新健康状态
            self.state_manager.update_health(
                provider.name,
                is_healthy=(result.status != ResultStatus.ERROR),
            )

            # 更新响应时间
            elapsed_ms = (time.time() - start_time) * 1000
            result.response_time = elapsed_ms / 1000

            # 更新性能监控数据
            is_success = result.status in (ResultStatus.OK, ResultStatus.PARTIAL)
            _update_provider_stats(provider.name, is_success, elapsed_ms)

            # A4 — 结构化日志
            status_str = result.status.value
            logger.info(
                f"Provider 执行完成 provider={provider.name} "
                f"duration_ms={elapsed_ms:.0f} "
                f"status={status_str} "
                f"items={len(result.items)} "
                f"quota_remaining={quota_remaining} {_req_str}"
            )

            return result

        except NonRetryableError:
            # 不可重试，记录并传递
            elapsed_ms = (time.time() - start_time) * 1000
            _update_provider_stats(provider.name, False, elapsed_ms)
            raise

        except RetryableError:
            # 可重试，记录并传递
            elapsed_ms = (time.time() - start_time) * 1000
            # stats already updated in the branches above
            raise

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            _update_provider_stats(provider.name, False, elapsed_ms)

            error_str = str(e)
            error_type = "Unknown"
            error_code = "EXECUTION_ERROR"

            err_lower = error_str.lower()
            if "timeout" in err_lower:
                error_type = "Timeout"
                error_code = "Timeout"
            elif "quota" in err_lower or "usage limit" in err_lower:
                error_type = "Quota"
                error_code = "QUOTA_EXCEEDED"
            elif "config" in err_lower or "invalid" in err_lower or "not found" in err_lower:
                error_type = "Config"
                error_code = "CONFIG_ERROR"

            # A4 — 完整错误上下文
            logger.error(
                f"Provider 执行失败 provider={provider.name} "
                f"duration_ms={elapsed_ms:.0f} "
                f"error_type={error_type} "
                f"error_code={error_code} {_req_str}"
            )

            # 更新健康状态
            self.state_manager.update_health(
                provider.name,
                is_healthy=False,
                error_message=error_str,
                error_code=error_code,
            )

            # 判断是否可重试
            if error_type == "Timeout":
                raise SearchTimeoutError(
                    f"Provider 超时: {provider.name} ({elapsed_ms:.0f}ms) - {error_str}",
                    retry_after=2.0,
                )
            elif error_type == "Quota":
                raise QuotaExhaustedError(
                    f"Provider 配额耗尽: {provider.name} - {error_str}"
                )
            else:
                if "connect" in err_lower or "reset" in err_lower or "refused" in err_lower:
                    raise RetryableError(
                        f"Provider 连接失败: {provider.name} - {error_str}",
                        retry_after=1.0,
                    )
                raise NonRetryableError(
                    f"Provider 执行失败: {provider.name} - {error_str}"
                )

    async def _execute_single_provider(
        self,
        provider: ProviderConfig,
        request: SearchRequest,
    ) -> OrchestratorSearchResult:
        """
        执行单个 provider 的搜索（外部入口，带重试）。

        Phase 2 R3: 执行完成后，记录性能数据到 AdaptiveRouter（如果启用）。

        Args:
            provider: Provider 配置
            request: 搜索请求

        Returns:
            搜索结果
        """
        start_time = time.time()

        try:
            result = await self._execute_with_retry(provider, request)

            # Phase 2 R3: 记录性能数据
            elapsed_ms = (time.time() - start_time) * 1000
            success = result.status in (ResultStatus.OK, ResultStatus.PARTIAL)
            self._record_router_perf(provider.name, request, success, elapsed_ms)

            return result

        except SearchError as e:
            # 重试耗尽或不可重试，返回错误结果
            error_str = str(e)
            error_type = "RetryExhausted" if isinstance(e, RetryableError) else type(e).__name__

            logger.error(
                f"Provider 最终失败 provider={provider.name} "
                f"error_type={error_type} "
                f"error={error_str}"
            )

            # Phase 2 R3: 记录失败
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_router_perf(provider.name, request, False, elapsed_ms)

            return OrchestratorSearchResult(
                version="1.0.0",
                status=ResultStatus.ERROR,
                error=f"provider={provider.name} error_type={error_type} error={error_str}",
                provider=provider.name,
                provider_type=provider.type,
                query=request.query,
                items=[],
                metadata={},
            )
        except Exception as e:
            logger.error(
                f"Provider 意外异常 provider={provider.name} "
                f"error={e}"
            )

            # Phase 2 R3: 记录失败
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_router_perf(provider.name, request, False, elapsed_ms)

            return OrchestratorSearchResult(
                version="1.0.0",
                status=ResultStatus.ERROR,
                error=str(e),
                provider=provider.name,
                provider_type=provider.type,
                query=request.query,
                items=[],
                metadata={},
            )

    async def _execute_mcp_provider(
        self,
        provider: ProviderConfig,
        request: SearchRequest,
    ) -> OrchestratorSearchResult:
        """
        执行 MCP provider 的搜索

        Args:
            provider: Provider 配置
            request: 搜索请求

        Returns:
            搜索结果
        """
        # 构造参数
        arguments = self._build_arguments(provider, request)

        # 调用 MCP 工具
        response = await self.mcp_client.call_tool(
            server_name=provider.mcp_server or provider.name,
            tool_name=provider.mcp_tool_name or "search",
            arguments=arguments,
            timeout=provider.timeout,
        )

        # 解析响应
        return self._parse_response(provider, request, response)

    async def _execute_http_provider(
        self,
        provider: ProviderConfig,
        request: SearchRequest,
    ) -> OrchestratorSearchResult:
        """
        执行 HTTP provider 的搜索

        流程:
        1. 构建请求体（基于 call_parameters 映射 request 参数）
        2. 拼接请求头（provider.http_headers + Content-Type）
        3. 发送 HTTP 请求（GET 用 params，POST 用 json body）
        4. 解析响应（复用 _parse_response 的通用解析逻辑）
        5. 超时控制和错误处理

        Args:
            provider: Provider 配置
            request: 搜索请求

        Returns:
            搜索结果
        """
        logger.debug(f"执行 HTTP provider provider={provider.name}")

        # 1. 构造请求参数
        arguments = self._build_arguments(provider, request)

        # 2. 拼接请求头
        headers = dict(provider.http_headers)
        headers.setdefault("Content-Type", "application/json")

        # 3. 获取 endpoint
        endpoint = provider.http_endpoint
        if not endpoint:
            return OrchestratorSearchResult(
                version="1.0.0",
                status=ResultStatus.ERROR,
                error=f"HTTP provider {provider.name} 未配置 http_endpoint",
                provider=provider.name,
                provider_type=provider.type,
                query=request.query,
                items=[],
                metadata={},
            )

        # 4. 创建 HTTP 会话（延迟初始化）
        if self._http_session is None:
            self._http_session = aiohttp.ClientSession()

        # 5. 确定请求参数
        method = provider.http_method.upper()
        use_params = method == "GET"
        use_json = method in ("POST", "PUT", "PATCH")

        try:
            async with self._http_session.request(
                method=method,
                url=endpoint,
                headers=headers,
                params=arguments if use_params else None,
                json=arguments if use_json else None,
                timeout=aiohttp.ClientTimeout(total=provider.timeout),
            ) as response:
                # 6. 非 200 处理
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"HTTP provider {provider.name} 返回 {response.status}: "
                        f"error_code=HTTP_{response.status} "
                        f"error_text={error_text[:200]}"
                    )
                    return OrchestratorSearchResult(
                        version="1.0.0",
                        status=ResultStatus.ERROR,
                        error=f"HTTP {response.status}: {error_text[:200]}",
                        provider=provider.name,
                        provider_type=provider.type,
                        query=request.query,
                        items=[],
                        metadata={"http_status": response.status},
                    )

                # 7. 解析 JSON 响应
                response_data = await response.json()
                return self._parse_response(provider, request, response_data)

        except asyncio.TimeoutError:
            logger.error(
                f"HTTP provider {provider.name} 超时 ({provider.timeout}s)"
            )
            return OrchestratorSearchResult(
                version="1.0.0",
                status=ResultStatus.TIMEOUT,
                error=f"HTTP provider {provider.name} 超时 ({provider.timeout}s)",
                provider=provider.name,
                provider_type=provider.type,
                query=request.query,
                items=[],
                metadata={},
            )

    def _build_arguments(
        self,
        provider: ProviderConfig,
        request: SearchRequest,
    ) -> Dict[str, Any]:
        """
        构造 provider 调用参数

        根据 provider.call_parameters 进行参数名映射和类型转换

        Args:
            provider: Provider 配置
            request: 搜索请求

        Returns:
            参数字典
        """
        # 基础参数映射
        param_mapping = {
            "query": request.query,
            "num_results": request.num_results,
            "offset": request.offset,
        }

        # 高级参数
        if request.include_domains:
            param_mapping["include_domains"] = request.include_domains

        if request.exclude_domains:
            param_mapping["exclude_domains"] = request.exclude_domains

        # 应用 provider 的参数映射
        final_arguments = {}
        for target_key, source_config in provider.call_parameters.items():
            if isinstance(source_config, str):
                # 简单映射: "target_key": "source_key"
                source_key = source_config
                if source_key in param_mapping:
                    final_arguments[target_key] = param_mapping[source_key]
            elif isinstance(source_config, dict):
                # 复杂映射: {"source": "source_key", "type": "integer"}
                source_key = source_config.get("source")
                param_type = source_config.get("type", "auto")

                if source_key and source_key in param_mapping:
                    value = param_mapping[source_key]

                    # 类型转换
                    if param_type == "integer":
                        value = int(value)
                    elif param_type == "float":
                        value = float(value)
                    elif param_type == "bool":
                        value = bool(value)
                    elif param_type == "list":
                        if isinstance(value, str):
                            value = [value]
                        elif not isinstance(value, list):
                            value = list(value)

                    final_arguments[target_key] = value

        # 如果没有映射，使用默认参数
        if not final_arguments:
            final_arguments = {
                "query": request.query,
                "num_results": request.num_results,
            }

        return final_arguments

    def _parse_response(
        self,
        provider: ProviderConfig,
        request: SearchRequest,
        response: Dict[str, Any],
    ) -> OrchestratorSearchResult:
        """
        解析 provider 响应。

        支持两种格式：
        1. MCP 标准格式: {"content": [{"type": "text", "text": "..."}], "isError": false}
           （McporterMCPClient 返回的标准 MCP 响应）
        2. 传统格式: {"result": [...], "status": "error"}
           （模拟模式的兼容格式）

        从 content[0].text 中提取 JSON 字符串，解析为结构化结果。
        不同 provider 的 JSON 结构不同，通过 result_mapping 统一字段。
        """
        import json

        # 检查 MCP 标准格式的错误标志
        if response.get("isError", False):
            return OrchestratorSearchResult(
                version="1.0.0",
                status=ResultStatus.ERROR,
                error=response.get("error", "MCP 工具返回错误"),
                provider=provider.name,
                provider_type=provider.type,
                query=request.query,
                items=[],
                metadata={"raw_response": response},
            )

        # 检查传统格式的错误
        if response.get("status") == "error":
            return OrchestratorSearchResult(
                version="1.0.0",
                status=ResultStatus.ERROR,
                error=response.get("error", "未知错误"),
                provider=provider.name,
                provider_type=provider.type,
                query=request.query,
                items=[],
                metadata={"raw_response": response},
            )

        # 从 MCP 标准格式的 content 中提取纯文本
        raw_result = []
        content = response.get("content", [])
        if content and isinstance(content, list):
            text_content = content[0].get("text", "") if isinstance(content[0], dict) else ""
            if text_content:
                try:
                    parsed = json.loads(text_content)
                    raw_result = self._extract_search_items(provider, parsed)
                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    logger.debug(f"解析 MCP 响应 JSON 失败 error={e}")
        else:
            # 兼容格式: 尝试从常见 JSON 结构中提取结果列表
            # 用 _extract_search_items 处理 HTTP provider 的直接 JSON 响应
            raw_result = self._extract_search_items(provider, response)
            # 如果 _extract_search_items 没找到，fallback 到 response.get("result", [])

        if not isinstance(raw_result, list):
            # 最后 fallback: 检查是否有 "data" 或 "items" 字段
            if isinstance(response, dict):
                raw_result = response.get("data", response.get("items", []))
            if not isinstance(raw_result, list):
                raw_result = []

        # 应用结果映射
        items = []
        for raw_item in raw_result:
            if not isinstance(raw_item, dict):
                continue
            item = self._parse_search_item(provider, raw_item)
            items.append(item)

        # 确定状态
        if len(items) == 0:
            status = ResultStatus.NO_MATCH
        elif len(items) >= request.num_results:
            status = ResultStatus.OK
        else:
            status = ResultStatus.PARTIAL

        return OrchestratorSearchResult(
            version="1.0.0",
            status=status,
            error=None,
            provider=provider.name,
            provider_type=provider.type,
            query=request.query,
            items=items,
            total_results=response.get("totalResults"),
            metadata={"raw_response": response},
        )

    def _extract_search_items(
        self,
        provider: ProviderConfig,
        parsed: Dict[str, Any],
    ) -> list:
        """
        从解析后的 JSON 中提取搜索结果列表。

        不同 provider 的 JSON 结构不同:
        - open-websearch: {"results": [{title, url, content, publishedDate}]}
        - exa: {"results": [{title, url, snippet, published_date}]}
        - minimax: {"organic": [{title, link, snippet, date}]}
        - brave: {"web": {"results": [{title, url, description, age}]}}
        """
        # 通用格式 1: 根级别的 "results"
        results = parsed.get("results")
        if isinstance(results, list):
            return results

        # 通用格式 2: 根级别的 "organic"（如 MiniMax）
        organic = parsed.get("organic")
        if isinstance(organic, list):
            return organic

        # 通用格式 3: 嵌套的 "web.results"（如 Brave）
        web = parsed.get("web")
        if isinstance(web, dict):
            web_results = web.get("results")
            if isinstance(web_results, list):
                return web_results

        # 通用格式 4: 根级别的 "result"
        result = parsed.get("result")
        if isinstance(result, list):
            return result

        logger.debug(f"未识别的搜索结果格式 provider={provider.name} keys={list(parsed.keys())}")
        return []

    def _parse_search_item(
        self,
        provider: ProviderConfig,
        raw_item: Dict[str, Any],
    ) -> SearchItem:
        """
        解析单个搜索结果项

        根据 provider.result_mapping 进行字段名映射。
        BATTLE-R4-FIXES.md Fix 4 — 支持 published_date 和 score 字段。

        result_mapping 值的含义：
        - 字符串：provider 返回的原始字段名
        - None/~：该 provider 不提供此字段

        Args:
            provider: Provider 配置
            raw_item: 原始结果项

        Returns:
            SearchItem 对象
        """
        # 默认字段映射（兼容未配置 result_mapping 的 provider）
        default_mapping = {
            "title": ["title", "name"],
            "url": ["url", "link", "link"],
            "snippet": ["snippet", "description", "abstract"],
        }

        # 使用 provider 的映射（如果有）
        mapping = provider.result_mapping if provider.result_mapping else {}

        # 提取基本字段
        title = self._extract_field(raw_item, mapping.get("title", default_mapping["title"]))
        url = self._extract_field(raw_item, mapping.get("url", default_mapping["url"]))
        snippet = self._extract_field(raw_item, mapping.get("snippet", default_mapping["snippet"]))

        # 提取 published_date（Fix 4）
        published_date = None
        pd_mapping = mapping.get("published_date", None)
        if pd_mapping is not None:
            published_date = self._extract_field(raw_item, pd_mapping)

        # 提取 score（Fix 4）
        score = 0.0
        score_mapping = mapping.get("score", None)
        if score_mapping is not None:
            try:
                raw_score = self._extract_field(raw_item, score_mapping)
                if raw_score is not None:
                    score = float(raw_score)
            except (ValueError, TypeError):
                score = 0.0

        # 创建 SearchItem
        item = SearchItem(
            title=title or "未知标题",
            url=url or "",
            snippet=snippet or "",
            score=score,
            published_date=published_date,
            raw_data=raw_item,
            source=provider.name,
        )

        return item

    def _extract_field(self, data: Dict[str, Any], field_names: Any) -> Any:
        """
        从字典中提取字段

        Args:
            data: 数据字典
            field_names: 字段名（可以是字符串、列表或 None）
                         None 表示此字段不可用，返回 None

        Returns:
            字段值，如果不存在返回 None
        """
        # None 表示字段不可用（result_mapping 值为 ~）
        if field_names is None:
            return None

        if isinstance(field_names, str):
            return data.get(field_names)

        if isinstance(field_names, list):
            for name in field_names:
                if name in data:
                    return data[name]

        return None

    async def close(self) -> None:
        """关闭引擎（清理资源）"""
        await self.mcp_client.close()
        if self._http_session is not None and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None
        logger.debug("SearchEngine 已关闭")

    # ────────────────────────────────────────────────────────
    # 监控接口（B2）
    # ────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """
        获取当前性能数据快照

        Returns:
            性能数据字典（providers, cache, quota）
        """
        # 同步 cache 统计数据
        cache_stats = self.cache_manager.get_stats()
        _perf_data["cache"]["hits"] = cache_stats.get("hits", 0)
        _perf_data["cache"]["misses"] = cache_stats.get("misses", 0)
        _perf_data["cache"]["size"] = cache_stats.get("size", 0)

        return dict(_perf_data)

    def reset_stats(self) -> None:
        """重置所有统计数据"""
        _perf_data["providers"].clear()
        _perf_data["cache"] = {"hits": 0, "misses": 0, "size": 0}
        _perf_data["quota"].clear()

        logger.debug("性能统计数据已重置")

    def _record_router_perf(
        self,
        provider_name: str,
        request: SearchRequest,
        success: bool,
        latency_ms: float,
    ) -> None:
        """
        记录 provider 性能数据到 AdaptiveRouter（Phase 2 R3）。

        仅在路由启用时记录。

        Args:
            provider_name: Provider 名称
            request: 搜索请求
            success: 是否成功
            latency_ms: 延迟（毫秒）
        """
        if not self.router or not self.router.config.enabled:
            return

        # 确定意图
        intent = request.intent or "general"

        self.router.record_result(
            provider=provider_name,
            intent=intent,
            success=success,
            latency_ms=latency_ms,
        )


__all__ = ["SearchEngine"]
