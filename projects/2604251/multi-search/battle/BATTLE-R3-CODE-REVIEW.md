# BATTLE-R3 — 代码工程视角全面复核（Code Review）

**审查者**：第三方代码审查者（Code Reviewer）
**审查标的**：BATTLE-R2 最终完整版设计（BATTLE-R2-EXECUTOR.md）
**审查范围**：从代码工程的视角进行复核，重点关注工程可行性、接口设计、并发安全、错误处理、依赖兼容性、编码准备度
**审查方式**：独立代码审查，不参考 R1/R2 预判

**总评**：方案在工程上**基本可行**，架构经过两轮审查后已趋于完善。但存在 5 个需要补充的关键信息和 1 个潜在的设计盲点。总体可编码性评分 **7.5/10**，补全缺失信息后可达 **8.5/10**。

---

## 一、总体评估

### 可编码性评分：7.5/10

**评分理由**：

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构清晰度 | ★★★★★ | 组件边界清晰，职责划分明确，易于编码实现 |
| 接口完整性 | ★★★★☆ | MCPClient ABC、CLI 参数、结果格式已定义，但细节需补充 |
| 并发安全性 | ★★★★☆ | 文件锁 + 原子写入方案正确，但实现细节需明确 |
| 错误处理 | ★★★☆☆ | YAML 容错、fallback 链已定义，但重试机制、异常捕获策略不完整 |
| 工程依赖 | ★★★☆☆ | Python 依赖清晰，但 mcporter/MCP 版本兼容性未考虑 |
| 实施可行性 | ★★★★☆ | Phase 0-2 顺序合理，但 Phase 0 缺少必要信息 |

### 一句话结论

**架构方向正确，两轮审查后设计趋于完善，但在进入 Phase 0 编码前必须补全 5 个关键信息（重试策略、异常捕获、类型转换、Windows 兼容、数据落盘版本兼容），否则编码即遇到阻塞问题。**

---

## 二、接口设计复核

### 2.1 MCPClient ABC — **基本合理，但需补充细节**

**当前定义**（BATTLE-R2-EXECUTOR.md §3.6）：

```python
class MCPClient(ABC):
    @abstractmethod
    async def list_tools(self) -> List[MCPToolDefinition]:
        ...

    @abstractmethod
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout_ms: int = 30000,
    ) -> MCPToolResult:
        ...

    @abstractmethod
    async def health_check(self, timeout_ms: int = 5000) -> bool:
        ...
```

**评价**：
- ✅ **优点**：抽象层设计正确，使用 ABC 避免了运行时具体实现依赖
- ✅ **优点**：使用 dataclass 定义返回类型，类型安全
- ✅ **优点**：方法签名清晰，符合 MCP 协议语义
- ⚠️ **不足**：缺少 `list_tools` 的超时参数，可能导致长时间卡住
- ⚠️ **不足**：缺少 `close()` 或 `shutdown()` 方法，资源清理不明确

**建议**：
```python
class MCPClient(ABC):
    @abstractmethod
    async def list_tools(self, timeout_ms: int = 10000) -> List[MCPToolDefinition]:
        """添加超时参数，默认 10s"""
        ...

    @abstractmethod
    async def close(self) -> None:
        """清理资源（关闭 HTTP 连接、子进程等）"""
        ...

    async def __aenter__(self):
        """支持 async with 语法"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """支持 async with 语法"""
        await self.close()
```

### 2.2 CLI 参数规范 — **参数过多但合理**

**当前定义**（BATTLE-R2-EXECUTOR.md §3.4）：

```
--query, --intent, --count, --max-timeout, --freshness,
--country, --search-lang, --offset, --safe-search, --format, --debug
```

**评价**：
- ✅ **优点**：参数覆盖了常见搜索场景（地域、语言、时效性、分页）
- ✅ **优点**：所有参数都有合理的默认值，调用方可以不传
- ✅ **优点**：使用短别名（`-q`, `-i`, `-c`），提升了命令行可用性
- ⚠️ **不足**：`--offset` 参数可能不适用于所有 provider（部分 provider 不支持分页）
- ⚠️ **不足**：参数验证策略未定义（哪些参数在 CLI 层验证，哪些在执行引擎层验证）

**建议**：
- 在 CLI 参数验证层只做**类型校验**（`--count` 是整数、`--max-timeout` 在范围内）
- 在执行引擎层做**业务逻辑校验**（`--offset` 在 provider 不支持时忽略并警告）
- 在文档中明确：CLI 层验证 vs Engine 层验证的边界

