# BATTLE-R3 — 代码审查缺口补全（Gap Resolution）

**审查者**：Code Review（第三方代码审查）
**补全者**：Executor（方案执行者）
**补全标的**：BATTLE-R2-EXECUTOR.md（最终完整版设计）
**目的**：将 BATTLE-R3 发现的 5 个信息缺口 + 3 个改进建议全部补全，使方案可编码性从 7.5→8.5+/10

**生效方式**：本文档作为 BATTLE-R2-EXECUTOR.md 的补充和修订。与 R2 设计不一致处，以本文档为准。

---

## Gap 1：重试策略（P1，补全后 engine.py 可开工）

### 问题

Provider YAML 中定义了 `call.retry: 2`，但没有说明：
- 什么情况下重试？
- 重试次数 `2` 的含义（最多 2 次还是重试 2 次）？
- 退避策略？
- 哪些异常不可重试？

### 补全方案

**重试条件判定矩阵：**

| 失败原因 | 可重试？ | 理由 |
|----------|---------|------|
| timeout | ✅ 可重试 | 网络问题，下次可能成功 |
| exception（连接错误/HTTP 5xx） | ✅ 可重试 | 服务端临时故障 |
| quota_exhausted | ❌ 不可重试 | 配额耗尽重试无意义，应跳过 |
| api_key_invalid | ❌ 不可重试 | 配置错误，重试一百次一样失败 |
| no_match（0 结果） | ❌ 不可重试 | 提供商正常返回无结果，重试结果不变 |

**`retry` 字段含义：**

```yaml
# Provider YAML
call:
  retry: 2    # 最多 retry+1 次尝试，失败后补偿重试 1 次
```

```
retry: 0 → 不重试，最多 1 次调用
retry: 1 → 失败后重试 1 次，最多 2 次调用
retry: 2 → 失败后重试 2 次，最多 3 次调用
```

**退避策略：**

```python
# 退避策略：固定 1s 间隔（v1.0 简化版，不引入指数退避）
async def call_with_retry(provider, query):
    max_attempts = provider.retry + 1
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = await call_provider(provider, query)
            return result
        except RetryableError as e:
            last_exception = e
            if attempt < max_attempts:
                await asyncio.sleep(1)  # 固定 1s 间隔
                continue
        except NonRetryableError as e:
            last_exception = e
            break  # 不可重试，立即退出

    # 全部失败
    return MCPToolResult(success=False, error=str(last_exception))
```

- **v1.0 使用固定 1s 间隔**，不引入指数退避/抖动
- 如果将来需要更复杂的退避，可以配置在 Provider YAML 中

**代码中的异常分类：**

```python
class RetryableError(Exception):
    """可重试的异常（超时、连接错误、5xx）"""
    pass

class NonRetryableError(Exception):
    """不可重试的异常（配额耗尽、API Key 无效、参数错误、4xx）"""
    pass
```

**`McporterMCPClient` 调用中的异常处理：**

```python
async def call_tool(self, tool_name, arguments, timeout_ms=30000):
    try:
        resp = await asyncio.wait_for(
            self._make_http_request(tool_name, arguments),
            timeout=timeout_ms / 1000
        )
        if resp.status == 200:
            return MCPToolResult(success=True, data=resp.json(), latency_ms=...)
        elif resp.status in (502, 503, 504):
            raise RetryableError(f"mcporter HTTP {resp.status}")
        elif resp.status == 429:
            raise NonRetryableError("quota_exhausted")
        elif resp.status in (400, 401, 403, 404):
            raise NonRetryableError(f"mcporter HTTP {resp.status}")
        else:
            raise RetryableError(f"mcporter HTTP {resp.status}")
    except asyncio.TimeoutError:
        raise RetryableError("timeout")
    except aiohttp.ClientError as e:
        raise RetryableError(f"connection error: {e}")
```

---

## Gap 2：异常捕获策略（P1，补全后 engine.py 可开工）

### 问题

并行调用多个 provider 时，单个 provider 的异常如何影响整个搜索过程没有定义。

### 补全方案

**原则：异常隔离 + 独立上报**

每个 provider 调用的异常相互隔离，不影响其他 provider 的执行。单个 provider 的异常记录在 `metadata.engines_failed` 中，继续执行其他 provider。

