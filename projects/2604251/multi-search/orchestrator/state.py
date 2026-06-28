"""
orchestrator/state.py

状态管理模块。

本模块负责：
- Provider 健康状态管理（60 秒缓存）
- 配额计数器（使用 portalocker 原子操作）
- 运行时状态持久化
- 结构化日志（包含 healthy, quota_remaining）
"""

import os
import json
import time
import portalocker
from pathlib import Path
from typing import Dict, Optional
import logging

from .schema import (
    ProviderHealth,
    QuotaState,
    ProviderConfig,
)

logger = logging.getLogger("orchestrator.state")


class StateManager:
    """
    状态管理器

    管理 provider 健康状态和配额计数器
    """

    def __init__(self, runtime_dir: Optional[Path] = None):
        """
        初始化状态管理器

        Args:
            runtime_dir: 运行时状态目录（默认自动检测）
        """
        if runtime_dir is None:
            # 自动检测：从 orchestrator/_runtime 目录
            current_file = Path(__file__)
            self.runtime_dir = current_file.parent.parent / "_runtime"
        else:
            self.runtime_dir = Path(runtime_dir)

        # 确保运行时目录存在
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

        # 配额状态文件路径
        self.quota_state_file = self.runtime_dir / "quota-state.json"

        # 内存缓存
        self._health_cache: Dict[str, ProviderHealth] = {}
        self._quota_cache: Dict[str, QuotaState] = {}

        logger.debug(f"StateManager 初始化完成 runtime_dir={self.runtime_dir}")

    def get_health(self, provider_name: str) -> ProviderHealth:
        """
        获取 provider 健康状态（使用缓存）

        Args:
            provider_name: Provider 名称

        Returns:
            ProviderHealth 对象
        """
        # 检查缓存
        if provider_name in self._health_cache:
            health = self._health_cache[provider_name]

            # 检查是否过期（默认 60 秒）
            if time.time() - health.last_check_time < health.check_interval:
                logger.debug(f"使用缓存的健康状态 provider={provider_name} healthy={health.is_healthy}")
                return health

        # 创建新的健康状态
        health = ProviderHealth(
            provider_name=provider_name,
            is_healthy=True,  # 默认健康，让实际调用探测
            last_check_time=time.time(),
            check_interval=60,
        )

        # 缓存
        self._health_cache[provider_name] = health

        return health

    def update_health(
        self,
        provider_name: str,
        is_healthy: bool,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """
        更新 provider 健康状态

        Args:
            provider_name: Provider 名称
            is_healthy: 是否健康
            error_message: 错误描述（如果不健康）
            error_code: 错误码
        """
        health = self.get_health(provider_name)

        # 更新字段
        health.is_healthy = is_healthy
        health.last_check_time = time.time()
        health.error_message = error_message
        health.error_code = error_code

        # 更新统计
        if is_healthy:
            health.success_count += 1
            health.last_success_time = time.time()
        else:
            health.failure_count += 1

        # 缓存更新
        self._health_cache[provider_name] = health

        # 结构化日志
        remaining = None
        if provider_name in self._quota_cache:
            q = self._quota_cache[provider_name]
            remaining = q.quota_limit - q.request_count
        quota_str = f"quota_remaining={max(0, remaining)}" if remaining is not None else ""
        logger.debug(f"更新健康状态 provider={provider_name} healthy={is_healthy} {quota_str}")

    def is_healthy(self, provider_name: str) -> bool:
        """
        检查 provider 是否健康（使用缓存）

        Args:
            provider_name: Provider 名称

        Returns:
            bool: 是否健康
        """
        health = self.get_health(provider_name)

        # 检查是否过期
        if time.time() - health.last_check_time > health.check_interval:
            # 过期了，返回 True 让调用方实际探测
            return True

        return health.is_healthy

    def get_quota(self, provider_name: str, config: ProviderConfig) -> QuotaState:
        """
        获取 provider 配额状态

        Args:
            provider_name: Provider 名称
            config: Provider 配置

        Returns:
            QuotaState 对象
        """
        # 检查内存缓存
        if provider_name in self._quota_cache:
            quota = self._quota_cache[provider_name]

            # 检查时间窗口是否过期
            current_time = time.time()
            if current_time - quota.window_start_time < quota.quota_window:
                return quota

        # 从文件加载或创建新配额状态
        quota = self._load_quota(provider_name, config)

        # 缓存
        self._quota_cache[provider_name] = quota

        return quota

    def _load_quota(self, provider_name: str, config: ProviderConfig) -> QuotaState:
        """
        从文件加载配额状态

        Args:
            provider_name: Provider 名称
            config: Provider 配置

        Returns:
            QuotaState 对象
        """
        # 如果文件不存在，创建新状态
        if not self.quota_state_file.exists():
            return self._create_quota_state(provider_name, config)

        # 读取文件（使用文件锁）
        try:
            with open(self.quota_state_file, "r", encoding="utf-8") as f:
                portalocker.lock(f, portalocker.LOCK_SH)
                data = json.load(f)
                portalocker.unlock(f)

            # 解析 provider 的配额状态
            provider_data = data.get(provider_name)
            if not provider_data:
                return self._create_quota_state(provider_name, config)

            current_time = time.time()

            # 检查时间窗口是否过期
            window_start = provider_data.get("window_start_time", current_time)
            if current_time - window_start >= config.quota_window:
                # 时间窗口过期，重置计数
                logger.debug(f"配额时间窗口过期，重置 provider={provider_name}")
                return self._create_quota_state(provider_name, config)

            # 创建 QuotaState
            quota = QuotaState(
                provider_name=provider_name,
                quota_limit=config.quota_limit or 100,
                quota_window=config.quota_window,
                request_count=provider_data.get("request_count", 0),
                window_start_time=window_start,
                total_requests=provider_data.get("total_requests", 0),
                total_limit_exceeded=provider_data.get("total_limit_exceeded", 0),
                last_update_time=provider_data.get("last_update_time", current_time),
            )

            remaining = quota.quota_limit - quota.request_count
            logger.debug(f"加载配额状态 provider={provider_name} request_count={quota.request_count} quota_remaining={max(0, remaining)}")
            return quota

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"解析配额状态文件失败 error={e} 创建新状态")
            return self._create_quota_state(provider_name, config)

    def _create_quota_state(self, provider_name: str, config: ProviderConfig) -> QuotaState:
        """
        创建新的配额状态

        Args:
            provider_name: Provider 名称
            config: Provider 配置

        Returns:
            QuotaState 对象
        """
        current_time = time.time()

        quota = QuotaState(
            provider_name=provider_name,
            quota_limit=config.quota_limit or 100,
            quota_window=config.quota_window,
            request_count=0,
            window_start_time=current_time,
            total_requests=0,
            total_limit_exceeded=0,
            last_update_time=current_time,
        )

        # 持久化
        self._save_quota(quota)

        logger.debug(f"创建配额状态 provider={provider_name}")
        return quota

    def check_quota(self, provider_name: str, config: ProviderConfig) -> bool:
        """
        检查配额是否足够

        Args:
            provider_name: Provider 名称
            config: Provider 配置

        Returns:
            bool: 配额是否足够
        """
        # 如果没有配置配额限制，总是返回 True
        if config.quota_limit is None:
            return True

        quota = self.get_quota(provider_name, config)

        # 检查是否超过配额
        has_quota = quota.request_count < quota.quota_limit

        if not has_quota:
            logger.warning(f"配额已用尽 provider={provider_name} limit={quota.quota_limit} quota_remaining=0")

        return has_quota

    def increment_quota(self, provider_name: str, config: ProviderConfig) -> None:
        """
        增加配额计数

        Args:
            provider_name: Provider 名称
            config: Provider 配置
        """
        # 如果没有配置配额限制，不做任何操作
        if config.quota_limit is None:
            return

        quota = self.get_quota(provider_name, config)

        # 增加计数
        quota.request_count += 1
        quota.total_requests += 1
        quota.last_update_time = time.time()

        # 持久化
        self._save_quota(quota)

        # 更新缓存
        self._quota_cache[provider_name] = quota

        remaining = quota.quota_limit - quota.request_count
        logger.debug(f"增加配额计数 provider={provider_name} count={quota.request_count} quota_remaining={max(0, remaining)}")

    def _save_quota(self, quota: QuotaState) -> None:
        """
        保存配额状态到文件（使用原子写入）

        Args:
            quota: QuotaState 对象
        """
        try:
            # 读取现有数据
            if self.quota_state_file.exists():
                with open(self.quota_state_file, "r", encoding="utf-8") as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = {}
                    portalocker.unlock(f)
            else:
                data = {}

            # 更新 provider 的配额状态
            data[quota.provider_name] = {
                "quota_limit": quota.quota_limit,
                "quota_window": quota.quota_window,
                "request_count": quota.request_count,
                "window_start_time": quota.window_start_time,
                "total_requests": quota.total_requests,
                "total_limit_exceeded": quota.total_limit_exceeded,
                "last_update_time": quota.last_update_time,
            }

            # 写入临时文件
            temp_file = self.quota_state_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                json.dump(data, f, indent=2, ensure_ascii=False)
                portalocker.unlock(f)

            # 原子替换（os.replace 是原子操作）
            os.replace(temp_file, self.quota_state_file)

            remaining = quota.quota_limit - quota.request_count
            logger.debug(f"保存配额状态 provider={quota.provider_name} quota_remaining={max(0, remaining)}")

        except Exception as e:
            logger.error(f"保存配额状态失败 provider={quota.provider_name} error={e}")

    def reset_health_cache(self) -> None:
        """重置健康状态缓存"""
        self._health_cache.clear()
        logger.debug("重置健康状态缓存")

    def reset_quota_cache(self) -> None:
        """重置配额缓存（不从文件删除）"""
        self._quota_cache.clear()
        logger.debug("重置配额缓存")

    def get_all_health(self) -> Dict[str, ProviderHealth]:
        """
        获取所有 provider 的健康状态

        Returns:
            ProviderHealth 字典
        """
        return self._health_cache.copy()

    def get_all_quota(self) -> Dict[str, QuotaState]:
        """
        获取所有 provider 的配额状态

        Returns:
            QuotaState 字典
        """
        return self._quota_cache.copy()


__all__ = ["StateManager"]
