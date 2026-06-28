"""
orchestrator/aggregator.py

结果聚合模块。

本模块负责：
- 聚合多个 provider 的搜索结果
- 结果去重（基于 URL）
- 为结果分配状态
"""

import hashlib
from typing import List, Dict, Any
from collections import OrderedDict
import logging

from .schema import (
    OrchestratorSearchResult,
    SearchItem,
    ResultStatus,
    ProviderType,
)

logger = logging.getLogger("orchestrator.aggregator")


class ResultAggregator:
    """
    结果聚合器

    聚合多个 provider 的搜索结果并进行去重
    """

    def __init__(self, max_results: int = 50):
        """
        初始化结果聚合器

        Args:
            max_results: 最大结果数（默认 50）
        """
        self.max_results = max_results

        logger.debug(f"ResultAggregator 初始化完成，max_results={max_results}")

    def aggregate(
        self,
        results: List[OrchestratorSearchResult],
        query: str,
    ) -> OrchestratorSearchResult:
        """
        聚合多个搜索结果

        Args:
            results: 多个 provider 的搜索结果列表
            query: 原始查询

        Returns:
            聚合后的 OrchestratorSearchResult
        """
        if not results:
            # 所有 provider 均失败
            return OrchestratorSearchResult(
                version="1.0.0",
                status=ResultStatus.ALL_FAILED,
                error="所有 provider 均返回失败结果",
                provider="none",
                provider_type=ProviderType.MCP,
                query=query,
                items=[],
                metadata={"aggregated_from": []},
            )

        # 过滤掉完全失败的结果
        valid_results = [r for r in results if r.status != ResultStatus.ERROR and r.status != ResultStatus.TIMEOUT]

        if not valid_results:
            # 所有结果都是错误状态
            return OrchestratorSearchResult(
                version="1.0.0",
                status=ResultStatus.ALL_FAILED,
                error="所有 provider 返回错误或超时",
                provider="none",
                provider_type=ProviderType.MCP,
                query=query,
                items=[],
                metadata={"aggregated_from": [r.provider for r in results]},
            )

        # 去重聚合
        unique_items = self._deduplicate_items(valid_results)

        # 限制结果数量
        unique_items = list(unique_items.values())[:self.max_results]

        # 确定聚合状态
        status = self._determine_aggregate_status(valid_results)

        # 聚合性能指标
        total_response_time = sum(r.response_time for r in valid_results)
        avg_response_time = total_response_time / len(valid_results)

        # 聚合 fallback 信息
        fallback_triggered = any(r.fallback_triggered for r in valid_results)
        fallback_chain = []
        for r in valid_results:
            fallback_chain.extend(r.fallback_chain)

        # 创建聚合结果
        aggregated = OrchestratorSearchResult(
            version="1.0.0",
            status=status,
            error=None,
            provider="aggregated",
            provider_type=ProviderType.MCP,
            query=query,
            items=unique_items,
            metadata={
                "aggregated_from": [r.provider for r in valid_results],
                "total_items_before_dedup": sum(len(r.items) for r in valid_results),
                "total_items_after_dedup": len(unique_items),
                "avg_response_time": avg_response_time,
            },
            response_time=avg_response_time,
            total_results=len(unique_items),
            cached=any(r.cached for r in valid_results),
            fallback_triggered=fallback_triggered,
            fallback_chain=fallback_chain,
        )

        logger.info(
            f"聚合完成 providers={len(results)} "
            f"去重前 {sum(len(r.items) for r in valid_results)} 条 "
            f"去重后 {len(unique_items)} 条 "
            f"status={status.value}"
        )

        return aggregated

    def _deduplicate_items(
        self,
        results: List[OrchestratorSearchResult],
    ) -> "OrderedDict[str, SearchItem]":
        """
        去重搜索结果项（基于 URL）

        Args:
            results: 搜索结果列表

        Returns:
            OrderedDict (URL -> SearchItem)，保留首次出现的项
        """
        unique_items = OrderedDict()

        for result in results:
            for item in result.items:
                # 使用 URL 作为唯一键
                url = item.url

                # 如果 URL 不存在，添加到结果中
                if url not in unique_items:
                    unique_items[url] = item
                    logger.debug(f"添加新结果: {url}")
                else:
                    # URL 已存在，可以选择保留评分更高的
                    existing_item = unique_items[url]
                    if item.score > existing_item.score:
                        unique_items[url] = item
                        logger.debug(f"替换为更高评分的结果: {url}, score={item.score}")

        return unique_items

    def _determine_aggregate_status(
        self,
        results: List[OrchestratorSearchResult],
    ) -> ResultStatus:
        """
        确定聚合结果的状态

        Args:
            results: 搜索结果列表

        Returns:
            聚合状态
        """
        # 统计各种状态
        status_count = {}
        for result in results:
            status = result.status
            status_count[status] = status_count.get(status, 0) + 1

        # 统计总结果数
        total_items = sum(len(r.items) for r in results)

        # 规则 1: 如果有任何 OK 状态且有结果，返回 OK
        if status_count.get(ResultStatus.OK, 0) > 0 and total_items > 0:
            return ResultStatus.OK

        # 规则 2: 如果有 PARTIAL 状态且有结果，返回 PARTIAL
        if status_count.get(ResultStatus.PARTIAL, 0) > 0 and total_items > 0:
            return ResultStatus.PARTIAL

        # 规则 3: 如果有 NO_MATCH 状态且无结果，返回 NO_MATCH
        if status_count.get(ResultStatus.NO_MATCH, 0) > 0 and total_items == 0:
            return ResultStatus.NO_MATCH

        # 规则 4: 如果有任何结果，返回 PARTIAL
        if total_items > 0:
            return ResultStatus.PARTIAL

        # 规则 5: 默认返回 ALL_FAILED
        return ResultStatus.ALL_FAILED

    def merge_single_result(
        self,
        result: OrchestratorSearchResult,
        query: str,
    ) -> OrchestratorSearchResult:
        """
        包装单个搜索结果（用于统一接口）

        Args:
            result: 单个 provider 的搜索结果
            query: 原始查询

        Returns:
            包装后的结果（如果不需要包装则直接返回）
        """
        # 直接返回原结果
        return result


__all__ = ["ResultAggregator"]
