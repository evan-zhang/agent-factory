# BATTLE-R2 — 执行者回应与最终完整方案设计（Blue / Executor）

**执行者**：方案设计者（Executor）
**审查者**：Red（独立审查）
**审查标的**：BATTLE-R1 最终修订版
**状态**：R2 审查 → 逐一回应 → 输出最终完整版设计

---

## 一、逐条回应 R2 审查裁决

---

### Issue 1：MCP 参数映射缺失 — **ACCEPT**（P0 阻塞级）

**裁决**：REJECT

**回应**：接受裁决。这是 P0 级阻塞问题——编排器核心职责是"调用 MCP tool"，如果没有参数映射，编排器无法对不同 provider 生成正确的 MCP 调用参数。

**修正方案**：在 Provider YAML 的 `call` 节新增 `parameters` 子节，定义 normalized 参数名 → MCP tool 参数的映射关系、是否必填、默认值。执行引擎按照映射表对每个 provider 独立构建调用参数。

**新增的 YAML 结构**：
```yaml
call:
  timeout_ms: 30000
  retry: 2
  required_env: [BRAVE_API_KEY]
  parameters:
    query:
      mcp_param: "query"
      required: true
    count:
      mcp_param: "count"
      default: 10
    country:
      mcp_param: "country"
      default: "US"
    search_lang:
      mcp_param: "search_lang"
      default: "en"
    freshness:
      mcp_param: "freshness"
      default: null
```

执行引擎逻辑：
1. 接收 normalized 参数集（全局统一入参）
2. 查询 provider YAML 的 `call.parameters` 映射
3. 对每个 provider，只传入 mapped 参数，忽略未定义的
4. `required: true` 但未传入 → 抛出明确错误
5. `default` 有值但未传入 → 使用默认值
6. `default: null` → 不传该参数

生效位置：`orchestrator/config.py`（加载 YAML 时校验 parameters）、`orchestrator/engine.py`（构建调用时应用映射）

---

### Issue 2：安装分发链缺失 — **ACCEPT**（P0 阻塞级）

**裁决**：REJECT

**回应**：接受裁决。`search` 命令的安装路径和调用方式必须明确定义，否则 SKILL.md 和 calling agent 无法确定调用方式。

**修正方案**：推荐 方案 A（Skill 内嵌脚本 + SKILL_DIR 环境变量）。

**完整的安装和分发链**：

1. **Skill 安装后的目录结构**：
```
{skill_dir}/
├── SKILL.md                    # Skill 定义
├── orchestrator/               # 编排器代码
│   ├── cli.py                  # CLI 入口
│   ├── engine.py
│   └── ...
└── bin/
    └── search                  # shell wrapper：python3 {SKILL_DIR}/orchestrator/cli.py "$@"
```

2. **`search` 命令的实际执行路径**：
```bash
# SKILL.md 内部定义函数或 command_template
# orchestrator/bin/search 是 shell wrapper：
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
exec python3 "$SKILL_DIR/orchestrator/cli.py" "$@"
```

3. **SKILL.md 中如何调用**：
```yaml
# SKILL.md 中声明 command 或 inline function
# 方式一：通过 skill 的 tools.command 引用 wrapper
command: "{{skill_dir}}/bin/search"

# 方式二：通过 OpenClaw 的 inline function
function:
  search:
    command: python3 {skill_dir}/orchestrator/cli.py
```

4. **升级兼容性**：
- 旧版本如果直接调用 SKILL.md 中定义的搜索 help function，需要更新函数体指向新 CLI
- 迁移期内新旧搜索函数并存：`search_v1`（旧链）和 `search`（编排器）

5. **本地开发**：
```bash
# 本地开发直接调用
cd orchestrator/
python3 -m orchestrator.cli search query="..." intent="..."
```

6. **不推荐方案**：全局 pip install（污染环境）、uvx（需要 PyPI 发布）

---

### Issue 3：配额计数器竞态条件 — **ACCEPT**（P2 低优，附加条件）

**裁决**：APPROVE 附条件

**回应**：完全接受 Auditor 的 4 条附加条件。已纳入最终设计。

**修正**：
1. **原子写入**：`write temp → os.rename(temp, quota-state.json)`，避免写半截导致 JSON 损坏
2. **文件锁**：使用 `fcntl.flock`（Linux/macOS）或 `portalocker`，避免并发丢失计数
3. **读取失败降级**：JSON 解析失败时，记录警告，重置为空状态（used=0），所有 provider 配额充足
4. **文档注明**：此计数器仅用于路由决策，不用于计费。并发写入可能丢失少量计数，属于可接受范围。

---

### Issue 4：三轮递进策略丢失 — **ACCEPT**（P1 重要）

**裁决**：REJECT

**回应**：接受裁决。三轮递进是 multi-search 的核心策略，需要在编排器中明确安置。