### 2.3 统一结果格式 — **设计合理，但需明确字段映射**

**当前定义**（BATTLE-R2-EXECUTOR.md §3.3）：

```yaml
OrchestratorSearchResult:
  required: [version, status, provider, query, items, metadata]
  properties:
    status: ok | partial | no_match | all_failed | error
    items:
      required: [title, url, snippet, source_engine]
      nullable: [published_date, score, content_type]
```

**评价**：
- ✅ **优点**：`status` 字段设计优秀，调用方一行模式匹配即可决定后续逻辑
- ✅ **优点**：`source_engine` 保留 provenance，去重后仍可追溯
- ✅ **优点**：`version` 字段支持 schema 演进
- ⚠️ **不足**：不同 MCP tool 的返回字段名不一致，映射规则未定义

**核心问题**：Brave 返回 `published_date`，MiniMax 返回 `date`，Tavily 返回 `publishedDate`。编排器如何统一到 `published_date`？

**建议**：
在 Provider YAML 的 `call` 节增加 `result_mapping` 定义：

```yaml
# providers/brave.yaml
call:
  parameters:
    query: {mcp_param: "query", required: true}
    # ...
  result_mapping:
    title: "title"                    # 直接映射
    url: "url"
    snippet: "description"           # Brave 的 description → snippet
    published_date: "date"            # Brave 的 date → published_date
    score: null                       # Brave 不提供排序分
```

**如果认为加 YAML 太重**，则在代码中硬编码常见映射规则，在文档中明确："当前版本支持 Brave/MiniMax/Tavily 的自动映射，新增 provider 需要在 aggregator.py 中添加映射规则"。

### 2.4 Provider YAML 描述符 — **parameters 映射设计优秀**

**当前定义**（BATTLE-R2-EXECUTOR.md §3.2）：

```yaml
call:
  parameters:
    query:
      mcp_param: "query"
      required: true
    count:
      mcp_param: "count"
      default: 10
```

**评价**：
- ✅ **优点**：R2 修正后，这是**关键改进**，解决了编排器无法生成正确 MCP 参数的核心问题
- ✅ **优点**：支持 `required`、`default`、`mcp_param`，覆盖了常见场景
- ✅ **优点**：每个 provider 独立定义参数映射，互不影响
- ⚠️ **不足**：缺少参数类型定义（string/int/boolean/enum）

**潜在问题**：
- Brave 的 `safe_search` 参数期望布尔值，但 CLI 传入的是字符串 `"true"/"false"`，需要类型转换
- Brave 的 `freshness` 参数是枚举（`day/week/month/year`），需要校验

**建议**：
在 `parameters` 中增加 `type` 字段（可选，用于类型转换和校验）：

```yaml
call:
  parameters:
    safe_search:
      mcp_param: "safe_search"
      type: boolean                    # 新增：类型转换
      default: true
    freshness:
      mcp_param: "freshness"
      type: enum                       # 新增：枚举校验
      enum: [day, week, month, year]
      default: null
```

**如果认为过度设计**，则在代码中硬编码常见参数的类型转换规则，在文档中明确。

---

## 三、并发安全复核

### 3.1 配额计数器 — **方案正确，实现细节需补充**

**当前设计**（BATTLE-R2-EXECUTOR.md §3.8）：

```
- 原子写入：write temp → os.rename(temp, quota-state.json)
- 文件锁：fcntl.flock（跨平台用 portalocker）
```

**评价**：
- ✅ **优点**：原子写入方案正确，避免了写半截导致 JSON 损坏
- ✅ **优点**：使用 `portalocker` 实现跨平台文件锁
- ✅ **优点**：R2 增加了降级策略（读取失败时重置为空状态）

**实现细节缺失**：

1. **文件锁的获取/释放时机未定义**
   ```python
   # 推荐实现
   async def increment_quota(provider_name: str):
       lock_file = "_runtime/quota-state.lock"
       with portalocker.Lock(lock_file, timeout=5):  # 获取锁，超时 5s
           data = load_quota_state()
           data[provider_name]["used"] += 1
           write_quota_state_atomic(data)  # 原子写入
       # 锁在 with 块结束时自动释放
   ```

2. **锁超时后的处理策略未定义**
   - 如果 5s 内无法获取锁（另一个进程持有锁），是抛异常？还是重试？还是返回？
   - 建议：抛出 `QuotaUpdateTimeout` 异常，上层捕获后记录警告，但不阻塞搜索

