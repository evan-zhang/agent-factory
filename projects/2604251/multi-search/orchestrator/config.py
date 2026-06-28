"""
orchestrator/config.py

配置加载器模块。

本模块负责：
- 扫描并加载 providers/*.yaml 配置文件
- 加载 intent-modes.yaml 配置
- 加载 fallback_order.yaml 配置
- 提供统一的配置查询接口
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .schema import (
    ProviderConfig,
    IntentModeConfig,
    RoundConfig,
    RoundTermination,
    QueryStrategy,
    FallbackChainConfig,
    ScorerConfig,
    RouterConfig,
    ProviderType,
    ResultStatus,
)

logger = logging.getLogger("orchestrator.config")


class ConfigLoader:
    """
    配置加载器

    扫描 orchestrator/ 目录下的所有 YAML 配置文件并提供查询接口
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        初始化配置加载器

        Args:
            base_dir: orchestrator 目录的基础路径（默认自动检测）
        """
        if base_dir is None:
            # 自动检测：从当前文件向上找到 orchestrator 目录
            current_file = Path(__file__)
            self.base_dir = current_file.parent
        else:
            self.base_dir = Path(base_dir)

        # 配置目录路径
        self.providers_dir = self.base_dir / "providers"
        self.intent_modes_file = self.base_dir / "intent-modes.yaml"
        self.fallback_order_file = self.base_dir / "fallback_order.yaml"
        self.scorer_config_file = self.base_dir / "scorer-config.yaml"
        self.router_config_file = self.base_dir / "router-config.yaml"

        # 缓存配置
        self._providers: Dict[str, ProviderConfig] = {}
        self._intent_modes: Dict[str, IntentModeConfig] = {}
        self._fallback_config: Optional[FallbackChainConfig] = None
        self._scorer_config: Optional[ScorerConfig] = None
        self._router_config: Optional[RouterConfig] = None

        logger.debug(f"ConfigLoader 初始化完成 base_dir={self.base_dir}")

    def load_all(self, reload: bool = False) -> None:
        """
        加载所有配置文件

        Args:
            reload: 是否重新加载（默认 False 使用缓存）
        """
        if reload or not self._providers:
            self._load_providers()

        if reload or not self._intent_modes:
            self._load_intent_modes()

        if reload or self._fallback_config is None:
            self._load_fallback_order()

        if reload or self._scorer_config is None:
            self._load_scorer_config()

        if reload or self._router_config is None:
            self._load_router_config()

        logger.info("所有配置文件加载完成")

    def _load_providers(self) -> None:
        """加载所有 provider 配置文件"""
        self._providers.clear()

        if not self.providers_dir.exists():
            logger.warning(f"providers 目录不存在 path={self.providers_dir}")
            return

        # 扫描所有 .yaml 文件
        for yaml_file in self.providers_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if not data:
                    logger.warning(f"Provider 配置文件为空 path={yaml_file}")
                    continue

                # 解析为 ProviderConfig
                config = self._parse_provider_config(data, yaml_file)
                self._providers[config.name] = config

                logger.debug(f"加载 provider 配置 name={config.name}")

            except Exception as e:
                logger.error(f"加载 provider 配置失败 path={yaml_file} error={e}")

        logger.info(f"加载了 {len(self._providers)} 个 provider 配置")

    def _parse_provider_config(self, data: dict, source_file: Path) -> ProviderConfig:
        """
        解析 provider 配置数据

        Args:
            data: YAML 解析后的字典
            source_file: 源文件路径（用于错误提示）

        Returns:
            ProviderConfig 对象
        """
        # 解析 provider 类型
        type_str = data.get("type", "mcp")
        try:
            provider_type = ProviderType(type_str.lower())
        except ValueError:
            logger.warning(f"无效的 provider type: {type_str}，使用默认 mcp")
            provider_type = ProviderType.MCP

        # 解析参数映射（call.parameters）
        call_parameters = data.get("call", {}).get("parameters", {})

        # 解析结果映射（call.result_mapping）
        result_mapping = data.get("call", {}).get("result_mapping", {})

        # 创建 ProviderConfig
        config = ProviderConfig(
            name=data.get("name", source_file.stem),
            display_name=data.get("display_name", data.get("name", source_file.stem)),
            type=provider_type,
            enabled=data.get("enabled", True),

            # MCP 配置
            mcp_server=data.get("mcp_server"),
            mcp_tool_name=data.get("mcp_tool_name"),

            # HTTP 配置
            http_endpoint=data.get("http_endpoint"),
            http_method=data.get("http_method", "POST"),
            http_headers=data.get("http_headers", {}),

            # 参数和结果映射
            call_parameters=call_parameters,
            result_mapping=result_mapping,

            # 配额管理
            quota_limit=data.get("quota_limit"),
            quota_window=data.get("quota_window", 60),

            # 超时设置
            timeout=data.get("timeout", 30),

            # 元数据
            metadata=data.get("metadata", {}),
        )

        return config

    def _load_intent_modes(self) -> None:
        """加载意图模式配置"""
        self._intent_modes.clear()

        if not self.intent_modes_file.exists():
            logger.warning(f"intent-modes.yaml 不存在 path={self.intent_modes_file}")
            return

        try:
            with open(self.intent_modes_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning("intent-modes.yaml 文件为空")
                return

            # 解析意图模式配置
            # 支持两种格式：
            # 1. 顶层字典：{ "NAVIGATION": {...}, "INFO": {...} }
            # 2. 列表格式：[ {"intent": "NAVIGATION", ...}, ... ]
            if isinstance(data, dict):
                for intent_name, intent_data in data.items():
                    if not isinstance(intent_data, dict):
                        continue

                    config = IntentModeConfig(
                        intent=intent_name,
                        query_strategy=intent_data.get("query_strategy", "broad"),
                        cache_ttl=intent_data.get("cache_ttl", 3600),
                        preferred_providers=intent_data.get("preferred_providers", []),
                        enable_fallback=intent_data.get("enable_fallback", True),
                        metadata=intent_data.get("metadata", {}),
                    )
                    # 解析三轮递进策略（BATTLE-R4-FIXES.md Fix 2）
                    strategy_rounds = self._parse_query_strategy(intent_data.get("query_strategy_config"))
                    if strategy_rounds:
                        config.strategy_rounds = strategy_rounds

                    self._intent_modes[intent_name] = config

            elif isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue

                    intent_name = item.get("intent")
                    if not intent_name:
                        continue

                    config = IntentModeConfig(
                        intent=intent_name,
                        query_strategy=item.get("query_strategy", "broad"),
                        cache_ttl=item.get("cache_ttl", 3600),
                        preferred_providers=item.get("preferred_providers", []),
                        enable_fallback=item.get("enable_fallback", True),
                        metadata=item.get("metadata", {}),
                    )
                    # 解析三轮递进策略
                    strategy_rounds = self._parse_query_strategy(item.get("query_strategy_config"))
                    if strategy_rounds:
                        config.strategy_rounds = strategy_rounds

                    self._intent_modes[intent_name] = config

            logger.info(f"加载了 {len(self._intent_modes)} 个意图模式配置")

        except Exception as e:
            logger.error(f"加载 intent-modes.yaml 失败 error={e}")

    def _load_fallback_order(self) -> None:
        """加载 fallback 链配置"""
        if not self.fallback_order_file.exists():
            logger.warning(f"fallback_order.yaml 不存在 path={self.fallback_order_file}")
            # 创建默认配置
            self._fallback_config = FallbackChainConfig(
                chain=["minimax", "tavily", "brave", "web_fetch"],
                trigger_on_status=[ResultStatus.ALL_FAILED, ResultStatus.ERROR, ResultStatus.NO_MATCH],
                max_depth=3,
            )
            return

        try:
            with open(self.fallback_order_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning("fallback_order.yaml 文件为空")
                return

            # 解析触发条件
            trigger_on_status = []
            for status_str in data.get("trigger_on_status", []):
                try:
                    trigger_on_status.append(ResultStatus(status_str.lower()))
                except ValueError:
                    logger.warning(f"无效的触发状态: {status_str}")

            config = FallbackChainConfig(
                chain=data.get("chain", []),
                trigger_on_status=trigger_on_status,
                max_depth=data.get("max_depth", 3),
                metadata=data.get("metadata", {}),
            )

            self._fallback_config = config

            logger.info(f"加载 fallback 链配置，链长度: {len(config.chain)}")

        except Exception as e:
            logger.error(f"加载 fallback_order.yaml 失败 error={e}")
            # 创建默认配置
            self._fallback_config = FallbackChainConfig(
                chain=["minimax", "tavily", "brave", "web_fetch"],
                trigger_on_status=[ResultStatus.ALL_FAILED, ResultStatus.ERROR, ResultStatus.NO_MATCH],
                max_depth=3,
            )

    def _parse_query_strategy(self, strategy_data: Optional[dict]) -> Optional[QueryStrategy]:
        """
        解析三轮递进策略配置（BATTLE-R4-FIXES.md Fix 2）

        YAML 格式:
          query_strategy_config:
            enabled: true
            rounds:
              - mode: precise
                query_template: '"{query}"'
                count: 5
                timeout_ms: 8000
                provider_filter: [minimax]
              - mode: broaden
                query_template: '{query}'
                count: 10
                timeout_ms: 10000
                provider_filter: []
              - mode: fallback
                query_template: '{query}'
                count: 15
                timeout_ms: 12000
                provider_filter: []
            round_termination:
              min_results: 3
              max_rounds: 3

        Args:
            strategy_data: YAML 中 query_strategy_config 节的字典

        Returns:
            QueryStrategy 对象，如果配置为 None 或无效返回 None
        """
        if not strategy_data or not isinstance(strategy_data, dict):
            return None

        enabled = strategy_data.get("enabled", True)
        if not enabled:
            return None

        rounds_data = strategy_data.get("rounds", [])
        if not rounds_data or not isinstance(rounds_data, list):
            return None

        # 解析每轮配置
        rounds = []
        for round_item in rounds_data:
            if not isinstance(round_item, dict):
                logger.warning(f"跳过无效的轮次配置 round_item={round_item}")
                continue

            round_config = RoundConfig(
                mode=round_item.get("mode", "broaden"),
                query_template=round_item.get("query_template", "{query}"),
                count=round_item.get("count", 10),
                timeout_ms=round_item.get("timeout_ms", 10000),
                provider_filter=round_item.get("provider_filter", []),
            )
            rounds.append(round_config)

        if not rounds:
            logger.warning("query_strategy 配置了 rounds 但未解析出有效轮次")
            return None

        # 解析提前终止条件（可选）
        termination_data = strategy_data.get("round_termination")
        round_termination = None
        if termination_data and isinstance(termination_data, dict):
            round_termination = RoundTermination(
                min_results=termination_data.get("min_results", 3),
                max_rounds=termination_data.get("max_rounds", len(rounds)),
            )

        return QueryStrategy(
            enabled=True,
            rounds=rounds,
            round_termination=round_termination,
        )

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """
        获取指定名称的 provider 配置

        Args:
            name: Provider 名称

        Returns:
            ProviderConfig 对象，如果不存在返回 None
        """
        if not self._providers:
            self.load_all()

        return self._providers.get(name)

    def list_providers(self, enabled_only: bool = True) -> List[ProviderConfig]:
        """
        列出所有 provider 配置

        Args:
            enabled_only: 是否只返回启用的 provider

        Returns:
            ProviderConfig 列表
        """
        if not self._providers:
            self.load_all()

        providers = list(self._providers.values())

        if enabled_only:
            providers = [p for p in providers if p.enabled]

        return providers

    def get_intent_mode(self, intent: str) -> Optional[IntentModeConfig]:
        """
        获取指定意图的模式配置

        Args:
            intent: 意图名称

        Returns:
            IntentModeConfig 对象，如果不存在返回 None
        """
        if not self._intent_modes:
            self.load_all()

        return self._intent_modes.get(intent)

    def list_intent_modes(self) -> List[IntentModeConfig]:
        """
        列出所有意图模式配置

        Returns:
            IntentModeConfig 列表
        """
        if not self._intent_modes:
            self.load_all()

        return list(self._intent_modes.values())

    def _load_scorer_config(self) -> None:
        """
        加载评分器配置（scorer-config.yaml）。

        如果文件不存在或解析失败，使用默认配置（ScorerConfig()）。
        """
        if not self.scorer_config_file.exists():
            logger.info("scorer-config.yaml 不存在，使用默认评分器配置")
            self._scorer_config = ScorerConfig()
            return

        try:
            with open(self.scorer_config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                logger.warning("scorer-config.yaml 为空或格式无效，使用默认配置")
                self._scorer_config = ScorerConfig()
                return

            # 解析权重
            weights = data.get("weights", {})
            authority_weight = weights.get("authority", 0.5)
            freshness_weight = weights.get("freshness", 0.3)
            relevance_weight = weights.get("relevance", 0.2)

            # 解析权威性分级
            authority_tiers = {
                entry["pattern"]: entry["score"]
                for entry in data.get("authority_tiers", [])
                if "pattern" in entry and "score" in entry
            }
            # 如果 YAML 中没有配置 authority_tiers，保留默认值
            if not authority_tiers:
                authority_tiers = {
                    "*.gov.cn": 1.0,
                    "*.gov.*": 1.0,
                    "*.edu.cn": 0.8,
                    "*.ac.cn": 0.8,
                    "people.com.cn": 0.6,
                    "xinhuanet.com": 0.6,
                    "cctv.com": 0.6,
                    "chinanews.com": 0.6,
                    "gmw.cn": 0.6,
                    "*.org.cn": 0.4,
                    "*.com.cn": 0.4,
                }

            # 解析时效性阈值
            freshness_cutoffs_raw = data.get("freshness_cutoffs", [])
            if freshness_cutoffs_raw and isinstance(freshness_cutoffs_raw, list):
                freshness_cutoffs = [
                    (entry["days"], entry["score"])
                    for entry in freshness_cutoffs_raw
                    if "days" in entry and "score" in entry
                ]
            else:
                freshness_cutoffs = [
                    (30, 1.0),
                    (90, 0.8),
                    (180, 0.6),
                    (365, 0.4),
                    (730, 0.2),
                ]

            self._scorer_config = ScorerConfig(
                authority_weight=authority_weight,
                freshness_weight=freshness_weight,
                relevance_weight=relevance_weight,
                authority_tiers=authority_tiers,
                freshness_cutoffs=freshness_cutoffs,
                unknown_authority_score=data.get("unknown_authority_score", 0.1),
                no_date_freshness_score=data.get("no_date_freshness_score", 0.1),
            )

            logger.info("加载评分器配置完成")

        except Exception as e:
            logger.error(f"加载 scorer-config.yaml 失败 error={e}，使用默认配置")
            self._scorer_config = ScorerConfig()

    def get_scorer_config(self) -> ScorerConfig:
        """
        获取评分器配置。

        如果未加载，先加载。如果加载失败，返回默认配置。

        Returns:
            ScorerConfig 对象
        """
        if self._scorer_config is None:
            self._load_scorer_config()

        if self._scorer_config is None:
            self._scorer_config = ScorerConfig()

        return self._scorer_config

    def _load_router_config(self) -> None:
        """
        加载路由器配置（router-config.yaml）。

        如果文件不存在或解析失败，使用默认配置（enabled=False）。
        """
        if not self.router_config_file.exists():
            logger.info("router-config.yaml 不存在，使用默认路由器配置 (disabled)")
            self._router_config = RouterConfig()
            return

        try:
            with open(self.router_config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                logger.warning("router-config.yaml 为空或格式无效，使用默认配置")
                self._router_config = RouterConfig()
                return

            # 解析自适应路由器配置
            adaptive = data.get("adaptive_router", {})
            if not isinstance(adaptive, dict):
                adaptive = {}

            # 评分权重
            scoring = adaptive.get("scoring", {})
            if not isinstance(scoring, dict):
                scoring = {}

            # 持久化配置
            persistence = adaptive.get("persistence", {})
            if not isinstance(persistence, dict):
                persistence = {}

            self._router_config = RouterConfig(
                enabled=adaptive.get("enabled", False),
                max_providers=adaptive.get("max_providers", 3),
                min_history=adaptive.get("min_history", 5),
                default_strategy=adaptive.get("default_strategy", "parallel"),
                success_weight=scoring.get("success_weight", 0.5),
                latency_weight=scoring.get("latency_weight", 0.3),
                llm_score_weight=scoring.get("llm_score_weight", 0.2),
                persistence_enabled=persistence.get("enabled", True),
                persistence_file=persistence.get("file", "_runtime/router-perf.json"),
            )

            logger.info(f"加载路由器配置完成 enabled={self._router_config.enabled}")

        except Exception as e:
            logger.error(f"加载 router-config.yaml 失败 error={e}，使用默认配置")
            self._router_config = RouterConfig()

    def get_router_config(self) -> RouterConfig:
        """
        获取路由器配置。

        如果未加载，先加载。如果加载失败，返回默认配置（disabled）。

        Returns:
            RouterConfig 对象
        """
        if self._router_config is None:
            self._load_router_config()

        if self._router_config is None:
            self._router_config = RouterConfig()

        return self._router_config

    def get_fallback_config(self) -> FallbackChainConfig:
        """
        获取 fallback 链配置

        Returns:
            FallbackChainConfig 对象
        """
        if self._fallback_config is None:
            self.load_all()

        # 如果加载失败，返回默认配置
        if self._fallback_config is None:
            self._fallback_config = FallbackChainConfig(
                chain=["minimax", "tavily", "brave", "web_fetch"],
                trigger_on_status=[ResultStatus.ALL_FAILED, ResultStatus.ERROR, ResultStatus.NO_MATCH],
                max_depth=3,
            )

        return self._fallback_config


__all__ = ["ConfigLoader"]