**并行调用的完整实现逻辑：**

```python
async def execute_parallel(providers, query, global_timeout_ms=15000):
    """
    并行调用多个 provider。
    - 每个 provider 独立 try-except，互不影响
    - 全局超时管理
    - 异常记录在 engines_failed 中
    """
    tasks = []
    for provider in providers:
        task = asyncio.create_task(
            call_with_retry(provider, query)
        )
        tasks.append((provider.name, task))

    # 全局超时
    done, pending = await asyncio.wait(
        [t for _, t in tasks],
        timeout=global_timeout_ms / 1000,
        return_when=asyncio.FIRST_COMPLETED  # 最快结果优先
    )

    # 取消 pending 任务
    for _, task in tasks:
        if task in pending:
            task.cancel()

    # 收集结果
    engines_tried = []
    engines_succeeded = []
    engines_failed = []
    aggregated_items = []
    start_time = time.monotonic()

    for provider_name, task in tasks:
        engines_tried.append(provider_name)
        if task in done:
            try:
                result = task.result()
                if result.success:
                    engines_succeeded.append(provider_name)
                    # 标准化 provider 的结果
                    items = normalize_provider_result(provider_name, result.data)
                    aggregated_items.extend(items)
                else:
                    engines_failed.append({
                        "engine": provider_name,
                        "reason": "call_failed"
                    })
            except RetryableError as e:
                engines_failed.append({
                    "engine": provider_name,
                    "reason": "timeout" if "timeout" in str(e).lower() else "exception"
                })
            except asyncio.CancelledError:
                engines_failed.append({
                    "engine": provider_name,
                    "reason": "timeout"  # 被全局超时取消
                })
        else:
            # pending 任务（已超时）
            engines_failed.append({
                "engine": provider_name,
                "reason": "timeout"
            })

    total_latency = int((time.monotonic() - start_time) * 1000)

    # 确定 status
    if engines_succeeded:
        status = "ok" if not engines_failed else "partial"
    elif engines_tried and not engines_succeeded:
        status = "all_failed"
    else:
        status = "no_match"

    return OrchestratorSearchResult(
        version="1.0",
        status=status,
        provider="orchestrator",
        query=query,
        items=aggregated_items,
        metadata=SearchMetadata(
            engines_tried=engines_tried,
            engines_succeeded=engines_succeeded,
            engines_failed=engines_failed,
            total_latency_ms=total_latency,
            ...
        )
    )
```

**全局超时配置：**

```yaml
# intent-modes.yaml
intent_modes:
  chinese-policy:
    strategy: hybrid
    external_timeout_ms: 15000  # 全局超时 15s
    internal_timeout_per_provider_ms: 8000  # 单 provider 超时 8s
```

`external_timeout_ms` 是全局超时，`internal_timeout_per_provider_ms` 是单个 provider 调用的超时。两者同时生效——哪个先到就按哪个处理。

---

## Gap 3：参数类型转换（P2，补全后 cli.py 可开工）

### 问题

CLI 传入的参数都是字符串，但 MCP tool 的参数需要：
- 布尔值：`safe_search=true` → `True`
- 整数：`count=10` → `10`
- 枚举：`freshness=day` → 需要校验
- 可选值：`default: null` → 不传参

### 补全方案

**Provider YAML 中增加 `type` 字段：**

```yaml
# providers/brave.yaml
call:
  parameters:
    query:
      mcp_param: "query"
      required: true
      type: string           # 字符串，默认
    count:
      mcp_param: "count"
      default: 10
      type: integer           # 需要 int() 转换
      range: [1, 50]          # 校验范围
    country:
      mcp_param: "country"
      default: "US"
      type: string
      max_length: 2           # ISO 3166-1 alpha-2
    search_lang:
      mcp_param: "search_lang"
      default: "en"
      type: string
    safe_search:
      mcp_param: "safe_search"
      default: true
      type: boolean           # "true"/"false" → True/False
    freshness:
      mcp_param: "freshness"
      default: null
      type: enum              # 枚举值校验
      enum: [day, week, month, year]
    offset:
      mcp_param: "offset"
      default: 0
      type: integer
      range: [0, 1000]
```

**支持的类型表（v1.0）：**