3. **并发更新丢失计数的影响评估**
   - 文档说"仅用于路由决策，不用于计费"，但需要明确：丢失计数会导致配额用得比预期快，还是慢？
   - 分析：丢失计数 → used 值比实际小 → 认为配额充足 → 继续使用 → 实际配额消耗更快 → 达到真实配额上限时，used 值可能还显示"未满"
   - **结论**：丢失计数会导致配额用得比预期**更快**（而非更慢），但这不是问题，因为配额上限由 provider API 控制，编排器的计数器只是近似值

**建议**：
在文档中明确：
- 文件锁超时时间（建议 5s）
- 锁超时后的处理策略（抛异常，记录警告，不阻塞搜索）
- 丢失计数对配额使用的影响（配额用得更快，但不影响正确性）

### 3.2 并行 Provider 调用 — **方案正确，异常捕获需补充**

**当前设计**（BATTLE-R2-EXECUTOR.md §3.1）：

```
执行引擎：并行/串行/hybrid 调度
全局超时管理：10-15s（不是 provider 超时的和）
```

**评价**：
- ✅ **优点**：全局超时管理方案正确，避免总耗时 = 各 provider 超时之和
- ✅ **优点**：使用 `asyncio.wait` 或 `asyncio.gather` 支持并行执行
- ✅ **优点**：R2 明确了"同底层引擎 provider 不并行"规则

**实现细节缺失**：

1. **异常捕获策略未定义**
   ```python
   # 推荐实现
   async def call_provider_parallel(providers, query, timeout_ms):
       tasks = [asyncio.create_task(call_provider(p, query)) for p in providers]
       done, pending = await asyncio.wait(
           tasks,
           timeout=timeout_ms / 1000,
           return_when=asyncio.ALL_COMPLETED
       )

       results = []
       for task in done:
           try:
               result = task.result()
               if result.success:
                   results.append(result)
               else:
                   log_warning(f"Provider failed: {result.raw}")  # 记录失败
           except Exception as e:
               log_error(f"Provider raised exception: {e}")  # 捕获异常

       # 取消未完成的任务
       for task in pending:
           task.cancel()

       return results
   ```

2. **全局超时的实现方式未定义**
   ```python
   # 方式一：使用 asyncio.wait 的 timeout 参数（推荐）
   done, pending = await asyncio.wait(tasks, timeout=15)

   # 方式二：使用 asyncio.Timeout
   async with asyncio.timeout(15):
       results = await asyncio.gather(*tasks)

   # 方式三：使用 asyncio.wait_for
   results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=15)
   ```

   建议：使用方式一（`asyncio.wait`），因为它可以获取"已完成"和"未完成"的任务列表，便于取消未完成任务。

**建议**：
在文档中明确：
- 异常捕获策略：每个 provider 调用独立 try-except，不影响其他 provider
- 全局超时实现方式：使用 `asyncio.wait(timeout=...)`，取消未完成任务
- 部分成功时的处理：返回成功 provider 的结果，metadata 中记录失败 provider

### 3.3 健康探测缓存 — **方案正确**

**当前设计**（BATTLE-R2-EXECUTOR.md §3.8）：

```
按需探测 + 60s 缓存
5 分钟内上次失败则仍标记不可用
```

**评价**：
- ✅ **优点**：按需探测避免了不必要的 MCP 连接开销
- ✅ **优点**：缓存 1 分钟，避免频繁探测
- ✅ **优点**：失败后 5 分钟内不重试，避免反复调用失败的 provider
- ✅ **优点**：依赖 mcporter 的进程自愈能力，编排器不做重复工作

**实现细节正确**：
```python
if now - last_check < 60:           # 1 分钟内复用
    return last_ok
if now - last_check < 300:         # 5 分钟内上次失败则仍失败
    if not last_ok:
        return False
```

**建议**：无需修改，方案正确。

---

## 四、错误处理复核

### 4.1 YAML 加载容错 — **设计优秀**

**当前设计**（BATTLE-R2-EXECUTOR.md §3.7）：

```python
for yaml_file in glob("*.yaml"):
    try:
        data = yaml.safe_load(read_file(yaml_file))
        validate_provider_schema(data)
        loaded.append(ProviderDescriptor(data))
    except yaml.YAMLError as e:
        skipped.append({file: yaml_file, reason: f"YAML syntax error: {e}"})
        continue
    except ValidationError as e:
        skipped.append({file: yaml_file, reason: f"Missing required field: {e}"})
        continue
```