**修正方案**：在 `intent-modes.yaml` 中为每个 intent 添加 `query_strategy` 定义，明确轮次执行策略。

```yaml
intent_modes:
  chinese-policy:
    strategy: hybrid
    external_timeout_ms: 15000
    providers: [minimax, brave, web_fetch]
    query_strategy:
      enabled: true                    # 是否启用三轮递进
      rounds:
        - mode: precise                # 精准：原样 query，要求高相关
          count: 5
          timeout_ms: 8000
          provider_filter: [minimax]   # 精准轮仅限这些 provider
        - mode: broaden                # 泛搜：扩展 query
          count: 10
          timeout_ms: 10000
          provider_filter: []          # 空 = 全部 intent provider
        - mode: fallback               # 兜底：全部 provider 不限条件
          count: 15
          timeout_ms: 12000
          provider_filter: []
      round_termination:               # 提前终止条件
        min_results: 3                 # 当前轮达到 N 条即不执行后续轮次
        max_rounds: 3                  # 最大轮次数

  general:
    strategy: parallel
    external_timeout_ms: 10000
    providers: [all]
    query_strategy:
      enabled: false                   # 通用搜索不做三轮递进
```

**执行引擎的三轮递进逻辑**：
1. 先执行 precise 轮（仅限指定 provider），达到 min_results 则终止
2. 未达标时执行 broaden 轮（扩展 query + 全部 provider）
3. 仍不达标时执行 fallback 轮（降门槛 + 全部 provider）
4. 三轮结果去重后返回

**扩张 query 的策略**：当前版本暂不实现 query 改写（需要 LLM 介入）。三轮递进仅通过扩展 provider 范围 + 增大 count 实现"泛搜"和"兜底"。query 改写作为未来优化项。

---

### Issue 5：结果格式缺少 status 字段 — **ACCEPT**（P1 重要）

**裁决**：REJECT

**回应**：接受裁决。调用方需要顶层字段来判断结果质量状态。

**修正方案**：在统一输出格式顶层新增 `status` 和 `error` 字段。

```
OrchestratorSearchResult:
  required: [version, status, provider, query, items, metadata]
  properties:
    version: "1.0"
    status: ok | partial | no_match | all_failed | error
    error: string (仅在 status=error 时存在)
    provider: "orchestrator"
    query: "社保缴费比例"
    items: [...]
    metadata:
      engines_tried: [brave, minimax]
      engines_succeeded: [brave]
      engines_failed: [{engine: "minimax", reason: "timeout"}]
      ...
```

| status | items | 含义 |
|--------|-------|------|
| ok | 有结果 | 至少一个 engine 返回了结果，无失败 |
| partial | 有结果 | 部分 engine 失败但仍有结果 |
| no_match | [] | 所有 engine 正常但无匹配 |
| all_failed | [] | 所有 engine 失败，调用方应回退 |
| error | [] | 编排器自身出错 |

调用方单行模式匹配即可决定后续逻辑。

---

### Issue 6：intent 列表不可见 — **ACCEPT**（P1 重要）

**裁决**：REJECT

**回应**：接受裁决。调用方需要知道可选 intent 列表。

**修正方案**：在 `search` CLI 中添加 `list-intents` 子命令。

```bash
search list-intents --format json

→
{
  "intents": [
    {
      "name": "chinese-policy",
      "description": "中文政策法规搜索，优先使用支持中文语义的引擎",
      "providers": ["minimax", "brave", "web_fetch"]
    },
    {
      "name": "english-academic",
      "description": "英文学术论文/技术文档搜索",
      "providers": ["brave", "tavily", "heventure_ddg"]
    },
    {
      "name": "news",
      "description": "新闻搜索，含时效性排序",
      "providers": ["brave_news", "minimax"]
    },
    {
      "name": "general",
      "description": "通用搜索，默认意图",
      "providers": ["all"]
    }
  ]
}
```

调用方在初始化时调用 `search list-intents` 并缓存，可以：
- 在用户交互时展示可选意图
- 新增 intent 后自动感知

---

### Issue 7：旧链无实现 — **ACCEPT**（P1 重要）

**裁决**：REJECT

**回应**：接受裁决。方案 A（旧链作为编排器的内置 fallback）是最合理的选择。

**修正方案**：在 `orchestrator/` 中实现 `fallback_chain` 模块。

```
orchestrator/
├── fallback_chain.py      # 新：串行按优先级执行 provider 的 fallback 链
```

`fallback_chain.py` 职责：
1. 接收 provider 优先级列表（按 provider YAML 注册顺序或独立的 `fallback_order.yaml`）
2. 串行逐个调用，一个失败立即尝试下一个
3. 任意成功返回该 provider 的结果
4. 全部失败 → `status: all_failed`
5. 每个 provider 调用有自己的超时

