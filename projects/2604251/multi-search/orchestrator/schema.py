"""
orchestrator/schema.py

定义所有数据结构（dataclass），作为整个 orchestrator 模块的数据契约。

本模块包含：
- ProviderConfig: Provider YAML 配置的数据类表示
- IntentModeConfig: 意图模式配置的数据类表示
- SearchRequest: 搜索请求的数据类
- SearchItem: 单个搜索结果项
- OrchestratorSearchResult: 搜索响应的完整结构（符合 BATTLE-R4-FIXES.md Fix 5）
- ProviderHealth: Provider 健康状态
- QuotaState: 本地配额计数器状态
- CacheEntry: 缓存条目
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import time


# ────────────────────────────────────────────────────────
# 异常层级体系
# ────────────────────────────────────────────────────────

class SearchError(Exception):
    """搜索异常基类"""
    pass


class RetryableError(SearchError):
    """可重试异常（超时、网络波动）

    Attributes:
        retry_after: 建议重试间隔（秒）
    """
    def __init__(self, message: str, retry_after: float = 1.0):
        super().__init__(message)
        self.retry_after = retry_after


class NonRetryableError(SearchError):
    """不可重试异常（配置错误、配额耗尽）"""
    pass


class ProviderUnavailableError(NonRetryableError):
    """Provider 不可用"""
    pass


class QuotaExhaustedError(NonRetryableError):
    """配额用尽"""
    pass


class SearchTimeoutError(RetryableError):
    """搜索超时"""
    def __init__(self, message: str, retry_after: float = 2.0):
        super().__init__(message, retry_after=retry_after)


class ProviderType(Enum):
    """Provider 类型枚举"""
    MCP = "mcp"          # 通过 MCP 调用（如 mcporter 管理的 MiniMax/Tavily）
    HTTP = "http"        # 直接 HTTP API 调用
    HYBRID = "hybrid"    # 混合模式


class ResultStatus(Enum):
    """搜索结果状态枚举"""
    OK = "ok"                    # 成功，有结果
    PARTIAL = "partial"          # 部分成功，有少量结果
    NO_MATCH = "no_match"        # 成功但无匹配结果
    ERROR = "error"              # 执行失败（超时/异常）
    ALL_FAILED = "all_failed"    # 所有 provider 均失败
    RATE_LIMITED = "rate_limited"  # 配额用尽/限流
    TIMEOUT = "timeout"          # 超时


@dataclass
class ProviderConfig:
    """
    Provider YAML 配置的数据类表示

    对应 providers/*.yaml 的结构
    """
    name: str                          # Provider 唯一标识（如 "minimax", "brave"）
    display_name: str                 # 显示名称（如 "MiniMax Search"）
    type: ProviderType                 # Provider 类型
    enabled: bool = True               # 是否启用

    # MCP 相关配置
    mcp_server: Optional[str] = None   # MCP 服务器名称（如 "minimax", "tavily"）
    mcp_tool_name: Optional[str] = None  # MCP 工具名称（如 "web_search", "search"）

    # HTTP 相关配置
    http_endpoint: Optional[str] = None   # HTTP API 端点
    http_method: str = "POST"             # HTTP 方法
    http_headers: Dict[str, str] = field(default_factory=dict)  # HTTP 请求头

    # 参数映射（将统一参数名映射到 provider 特定参数名）
    call_parameters: Dict[str, Any] = field(default_factory=dict)

    # 结果字段映射（将 provider 响应字段映射到统一字段名）
    result_mapping: Dict[str, str] = field(default_factory=dict)

    # 配额管理
    quota_limit: Optional[int] = None     # 配额上限（每分钟请求数）
    quota_window: int = 60                 # 配额时间窗口（秒）

    # 超时设置
    timeout: int = 30                      # 请求超时时间（秒）

    # 其他元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoundConfig:
    """
    三轮递进中的一个轮次配置（BATTLE-R4-FIXES.md Fix 2）

    定义每轮的搜索模式、query 改写模板、provider 筛选规则。
    """
    mode: str                           # 轮次模式: precise | broaden | fallback
    query_template: str                 # Query 改写模板，如 '"{query}"' 或 '{query}'
    count: int = 10                     # 本轮期望结果数
    timeout_ms: int = 10000             # 本轮超时（毫秒）
    provider_filter: List[str] = field(default_factory=list)  # 空列表 = 全部 provider


@dataclass
class RoundTermination:
    """
    三轮递进提前终止条件（BATTLE-R4-FIXES.md Fix 2）

    当去重后结果数达到 min_results 时提前终止后续轮次。
    """
    min_results: int = 3                # 最小结果数，达到后提前终止
    max_rounds: int = 3                 # 最大轮次数


@dataclass
class QueryStrategy:
    """
    查询策略配置（BATTLE-R4-FIXES.md Fix 2）

    包含三轮递进的所有配置信息。
    """
    enabled: bool = False               # 是否启用三轮递进
    rounds: List[RoundConfig] = field(default_factory=list)  # 轮次列表
    round_termination: Optional[RoundTermination] = None     # 提前终止条件


@dataclass
class IntentModeConfig:
    """
    意图模式配置的数据类表示

    对应 intent-modes.yaml 的结构
    """
    intent: str                         # 意图名称（如 "NAVIGATION", "INFO"）
    query_strategy: str = "broad"       # 查询策略（"precise", "broad", "fallback"）
    cache_ttl: int = 3600              # 缓存存活时间（秒，默认 1 小时）

    # 首选 provider 列表（按优先级排序）
    preferred_providers: List[str] = field(default_factory=list)

    # 三轮递进查询策略（BATTLE-R4-FIXES.md Fix 2）
    strategy_rounds: Optional[QueryStrategy] = None

    # 是否启用 fallback 链
    enable_fallback: bool = True

    # 其他配置
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchRequest:
    """
    搜索请求的数据类

    封装所有搜索输入参数
    """
    query: str                          # 搜索查询文本
    intent: Optional[str] = None       # 用户意图（可选，用于查询策略选择）

    # 查询参数
    num_results: int = 10              # 期望结果数量
    offset: int = 0                    # 结果偏移量（用于分页）

    # 高级筛选
    include_domains: Optional[List[str]] = None   # 限定域名（如 ["gov.cn"]）
    exclude_domains: Optional[List[str]] = None   # 排除域名

    # 时间范围
    start_date: Optional[str] = None    # 开始日期（ISO 8601）
    end_date: Optional[str] = None      # 结束日期（ISO 8601）

    # 其他选项
    options: Dict[str, Any] = field(default_factory=dict)

    # 请求元数据
    request_id: Optional[str] = None    # 请求唯一标识
    timestamp: float = field(default_factory=time.time)  # 请求时间戳


@dataclass
class SearchItem:
    """
    单个搜索结果项的数据类

    表示一条搜索结果，包含标题、摘要、URL 等标准字段
    """
    title: str                          # 结果标题
    url: str                            # 结果 URL
    snippet: str                        # 结果摘要/描述

    # 评分和元数据
    score: float = 0.0                  # 相关性评分（0-1）

    # Phase 2 R2: 质量评分详情（各维度得分）
    score_detail: Dict[str, float] = field(default_factory=dict)  # {"total": 0.85, "authority": 1.0, "freshness": 0.8, "relevance": 0.6}

    # 额外字段
    published_date: Optional[str] = None    # 发布日期
    author: Optional[str] = None            # 作者
    thumbnail: Optional[str] = None         # 缩略图 URL

    # Provider 原始数据（保留完整响应用于调试）
    raw_data: Dict[str, Any] = field(default_factory=dict)

    # 来源标识
    source: Optional[str] = None         # 来源 provider


@dataclass
class OrchestratorSearchResult:
    """
    搜索响应的完整结构（符合 BATTLE-R4-FIXES.md Fix 5）

    这是 orchestrator 对外暴露的主数据结构，包含所有必要字段
    """
    # 非默认参数（必需）
    version: str                         # 版本号（如 "1.0.0"）
    status: ResultStatus                 # 结果状态
    provider: str                        # 实际使用的 provider 名称
    query: str                           # 实际执行的查询（可能经过 template 处理）

    # 默认参数（可选）
    # 错误信息（当 status 为 ERROR/ALL_FAILED 时）
    error: Optional[str] = None          # 错误描述

    # Provider 信息
    provider_type: ProviderType = ProviderType.MCP  # Provider 类型

    # 查询信息
    original_query: Optional[str] = None  # 用户原始查询

    # 结果列表
    items: List[SearchItem] = field(default_factory=list)  # 搜索结果项列表

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 性能指标
    response_time: float = 0.0          # 响应时间（秒）
    total_results: Optional[int] = None  # 总结果数（如果 provider 提供）

    # 缓存信息
    cached: bool = False                # 是否来自缓存
    cache_hit_rate: Optional[float] = None  # 缓存命中率（0-1）

    # Fallback 信息
    fallback_triggered: bool = False    # 是否触发了 fallback
    fallback_chain: List[str] = field(default_factory=list)  # Fallback 链轨迹

    # 配额信息
    quota_remaining: Optional[int] = None    # 剩余配额
    quota_reset_time: Optional[float] = None  # 配额重置时间


@dataclass
class ProviderHealth:
    """
    Provider 健康状态的数据类

    用于缓存 provider 的可用性状态，避免反复探测不可用 provider
    """
    provider_name: str                   # Provider 名称
    is_healthy: bool                     # 是否健康（可用）

    # 健康检查信息
    last_check_time: float               # 上次检查时间（epoch timestamp）
    check_interval: int = 60             # 检查间隔（秒，默认 60 秒）

    # 错误信息（如果不健康）
    error_message: Optional[str] = None  # 错误描述
    error_code: Optional[str] = None     # 错误码

    # 统计信息
    success_count: int = 0               # 成功次数
    failure_count: int = 0               # 失败次数
    last_success_time: Optional[float] = None  # 上次成功时间

    # 配额状态
    quota_remaining: Optional[int] = None    # 剩余配额
    quota_reset_time: Optional[float] = None  # 配额重置时间

    # 其他元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuotaState:
    """
    本地配额计数器状态的数据类

    用于管理每个 provider 的请求配额，支持原子操作
    """
    # 非默认参数（必需）
    provider_name: str                   # Provider 名称
    quota_limit: int                     # 配额上限（每分钟请求数）
    window_start_time: float             # 窗口开始时间（epoch timestamp）
    last_update_time: float               # 最后更新时间（epoch timestamp）

    # 默认参数（可选）
    quota_window: int = 60               # 配额时间窗口（秒）

    # 当前窗口内的请求计数
    request_count: int = 0               # 当前窗口请求数

    # 统计信息
    total_requests: int = 0              # 总请求数（累计）
    total_limit_exceeded: int = 0        # 配额超限次数


@dataclass
class CacheEntry:
    """
    缓存条目的数据类

    用于进程级内存缓存，支持 TTL 过期
    """
    key: str                             # 缓存键（通常是 query 的 hash）
    result: OrchestratorSearchResult     # 缓存的搜索结果

    # TTL 管理
    created_time: float                  # 创建时间（epoch timestamp）
    ttl: int = 3600                      # 存活时间（秒，默认 1 小时）

    # 访问统计
    access_count: int = 0                # 访问次数
    last_access_time: Optional[float] = None  # 最后访问时间

    # 其他元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return time.time() - self.created_time > self.ttl

    @property
    def time_to_live(self) -> float:
        """返回剩余存活时间（秒）"""
        elapsed = time.time() - self.created_time
        return max(0, self.ttl - elapsed)


@dataclass
class FallbackChainConfig:
    """
    Fallback 链配置的数据类

    对应 fallback_order.yaml 的结构
    """
    # Fallback 链（按优先级排序）
    chain: List[str] = field(default_factory=list)

    # 触发条件
    trigger_on_status: List[ResultStatus] = field(default_factory=list)

    # 最大 fallback 深度
    max_depth: int = 3

    # 其他配置
    metadata: Dict[str, Any] = field(default_factory=dict)


# ────────────────────────────────────────────────────────
# Phase 2 R3: Adaptive Provider Router 类型定义
# ────────────────────────────────────────────────────────


@dataclass
class ProviderPerformance:
    """
    单个 provider 的性能统计数据。

    按 provider + intent 维度记录，用于自适应路由决策。
    """
    provider: str                    # provider 名
    intent: str                     # 意图类型（policy/info/news/navigation/general）
    total_calls: int = 0
    success_calls: int = 0
    total_latency_ms: float = 0.0
    last_call_time: float = 0.0     # 最后一次调用的 epoch 时间戳

    @property
    def success_rate(self) -> float:
        """当前成功率"""
        return self.success_calls / max(self.total_calls, 1)

    @property
    def avg_latency_ms(self) -> float:
        """平均延迟"""
        return self.total_latency_ms / max(self.total_calls, 1)


@dataclass
class RoutingDecision:
    """
    路由决策结果。

    包含选出的 provider 列表（按推荐顺序）、决策理由和轮询策略。
    """
    selected_providers: List[str]    # 选出的 provider（按推荐顺序）
    rationale: str                   # 决策理由（用于日志）
    round_strategy: str = "parallel" # parallel / serial / hybrid


@dataclass
class RouterConfig:
    """
    自适应路由器的配置。

    控制是否启用、评分权重、持久化等。
    默认 disabled（enabled: false），需要用户显式启用。
    """
    enabled: bool = False            # 是否启用自适应路由
    max_providers: int = 3           # 单次搜索最大 provider 数
    min_history: int = 5             # 最少历史调用次数后才启用自适应
    default_strategy: str = "parallel"

    # 评分权重
    success_weight: float = 0.5      # 成功率权重
    latency_weight: float = 0.3      # 延迟权重
    llm_score_weight: float = 0.2    # LLM provider_score 权重

    # 持久化配置
    persistence_enabled: bool = True
    persistence_file: str = "_runtime/router-perf.json"


# ────────────────────────────────────────────────────────
# Phase 2 R2: Quality Scorer 类型定义
# ────────────────────────────────────────────────────────


@dataclass
class ScorerConfig:
    """
    质量评分器配置

    控制三个评分维度的权重和评分策略参数。
    """
    authority_weight: float = 0.5       # 权威性权重
    freshness_weight: float = 0.3       # 时效性权重
    relevance_weight: float = 0.2       # 相关性权重

    # 权威性评分层级（URL 域名 → 分数）
    # 键为 glob 模式，值为评分
    authority_tiers: Dict[str, float] = field(default_factory=lambda: {
        # tier_1: 政府官网
        "*.gov.cn": 1.0,
        "*.gov.*": 1.0,
        # tier_2: 学术/高校
        "*.edu.cn": 0.8,
        "*.ac.cn": 0.8,
        # tier_3: 官方媒体
        "people.com.cn": 0.6,
        "xinhuanet.com": 0.6,
        "cctv.com": 0.6,
        "chinanews.com": 0.6,
        "gmw.cn": 0.6,
        # tier_4: 行业/专业网站
        "*.org.cn": 0.4,
        "*.com.cn": 0.4,
    })

    # 时效性评分阈值（天数 → 分数）
    freshness_cutoffs: List[tuple] = field(default_factory=lambda: [
        (30, 1.0),
        (90, 0.8),
        (180, 0.6),
        (365, 0.4),
        (730, 0.2),
    ])

    # 未知域名的默认分数
    unknown_authority_score: float = 0.1
    # 无日期时的默认时效性分数
    no_date_freshness_score: float = 0.1


# ────────────────────────────────────────────────────────
# Phase 2 R1: LLM Query Agent 类型定义
# ────────────────────────────────────────────────────────


@dataclass
class SuggestedQuery:
    """单条 LLM 建议的查询"""
    query: str                       # 改写后的查询文本
    target_providers: List[str] = field(default_factory=list)  # 建议使用哪些 provider
    rationale: str = ""              # 为什么这样改写（用于日志和调试）


@dataclass
class QueryIntent:
    """LLM 返回的查询意图分析"""
    intent: str = "general"          # policy / info / news / navigation / general
    entities: Dict[str, str] = field(default_factory=dict)  # 实体：{"city": "深圳", "department": "人社局"}
    suggested_queries: List[SuggestedQuery] = field(default_factory=list)  # 2-3 条优化查询
    provider_scores: Dict[str, float] = field(default_factory=dict)  # provider 评分：{"minimax": 0.9}
    site_restrictions: List[str] = field(default_factory=list)  # site: 限制：["gov.cn"]


@dataclass
class LLMConfig:
    """LLM 查询代理配置"""
    enabled: bool = False             # 是否启用（默认关闭）
    cache_ttl: int = 3600            # 缓存 TTL（秒）
    timeout: int = 10                # LLM API 超时（秒）
    endpoint: str = "https://api.evan-zhang.com/v1/chat/completions"
    model: str = "deepseek-v4-flash"
    max_tokens: int = 512
    temperature: float = 0.3


# 导出所有 dataclass
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
    # Phase 2 R2
    "ScorerConfig",
    # Phase 2 R1
    "SuggestedQuery",
    "QueryIntent",
    "LLMConfig",
    # Phase 2 R3
    "ProviderPerformance",
    "RoutingDecision",
    "RouterConfig",
]