**评价**：
- ✅ **优点**：逐文件加载，互不影响
- ✅ **优点**：捕获 `YAMLError` 和 `ValidationError`，区分语法错误和字段缺失
- ✅ **优点**：最终输出加载报告：`Loaded 5/6 providers, 1 skipped (reason)`
- ✅ **优点**：R2 盲点 2 已被妥善处理

**建议**：无需修改，设计优秀。

### 4.2 Provider 调用失败 — **策略不完整**

**当前设计**（BATTLE-R2-EXECUTOR.md §3.3）：

```yaml
engines_failed:
  - engine: "tavily"
    reason: "timeout" | "exception" | "quota_exhausted" | "no_match"
```

**评价**：
- ✅ **优点**：失败原因分类清晰（超时/异常/配额/无匹配）
- ✅ **优点**：失败信息记录在 `metadata.engines_failed` 中，便于调试
- ⚠️ **不足**：重试机制未定义

**重试机制缺失**：

Provider YAML 中定义了 `call.retry`，但重试策略未说明：
- 什么情况下重试？（超时？异常？配额耗尽？）
- 重试几次？（`retry: 2` 表示最多 2 次，还是 1 次失败后重试 2 次？）
- 重试前是否等待？（退避策略：立即重试？等待 1s？指数退避？）
- 配额耗尽是否重试？（不应该重试，配额耗尽后重试无意义）

**建议**：
在文档中明确重试策略：
- **可重试的异常**：超时、网络错误、HTTP 5xx
- **不可重试的异常**：配额耗尽、API Key 无效、HTTP 4xx（参数错误）
- **重试次数**：`retry: 2` 表示最多调用 2 次（1 次失败后重试 1 次）
- **退避策略**：立即重试（或者等待 1s，如果担心 rate limit）
- **配额耗尽不重试**：直接标记失败，不消耗额外配额

### 4.3 Fallback 链 — **设计优秀**

**当前设计**（BATTLE-R2-EXECUTOR.md §一-Issue 7）：

```python
fallback_chain.py:
  接收 provider 优先级列表
  串行逐个调用，一个失败立即尝试下一个
  任意成功返回该 provider 的结果
  全部失败 → status: all_failed
```

**评价**：
- ✅ **优点**：R2 Issue 7 的修正方案优秀，旧链成为编排器的内置能力
- ✅ **优点**：避免了两份实现、两份维护的问题
- ✅ **优点**：fallback chain 可以复用 Provider YAML 和 MCPClient 抽象
- ✅ **优点**：每个 provider 调用有自己的超时，避免一个 provider 卡住整个 fallback

**建议**：无需修改，设计优秀。

### 4.4 环境变量验证 — **职责边界需明确**

**当前设计**（BATTLE-R2-EXECUTOR.md §3.2）：

```yaml
call:
  required_env: [BRAVE_API_KEY]
```

**评价**：
- ✅ **优点**：Provider YAML 中声明了需要的环境变量
- ⚠️ **不足**：验证时机未明确

**职责边界问题**：
- 谁负责验证环境变量？编排器？MCP Server？
- 何时验证？启动时？调用前？
- 验证失败时的行为？跳过该 provider？报错？

**建议**：
在文档中明确职责边界：
- **编排器负责验证**：在调用 provider 前，检查 `required_env` 中的环境变量是否存在
- **验证时机**：调用前验证（不是启动时，因为环境变量可能在运行时设置）
- **验证失败行为**：跳过该 provider，记录警告，`engines_failed` 中记录 `reason: "missing_env_vars"`
- **MCP 层不负责验证**：MCP Server 返回错误时，编排器捕获异常并统一处理

---

## 五、工程依赖复核

### 5.1 Python 版本和 pip 依赖 — **清晰**

**当前定义**（BATTLE-R2-EXECUTOR.md §3.10）：

```
Phase 0（基础设施）：
  ├─ Python 异步库框架 + CLI 入口
  ├─ MCPClient 抽象层
  └─ 配额计数器（原子写入 + 文件锁）
```

**推断的依赖**：
- Python 3.9+（asyncio 标准库，`asyncio.timeout` 需要 Python 3.11+ 或 `asyncio-timeout` backport）
- aiohttp（HTTP 客户端，用于 mcporter 调用）
- PyYAML（YAML 解析）
- portalocker（跨平台文件锁）