```yaml
# 独立的 fallback_order.yaml（可选，不必须）
fallback_order:
  - minimax
  - brave
  - tavily
  - exa
  - web_fetch
```

**新旧关系**：
- 编排器正常执行（带 intent 路由）→ 执行引擎按 intent 策略调用
- 编排器全部失败 → `fallback_chain` 串行逐个尝试所有 provider
- fallback_chain 本身也是编排器的一部分，不依赖外部脚本
- 旧 SKILL.md 的线性降级链描述降级为"参考文档"

---

## 二、额外盲点逐一回应

---

### Blind Spot 1：输入参数接口未定义 — **重大**，已纳入 Phase 0

**回应**：接受。必须在 Phase 0 明确 CLI 完整参数列表。

**`search` CLI 完整参数规范（v1.0）**：

```
search [command] [options]

子命令：
  search             执行搜索（默认子命令）
  probe <name>      对指定 provider 执行健康检查
  list-intents      列出可用 intent 列表

search 子命令参数：
  --query, -q        STRING  必填    搜索查询
  --intent, -i       STRING  可选    搜索意图，默认 "general"
  --count, -c        INT     可选    返回结果数，默认 10，范围 [1, 50]
  --max-timeout      INT     可选    全局超时(ms)，默认 15000，范围 [1000, 60000]
  --freshness        STRING  可选    时效性，day/week/month/year/null，默认 null
  --country          STRING  可选    地域限定，ISO 3166-1 alpha-2，默认空
  --search-lang      STRING  可选    搜索语言，BCP 47，默认空
  --offset           INT     可选    分页偏移量，默认 0，范围 [0, 1000]
  --safe-search      BOOL    可选    安全搜索，默认 true
  --format           STRING  可选    输出格式，json（默认）/text
  --debug            BOOL    可选    调试模式，默认 false

probe 子命令参数：
  <name>             STRING  必填    Provider 名称
  --timeout          INT     可选    探测超时(ms)，默认 5000

list-intents 子命令参数：
  --format           STRING  可选    输出格式，json（默认）/text

环境变量：
  SKILL_DIR          STRING  可选    Skill 根目录（用于定位 provider 配置）
```

**SKILL.md 中 search command_template 定义**：
```yaml
# command_template 中的参数占位符
# {query} {intent} {count} {max_timeout} 由 calling agent 填充
command: "python3 {skill_dir}/orchestrator/cli.py search --query \"{query}\" --intent \"{intent}\" --count {count} --max-timeout {max_timeout} --format json"
```

---

### Blind Spot 2：Provider YAML 加载容错 — **重大**，已纳入 Phase 0

**回应**：接受。必须在 Phase 0 实现 YAML 加载容错机制。

**加载逻辑**：

```
load_providers(providers_dir):
    loaded = []
    skipped = []
    for yaml_file in glob(providers_dir + "/*.yaml"):
        try:
            data = yaml.safe_load(read_file(yaml_file))
            validate_provider_schema(data)   # 校验必填字段
            loaded.append(ProviderDescriptor(data))
        except yaml.YAMLError as e:
            skipped.append({file: yaml_file, reason: f"YAML syntax error: {e}"})
            continue
        except ValidationError as e:
            skipped.append({file: yaml_file, reason: f"Missing required field: {e}"})
            continue
    # 输出加载报告
    log(f"Loaded {len(loaded)}/{len(loaded) + len(skipped)} providers")
    for s in skipped:
        log(f"  SKIPPED: {s[file]} — {s[reason]}")
    return loaded
```

**必填字段校验规则**：
```
required_fields = [
    "name",           # 字符串，provider 唯一标识
    "type",           # 字符串，mcp / http / mock
    "tool",           # 字符串，MCP tool 名称
    "capabilities",   # 对象，至少包含 languages / content_types 之一
    "call",           # 对象
    "call.timeout_ms",    # 整数
    "call.parameters",    # 对象
    "call.parameters.query",  # 对象，至少有一个 query 参数
]
```

**Schema 校验独立的 concern**：当前使用简单字段校验，未来可迁移到 JSON Schema。不在 Phase 0 引入 JSON Schema 依赖。

---

### Blind Spot 3：结果聚合策略未定义 — **中等**，Phase 1 补充

**回应**：接受。补充聚合策略定义。

**聚合策略 v1.0（明确说"简单方案"）**：

1. **去重**：以 URL 为主键去重。同一 URL 出现多次时保留第一个（按 provider 在 intent 配置中的顺序）。不检查 title/snippet 相似度。
2. **排序**：按 provider 在 intent 配置中的顺序排列。同一 provider 内保持原始返回顺序。不按评分/时间/相关性排序。
3. **截断**：默认截断至 `count` 条（CLI 传入的 count 参数）。如果去重后不足 count，则全部返回。
4. **特殊处理**：同底层引擎的 provider（如 brave + brave_news）的结果也去做重。因为 URL 是全局唯一的。