| type | CLI 输入 | 转换规则 | MCP 输出 | 范围校验 |
|------|---------|----------|---------|---------|
| string | `"hello"` | 原样 | `"hello"` | max_length |
| integer | `"10"` | `int()` | `10` | range: [min, max] |
| boolean | `"true"` | `str.lower == "true"` | `True` | 无 |
| enum | `"day"` | 校验在 enum 列表中 | `"day"` | enum: [...] |
| null | — | 不传参 | 跳过 | 无 |

**参数验证位置：**

```
CLI 入口（cli.py）：       类型转换 + 范围校验
执行引擎（engine.py）：     必填检查 + 跳过未映射参数
MCP 调用层（mcp_client）：  不验证，传入即可
```

**`type` 字段可选，默认 `string`。** 不指定 type 的 parameter 视为字符串，不做转换。

**转换实现逻辑：**

```python
def convert_parameter(value, param_def: ParameterDef) -> Any:
    """
    将 CLI 传入的字符串值转换为 MCP tool 需要的类型。
    """
    if param_def.default is None and value is None:
        return None  # 不传参

    param_type = param_def.type or "string"

    if param_type == "string":
        return str(value)
    elif param_type == "integer":
        try:
            v = int(value)
            if param_def.range:
                min_v, max_v = param_def.range
                if v < min_v or v > max_v:
                    raise ValueError(f"Value {v} out of range [{min_v}, {max_v}]")
            return v
        except (ValueError, TypeError) as e:
            raise ParameterError(f"Invalid integer for '{param_def.mcp_param}': {e}")
    elif param_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)
    elif param_type == "enum":
        if value not in param_def.enum:
            raise ParameterError(
                f"Invalid value '{value}' for '{param_def.mcp_param}': "
                f"must be one of {param_def.enum}"
            )
        return value
    else:
        return str(value)
```

---

## Gap 4：Windows 兼容性（P2，补全后 state.py 跨平台可工作）

### 问题

- `os.rename` 在 Windows 上如果目标文件已存在会抛出异常（而 Unix 会覆盖）
- `fcntl.flock` 是 POSIX 专有 API，Windows 不可用

### 补全方案

**原子写入统一使用 `os.replace`：**

```python
import os

# os.replace 在 Python 3.3+ 所有平台上都支持原子覆盖
def atomic_write(target_path: str, content: str):
    """原子写入文件。所有平台上保证原子性。"""
    temp_path = target_path + ".tmp"
    with open(temp_path, "w") as f:
        f.write(content)
    os.replace(temp_path, target_path)  # 跨平台原子覆盖
```

注意：`os.replace` 在 Windows 上的原子性不如 Unix 强（无法重命名到已存在的文件时会失败），但在文件系统相同的场景下足够了。

**文件锁使用 `portalocker`（已在要求在 requirements.txt 中）：**

```python
import portalocker

def with_quota_lock(provider_name: str, update_fn):
    """
    在文件锁保护下执行 quota 状态更新。
    锁超时 5s，获取不到则抛 LockTimeoutError。
    """
    lock_path = "_runtime/quota-state.lock"
    with portalocker.Lock(
        lock_path,
        timeout=5,               # 等待锁的最长时间
        flags=portalocker.LOCK_EX
    ):
        data = load_quota_state()
        update_fn(data)
        atomic_write("_runtime/quota-state.json", json.dumps(data, indent=2))
```

**`portalocker` 跨平台兼容矩阵：**

| 平台 | 锁机制 | 依赖 |
|------|--------|------|
| Linux | `fcntl.flock` | portalocker |
| macOS | `fcntl.flock` | portalocker |
| Windows | `msvcrt.locking` | portalocker |

**Windows 兼容性声明：**

- v1.0 目标平台：**macOS、Linux**（CI 测试）
- Windows 支持：**Phase 2 中补充**（需要 Windows runner 测试）
- 当前 Windows 上可运行，但未经过充分测试
- 注意事项：`os.replace` 在 Windows 上如果目标文件被占用会失败（多进程同时写入），通过文件锁规避

---

## Gap 5：数据落盘版本兼容性（P2，补全后迁移路径清晰）

### 问题

编排器的结果格式与旧 multi-search 的结果格式不兼容。调用方解析结果时可能出错。