**评价**：
- ✅ **优点**：依赖清晰，都是常见库
- ⚠️ **不足**：Python 版本要求未明确
- ⚠️ **不足**：pip 依赖列表未提供

**建议**：
在 Phase 0 前补充：

```txt
# requirements.txt
aiohttp>=3.8.0
PyYAML>=6.0
portalocker>=2.0.0

# Python 3.11- 不支持 asyncio.timeout，需要 backport
# Python 3.9-3.10 使用以下替代
asyncio-timeout>=4.0.0  # 如果 Python < 3.11
```

```txt
# Python 版本要求
Python >= 3.9
推荐 Python 3.11+（支持 asyncio.timeout，否则需要 backport）
```

### 5.2 mcporter 和 MCP Server 版本兼容性 — **未考虑**

**潜在问题**：
- mcporter 的 API 可能变化，如果 `McporterMCPClient` 硬编码了 API 路径（`/mcp/{server_name}/tools/list`），mcporter 升级后可能不兼容
- 不同 MCP Server 的协议版本不同（MCP 协议本身有版本），编排器是否兼容？

**建议**：
在文档中明确：
- **mcporter 版本要求**：`mcporter >= 1.0.0`（需要查看 mcporter 的版本策略）
- **MCP 协议版本**：当前支持 MCP 协议 2024-11-05 版本（或最新稳定版）
- **版本兼容性策略**：`McporterMCPClient` 通过 mcporter 的 HTTP API 调用，只要 mcporter 保持 API 兼容，编排器不受影响

### 5.3 跨平台兼容性 — **Windows 兼容性未考虑**

**当前设计**：
- 文件锁使用 `fcntl.flock`（Linux/macOS）或 `portalocker`（跨平台）
- 原子写入使用 `os.rename`（POSIX 系统保证原子性）

**潜在问题**：
- **Windows 上的 `os.rename` 不保证原子性**：如果目标文件已存在，`os.rename` 在 Windows 上会抛出异常（不同于 POSIX 的覆盖行为）
- **Windows 上的文件锁**：`portalocker` 在 Windows 上使用不同的锁机制（`msvcrt.locking`），需要测试

**建议**：
在文档中明确：
- **Windows 兼容性**：当前版本主要支持 Linux/macOS，Windows 支持在 Phase 2 中补充
- **Windows 上的原子写入**：使用 `os.replace` 而非 `os.rename`（Python 3.3+ 的 `os.replace` 在 Windows 上是原子的）
- **跨平台代码**：
  ```python
  import os
  atomic_rename = os.replace if os.name == 'nt' else os.rename
  atomic_rename(temp_path, target_path)
  ```

### 5.4 各平台测试覆盖 — **未定义**

**建议**：
在 Phase 1 或 Phase 2 中添加：
- **CI 测试**：Linux/macOS 自动化测试
- **Windows 测试**：手动测试或 GitHub Actions 的 windows-latest runner
- **测试 Provider**：至少测试 2-3 个真实 provider（Brave, MiniMax, Tavily）

---

## 六、编码前准备度

### 6.1 当前设计缺少的关键信息

#### **信息缺口 1：重试策略（P1 重要）**

**缺失内容**：
- 什么情况下重试？（超时？异常？配额耗尽？）
- 重试几次？（`retry: 2` 的含义）
- 退避策略？（立即重试？等待 1s？指数退避？）
- 配额耗尽是否重试？（不应该）

**影响**：
- Phase 0 编码时，engine.py 无法实现 `call` 的重试逻辑
- 不同开发者可能实现不同的重试策略，导致不一致的行为

**建议补全**：
在文档中明确重试策略（见 §4.2）。

#### **信息缺口 2：异常捕获策略（P1 重要）**

**缺失内容**：
- 并行 provider 调用时，如何捕获单个 provider 的异常？
- 异常是否影响其他 provider 的调用？
- 异常信息如何记录在 `metadata.engines_failed` 中？

**影响**：
- Phase 1 编码 engine.py 时，并行调用的异常处理逻辑不明确
- 可能导致一个 provider 异常影响整个搜索调用

**建议补全**：
在文档中明确异常捕获策略（见 §3.2）。

#### **信息缺口 3：参数类型转换（P2 低优）**