示例：
```yaml
# intent 配置
chinese-policy:
  providers: [minimax, brave, web_fetch]
```
MiniMax 返回 5 条 → Brave 返回 8 条（其中 2 条 URL 与 MiniMax 重复）→ web_fetch 返回 3 条（1 条重复）
→ 去重后: (5 + 6 unique + 2 unique) = 13 条 → 截断至 count=10 → 输出 10 条
→ 排序：MiniMax(5) + Brave(5) → 按 intent provider 顺序和各自原始顺序

**未来优化方向**：相关性排序、时间倒序、provider 权重排序。在第一版中不实现。

---

### Blind Spot 4：MCPClient 接口未定义 — **中等**，纳入 Phase 0

**回应**：接受。在 Phase 0 给出 MCPClient 的 Python protocol/ABC 定义，不依赖具体运行时。

```python
# orchestrator/mcp_client.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class MCPToolResult:
    """MCP tool 调用返回结果"""
    success: bool
    data: Any                         # 解析后的数据
    raw: str                          # 原始响应（用于调试）
    latency_ms: int                   # 调用耗时

@dataclass
class MCPToolDefinition:
    """MCP tool 的能力描述"""
    name: str
    description: str
    input_schema: Dict[str, Any]      # JSON Schema

class MCPClient(ABC):
    """
    MCP Client 抽象接口。
    不依赖具体运行时（OpenClaw mcporter vs Hermes direct stdio）。
    """

    @abstractmethod
    async def list_tools(self) -> List[MCPToolDefinition]:
        """列出 MCP Server 支持的所有 tool"""
        ...

    @abstractmethod
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout_ms: int = 30000,
    ) -> MCPToolResult:
        """调用 MCP tool，返回结果"""
        ...

    @abstractmethod
    async def health_check(self, timeout_ms: int = 5000) -> bool:
        """检查 MCP Server 是否存活"""
        ...
```

**OpenClaw 实现（mcporter 版本）**：
```python
class McporterMCPClient(MCPClient):
    """
    通过 mcporter 子进程与 MCP Server 通信。
    mcporter 负责进程管理和生命周期。
    """
    def __init__(self, mcporter_url: str, server_name: str):
        self.mcporter_url = mcporter_url
        self.server_name = server_name

    async def list_tools(self) -> List[MCPToolDefinition]:
        # 通过 mcporter 的 HTTP API 调用 MCP 的 tools/list
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"{self.mcporter_url}/mcp/{self.server_name}/tools/list",
                timeout=aiohttp.ClientTimeout(total=10)
            )
            ...

    async def call_tool(self, tool_name, arguments, timeout_ms=30000) -> MCPToolResult:
        # 通过 mcporter HTTP API 调用
        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    f"{self.mcporter_url}/mcp/{self.server_name}/call",
                    json={"tool": tool_name, "arguments": arguments},
                    timeout=aiohttp.ClientTimeout(total=timeout_ms/1000)
                )
                data = await resp.json()
                return MCPToolResult(
                    success=True,
                    data=data,
                    raw=str(data),
                    latency_ms=int((time.time() - start) * 1000)
                )
        except Exception as e:
            return MCPToolResult(
                success=False,
                data=None,
                raw=str(e),
                latency_ms=int((time.time() - start) * 1000)
            )

    async def health_check(self, timeout_ms=5000) -> bool:
        try:
            tools = await self.list_tools()
            return len(tools) > 0
        except Exception:
            return False
```

---

### Blind Spot 5：Intent→Capabilities 自动匹配 — **中等**，仅标注

**回应**：接受标注。在最终版设计文档中明确标注此局限性。

**已在最终设计中标明**（见 §3.2 配置总纲 → **已知局限性** 节）：
- 当前 intent→provider 是静态映射，不与 provider capabilities 自动匹配
- 添加新 provider 后需要手动更新 intent 映射表
- 未来可能的优化方向：基于 capabilities 的自动匹配（不在 v1.0 范围内）

---

## 三、最终完整版设计（集成所有 R1+R2 修订）

### 3.1 架构总图

