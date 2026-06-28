"""
orchestrator/mcp_client.py

MCP 客户端模块。

本模块负责：
- 定义 MCPClient 抽象基类
- 实现 McporterMCPClient（通过 mcporter CLI 子进程调用 MCP 工具）
- 提供统一的 MCP 工具调用接口

mcporter 版本：0.7.3（CLI 子进程通信，非 HTTP API）
"""

import asyncio
import json
import shlex
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger("orchestrator.mcp_client")


class MCPClient(ABC):
    """
    MCP 客户端抽象基类。
    所有 MCP 客户端必须实现此接口。
    """

    @abstractmethod
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        调用 MCP 工具。

        Args:
            server_name: MCP 服务器名称
            tool_name: 工具名称
            arguments: 工具参数字典
            timeout: 超时时间（秒）

        Returns:
            工具调用结果（字典格式，包含 content 和 isError 等字段）

        Raises:
            Exception: 调用失败时抛出异常
        """
        ...

    @abstractmethod
    async def list_tools(self, server_name: str, timeout: float = 10.0) -> list:
        """
        列出 MCP 服务器的所有工具。

        Args:
            server_name: MCP 服务器名称
            timeout: 超时时间（秒）

        Returns:
            工具列表，每项包含 name、description、inputSchema

        Raises:
            Exception: 调用失败时抛出异常
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """
        检查 MCP 客户端是否可用。

        Returns:
            True 可用，False 不可用
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """释放资源（子进程、网络连接等）"""
        ...


class McporterMCPClient(MCPClient):
    """
    Mcporter MCP 客户端实现（mcporter 0.7.3+）。

    通过 mcporter CLI 子进程调用 MCP 工具：
    - mcporter list <server> --json → 获取工具列表
    - mcporter call <server>.<tool> key=value → 调用工具

    不依赖 HTTP API（mcporter 0.7.3 无 HTTP 服务端）。
    """

    def __init__(self, mcporter_path: str = "mcporter", simulate: bool = False):
        """
        Args:
            mcporter_path: mcporter 可执行文件路径，默认从 PATH 查找
            simulate: 是否强制模拟模式（不调用真实 mcporter）
        """
        self.mcporter_path = mcporter_path
        self.simulate = simulate
        self._available_cache: Optional[bool] = None
        self._available_cache_time: float = 0.0

        logger.debug(
            f"McporterMCPClient 初始化，mcporter_path={mcporter_path}, simulate={simulate}"
        )

    async def is_available(self) -> bool:
        """
        检查 mcporter 是否可用。
        通过运行 'mcporter list' 快速检查。结果缓存 60 秒。
        """
        if self.simulate:
            return False

        # 缓存判断：60 秒内复用
        import time
        now = time.monotonic()
        if self._available_cache is not None and (now - self._available_cache_time) < 60:
            return self._available_cache

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    self.mcporter_path,
                    "list",
                    "--json",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ),
                timeout=10.0,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.debug(f"mcporter 不可用 returncode={proc.returncode}")
                self._available_cache = False
                self._available_cache_time = time.monotonic()
                return False

            # 尝试解析 JSON，确认 mcporter 返回有效数据
            try:
                data = json.loads(stdout)
                self._available_cache = True
            except (json.JSONDecodeError, TypeError):
                self._available_cache = False

            self._available_cache_time = time.monotonic()
            logger.debug(f"mcporter 可用性: {self._available_cache}")
            return self._available_cache

        except (FileNotFoundError, subprocess.SubprocessError, asyncio.TimeoutError) as e:
            logger.debug(f"mcporter 不可用 error={e}")
            self._available_cache = False
            self._available_cache_time = time.monotonic()
            return False

    async def list_tools(self, server_name: str, timeout: float = 10.0) -> list:
        """
        通过 mcporter list <server> --json 获取工具列表。

        返回 [{name, description, inputSchema}, ...]
        """
        if self.simulate or not await self.is_available():
            return await self._simulate_list_tools(server_name)

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    self.mcporter_path,
                    "list",
                    server_name,
                    "--json",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ),
                timeout=timeout,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                err_text = stderr.decode("utf-8", errors="replace").strip()
                raise Exception(
                    f"mcporter list 失败（exit={proc.returncode}）: {err_text}"
                )

            data = json.loads(stdout)
            # mcporter --json 返回 {"mode": "server", "tools": [...]}
            tools = data.get("tools", [])
            logger.debug(
                f"列出 MCP 工具成功: server={server_name}, 工具数量={len(tools)}"
            )
            return tools

        except FileNotFoundError:
            raise Exception(f"未找到 mcporter（{self.mcporter_path}），请确认已安装")
        except json.JSONDecodeError as e:
            raise Exception(f"mcporter list 输出解析失败: {e}")
        except asyncio.TimeoutError:
            raise Exception(f"mcporter list 超时: server={server_name}")

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        通过 mcporter call <server>.<tool> key=value 调用 MCP 工具。

        mcporter call 的输出是 MCP tool 返回的纯文本内容（非 JSON）。
        我们会将其包装为标准格式 {content, isError}。
        """
        if self.simulate or not await self.is_available():
            logger.warning(
                f"Mcporter 不可用，使用模拟模式调用: {server_name}.{tool_name}"
            )
            return await self._simulate_call(server_name, tool_name, arguments)

        # 构造参数列表：mcporter call <server>.<tool> key1=value1 key2=value2
        selector = f"{server_name}.{tool_name}"
        cmd_args = [self.mcporter_path, "call", selector]
        for key, value in arguments.items():
            # mcporter call 参数使用 key=value 格式
            # 需要 shell 安全的引号处理
            if value is None:
                continue
            str_val = str(value)
            # 如果包含空格或特殊字符，加引号
            if " " in str_val or '"' in str_val or "'" in str_val:
                cmd_args.append(f"{key}={shlex.quote(str_val)}")
            else:
                cmd_args.append(f"{key}={str_val}")

        logger.debug(f"调用 MCP 工具: {selector}, args={arguments}")

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ),
                timeout=timeout,
            )
            stdout, stderr = await proc.communicate()

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0:
                # mcporter call 返回非 0 时，stderr 通常包含错误信息
                err_msg = stderr_str or f"exit code {proc.returncode}"
                logger.warning(f"MCP 工具调用失败: {selector}, {err_msg}")

                # 判断是否配额耗尽
                if "quota" in err_msg.lower() or "usage limit" in err_msg.lower():
                    raise Exception(f"quota_exhausted: {err_msg}")
                elif "timeout" in err_msg.lower():
                    raise Exception(f"timeout: {err_msg}")
                else:
                    raise Exception(f"call_failed: {err_msg}")

            # mcporter 将工具输出返回为纯文本
            # 尝试解析 JSON（如果工具返回了 JSON），否则保留文本
            content_text = stdout_str.strip()
            try:
                parsed = json.loads(content_text)
                return {"content": [{"type": "text", "text": json.dumps(parsed)}], "isError": False}
            except (json.JSONDecodeError, TypeError):
                return {"content": [{"type": "text", "text": content_text}], "isError": False}

        except asyncio.TimeoutError:
            err_msg = f"MCP 工具调用超时: {selector}（{timeout}s）"
            logger.error(err_msg)
            raise Exception(f"timeout: {err_msg}")

        except FileNotFoundError:
            raise Exception(f"未找到 mcporter（{self.mcporter_path}），请确认已安装")

    async def close(self) -> None:
        """McporterMCPClient 不需要特殊清理，pass"""
        logger.debug("McporterMCPClient 关闭")
        pass

    # ------------------------------------------------------------------ #
    #  模拟模式（mock data，用于开发和演示）
    # ------------------------------------------------------------------ #

    async def _simulate_call(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """模拟 MCP 工具调用。"""
        await asyncio.sleep(0.1)
        query = arguments.get("query", arguments.get("q", "unknown"))

        if server_name == "minimax":
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "organic": [
                            {
                                "title": f"[模拟] MiniMax 结果 1 - {query}",
                                "link": "https://example.com/mm1",
                                "snippet": "MiniMax 模拟搜索结果",
                                "date": "2026-06-06",
                            },
                            {
                                "title": f"[模拟] MiniMax 结果 2 - {query}",
                                "link": "https://example.com/mm2",
                                "snippet": "MiniMax 另一个搜索结果",
                                "date": "2026-06-05",
                            },
                        ]
                    }),
                }],
                "isError": False,
            }
        elif server_name == "tavily":
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "results": [
                            {
                                "title": f"[模拟] Tavily 结果 - {query}",
                                "url": "https://example.com/tavily1",
                                "content": "Tavily 模拟搜索结果",
                                "publishedDate": "2026-06-04",
                                "score": 0.95,
                            },
                        ]
                    }),
                }],
                "isError": False,
            }
        elif server_name == "brave":
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "web": {
                            "results": [
                                {
                                    "title": f"[模拟] Brave 结果 - {query}",
                                    "url": "https://example.com/brave1",
                                    "description": "Brave 模拟搜索结果",
                                    "age": "1d",
                                },
                            ]
                        }
                    }),
                }],
                "isError": False,
            }
        elif server_name == "exa":
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "results": [
                            {
                                "title": f"[模拟] Exa 结果 - {query}",
                                "url": "https://example.com/exa1",
                                "snippet": "Exa 模拟搜索结果",
                                "published_date": "2026-06-03",
                            },
                        ]
                    }),
                }],
                "isError": False,
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "result": f"[模拟] {server_name}.{tool_name} 调用结果"
                    }),
                }],
                "isError": False,
            }

    async def _simulate_list_tools(self, server_name: str) -> list:
        """模拟工具列表。"""
        await asyncio.sleep(0.1)

        tools_map = {
            "minimax": [
                {"name": "web_search", "description": "搜索网页", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}},
            ],
            "tavily": [
                {"name": "search", "description": "搜索网页", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}},
            ],
            "brave": [
                {"name": "search", "description": "Brave 搜索", "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}}}},
            ],
            "exa": [
                {"name": "web_search_exa", "description": "Exa 搜索", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}},
            ],
        }
        return tools_map.get(server_name, [{"name": "example_tool", "description": "模拟工具", "inputSchema": {}}])


# ------------------------------------------------------------------ #
#  模块导出
# ------------------------------------------------------------------ #

__all__ = ["MCPClient", "McporterMCPClient"]