**缺失内容**：
- CLI 传入的 `--safe-search` 是字符串 `"true"`，但 MCP 需要布尔值 `True`
- `--freshness` 是枚举，如何校验？
- `--count` 是字符串 `"10"`，需要转换为整数

**影响**：
- Phase 0 编码 cli.py 时，参数类型转换逻辑不明确
- 可能导致 MCP 调用参数错误

**建议补全**：
在 Provider YAML 的 `parameters` 中增加 `type` 字段（见 §2.4）。

#### **信息缺口 4：Windows 兼容性（P2 低优）**

**缺失内容**：
- Windows 上的原子写入使用 `os.replace` 而非 `os.rename`
- Windows 上的文件锁使用 `msvcrt.locking`，需要测试

**影响**：
- Phase 0 编码 state.py 时，配额计数器的原子写入可能在 Windows 上不工作
- Windows 用户无法使用编排器

**建议补全**：
在文档中明确 Windows 兼容性（见 §5.3）。

#### **信息缺口 5：数据落盘版本兼容性（P2 低优）**

**缺失内容**：
- 编排器的结果格式与旧 multi-search 的结果格式不兼容
- 调用方期望的 `items` 字段可能不存在（旧格式字段名不同）

**影响**：
- 调用方解析结果时可能出错
- 数据落盘的 `_data/multi-search/{session-id}/` 目录中，新旧格式混存

**建议补全**：
在文档中明确：
- **编排器的结果格式是 v2**，与旧格式不兼容
- **迁移策略**：调用方需要更新结果解析逻辑，支持新格式
- **数据落盘路径**：使用新的 session-id 避免新旧数据混存

### 6.2 编码者无法开工的场景

**场景 1**：编码者开始实现 `engine.py` 的并行调用逻辑，发现：
- 不知道如何捕获单个 provider 的异常（信息缺口 2）
- 不知道重试策略是什么（信息缺口 1）
- **无法开工**：必须先等待设计补全

**场景 2**：编码者开始实现 `cli.py` 的参数解析逻辑，发现：
- 不知道如何将 `--safe-search` 的字符串转换为布尔值（信息缺口 3）
- 不知道哪些参数在 CLI 层验证，哪些在 Engine 层验证（§2.2）
- **无法开工**：必须先等待设计补全

**场景 3**：编码者开始实现 `state.py` 的配额计数器，发现：
- 不知道 Windows 上如何实现原子写入（信息缺口 4）
- **无法开工**（如果编码者使用 Windows）：必须先等待设计补全

### 6.3 可以开工的部分

即使存在信息缺口，以下部分可以立即开工：

- ✅ **config.py**：YAML 加载、容错、加载报告（§3.7 已完整）
- ✅ **mcp_client.py**：MCPClient ABC 接口定义（§3.6 已完整）
- ✅ **aggregator.py**：URL 去重、provider 顺序排序（§3.5 已完整）
- ✅ **cli.py**：命令行参数解析（不含类型转换）
- ✅ **schema.py**：Provider YAML 校验规则（§3.7 已完整）
- ✅ **fallback_chain.py**：串行 fallback 逻辑（§一-Issue 7 已完整）

---

## 七、改进建议

### 7.1 应该改但没改的地方

#### **改进 1：添加 `list-providers` 子命令（P2 低优）**

**当前设计**：
- `search list-intents` 可以列出可用 intent
- 但没有 `list-providers` 命令列出所有 provider

**建议**：
在 CLI 中添加 `list-providers` 子命令：

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
      "health": "alive",  # alive / dead / unknown
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
- 运维人员查看所有 provider 的状态
- 调试时确认 provider 是否加载
- 查看配额使用情况

#### **改进 2：结果格式增加 `round` 字段（P2 低优）**

**当前设计**：
- 三轮递进策略已定义（§3.2），但结果格式中没有"当前执行到第几轮"的字段
- 调用方无法知道结果来自精准轮、泛搜轮还是兜底轮

**建议**：
在 `metadata` 中增加 `round` 字段（已在 BATTLE-R2-EXECUTOR.md §3.3 中定义，但未强调）：

```yaml
metadata:
  round: "precise" | "broaden" | "fallback"  # 当前执行到的轮次
```

**用途**：
- 调用方可以根据 `round` 调整后续策略（精准轮结果足够则不执行后续轮次）
- 调试时确认三轮递进是否生效

#### **改进 3：Provider YAML 增加 `enabled` 字段（P3 低优）**