```
┌──────────────────────────────────────────────────────────────┐
│                        调用方（Caller）                        │
│   search --query "..." --intent chinese-policy               │
└────────────────────────┬─────────────────────────────────────┘
                         │ CLI: python3 {skill_dir}/orchestrator/cli.py
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    Search Orchestrator                        │
│                                                              │
│  ┌────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │ CLI 入口    │  │ 执行引擎        │  │ 结果聚合器         │   │
│  │ search     │─▶│ 并行/串行/     │─▶│ 去重 + 格式化 +   │   │
│  │ probe      │  │ hybrid 调度    │  │ status 赋值       │   │
│  │ list-intents│  │ 三轮递进管理   │  └─────────┬─────────┘   │
│  └────────────┘  └───────┬───────┘            │             │
│                          │                     │             │
│  ┌────────────┐  ┌───────┴───────┐  ┌─────────┴─────────┐   │
│  │ 配置加载器   │  │ Provider 池   │  │ 状态管理器         │   │
│  │ YAML 目录   │  │ 各 provider   │  │ 健康 + 配额缓存    │   │
│  │ 容错加载    │  │ 参数映射构建  │  │ 原子写入 + 文件锁   │   │
│  └────────────┘  └───────┬───────┘  └───────────────────┘   │
│                          │                                    │
│  ┌────────────┐  ┌───────┴───────┐                          │
│  │ Fallback   │  │ MCPClient     │                          │
│  │ Chain      │  │ 抽象层         │                          │
│  │ 串行兜底    │  │ mcporter/     │                          │
│  └────────────┘  │ Hermes 实现   │                          │
│                   └───────────────┘                          │
└──────────────────────────────────────────────────────────────┘
                            │ MCP 协议
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  MCP Server  │  │  MCP Server  │  │  MCP Server  │
│  Brave       │  │  MiniMax     │  │  Tavily      │
│  (mcporter)  │  │  (mcporter)  │  │  (mcporter)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 3.2 配置总纲

#### Provider YAML 描述符（完整版，含 parameters 映射）

```yaml
# providers/brave.yaml
name: brave
type: mcp
tool: brave_web_search
description: Brave Search API，覆盖网页/新闻/图片，免费配额 2000 次/月

cost_tier: 1               # 0=免费无限 1=免费限配额 2=付费 3=价格高

capabilities:
  languages: [en, multi]
  content_types: [web, news, video, image]
  regions: [global]
  special: [llm_context, summarizer]

health_check:
  method: mcp_list_tools
  timeout_ms: 5000

quota:
  type: monthly
  limit: 2000
  reset_day: 1

call:
  timeout_ms: 30000
  retry: 2
  required_env: [BRAVE_API_KEY]
  parameters:
    query:
      mcp_param: "query"
      required: true
    count:
      mcp_param: "count"
      default: 10
    country:
      mcp_param: "country"
      default: "US"
    search_lang:
      mcp_param: "search_lang"
      default: "en"
    freshness:
      mcp_param: "freshness"
      default: null
    offset:
      mcp_param: "offset"
      default: 0
    safe_search:
      mcp_param: "safe_search"
      default: "moderate"
```

```yaml
# providers/minimax.yaml
name: minimax
type: mcp
tool: minimax_web_search
description: MiniMax 搜索 API，对中国政策/中文内容有较好覆盖

cost_tier: 1
capabilities:
  languages: [zh, en]
  content_types: [web, news]
  regions: [cn, global]
  special: []

health_check:
  method: mcp_list_tools
  timeout_ms: 5000

quota:
  type: weekly
  limit: 500
  reset_day: 1

call:
  timeout_ms: 30000
  retry: 2
  required_env: [MINIMAX_API_KEY]
  parameters:
    query:
      mcp_param: "query"
      required: true
    # MiniMax 忽略 count/country/search_lang/freshness/offset/safe_search
    # 这些参数在调用时自动过滤
```

```yaml
# providers/tavily.yaml
name: tavily
type: mcp
tool: tavily_search
description: Tavily AI-Optimized Search，针对 LLM 场景优化

cost_tier: 2
capabilities:
  languages: [en]
  content_types: [web, news]
  regions: [global]
  special: [llm_context, deep_search]

health_check:
  method: mcp_list_tools
  timeout_ms: 5000

quota:
  type: monthly
  limit: 1000
  reset_day: 1

call:
  timeout_ms: 45000
  retry: 1
  required_env: [TAVILY_API_KEY]
  parameters:
    query:
      mcp_param: "query"
      required: true
    count:
      mcp_param: "max_results"
      default: 10
    search_depth:
      mcp_param: "search_depth"
      default: "basic"
    freshness:
      mcp_param: "time_range"
      default: null
    safe_search:
      mcp_param: "include_answer"
      default: false
```

```yaml
# providers/exa.yaml
name: exa
type: mcp
tool: exa_search
description: Exa Search，专注深度搜索和企业级内容

cost_tier: 3
capabilities:
  languages: [en]
  content_types: [web, news, company]
  regions: [global]
  special: [deep_search, enterprise]

health_check:
  method: mcp_list_tools
  timeout_ms: 5000

quota:
  type: pay_per_call
  limit: null
  reset_day: null

call:
  timeout_ms: 60000
  retry: 1
  required_env: [EXA_API_KEY]
  parameters:
    query:
      mcp_param: "query"
      required: true
    count:
      mcp_param: "num_results"
      default: 10
    country:
      mcp_param: "country"
      default: null
    include_domains:
      mcp_param: "include_domains"
      default: []
    exclude_domains:
      mcp_param: "exclude_domains"
      default: []