### 补全方案

**新旧格式对比：**

| 字段 | 旧格式（v1） | 新格式（v2） | 兼容性 |
|------|-------------|-------------|--------|
| version | 不存在 | "1.0" | 新字段 |
| status | 不存在 | "ok" / "partial" / ... | 新字段 |
| provider | "minimax" | "orchestrator" | 不兼容 |
| items[].source_engine | 不存在 | "brave" | 新字段 |
| engines_tried | 不存在 | ["brave", ...] | 新字段 |
| engines_failed | 不存在 | [...] | 新字段 |

**迁移策略（Phase 1→Phase 2）：**

```
Phase 1（兼容期 = 新旧并存）：
- 旧 search(query) → 返回旧格式（v1）
- 新 search(query, intent=...) → 返回新格式（v2）
- 调用方按需选择

Phase 2（统一期 = 仅新格式）：
- search(query) → 返回 v2 格式
- 旧 v1 格式停止输出
- 调用方统一使用 v2 格式解析
```

**调用方适配指南：**

```python
# 调用方解析新旧两种格式的兼容代码
def parse_search_result(raw: dict):
    if "version" in raw:
        return parse_v2_result(raw)    # 编排器输出
    else:
        return parse_v1_result(raw)    # 旧链输出
        # 转换为 v2 格式
        return OrchestratorSearchResult(
            version="v1-migrated",
            status="ok" if raw.get("results") else "no_match",
            provider=raw.get("engine", "legacy"),
            ...
        )
```

**数据落盘路径：**

```
# 旧格式
_data/multi-search/{session-id}/search_results.json  → v1 格式

# 新格式
_data/multi-search/{session-id}/search_results_v2.json  → v2 格式

# 或统一路径（Phase 2 切换后）
_data/multi-search/{session-id}/search_results.json  → v2 格式（覆盖旧文件）
```

**Phase 2 切换不会破坏旧数据**，因为旧数据已经被写入到 hash 命名的 session 目录中，不会被覆盖。

---

## 改进 1：添加 `list-providers` 子命令（P2）

在 CLI 中添加：

```bash
search list-providers --format json

→
{
  "providers": [
    {
      "name": "brave",
      "type": "mcp",
      "description": "Brave Search API",
      "cost_tier": 1,
      "capabilities": {
        "languages": ["en", "multi"],
        "content_types": ["web", "news"]
      },
      "health": "alive",         # alive / dead / unknown
      "quota": {
        "limit": 2000,
        "used": 347,
        "reset_at": "2026-07-01T00:00:00Z"
      }
    },
    ...
  ]
}
```

**用途**：
- 运维人员查看所有 provider 状态
- 调试时确认 provider 是否加载
- 查看配额使用情况

**实现位置**：`cli.py` 中新增 `list_providers` 命令处理函数，调用 `config.py` 的已加载 provider 列表 + `state.py` 的健康/配额状态。

---

## 改进 2：结果格式增加 `round` 字段（P2）

在 `metadata` 中增加 `round` 字段：

```yaml
metadata:
  round: "precise" | "broaden" | "fallback" | null  # 仅三轮递进时存在
```

**用途**：
- 调用方可以根据 `round` 判断搜索结果是否来自完整的三轮递进
- 精准轮搜到足够结果就直接返回，不需要执行后续轮次

**实现位置**：`engine.py` 执行三轮递进时，记录当前轮次到 search result 的 metadata 中。

---

## 改进 3：Provider YAML 增加 `enabled` 字段（P3）

```yaml
# providers/brave.yaml
name: brave
enabled: true           # 新增：是否启用此 provider
type: mcp
...
```

**用途**：
- 临时禁用某个 provider（比如 API 故障），不需要删除 YAML 文件
- 新添加的 provider 默认 `enabled: true`

**实现**：配置加载器加载时检查 `enabled` 字段，为 `false` 时跳过但不报错。

---

## 汇总：补全后的 Phase 0 开工清单

