"""
orchestrator/__init__.py

Multi-Search Search Orchestrator 包入口。

本模块提供：
- 统一的 logging 配置
- 主要类的导出接口
- 包级别的初始化逻辑
"""

import logging
import sys
from typing import Optional

# 配置根 logger
def _setup_logging(level: Optional[int] = None) -> None:
    """
    配置 orchestrator 模块的 logging 系统

    Args:
        level: logging 级别（默认根据环境变量 DEBUG 开关设置）
    """
    # 创建 orchestrator 专用的 logger
    logger = logging.getLogger("orchestrator")

    # 如果已经配置过，跳过
    if logger.handlers:
        return

    # 根据环境变量或参数确定日志级别
    if level is None:
        # 检查 DEBUG 开关
        import os
        level = logging.DEBUG if os.environ.get("DEBUG") else logging.INFO

    logger.setLevel(level)

    # 创建控制台处理器
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # 设置格式
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # 防止日志传播到根 logger（避免重复）
    logger.propagate = False

    # 设置其他库的日志级别（减少噪音）
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# 执行 logging 初始化
_setup_logging()

# 导出主要类和函数
from .schema import (
    # 异常类
    SearchError,
    RetryableError,
    NonRetryableError,
    ProviderUnavailableError,
    QuotaExhaustedError,
    SearchTimeoutError,
    # Schema
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
    ProviderHealth,
    QuotaState,
    CacheEntry,
    FallbackChainConfig,
    # Phase 2 R1
    SuggestedQuery,
    QueryIntent,
    LLMConfig,
    # Phase 2 R2
    ScorerConfig,
    # Phase 2 R3
    ProviderPerformance,
    RoutingDecision,
    RouterConfig,
)

from .config import ConfigLoader
from .mcp_client import MCPClient, McporterMCPClient
from .state import StateManager
from .cache import CacheManager
from .aggregator import ResultAggregator
from .fallback_chain import FallbackChain
from .engine import SearchEngine, apply_query_template
from .llm_agent import LLMQueryAgent, LLM_SYSTEM_PROMPT
from .scorer import ResultScorer
from .router import AdaptiveRouter

__all__ = [
    # 异常类
    "SearchError",
    "RetryableError",
    "NonRetryableError",
    "ProviderUnavailableError",
    "QuotaExhaustedError",
    "SearchTimeoutError",
    # Schema
    "ProviderType",
    "ResultStatus",
    "ProviderConfig",
    "RoundConfig",
    "RoundTermination",
    "QueryStrategy",
    "IntentModeConfig",
    "SearchRequest",
    "SearchItem",
    "OrchestratorSearchResult",
    "ProviderHealth",
    "QuotaState",
    "CacheEntry",
    "FallbackChainConfig",
    # Phase 2 R1 Schema
    "SuggestedQuery",
    "QueryIntent",
    "LLMConfig",
    # Phase 2 R2 Schema
    "ScorerConfig",
    # Phase 2 R3 Schema
    "ProviderPerformance",
    "RoutingDecision",
    "RouterConfig",
    # Core Components
    "ConfigLoader",
    "MCPClient",
    "McporterMCPClient",
    "StateManager",
    "CacheManager",
    "ResultAggregator",
    "FallbackChain",
    "SearchEngine",
    # Phase 2 R1 Components
    "LLMQueryAgent",
    "LLM_SYSTEM_PROMPT",
    # Phase 2 R2 Components
    "ResultScorer",
    # Phase 2 R3 Components
    "AdaptiveRouter",
    # Functions
    "apply_query_template",
]

# 包元数据
__version__ = "1.0.0"
__author__ = "multi-search team"
__description__ = "Multi-Search Search Orchestrator - Phase 0 Infrastructure"