```

```yaml
# providers/web_fetch.yaml
name: web_fetch
type: mcp
tool: fetch
description: URL 抓取器，无搜索引擎，用于获取指定 URL 内容

cost_tier: 0
capabilities:
  languages: [all]
  content_types: [web]
  regions: [global]
  special: [fetch_only]

health_check:
  method: mcp_list_tools
  timeout_ms: 5000

quota:
  type: unlimited
  limit: null
  reset_day: null

call:
  timeout_ms: 15000
  retry: 1
  required_env: []
  parameters:
    url:
      mcp_param: "url"
      required: true
    # web_fetch 只需要 url 参数，不需要 query/count等
```

#### Intent-modes.yaml（完整版，含三轮递进配置）

```yaml
# orchestrator/intent-modes.yaml
#
# 注意：intent→provider 是静态映射，不与 provider capabilities 自动匹配。
# 添加新 provider 后需要手动更新此文件。

intent_modes:

  chinese-policy:
    description: "中文政策法规搜索，优先 MiniMax（中文语义），兜底 Brave"
    strategy: hybrid
    external_timeout_ms: 15000
    providers: [minimax, brave, web_fetch]
    query_strategy:
      enabled: true
      rounds:
        - mode: precise
          count: 5
          timeout_ms: 8000
          provider_filter: [minimax]
        - mode: broaden
          count: 10
          timeout_ms: 10000
          provider_filter: []
        - mode: fallback
          count: 15
          timeout_ms: 12000
          provider_filter: []
      round_termination:
        min_results: 3
        max_rounds: 3

  english-academic:
    description: "英文学术论文/技术文档搜索，优先 Brave 和 Tavily"
    strategy: parallel
    external_timeout_ms: 20000
    providers: [brave, tavily, exa]
    query_strategy:
      enabled: false

  news:
    description: "新闻搜索，含时效性排序"
    strategy: parallel
    external_timeout_ms: 10000
    providers: [brave_news, minimax]
    query_strategy:
      enabled: false

  general:
    description: "通用搜索，默认意图，全部 provider 并行"
    strategy: parallel
    external_timeout_ms: 10000
    providers: [all]
    query_strategy:
      enabled: false
```

#### Fallback 链配置（可选）

```yaml
# orchestrator/fallback_order.yaml
# 旧线性降级链的 provider 优先级顺序
# 仅在 orchestator 全部失败时使用

fallback_order:
  - minimax
  - brave
  - tavily
  - exa
  - web_fetch
  - heventure_ddg
```

不提供此文件时，fallback_chain 按 provider 加载顺序尝试。

### 3.3 统一结果格式（完整版，含 status）

```yaml
# 编排器统一输出格式 v1.0
OrchestratorSearchResult:
  type: object
  required: [version, status, provider, query, items, metadata]

  properties:
    version:
      type: string
      description: Schema 版本号，默认为 "1.0"，变更时递增次版本
      example: "1.0"

    status:
      type: string
      enum: [ok, partial, no_match, all_failed, error]
      description: |
        ok: 至少一个 provider 返回了结果（全部无失败）
        partial: 部分 provider 失败但仍有结果
        no_match: 所有 provider 正常但返回 0 结果
        all_failed: 所有 provider 失败（超时/异常/配额）
        error: 编排器自身出错（配置错误/CLI 异常）

    error:
      type: string
      description: 仅在 status=error 时存在，说明错误原因
      nullable: true
      example: "Provider YAML 加载失败: orchestrator/providers/brave.yaml 未找到"

    provider:
      type: string
      description: 名义 provider 名称（聚合结果时为 "orchestrator"）
      example: "orchestrator"

    query:
      type: string
      description: 实际执行的查询（当前版本不做查询改写）
      example: "社保缴费比例"

    items:
      type: array
      description: 搜索结果条目列表
      items:
        type: object
        required: [title, url, snippet, source_engine]
        properties:
          title:
            type: string
            description: 结果标题
          url:
            type: string
            description: 结果链接（去重主键）
            format: uri
          snippet:
            type: string
            description: 结果摘要
          source_engine:
            type: string
            description: 原始来源引擎名称
            example: "brave"
          published_date:
            type: string
            description: 发布日期（如果来源提供）
            format: date
            nullable: true
          score:
            type: number
            description: 来源提供的排序分（如果有）
            nullable: true
          content_type:
            type: string
            description: 内容类型提示
            enum: [policy, news, general, academic, technical]
            nullable: true

    metadata:
      type: object
      required: [engines_tried, engines_succeeded, total_latency_ms, intent, strategy]

      properties:
        engines_tried:
          type: array
          items: { type: string }
          example: ["brave", "minimax", "tavily"]

        engines_succeeded:
          type: array
          items: { type: string }
          example: ["brave", "minimax"]

        engines_failed:
          type: array
          items:
            type: object
            properties:
              engine: { type: string }
              reason:
                type: string
                enum: [timeout, exception, quota_exhausted, no_match]
          example:
            - engine: "tavily"
              reason: "quota_exhausted"

        total_latency_ms:
          type: integer
          description: 从调用到返回的总耗时
          example: 2847

        quota_impact:
          type: object
          additionalProperties: { type: integer }
          description: 本次调用对各 provider 配额的消耗情况
          example:
            brave: 1
            minimax: 0
            tavily: 0

        intent:
          type: string
          description: 本次搜索的意图
          example: "chinese-policy"

        strategy:
          type: string
          enum: [serial, parallel, hybrid]
          description: 执行策略
          example: "hybrid"

        round:
          type: string
          description: 三轮递进当前执行到的轮次（仅在 query_strategy.enabled=true 时存在）
          enum: [precise, broaden, fallback]
          nullable: true
          example: "precise"