| 模块 | 缺口依赖 | 可开工 | 备注 |
|------|---------|--------|------|
| `cli.py` | Gap 3（类型转换） | ✅ 已补全 | 参数解析可开工 |
| `engine.py` | Gap 1（重试）+ Gap 2（异常） | ✅ 已补全 | 并行/串行执行可开工 |
| `aggregator.py` | 无 | ✅ R2 已补全 | URL 去重 + provider 顺序排序 |
| `fallback_chain.py` | 无 | ✅ R2 已补全 | 串行 fallback |
| `config.py` | 无 | ✅ R2 已补全 | YAML 扫描 + 容错 + 加载报告 |
| `state.py` | Gap 4（Windows 兼容） | ✅ 已补全 | 原子写入 + 文件锁 |
| `mcp_client.py` | Gap 1（重试分类） | ✅ 已补全 | ABC + Mcporter 实现 |
| `schema.py` | 无 | ✅ 已补全 | YAML 校验规则 |

**全部 8 个模块已可编码。** 无剩余阻塞缺口。

**pip 依赖（确定版）：**

```
aiohttp>=3.8.0
PyYAML>=6.0
portalocker>=2.0.0
```

**Python 版本要求（确定版）：**

```
Python >= 3.9
Python 3.11+ 推荐（asyncio.timeout 原生支持）
Python 3.9-3.10 需要：asyncio-timeout>=4.0.0
```

**目标平台：**
- v1.0 主目标：macOS、Linux
- Windows：Phase 2 补充测试

---

## Gap 6：测试策略（P1，编码前必须定义）

### 问题

全方案没有提及如何验证编排器正确工作。没有测试策略意味着：
- 编码时不知道正确行为是什么
- 改代码时不知道有没有破坏已有功能
- 对接真实 MCP Server 前无法离线验证

### 补全方案

**三层测试结构：**

```
tests/
├── unit/              # 单元测试（不依赖外部服务）
│   ├── test_config.py       # YAML 加载、容错、schema 校验
│   ├── test_cli.py           # 参数解析、类型转换
│   ├── test_aggregator.py    # URL 去重、provider 排序、status 判定
│   ├── test_fallback_chain.py # 串行 fallback 逻辑
│   └── test_state.py         # 配额计数器、文件锁、原子写入
├── integration/       # 集成测试（需要 mcporter + 测试 provider）
│   ├── test_mcp_client.py    # McporterMCPClient 调用
│   ├── test_engine.py        # 并行/串行执行 + 三轮递进
│   └── test_cli_e2e.py       # 端到端：search 命令完整调用
└── mock/              # Mock 数据（用于替代真实 MCP，加速测试）
    ├── brave_response.json    # Brave 的 mock 返回
    ├── minimax_response.json  # MiniMax 的 mock 返回
    └── tavily_response.json   # Tavily 的 mock 返回
```

**各层职责：**

| 层级 | 测试对象 | 依赖 | 运行频率 |
|------|---------|------|---------|
| unit | 配置加载、参数解析、去重、状态管理 | 无（纯代码逻辑） | 每次提交 |
| integration | MCP 调用、引擎执行 | mcporter + mock MCP | 每次提交 |
| e2e | CLI 入口完整链路 | mcporter + mock MCP | PR 合并前 |

**Mock MCP Server（测试核心基础架构）：**

```python
# tests/mock/mcp_server.py
# 用 Python asyncio 启动一个假的 MCP Server，返回预设的 mock 数据
# 避免在测试中调用真实 Brave/MiniMax API（消耗配额、依赖网络）

class MockMCPServer:
    """
    模拟 MCP Server，支持 tools/list 和 tools/call。
    通过预设响应数据，验证编排器的 MCPClient 抽象层是否正确。
    """
    async def handle_request(self, request):
        if request.method == "tools/list":
            return self.tools_list_response
        elif request.method == "tools/call":
            tool_name = request.params.get("name")
            return self.tool_responses.get(tool_name, {"error": "unknown tool"})

# 启动方式：
# python3 tests/mock/mcp_server.py --port 8321
# 编排器配置中指向此 mock server 代替 mcporter
```

**测试用例关键覆盖：**

Unit tests（P0，必须覆盖）：
- YAML 加载成功/文件不存在/语法错误/字段缺失
- CLI 参数解析：所有参数类型转换正确
- 聚合去重：URL 重复/同 provider 重复/跨 provider 重复
- status 判定：ok/partial/no_match/all_failed/error
- 配额状态：读取成功/读取失败（JSON 损坏）/原子写入冲突

