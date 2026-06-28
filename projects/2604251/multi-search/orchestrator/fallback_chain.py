"""
orchestrator/fallback_chain.py

Fallback 链模块。

本模块负责：
- 串行 fallback 兜底逻辑
- 按优先级顺序尝试多个 provider
- 触发条件判断
- 请求追踪 ID 传递（通过 SearchRequest.request_id）
"""

import asyncio
import logging
from typing import List, Optional, Callable, Any

from .schema import (
    OrchestratorSearchResult,
    SearchRequest,
    ProviderConfig,
    FallbackChainConfig,
    ResultStatus,
)

logger = logging.getLogger("orchestrator.fallback_chain")


class FallbackChain:
    """
    Fallback 链管理器

    按优先级顺序串行尝试多个 provider，直到成功或达到最大深度
    """

    def __init__(self, config: Optional[FallbackChainConfig] = None):
        """
        初始化 Fallback 链

        Args:
            config: Fallback 链配置（如果为 None 则使用默认配置）
        """
        if config is None:
            # 使用默认配置
            self.config = FallbackChainConfig(
                chain=["minimax", "tavily", "brave", "web_fetch"],
                trigger_on_status=[
                    ResultStatus.ALL_FAILED,
                    ResultStatus.ERROR,
                    ResultStatus.NO_MATCH,
                ],
                max_depth=3,
            )
        else:
            self.config = config

        logger.debug(
            f"FallbackChain 初始化完成 chain={self.config.chain} "
            f"max_depth={self.config.max_depth}"
        )

    def should_trigger(self, result: OrchestratorSearchResult) -> bool:
        """
        判断是否应该触发 fallback

        Args:
            result: 搜索结果

        Returns:
            bool: 是否应该触发 fallback
        """
        # 检查状态是否在触发条件中
        should_trigger = result.status in self.config.trigger_on_status

        # 特殊情况：如果状态是 ok 或 partial，不触发 fallback
        if result.status in (ResultStatus.OK, ResultStatus.PARTIAL):
            should_trigger = False

        if should_trigger:
            logger.debug(f"触发 fallback status={result.status.value}")

        return should_trigger

    async def execute(
        self,
        providers: List[ProviderConfig],
        search_func: Callable[..., Any],
        request: SearchRequest,
        **kwargs,
    ) -> OrchestratorSearchResult:
        """
        执行 fallback 链

        按优先级顺序串行尝试多个 provider，直到成功或达到最大深度

        Args:
            providers: Provider 配置列表（按优先级排序）
            search_func: 搜索函数 (provider, request) -> result
            request: 搜索请求
            **kwargs: 额外的关键字参数（忽略，request_id 通过 request.request_id 传递）

        Returns:
            搜索结果（可能是成功的或最后一个失败的结果）
        """
        _req_str = f"req={request.request_id}" if request.request_id else ""

        if not providers:
            # 没有 provider 可用
            return OrchestratorSearchResult(
                version="1.0.0",
                status=ResultStatus.ALL_FAILED,
                error="没有可用的 provider",
                provider="none",
                query=request.query,
                items=[],
                metadata={"fallback_chain": []},
            )

        # 限制 fallback 深度
        max_providers = min(len(providers), self.config.max_depth)
        providers_to_try = providers[:max_providers]

        # 记录 fallback 链轨迹
        fallback_chain = []

        # 最后一个结果（用于 fallback 失败时返回）
        last_result = None

        for idx, provider in enumerate(providers_to_try):
            logger.info(
                f"Fallback 尝试 {idx + 1}/{max_providers} "
                f"provider={provider.name} {_req_str}"
            )

            # 记录轨迹
            fallback_chain.append(provider.name)

            try:
                # 执行搜索（request_id 通过 request.request_id 传递）
                result = await search_func(provider, request)
                last_result = result

                # 更新 fallback 链信息
                result.fallback_triggered = True
                result.fallback_chain = fallback_chain.copy()

                # 检查结果状态
                if result.status == ResultStatus.OK:
                    # 成功，停止 fallback
                    logger.info(
                        f"Fallback 成功 provider={provider.name} "
                        f"结果数={len(result.items)} {_req_str}"
                    )
                    return result

                elif result.status == ResultStatus.PARTIAL and len(result.items) > 0:
                    # 部分成功但有结果，可以停止 fallback
                    logger.info(
                        f"Fallback 部分成功 provider={provider.name} "
                        f"结果数={len(result.items)} {_req_str}"
                    )
                    return result

                # 否则继续 fallback
                logger.debug(
                    f"Fallback 继续 provider={provider.name} "
                    f"status={result.status.value} {_req_str}"
                )

            except Exception as e:
                logger.error(
                    f"Fallback 执行失败 provider={provider.name} "
                    f"error={e} {_req_str}"
                )

                # 创建错误结果
                last_result = OrchestratorSearchResult(
                    version="1.0.0",
                    status=ResultStatus.ERROR,
                    error=str(e),
                    provider=provider.name,
                    query=request.query,
                    items=[],
                    metadata={"fallback_chain": fallback_chain.copy()},
                )

        # 所有 provider 都失败
        if last_result:
            last_result.fallback_triggered = True
            last_result.fallback_chain = fallback_chain
            logger.warning(
                f"Fallback 失败 已尝试 {len(fallback_chain)} 个 provider {_req_str}"
            )
        else:
            # 不应该发生，但为了健壮性
            last_result = OrchestratorSearchResult(
                version="1.0.0",
                status=ResultStatus.ALL_FAILED,
                error="Fallback 链执行失败",
                provider="none",
                query=request.query,
                items=[],
                metadata={"fallback_chain": fallback_chain},
            )

        return last_result

    def get_chain(self) -> List[str]:
        """
        获取 fallback 链

        Returns:
            Provider 名称列表
        """
        return self.config.chain.copy()

    def set_chain(self, chain: List[str]) -> None:
        """
        设置 fallback 链

        Args:
            chain: Provider 名称列表（按优先级排序）
        """
        self.config.chain = chain
        logger.debug(f"更新 fallback 链 chain={chain}")


__all__ = ["FallbackChain"]