```

### 3.4 CLI 规范

```
search [command]

子命令:
  search                 执行搜索（默认子命令）
  probe <name>          健康检查指定 provider
  list-intents          列出可用 intent 列表

search 子命令:
  --query, -q        STRING  必填    搜索查询
  --intent, -i       STRING  可选    默认 "general"
  --count, -c        INT     可选    默认 10，范围 [1,50]
  --max-timeout      INT     可选    默认 15000(ms)，范围 [1000,60000]
  --freshness        STRING  可选    day/week/month/year/null
  --country          STRING  可选    ISO 3166-1 alpha-2
  --search-lang      STRING  可选    BCP 47
  --offset           INT     可选    默认 0，范围 [0,1000]
  --safe-search      BOOL    可选    默认 true
  --format           STRING  可选    json(默认)/text
  --debug            BOOL    可选    默认 false

probe 子命令:
  <name>             STRING  必填
  --timeout          INT     可选    默认 5000(ms)

list-intents 子命令:
  --format           STRING  可选    json(默认)/text
```

### 3.5 聚合策略

**v1.0 简略策略**：
1. **去重**：以 URL 为主键。同 URL 出现多次保留第一个（按 intent provider 顺序）。
2. **排序**：按 provider 在 intent 配置中的顺序排列。同 provider 内保持原始顺序。
3. **截断**：至多 `count` 条。不足 count 则全部返回。
4. **不过度设计**：不实现相关性排序、时间倒序、权重排序。

---

### 3.6 MCPClient 接口定义

（见本文档 §二-Blind Spot 4 中的 Python protocol/ABC 定义）

文件位置：`orchestrator/mcp_client.py`（Phase 0 输出）

两个实现：
- `McporterMCPClient` — 通过 mcporter HTTP API 调用（Phase 0）
- `DirectStdioMCPClient` — 直接 MCP stdio 通信（Phase 2，Hermes 平台）

---

### 3.7 Provider YAML 加载容错

（见本文档 §二-Blind Spot 2 中的加载逻辑）

核心原则：
- 逐文件加载，互不影响
- 格式错误/缺字段 → 跳过并记录警告
- 最终输出加载报告：`Loaded 5/6 providers, 1 skipped (reason)`

---

### 3.8 配额计数器

**文件**：`_runtime/quota-state.json`

**写入规则**：
- 原子写入：write temp → os.rename(temp, quota-state.json)
- 文件锁：fcntl.flock（跨平台用 portalocker）
- 读取失败时降级：重置为空状态，记录警告

**已知局限性**：
- 仅用于路由决策，不用于计费
- 并发写入可能丢失少量计数，属于可接受范围

---

### 3.9 已知局限性

1. **Intent→Capabilities 自动匹配缺失**：当前 intent→provider 是静态映射，不与 provider capabilities 自动匹配。添加新 provider 后需要手动更新 intent 映射表。未来可能的优化方向：基于 capabilities 的自动匹配（不在 v1.0 范围内）。

2. **三轮递进不做 query 改写**：当前版本的三轮递进仅通过扩展 provider 范围 + 增大 count 实现"泛搜"和"兜底"。query 改写（加引号、site:限定、同义词扩展）需要 LLM 介入，作为未来优化项。

3. **结果不进行相关性排序**：v1.0 按 provider 顺序排列。未来可以引入基于语义的相关性排序，但当前不做。

4. **配额近似值**：并发写入可能丢失计数，但仅用于路由决策，不做计费。

---

### 3.10 实施顺序

```
Phase 0（基础设施）：
  ├─ Python 异步库框架 + CLI 入口（search, probe, list-intents）
  ├─ Provider YAML 描述符目录 + parameters 映射
  ├─ 配置加载器（逐文件加载 + 容错处理 + 加载报告）
  ├─ 统一结果格式 v1.0（含 status 字段）
  ├─ 按需健康探测 + 60s 缓存
  ├─ MCPClient 抽象层接口定义（ABC）+ McporterMCPClient 实现
  ├─ 完整 CLI 参数规范（query, intent, count, max_timeout 等）
  └─ fallback_chain 模块（串行兜底 + fallback_order.yaml）