Integration tests（P1，编码后补充）：
- McporterMCPClient 成功/失败/超时
- 并行执行：超时一个不影响其他
- 三轮递进：精准轮 -> 泛搜轮 -> 兜底轮正确流转
- fallback 链：第一个失败自动尝试下一个

**测试运行命令：**

```bash
# 单元测试（快，< 1s）
python3 -m pytest tests/unit/ -v

# 集成测试（需要 mock MCP Server）
python3 -m pytest tests/integration/ -v

# 全部测试
python3 -m pytest tests/ -v
```

**测试依赖（pip）：**

```
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

---

## Gap 7：mcporter 版本兼容性（P2，运维层面）

### 问题

编排器的 `McporterMCPClient` 通过 mcporter HTTP API 进行 MCP 调用。mcporter 升级可能改变 API 路径或响应格式。当前方案没有说明 mcporter 的最低版本和兼容性策略。

### 补全方案

**mcporter 版本要求：**

```
mcporter >= 1.0.0     # 推荐 v1.latest
mcporter >= 0.9.0     # 最小兼容版本
```

版本从 OpenClaw 安装中获取：

```bash
# 检查 mcporter 版本
mcporter --version      # 输出类似 "mcporter/1.2.3"

# 检查 mcporter API 是否可用
curl http://localhost:8321/mcp/brave/tools/list
curl http://localhost:8321/mcp/brave/tools/call
```

**McporterMCPClient 的 API 调用路径：**

```python
# mcporter v1.x 的 HTTP API 路径（需确认）
/servers/{server_name}/tools/list    # GET → 列出 tool
/servers/{server_name}/tools/call    # POST → 调用 tool
```

> 注意：上述 API 路径基于 mcporter 常见设计，**建议 Phase 0 前用实际 mcporter 实例验证路径**。如果 mcporter 使用不同路径（如 `/mcp/{name}/...`），在 `McporterMCPClient` 中调整即可，不影响 ABC 抽象层。

**MCP 协议版本要求：**

```
MCP 协议版本：2024-11-05（当前最新稳定版）
向后兼容：McporterMCPClient 不依赖特定 MCP 协议特性，只使用基础 tools/list 和 tools/call
协议升级：MCP 协议向后兼容，升级不破坏编排器
```

**版本兼容性策略（一旦 mcporter API 变更）：**

```python
class McporterMCPClient(MCPClient):
    def __init__(self, base_url: str, server_name: str):
        self.base_url = base_url
        self.server_name = server_name
        # 预留版本协商机制
        self.api_version = self._detect_api_version()

    def _detect_api_version(self) -> str:
        """
        尝试探测 mcporter API 版本。
        先试 v2 路径，不行退回 v1。
        """
        for path, version in [
            ("/servers/{}/tools/list", "v2"),
            ("/mcp/{}/tools/list", "v1"),
        ]:
            url = f"{self.base_url}{path.format(self.server_name)}"
            try:
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    return version
            except:
                continue
        raise RuntimeError("Cannot detect mcporter API version")
```

> 备注：版本探测机制是优雅做法，但如果 mcporter 版本很少升级，可以在 `config.py` 中硬编码 API 路径模板。具体根据 mcporter 的版本发布频率决定。

---

## Gap 8：日志策略（P1，排查问题的必备能力）

### 问题

当前方案只提到 `--debug` 开关和 `log()` 调用，但没有定义日志的格式、级别、输出位置、文件大小管理。出问题没法查。

### 补全方案

**日志级别定义：**

| 级别 | 用途 | 示例 |
|------|------|------|
| ERROR | 不可恢复的错误 | provider 调用异常、YAML 加载失败 |
| WARNING | 可恢复的异常 | 某个 provider 失败（降级处理）、配额耗尽 |
| INFO | 主要流程信息 | intent 选择、provider 决策、结果摘要 |
| DEBUG | 调试详情 | 每次 MCP 调用的参数/响应/耗时 |
| TRACE | 详细跟踪 | 完整请求/响应体、内部状态变化 |

**默认日志配置：**

```yaml
# orchestrator/logging.yaml（或硬编码在 cli.py 中）
version: 1
formatters:
  detailed:
    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt: "%Y-%m-%dT%H:%M:%S%z"
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: detailed
  file:
    class: logging.handlers.RotatingFileHandler
    filename: "_runtime/orchestrator.log"
    maxBytes: 10485760        # 10MB 轮转
    backupCount: 3
    level: DEBUG
    formatter: detailed
