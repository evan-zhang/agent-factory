"""
orchestrator/router.py

Adaptive Provider Router (Phase 2 R3)。

核心职责：
  根据历史成功率 + 延迟 + LLM provider_scores 动态选择最优 provider 组合。
  替代静态的 preferred_providers 固定列表。

架构：
  engine._get_providers()
    ↓ (enabled)
  AdaptiveRouter.select_providers()
    ↓
  RoutingDecision(selected_providers, rationale, round_strategy)

数据流：
  _execute_single_provider() 调用完成后
    ↓
  engine 调用 AdaptiveRouter.record_result()
    ↓
  写入 _runtime/router-perf.json（portalocker 文件锁）
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import portalocker

from .schema import (
    ProviderConfig,
    ProviderPerformance,
    RouterConfig,
    RoutingDecision,
)

logger = logging.getLogger("orchestrator.router")


class AdaptiveRouter:
    """
    自适应 provider 路由。

    根据历史表现 + 当前配额 + 意图选择最优 provider 组合。
    同时支持静态回退（无历史数据时使用默认配置）。
    """

    def __init__(self, config: RouterConfig, runtime_dir: Optional[Path] = None):
        """
        初始化自适应路由器。

        Args:
            config: 路由器配置
            runtime_dir: 运行时目录（存储持久化文件），默认自动检测 config.py 同级
        """
        self.config = config

        if runtime_dir is None:
            current_file = Path(__file__)
            self._runtime_dir = current_file.parent / "_runtime"
        else:
            self._runtime_dir = Path(runtime_dir)

        self._runtime_dir.mkdir(parents=True, exist_ok=True)

        # provider 性能数据（按 (provider, intent) 索引）
        # key: f"{provider}:{intent}" → ProviderPerformance
        self._perf: Dict[str, ProviderPerformance] = {}

        self._load_perf_data()

        logger.debug(
            f"AdaptiveRouter 初始化完成 "
            f"enabled={config.enabled} "
            f"persistence_file={self._perf_file}"
        )

    # ────────────────────────────────────────────────────────
    # 公开接口
    # ────────────────────────────────────────────────────────

    def select_providers(
        self,
        intent: str,
        available_providers: List[ProviderConfig],
        llm_scores: Optional[Dict[str, float]] = None,
    ) -> RoutingDecision:
        """
        根据历史表现 + 意图 + 配额选择 provider。

        选择流程：
        1. 从 available_providers 中剔除不健康的
        2. 按综合得分排序（若有 LLM provider_scores，则作为权重）
        3. 取 top N（由 config.max_providers 决定）
        4. 如果没有任何历史数据，回退到原始顺序

        这是纯计算操作（读内存数据），不需要异步。

        Args:
            intent: 意图类型
            available_providers: 可用的 provider 列表
            llm_scores: LLM 提供的 provider 评分（可选）

        Returns:
            路由决策
        """
        if not self.config.enabled:
            return self._static_fallback(available_providers, intent)

        # 1. 过滤不健康 provider（无历史数据的不算不健康）
        healthy_providers = [p for p in available_providers if p.enabled]

        if not healthy_providers:
            return self._static_fallback(available_providers, intent)

        # 2. 检查是否有足够的历史数据
        total_history_calls = 0
        has_history = False
        for p in healthy_providers:
            key = f"{p.name}:{intent}"
            perf = self._perf.get(key)
            if perf:
                has_history = True
                total_history_calls += perf.total_calls

        if not has_history or total_history_calls < self.config.min_history:
            logger.debug(
                f"历史数据不足 ({total_history_calls}/{self.config.min_history})，"
                f"使用静态回退 intent={intent}"
            )
            return self._static_fallback(healthy_providers, intent)

        # 3. 按综合得分排序
        scored = []
        for provider in healthy_providers:
            perf = self._perf.get(f"{provider.name}:{intent}")
            score = self._compute_score(perf, provider.name, intent, llm_scores)
            scored.append((provider.name, score))

        # 4. 按得分降序排列
        scored.sort(key=lambda x: x[1], reverse=True)

        # 5. 取 top N
        selected = [name for name, _ in scored[:self.config.max_providers]]

        # 6. 构建 rationale
        score_details = "; ".join(
            f"{name}={score:.3f}" for name, score in scored[:self.config.max_providers]
        )
        rationale = (
            f"自适应路由: intent={intent} "
            f"total_history={total_history_calls} "
            f"top_scores=[{score_details}]"
        )

        logger.info(rationale)

        return RoutingDecision(
            selected_providers=selected,
            rationale=rationale,
            round_strategy=self.config.default_strategy,
        )

    def record_result(
        self,
        provider: str,
        intent: str,
        success: bool,
        latency_ms: float,
    ) -> None:
        """
        记录一次调用的性能数据。

        Args:
            provider: Provider 名称
            intent: 意图类型
            success: 是否成功
            latency_ms: 延迟（毫秒）
        """
        if not self.config.enabled:
            return

        key = f"{provider}:{intent}"
        perf = self._perf.get(key)

        if perf is None:
            perf = ProviderPerformance(
                provider=provider,
                intent=intent,
            )
            self._perf[key] = perf

        perf.total_calls += 1
        if success:
            perf.success_calls += 1
        perf.total_latency_ms += latency_ms
        perf.last_call_time = time.time()

        logger.debug(
            f"记录性能数据 provider={provider} "
            f"intent={intent} "
            f"success={success} "
            f"latency_ms={latency_ms:.0f} "
            f"total_calls={perf.total_calls} "
            f"success_rate={perf.success_rate:.2f}"
        )

        # 持久化
        self._save_perf_data()

    def get_performance_report(self) -> Dict:
        """
        获取性能报告（用于 CLI status 命令）。

        Returns:
            {
                "enabled": bool,
                "data_points": int,
                "providers": { provider_name: ProviderPerformance dict, ... }
            }
        """
        report = {
            "enabled": self.config.enabled,
            "data_points": len(self._perf),
            "providers": {},
        }

        for key, perf in self._perf.items():
            provider_name = perf.provider
            if provider_name not in report["providers"]:
                report["providers"][provider_name] = {
                    "name": provider_name,
                    "total_calls": 0,
                    "success_calls": 0,
                    "fail_calls": 0,
                    "total_latency_ms": 0.0,
                    "avg_latency_ms": 0.0,
                    "success_rate": 0.0,
                    "by_intent": {},
                }
            pdata = report["providers"][provider_name]
            pdata["total_calls"] += perf.total_calls
            pdata["success_calls"] += perf.success_calls
            pdata["fail_calls"] += perf.total_calls - perf.success_calls
            pdata["total_latency_ms"] += perf.total_latency_ms
            if pdata["total_calls"] > 0:
                pdata["avg_latency_ms"] = pdata["total_latency_ms"] / pdata["total_calls"]
                pdata["success_rate"] = pdata["success_calls"] / pdata["total_calls"]
            pdata["by_intent"][perf.intent] = {
                "total_calls": perf.total_calls,
                "success_calls": perf.success_calls,
                "avg_latency_ms": perf.avg_latency_ms,
                "success_rate": perf.success_rate,
            }

        return report

    # ────────────────────────────────────────────────────────
    # 内部方法
    # ────────────────────────────────────────────────────────

    def _compute_score(
        self,
        perf: Optional[ProviderPerformance],
        provider_name: str,
        intent: str,
        llm_scores: Optional[Dict[str, float]],
    ) -> float:
        """
        计算 provider 的综合得分。

        score = success_rate × success_weight + (1000 / avg_latency_ms) × latency_weight
               + llm_score × llm_score_weight

        Args:
            perf: Provider 性能数据（None = 无历史数据）
            provider_name: Provider 名称
            intent: 意图类型
            llm_scores: LLM 评分映射

        Returns:
            综合得分
        """
        score = 0.0

        # 成功率得分
        if perf and perf.total_calls > 0:
            success_component = perf.success_rate * self.config.success_weight
            score += success_component

            # 延迟得分（将延迟映射到 0-1 区间：1000ms 延迟 = 1.0 分）
            if perf.avg_latency_ms > 0:
                latency_score = 1000.0 / (perf.avg_latency_ms + 1)
                latency_component = min(1.0, latency_score) * self.config.latency_weight
                score += latency_component

        # LLM provider_score
        if llm_scores and provider_name in llm_scores:
            llm_score = max(0.0, min(1.0, llm_scores[provider_name]))
            score += llm_score * self.config.llm_score_weight

        return score

    def _static_fallback(
        self,
        available_providers: List[ProviderConfig],
        intent: str,
    ) -> RoutingDecision:
        """
        静态回退：按原始顺序取前 N 个 provider。

        Args:
            available_providers: 可用的 provider 列表
            intent: 意图类型（用于日志）

        Returns:
            路由决策
        """
        selected = [p.name for p in available_providers[:self.config.max_providers]]

        ratio = f"enabled={len(available_providers)} selected={len(selected)}"
        logger.debug(f"静态回退路由 intent={intent} {ratio}")

        return RoutingDecision(
            selected_providers=selected,
            rationale=f"静态回退 (intent={intent})",
            round_strategy=self.config.default_strategy,
        )

    # ────────────────────────────────────────────────────────
    # 持久化
    # ────────────────────────────────────────────────────────

    @property
    def _perf_file(self) -> Path:
        """返回性能数据文件的路径。"""
        if os.path.isabs(self.config.persistence_file):
            return Path(self.config.persistence_file)
        return self._runtime_dir / self.config.persistence_file

    def _load_perf_data(self) -> None:
        """
        从文件加载持久化的性能数据。

        格式：{ "provider:intent": { ... ProviderPerformance fields ... } }
        """
        if not self.config.persistence_enabled:
            return

        perf_file = self._perf_file
        if not perf_file.exists():
            logger.debug(f"性能数据文件不存在 path={perf_file}")
            return

        try:
            with open(perf_file, "r", encoding="utf-8") as f:
                portalocker.lock(f, portalocker.LOCK_SH)
                data = json.load(f)
                portalocker.unlock(f)

            for key, entry in data.items():
                self._perf[key] = ProviderPerformance(
                    provider=entry.get("provider", key.split(":")[0]),
                    intent=entry.get("intent", key.split(":")[1] if ":" in key else "general"),
                    total_calls=entry.get("total_calls", 0),
                    success_calls=entry.get("success_calls", 0),
                    total_latency_ms=entry.get("total_latency_ms", 0.0),
                    last_call_time=entry.get("last_call_time", 0.0),
                )

            logger.debug(f"加载性能数据完成 entries={len(data)} file={perf_file}")

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"解析性能数据失败 path={perf_file} error={e}")

    def _save_perf_data(self) -> None:
        """
        将性能数据写入持久化文件。

        使用 portalocker 做文件锁，原子写入（临时文件 + rename）。
        """
        if not self.config.persistence_enabled:
            return

        perf_file = self._perf_file

        try:
            # 构建序列化数据
            data = {}
            for key, perf in self._perf.items():
                data[key] = {
                    "provider": perf.provider,
                    "intent": perf.intent,
                    "total_calls": perf.total_calls,
                    "success_calls": perf.success_calls,
                    "total_latency_ms": perf.total_latency_ms,
                    "last_call_time": perf.last_call_time,
                }

            # 写入临时文件（原子替换）
            temp_file = perf_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                json.dump(data, f, indent=2, ensure_ascii=False)
                portalocker.unlock(f)

            # 原子替换
            if perf_file.exists():
                os.replace(temp_file, perf_file)
            else:
                perf_file.parent.mkdir(parents=True, exist_ok=True)
                perf_file.write_text(temp_file.read_text(encoding="utf-8"))
                temp_file.unlink()

            logger.debug(f"保存性能数据完成 entries={len(data)}")

        except Exception as e:
            logger.error(f"保存性能数据失败 error={e}")


__all__ = ["AdaptiveRouter"]
