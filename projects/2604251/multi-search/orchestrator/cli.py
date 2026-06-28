"""
orchestrator/cli.py

CLI 入口模块。

本模块负责：
- 提供命令行接口（search, probe, list-intents, list-providers）
- 解析命令行参数
- 格式化输出结果
"""

import asyncio
import json
import sys
from typing import Optional, List
import logging

from .schema import SearchRequest
from .config import ConfigLoader
from .engine import SearchEngine

logger = logging.getLogger("orchestrator.cli")


class CLI:
    """
    命令行接口

    提供四个主要命令：
    - search: 执行搜索
    - probe: 探测环境
    - list-intents: 列出所有意图模式
    - list-providers: 列出所有 provider
    """

    def __init__(self):
        """初始化 CLI"""
        self.config_loader = ConfigLoader()
        self.config_loader.load_all()

    async def search(
        self,
        query: str,
        intent: Optional[str] = None,
        num_results: int = 10,
        parallel: bool = True,
        max_providers: int = 3,
        output_format: str = "json",
    ) -> None:
        """
        执行搜索命令

        Args:
            query: 搜索查询
            intent: 用户意图（可选）
            num_results: 期望结果数量
            parallel: 是否并行执行
            max_providers: 最大 provider 数量
            output_format: 输出格式（json, pretty）
        """
        # 创建搜索请求
        request = SearchRequest(
            query=query,
            intent=intent,
            num_results=num_results,
        )

        # 创建搜索引擎
        engine = SearchEngine(config_loader=self.config_loader)

        try:
            # 执行搜索
            result = await engine.search(
                request=request,
                parallel=parallel,
                max_providers=max_providers,
            )

            # 格式化输出
            if output_format == "json":
                self._print_json(result)
            else:
                self._print_pretty(result)

        finally:
            # 清理资源
            await engine.close()

    async def probe(self) -> None:
        """
        探测环境命令

        检查所有 provider 的可用性和健康状态
        """
        print("=== 环境探测 ===\n")

        # 列出所有 provider
        providers = self.config_loader.list_providers(enabled_only=True)

        if not providers:
            print("没有启用的 provider")
            return

        print(f"发现 {len(providers)} 个启用的 provider:\n")

        for provider in providers:
            print(f"Provider: {provider.display_name} ({provider.name})")
            print(f"  类型: {provider.type.value}")
            print(f"  MCP 服务器: {provider.mcp_server or 'N/A'}")
            print(f"  MCP 工具: {provider.mcp_tool_name or 'N/A'}")
            print(f"  配额限制: {provider.quota_limit or '无限制'}/{provider.quota_window}s")
            print(f"  超时: {provider.timeout}s")
            print()

    def list_intents(self) -> None:
        """
        列出所有意图模式命令
        """
        print("=== 意图模式列表 ===\n")

        intent_modes = self.config_loader.list_intent_modes()

        if not intent_modes:
            print("没有配置意图模式")
            return

        for mode in intent_modes:
            print(f"意图: {mode.intent}")
            print(f"  查询策略: {mode.query_strategy}")
            print(f"  缓存 TTL: {mode.cache_ttl}s")
            print(f"  首选 Provider: {', '.join(mode.preferred_providers)}")
            print(f"  启用 Fallback: {mode.enable_fallback}")
            print()

    def list_providers(self) -> None:
        """
        列出所有 provider 命令
        """
        print("=== Provider 列表 ===\n")

        providers = self.config_loader.list_providers(enabled_only=False)

        if not providers:
            print("没有配置 provider")
            return

        for provider in providers:
            status = "✓" if provider.enabled else "✗"
            print(f"{status} {provider.display_name} ({provider.name})")
            print(f"  类型: {provider.type.value}")
            print(f"  状态: {'启用' if provider.enabled else '禁用'}")

            if provider.mcp_server:
                print(f"  MCP 服务器: {provider.mcp_server}")
                print(f"  MCP 工具: {provider.mcp_tool_name or 'N/A'}")

            if provider.http_endpoint:
                print(f"  HTTP 端点: {provider.http_endpoint}")

            print()

    async def status(self) -> None:
        """
        查看性能监控状态命令

        输出 provider 性能统计、缓存命中率、配额状态和路由器状态。
        """
        print("=== 性能监控状态 ===\n")

        # 创建临时引擎获取性能数据
        engine = SearchEngine(config_loader=self.config_loader)
        try:
            stats = engine.get_stats()
        finally:
            await engine.close()

        # Phase 2 R3: 打印 Adaptive Router 状态
        print("Adaptive Router:")
        router = engine.router
        if router:
            cfg = router.config
            print(f"  enabled: {cfg.enabled}")
            report = router.get_performance_report()
            print(f"  data points: {report['data_points']}")

            if report["providers"]:
                print("  Provider Performance:")
                for name, pdata in sorted(report["providers"].items()):
                    calls = pdata["total_calls"]
                    succ = pdata["success_calls"]
                    rate = f"{succ}/{calls}({pdata['success_rate']*100:.0f}%)" if calls else "-"
                    avg_lat = f"{pdata['avg_latency_ms']:.0f}ms" if calls else "-"
                    print(f"    {name:<10} calls={calls} success={rate} avg_latency={avg_lat}")
            else:
                print("  暂无数据")
        else:
            print("  未初始化")
        print()

        # 打印 Provider 统计
        print("Provider:")
        providers = stats.get("providers", {})
        if not providers:
            print("  暂无数据")
        else:
            for name, pdata in sorted(providers.items()):
                avg_ms = pdata.get("avg_latency_ms", 0)
                min_ms = pdata.get("min_ms", 0)
                max_ms = pdata.get("max_ms", 0)
                avg_txt = f"{avg_ms:.0f}" if avg_ms else "-"
                min_txt = f"{min_ms:.0f}" if min_ms else "-"
                max_txt = f"{max_ms:.0f}" if max_ms else "-"
                print(
                    f"  {name:<10} calls={pdata.get('calls', 0)} "
                    f"success={pdata.get('success', 0)} "
                    f"fail={pdata.get('fail', 0)} "
                    f"avg_latency={avg_txt}ms "
                    f"min={min_txt}ms "
                    f"max={max_txt}ms"
                )

        # 打印缓存统计
        print("\nCache:")
        cache = stats.get("cache", {})
        hits = cache.get("hits", 0)
        misses = cache.get("misses", 0)
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0.0
        print(
            f"  hit_rate: {hit_rate:.2f} "
            f"(hits={hits}, misses={misses})"
        )
        print(f"  size: {cache.get('size', 0)} entries")

        # 打印配额统计
        print("\nQuota:")
        quota = stats.get("quota", {})
        if not quota:
            print("  无配额限制")
        else:
            for name, qdata in sorted(quota.items()):
                remaining = qdata.get("remaining", 0)
                reset_in = qdata.get("reset_in", 0)
                print(
                    f"  {name:<10} remaining={remaining} "
                    f"(reset in {reset_in:.0f}s)"
                )
        print()

    def _print_json(self, result) -> None:
        """
        打印 JSON 格式结果

        Args:
            result: 搜索结果
        """
        # 转换为字典
        result_dict = {
            "version": result.version,
            "status": result.status.value,
            "error": result.error,
            "provider": result.provider,
            "query": result.query,
            "original_query": result.original_query,
            "total_results": result.total_results,
            "response_time": result.response_time,
            "cached": result.cached,
            "fallback_triggered": result.fallback_triggered,
            "fallback_chain": result.fallback_chain,
            "items": [
                {
                    "title": item.title,
                    "url": item.url,
                    "snippet": item.snippet,
                    "score": item.score,
                    "source": item.source,
                }
                for item in result.items
            ],
            "metadata": result.metadata,
        }

        # 打印 JSON
        json_str = json.dumps(result_dict, ensure_ascii=False, indent=2)
        print(json_str)

    def _print_pretty(self, result) -> None:
        """
        打印易读格式结果

        Args:
            result: 搜索结果
        """
        print(f"\n=== 搜索结果 ===")
        print(f"查询: {result.query}")
        print(f"Provider: {result.provider}")
        print(f"状态: {result.status.value}")
        print(f"结果数: {len(result.items)}")
        print(f"响应时间: {result.response_time:.2f}s")

        if result.fallback_triggered:
            print(f"Fallback 链: {' → '.join(result.fallback_chain)}")

        if result.error:
            print(f"错误: {result.error}")

        print(f"\n结果列表:")

        for idx, item in enumerate(result.items, 1):
            print(f"\n{idx}. {item.title}")
            print(f"   URL: {item.url}")
            print(f"   摘要: {item.snippet}")
            print(f"   来源: {item.source}")