```

**每条搜索调用至少记录：**

```
[INFO] search: query="社保缴费比例" intent="chinese-policy"
[INFO] engine: selected providers: [minimax, brave, web_fetch] (strategy=hybrid)
[INFO] engine: round 1 (precise): minimax → 3 results in 847ms
[INFO] engine: round 1 results OK (min_results=3), skipping rounds 2-3
[INFO] aggregator: 3 results from 1 engine, total_latency=847ms
```

```
[WARNING] engine: brave failed (timeout after 8000ms)
[WARNING] engine: minimax failed (quota_exhausted)
[INFO] engine: falling back to fallback_chain
[INFO] fallback: tavily → 5 results in 1234ms
```

**`--debug` 开关的影响：**

```
无 --debug：console INFO + file DEBUG
--debug：    console DEBUG + file TRACE（记录所有 MCP 请求/响应体）
```

**日志文件管理：**

```
_runtime/
  orchestrator.log         # 当前日志（DEBUG 级别）
  orchestrator.log.1       # 轮转归档
  orchestrator.log.2
  orchestrator.log.3

# 每条日志 <= 10MB，保留最近 3 个归档
# 总计最多 40MB 日志
```

**日志不记录的内容：**

- 完整的搜索结果内容（浪费空间）
- 搜索结果中的敏感信息（避免数据泄露）
- MCP 请求头中的 API Key

**Python logging 的实现约定：**

```python
# orchestrator/__init__.py
import logging

# 包级别日志器
logger = logging.getLogger("orchestrator")
logger.setLevel(logging.INFO)

# 子模块使用同个 logger
# engine.py
from . import logger
logger.debug(f"Calling {provider.name} with query={query}")
```

不使用自定义日志类，依赖 Python 标准库 `logging`。

---

## Gap 9：缓存策略（P2，节省配额和延迟）

### 问题

多次搜索相同或相似的 query（如用户两次请求相同话题），会重复调用所有 provider。浪费配额（每条消耗一次免费额度）和增加延迟。

### 补全方案

**缓存原则：**

1. **只缓存搜索结果，不缓存 provider 状态。** 健康/配额状态有自己的 60s 缓存机制，不受此缓存影响。
2. **v1.0 不做 query 相似度缓存。** 只有完全相同的 query + intent + count 组合命中缓存。
3. **缓存是优化而非保证。** 缓存不存在不影响正确性。
4. **默认禁用，通过 `--cache-ttl` 参数启用。** 不默认配缓存（避免数据过期）。

**缓存实现（简单版）：**

```python
# orchestrator/cache.py
# 进程级内存缓存，TTL 过期自动失效
# 不做 Redis/external cache，不做持久化

import time
import threading
from typing import Dict, Optional, Any

class SearchCache:
    """
    简单内存缓存，靠 TTL 过期。
    线程安全（读多写少，不考虑 LRU 淘汰）。
    key: (query, intent, count) → tuple
    """
    def __init__(self, ttl_seconds: int = 0):
        self._ttl = ttl_seconds
        self._data: Dict[tuple, tuple[float, Any]] = {}  # key → (timestamp, result)
        self._lock = threading.Lock()

    def get(self, key: tuple) -> Optional[Any]:
        if self._ttl <= 0:
            return None
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            ts, result = entry
            if time.monotonic() - ts > self._ttl:
                del self._data[key]
                return None
            return result

    def set(self, key: tuple, result: Any):
        if self._ttl <= 0:
            return
        with self._lock:
            self._data[key] = (time.monotonic(), result)

    def clear(self):
        with self._lock:
            self._data.clear()


# 全局缓存实例, 在 cli.py 中初始化
search_cache = SearchCache()
```

**默认 TTL：**

```yaml
# intent-modes.yaml
intent_modes:
  chinese-policy:
    strategy: hybrid
    cache_ttl: 60      # 60 秒内相同 query 直接返回缓存
    ...
  news:
    cache_ttl: 30      # 新闻更新快，缓存更短
    ...
  general:
    cache_ttl: 0       # 通用搜索不缓存（默认）
    ...