**当前设计**：
- 所有加载的 provider 都会被调用（如果 intent 匹配）
- 无法临时禁用某个 provider

**建议**：
在 Provider YAML 中增加 `enabled` 字段：

```yaml
# providers/brave.yaml
enabled: true  # false = 临时禁用，不参与路由
```

**用途**：
- 运维人员临时禁用某个 provider（维护、调试）
- 无需删除 YAML 文件或修改 intent 映射

#### **改进 4：增加 `--dry-run` 参数（P3 低优）**

**当前设计**：
- 调试时需要实际执行搜索才能知道会调用哪些 provider
- 无法在不消耗配额的情况下测试路由逻辑

**建议**：
在 CLI 中增加 `--dry-run` 参数：

```bash
search --query "社保缴费比例" --intent chinese-policy --dry-run

→
{
  "dry_run": true,
  "would_call_providers": ["minimax", "brave", "web_fetch"],
  "strategy": "hybrid",
  "query_strategy": {
    "rounds": [
      {"mode": "precise", "providers": ["minimax"]},
      {"mode": "broaden", "providers": ["minimax", "brave"]},
      {"mode": "fallback", "providers": ["minimax", "brave", "web_fetch"]}
    ]
  }
}
```

**用途**：
- 调试路由逻辑，不消耗配额
- 测试 intent 映射是否正确
- 验证三轮递进策略

### 7.2 过度设计的部分

**过度设计 1：三轮递进的 query 改写（已避免）**

**当前设计**：
- 三轮递进仅通过扩展 provider 范围 + 增大 count 实现"泛搜"和"兜底"
- query 改写（加引号、site:限定、同义词扩展）作为未来优化项

**评价**：
- ✅ **正确**：query 改写需要 LLM 介入，增加了复杂度、成本和延迟
- ✅ **正确**：当前版本不做 query 改写，避免了过度设计

**过度设计 2：Intent→Capabilities 自动匹配（已避免）**

**当前设计**：
- 当前 intent→provider 是静态映射，不与 provider capabilities 自动匹配
- 未来可能的优化方向：基于 capabilities 的自动匹配

**评价**：
- ✅ **正确**：自动匹配需要复杂的规则引擎或 LLM，增加了复杂度
- ✅ **正确**：静态映射简单、可维护、可预测

**过度设计 3：结果相关性排序（已避免）**

**当前设计**：
- v1.0 按 provider 顺序排列，不进行相关性排序
- 未来可以引入基于语义的相关性排序

**评价**：
- ✅ **正确**：相关性排序需要 LLM 或机器学习模型，增加了复杂度
- ✅ **正确**：provider 顺序排序简单、可预测

### 7.3 设计不足的部分

**不足 1：参数类型转换未定义（见信息缺口 3）**

**不足 2：重试策略未定义（见信息缺口 1）**

**不足 3：异常捕获策略未定义（见信息缺口 2）**

**不足 4：Windows 兼容性未考虑（见信息缺口 4）**

**不足 5：数据落盘版本兼容性未考虑（见信息缺口 5）**

---

## 八、最终裁决

### 8.1 方案可编码性评分：7.5/10

**扣分项**：
- -1.0 分：信息缺口 1-2（重试策略、异常捕获），P1 级阻塞问题
- -0.5 分：信息缺口 3（参数类型转换），P2 级低优问题
- -0.5 分：信息缺口 4-5（Windows 兼容、数据落盘兼容性），P2 级低优问题
- -0.5 分：mcporter/MCP 版本兼容性未考虑

**得分项**：
- +1.0 分：R2 修正后，架构方向正确，组件边界清晰
- +1.0 分：Provider YAML 的 parameters 映射设计优秀
- +1.0 分：统一结果格式的 status 字段设计优秀
- +0.5 分：并发安全方案正确（文件锁 + 原子写入）
- +0.5 分：YAML 加载容错设计优秀
- +0.5 分：Fallback chain 设计优秀
- +0.5 分：三轮递进策略清晰
- +0.5 分：实施顺序合理

### 8.2 补全缺失信息后的评分：8.5/10

**补全后**：
- 补全信息缺口 1-2（重试策略、异常捕获） → +1.0 分
- 补全信息缺口 3-5（参数类型转换、Windows 兼容、数据落盘兼容性） → +0.5 分
- 明确 mcporter/MCP 版本兼容性 → +0.5 分

**最终评分**：7.5 + 1.0 + 0.5 + 0.5 = 8.5/10