async def main_async():
    """异步主函数"""
    # 解析命令行参数
    args = sys.argv[1:]

    if not args:
        print("用法: python -m orchestrator.cli <command> [args...]")
        print("\n命令:")
        print("  search <query>      执行搜索")
        print("  probe               探测环境")
        print("  status              查看性能状态")
        print("  list-intents        列出所有意图模式")
        print("  list-providers      列出所有 provider")
        sys.exit(1)

    command = args[0]

    # 创建 CLI 实例
    cli = CLI()

    # 执行命令
    if command == "search":
        if len(args) < 2:
            print("错误: search 命令需要查询参数")
            sys.exit(1)

        query = args[1]

        # 解析可选参数
        intent = None
        num_results = 10
        parallel = True
        max_providers = 3
        output_format = "json"

        i = 2
        while i < len(args):
            if args[i] == "--intent" and i + 1 < len(args):
                intent = args[i + 1]
                i += 2
            elif args[i] == "--num-results" and i + 1 < len(args):
                num_results = int(args[i + 1])
                i += 2
            elif args[i] == "--serial":
                parallel = False
                i += 1
            elif args[i] == "--max-providers" and i + 1 < len(args):
                max_providers = int(args[i + 1])
                i += 2
            elif args[i] == "--pretty":
                output_format = "pretty"
                i += 1
            else:
                i += 1

        # 执行搜索
        await cli.search(
            query=query,
            intent=intent,
            num_results=num_results,
            parallel=parallel,
            max_providers=max_providers,
            output_format=output_format,
        )

    elif command == "probe":
        await cli.probe()

    elif command == "list-intents":
        cli.list_intents()

    elif command == "list-providers":
        cli.list_providers()

    elif command == "status":
        await cli.status()

    else:
        print(f"未知命令: {command}")
        sys.exit(1)


def main():
    """主函数（入口点）"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