```

**CLI 参数控制：**

```bash
search --query "社保" --intent chinese-policy --cache-ttl 60
search --query "社保" --intent chinese-policy --cache-ttl 0   # 禁用缓存
```

**未来方向（不在 v1.0 范围内）：**
- Query 相似度缓存（"社保缴费"和"社保缴纳"共享缓存）
- 持久化缓存（磁盘/Redis 跨进程共享）
- 缓存预热（预缓存常见 search）

---

## Gap 10：CI 流水线（P2，自动化质量保证）

### 问题

没有任何自动化验证。改了代码不知道有没有坏已有功能。多人协作时缺失质量门控。

### 补全方案

**CI 流水线结构：**

```yaml
# .github/workflows/ci.yml
name: orchestrator-ci

on:
  pull_request:
    paths:
      - "orchestrator/**"
      - "tests/**"
  push:
    branches: [master]
    paths:
      - "orchestrator/**"
      - "tests/**"

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ["3.9", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements.txt

      - name: Unit tests
        run: python3 -m pytest tests/unit/ -v --tb=short

      - name: Integration tests (with mock MCP)
        run: |
          python3 tests/mock/mcp_server.py &
          python3 -m pytest tests/integration/ -v --tb=short

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install linters
        run: pip install flake8 mypy

      - name: Lint
        run: flake8 orchestrator/

      - name: Type check
        run: mypy orchestrator/ --ignore-missing-imports
```

**流水线检查项：**

| 阶段 | 检查项 | 通过条件 | 耗时预估 |
|------|--------|---------|---------|
| lint | flake8 | 无语法/风格错误 | < 10s |
| type-check | mypy | 类型注解一致（--ignore-missing-imports） | < 20s |
| unit tests | pytest | 全部通过 | < 30s |
| integration tests | pytest + mock MCP | 全部通过 | < 60s |
| multi-python | 3.9/3.11/3.12 | 全部矩阵通过 | < 3min |
| multi-os | ubuntu/macos | 全部矩阵通过 | < 5min |

**本地运行（开发者提交前）：**

```bash
# 一键检查
python3 -m pytest tests/ -v                  # 全部测试
python3 -m flake8 orchestrator/              # 代码风格
python3 -m mypy orchestrator/ --ignore-missing-imports  # 类型检查
```

**GitHub Actions 的分支策略：**

1. 开发者在 feature branch 上提交 → CI 自动运行 lint + unit tests（快，< 1min）
2. 发起 PR → CI 自动运行全部测试（lint + unit + integration, < 5min）
3. PR 合并到 master → CI 再跑一次全部测试（确保合并后仍然通过）
4. PR 合并后自动清理 feature branch

> 注意：CI 不依赖真实 MCP Server，使用 mock MCP Server。真实 MCP 先由 mcporter 验证。

**lint/style 规则约定：**

```
flake8：遵循 PEP 8，忽略 E501（行长度，79 字符约束在搜索参数长时束缚）
mypy：--ignore-missing-imports（aiohttp/PyYAML 等外部库无 stubs）
```

---

## 汇总：全部 10 个缺口修正状态

| # | 缺口 | 优先级 | 状态 | 影响模块 |
|---|------|--------|------|---------|
| 1 | 重试策略 | P1 | ✅ 已补 | engine.py |
| 2 | 异常捕获策略 | P1 | ✅ 已补 | engine.py |
| 3 | 参数类型转换 | P2 | ✅ 已补 | cli.py |
| 4 | Windows 兼容性 | P2 | ✅ 已补 | state.py |
| 5 | 数据落盘版本兼容 | P2 | ✅ 已补 | SKILL.md |
| 6 | 测试策略 | P1 | ✅ 已补 | tests/ 目录 |
| 7 | mcporter 版本兼容 | P2 | ✅ 已补 | mcp_client.py |
| 8 | 日志策略 | P1 | ✅ 已补 | 全局模块 |
| 9 | 缓存策略 | P2 | ✅ 已补 | cache.py |
| 10 | CI 流水线 | P2 | ✅ 已补 | .github/workflows/ |

**全部 10 个缺口已补全。0 个阻塞缺口。**
