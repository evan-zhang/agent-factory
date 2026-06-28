"""
orchestrator/cache.py

缓存管理模块。

本模块负责：
- 进程级内存缓存
- TTL 过期管理
- 缓存命中率统计
- 结构化日志（包含 hit_rate, size）
"""

import hashlib
import time
import logging
from typing import Dict, Optional, Any
from collections import OrderedDict

from .schema import (
    CacheEntry,
    OrchestratorSearchResult,
    SearchRequest,
)

logger = logging.getLogger("orchestrator.cache")


class CacheManager:
    """
    缓存管理器

    提供进程级内存缓存，支持 TTL 过期和 LRU 淘汰
    """

    def __init__(self, max_size: int = 1000):
        """
        初始化缓存管理器

        Args:
            max_size: 最大缓存条目数（默认 1000）
        """
        self.max_size = max_size

        # 使用 OrderedDict 实现 LRU
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # 统计信息
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        logger.debug(f"CacheManager 初始化完成 max_size={max_size}")

    def _generate_key(self, request: SearchRequest) -> str:
        """
        生成缓存键

        Args:
            request: 搜索请求

        Returns:
            缓存键（hash 字符串）
        """
        # 将请求序列化为字符串
        key_parts = [
            request.query,
            str(request.num_results),
            str(request.offset),
            str(request.include_domains),
            str(request.exclude_domains),
            request.start_date or "",
            request.end_date or "",
        ]

        key_string = "|".join(key_parts)

        # 生成 hash
        hash_obj = hashlib.md5(key_string.encode("utf-8"))
        return hash_obj.hexdigest()

    def get(self, request: SearchRequest) -> Optional[OrchestratorSearchResult]:
        """
        从缓存获取搜索结果

        Args:
            request: 搜索请求

        Returns:
            OrchestratorSearchResult 对象，如果缓存不存在或已过期返回 None
        """
        key = self._generate_key(request)

        # 检查缓存
        if key not in self._cache:
            self._misses += 1
            hit_rate = self._get_hit_rate()
            logger.debug(
                f"缓存未命中 key={key} "
                f"hit_rate={hit_rate:.2f} "
                f"size={len(self._cache)}"
            )
            return None

        entry = self._cache[key]

        # 检查是否过期
        if entry.is_expired:
            # 删除过期条目
            del self._cache[key]
            self._misses += 1
            hit_rate = self._get_hit_rate()
            logger.debug(
                f"缓存过期 key={key} "
                f"hit_rate={hit_rate:.2f} "
                f"size={len(self._cache)}"
            )
            return None

        # 更新访问信息
        entry.access_count += 1
        entry.last_access_time = time.time()

        # 移动到末尾（LRU）
        self._cache.move_to_end(key)

        # 更新统计
        self._hits += 1

        hit_rate = self._get_hit_rate()
        logger.debug(
            f"缓存命中 key={key} "
            f"access_count={entry.access_count} "
            f"hit_rate={hit_rate:.2f} "
            f"size={len(self._cache)}"
        )
        return entry.result

    def set(
        self,
        request: SearchRequest,
        result: OrchestratorSearchResult,
        ttl: int = 3600,
    ) -> None:
        """
        将搜索结果存入缓存

        Args:
            request: 搜索请求
            result: 搜索结果
            ttl: 存活时间（秒，默认 1 小时）
        """
        key = self._generate_key(request)

        # 检查是否需要淘汰
        if len(self._cache) >= self.max_size and key not in self._cache:
            # 淘汰最旧的条目（LRU）
            self._evict_oldest()

        # 创建缓存条目
        entry = CacheEntry(
            key=key,
            result=result,
            created_time=time.time(),
            ttl=ttl,
            access_count=0,
            last_access_time=None,
        )

        # 存入缓存
        self._cache[key] = entry

        # 移动到末尾（LRU）
        self._cache.move_to_end(key)

        logger.debug(
            f"存入缓存 key={key} "
            f"ttl={ttl} "
            f"size={len(self._cache)}"
        )

    def _evict_oldest(self) -> None:
        """淘汰最旧的缓存条目（LRU）"""
        if not self._cache:
            return

        # 获取最旧的条目
        oldest_key = next(iter(self._cache))
        del self._cache[oldest_key]

        self._evictions += 1

        logger.debug(
            f"淘汰缓存条目 key={oldest_key} "
            f"size={len(self._cache)}"
        )

    def invalidate(self, request: SearchRequest) -> None:
        """
        使指定请求的缓存失效

        Args:
            request: 搜索请求
        """
        key = self._generate_key(request)

        if key in self._cache:
            del self._cache[key]
            logger.debug(f"使缓存失效 key={key}")

    def clear(self) -> None:
        """清空所有缓存"""
        cache_size = len(self._cache)
        self._cache.clear()

        logger.debug(f"清空所有缓存 size={cache_size}")

    def cleanup_expired(self) -> int:
        """
        清理过期的缓存条目

        Returns:
            清理的条目数
        """
        expired_keys = []

        for key, entry in self._cache.items():
            if entry.is_expired:
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"清理过期缓存 count={len(expired_keys)}")

        return len(expired_keys)

    def _get_hit_rate(self) -> float:
        """计算缓存命中率"""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total_requests = self._hits + self._misses
        hit_rate = self._get_hit_rate()

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }

    def get_size(self) -> int:
        """
        获取当前缓存大小

        Returns:
            缓存条目数
        """
        return len(self._cache)

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        logger.debug("重置缓存统计")


__all__ = ["CacheManager"]