Phase 1（功能）：
  ├─ Intent 映射表 + intent-modes.yaml（含 query_strategy）
  ├─ 并行/串行/混合执行引擎（含全局超时管理）
  ├─ 三轮递进逻辑（round_termination, provider_filter）
  ├─ 结果聚合去重（URL 主键 + provider 顺序）
  ├─ 失败处理 + fallback_chain 回退
  └─ Phase 1→Phase 2 共存配置

Phase 2（运维）：
  ├─ 配额本地追踪 + 原子写入 + 文件锁
  ├─ Provider 状态缓存持久化
  ├─ 调试日志（谁调了什么、耗时、结果、决策链路）
  ├─ Hermes DirectStdioMCPClient 实现
  └─ 数据落盘 schema 更新
```

---

### 3.11 目录结构（最终版）

```
orchestrator/
├── __init__.py                  # 模块入口
├── cli.py                      # CLI 入口（search, probe, list-intents）
├── engine.py                   # 执行引擎（调度 + 三轮递进管理）
├── aggregator.py               # 结果聚合去重 + status 赋值
├── fallback_chain.py           # 串行 fallback 兜底
├── config.py                   # 配置加载器（YAML 目录扫描 + 容错）
├── state.py                    # 状态管理器（健康 + 配额缓存，原子写入）
├── mcp_client.py               # MCPClient ABC + McporterMCPClient 实现
├── schema.py                   # Provider YAML 校验规则
├── providers/                  # Provider YAML 描述符目录
│   ├── brave.yaml
│   ├── minimax.yaml
│   ├── tavily.yaml
│   ├── exa.yaml
│   ├── web_fetch.yaml
│   └── heventure_ddg.yaml
├── intent-modes.yaml           # 意图映射配置（含 query_strategy）
├── fallback_order.yaml         # Fallback 链优先级（可选）
└── _runtime/                   # 运行时状态（gitignored）
    └── quota-state.json        # 本地配额计数器
```

---

## 四、R2 汇总

### 7 个问题裁决回应汇总

| # | 问题 | R2 裁决 | 执行者回应 | 优先级 | 修正动作 |
|---|------|---------|-----------|--------|---------|
| 1 | MCP 参数映射缺失 | REJECT | **ACCEPT** | P0 | Provider YAML 加 call.parameters 节 |
| 2 | 安装分发链缺失 | REJECT | **ACCEPT** | P0 | 明确 scheme A + search 调用路径 |
| 3 | 配额计数器竞态 | APPROVE 附条件 | **ACCEPT** | P2 | 原子写入 + 文件锁 + 降级 |
| 4 | 三轮递进丢失 | REJECT | **ACCEPT** | P1 | intent-modes.yaml 加 query_strategy |
| 5 | 缺少 status | REJECT | **ACCEPT** | P1 | 顶层加 status/error 字段 |
| 6 | intent 不可见 | REJECT | **ACCEPT** | P1 | CLI 加 list-intents 子命令 |
| 7 | 旧链无实现 | REJECT | **ACCEPT** | P1 | orchestrator 内实现 fallback_chain |

### 5 个盲点回应汇总

| # | 盲点 | 严重程度 | 修正 |
|---|------|---------|------|
| 1 | 输入参数接口未定义 | 重大 | Phase 0 前完成 CLI 参数规范定义 |
| 2 | YAML 加载容错未定义 | 重大 | Phase 0 实现逐文件加载 + 容错 + 加载报告 |
| 3 | 聚合策略未定义 | 中等 | Phase 1 按"URL 去重 + provider 顺序"策略 |
| 4 | MCPClient 接口未定义 | 中等 | Phase 0 输出 ABC + McporterMCPClient 实现 |
| 5 | Intent→Capabilities 自动匹配 | 中等 | 标注局限性，不在 v1.0 范围内 |

### 进入 Phase 0 编码的前提条件（全部满足）

1. ✅ Provider YAML 增加 parameters 映射定义（§3.2）
2. ✅ 明确 search CLI 的完整输入参数规范（§3.4）
3. ✅ 明确安装分发链（§一-Issue 2）
4. ✅ 明确 Phase 0 MCPClient 的接口定义（§3.6）
5. ✅ Provider YAML 加载容错机制（§3.7）

### 进入 Phase 1 编码的前提条件

1. ✅ 三轮递进策略安置（§3.2 intent-modes.yaml）
2. ✅ status 字段纳入统一输出格式（§3.3）
3. ✅ list-intents 子命令（§3.4）

---

*修正完毕。R1 R2 全部 12+7 个问题 + 5 个盲点已纳入最终设计。可进入 Phase 0 编码。*