### 8.3 进入 Phase 0 编码的前提条件

**必须补全的信息（P0 阻塞）**：
1. ✅ 重试策略（什么情况下重试、重试几次、退避策略、配额耗尽不重试）
2. ✅ 异常捕获策略（并行调用时如何捕获异常、异常是否影响其他 provider）

**建议补全的信息（P1 重要）**：
3. ✅ 参数类型转换（CLI 字符串如何转换为 MCP 参数的类型）
4. ✅ Windows 兼容性（原子写入、文件锁）
5. ✅ 数据落盘版本兼容性（新格式与旧格式不兼容、迁移策略）
6. ✅ mcporter/MCP 版本兼容性（mcporter 版本要求、MCP 协议版本）

### 8.4 可以立即开工的部分

**Phase 0 可以立即开工的部分**：
- ✅ config.py：YAML 加载、容错、加载报告
- ✅ mcp_client.py：MCPClient ABC 接口定义
- ✅ aggregator.py：URL 去重、provider 顺序排序
- ✅ cli.py：命令行参数解析（不含类型转换）
- ✅ schema.py：Provider YAML 校验规则
- ✅ fallback_chain.py：串行 fallback 逻辑

**需要补全信息后才能开工的部分**：
- ⏸️ engine.py：并行调用、异常捕获、重试策略（需要信息缺口 1-2）
- ⏸️ state.py：配额计数器的原子写入、Windows 兼容性（需要信息缺口 4）
- ⏸️ cli.py 参数类型转换（需要信息缺口 3）

---

## 九、总结

### 9.1 方案优势

1. **架构清晰**：组件边界明确，职责划分合理，易于编码实现
2. **接口设计优秀**：MCPClient ABC、统一结果格式、Provider YAML 描述符设计合理
3. **并发安全**：文件锁 + 原子写入方案正确，避免了竞态条件和文件损坏
4. **错误处理完善**：YAML 加载容错、Fallback chain、status 字段设计优秀
5. **两轮审查效果好**：R1 解决了 12 个架构问题，R2 解决了 7 个工程落地问题，方案趋于完善

### 9.2 方案不足

1. **信息缺口 1-2（P1 阻塞）**：重试策略、异常捕获策略未定义，导致 engine.py 无法开工
2. **信息缺口 3-5（P2 低优）**：参数类型转换、Windows 兼容性、数据落盘兼容性未考虑
3. **版本兼容性未考虑**：mcporter/MCP 版本兼容性、Windows 兼容性未明确
4. **辅助命令缺失**：`list-providers`、`--dry-run` 等调试辅助功能未定义

### 9.3 最终建议

**立即行动（进入 Phase 0 前必须完成）**：
1. 补全重试策略（文档中明确什么情况下重试、重试几次、退避策略）
2. 补全异常捕获策略（文档中明确并行调用的异常处理逻辑）
3. 补全参数类型转换（在 Provider YAML 中增加 `type` 字段，或在代码中硬编码）
4. 明确 Windows 兼容性（原子写入使用 `os.replace`、文件锁使用 `portalocker`）
5. 明确数据落盘版本兼容性（新格式 v2 与旧格式 v1 不兼容、迁移策略）
6. 明确 mcporter/MCP 版本兼容性（mcporter 版本要求、MCP 协议版本）

**Phase 0 编码可以立即开始**：
- config.py、mcp_client.py、aggregator.py、cli.py（参数解析）、schema.py、fallback_chain.py

**Phase 0 编码需要等待补全信息**：
- engine.py（并行调用、异常捕获、重试策略）
- state.py（配额计数器的原子写入、Windows 兼容性）
- cli.py 参数类型转换

**Phase 1-2 优化（可选）**：
- 添加 `list-providers` 子命令
- 添加 `--dry-run` 参数
- Provider YAML 增加 `enabled` 字段
- 结果格式增加 `round` 字段

---

**审查完毕。建议 Executor 在进入 Phase 0 编码前先补全 6 个关键信息（P0 阻塞 2 个 + P1 重要 4 个），总工作量约 1-2 小时的文档补充。补全后可编码性评分从 7.5/10 提升至 8.5/10，可以顺利进入 Phase 0 编码。**

---

*审查日期：2026-06-06*
*审查者：第三方代码审查者（Code Reviewer）*
*审查范围：BATTLE-R2 最终完整版设计（BATTLE-R2-EXECUTOR.md）*
