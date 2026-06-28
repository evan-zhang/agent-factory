# Multi-Search Search Orchestrator

## 架构总览

```
Phase 0 — Infrastructure Layer (已完成)
Phase 1 — 执行引擎增强 (已完成)
Phase 2 — 智能路由 + 质量评分 + LLM 查询改写 (已完成)
```

### Phase 2 数据流

```
SearchRequest
    ↓
[LLM Query Agent] ──可选──→ EnhancedQueryIntent (provider_scores + 改写query)
(默认 disabled)      ↓ 失败降级
    ↓
[Adaptive Router] ──可选──→ RoutingDecision (动态选择最优 provider)
(默认 disabled)      ↓ 降级到静态路由
    ↓
[Execution Engine] ────────→ 并行/串行执行多个 provider
    ↓
[Result Quality Scorer] ──→ 按权威性/时效性/相关性加权排序
(总是启用)
    ↓
OrchestratorSearchResult (items 已按质量排序)
```

## 目录结构

```
orchestrator/
├── __init__.py                # 包入口 + logging 配置
├── cli.py                    # CLI 入口（search, probe, list-intents, list-providers, status）
├── config.py                 # 配置加载器（扫描 providers/*.yaml + intent-modes.yaml）
├── engine.py                 # 执行引擎（并行/串行/三轮递进调度）
├── aggregator.py             # 结果聚合去重 + status 赋值
├── fallback_chain.py         # 串行 fallback 兜底
├── state.py                  # 状态管理器（健康 60s 缓存 + 配额原子计数器）
├── mcp_client.py             # MCPClient ABC + McporterMCPClient 实现
├── cache.py                  # 进程级内存缓存（可选 TTL）
├── schema.py                 # 所有 Python dataclass 定义
├── llm_agent.py              # Phase 2 R1: LLM Query Agent（可选，默认关闭）
├── scorer.py                 # Phase 2 R2: Result Quality Scorer（总是启用）
├── router.py                 # Phase 2 R3: Adaptive Provider Router（可选，默认关闭）
├── providers/                # Provider YAML 描述符目录
│   ├── brave.yaml
│   ├── minimax.yaml
│   ├── tavily.yaml
│   └── web_fetch.yaml
├── intent-modes.yaml         # 意图映射配置
├── fallback_order.yaml       # Fallback 链优先级
├── _runtime/                 # 运行时状态（gitignored）
│   ├── quota-state.json      # 本地配额计数器
│   └── router-perf.json      # Adaptive Router 性能数据
└── tests/                    # 测试集
    ├── test_engine.py        # 引擎单元测试（35 项）
    ├── test_integration.py   # 集成测试（26 项）
    ├── test_e2e.py           # 端到端测试（18 项）
    ├── test_llm_agent.py     # LLM Query Agent 测试
    ├── test_scorer.py        # Quality Scorer 测试
    └── test_router.py        # Adaptive Router 测试
```

## 关键特性

### Phase 0 — 基础设施
✅ **Python 3.9+ 兼容**
✅ **最小外部依赖**：aiohttp, PyYAML, portalocker
✅ **完整类型注解**：mypy 可通过
✅ **asyncio.ALL_COMPLETED 并发控制**
✅ **Fallback 触发条件**：status=all_failed/error/no_match 时触发
✅ **Provider 参数映射**：读取 YAML 的 call.parameters
✅ **结果字段映射**：读取 YAML 的 call.result_mapping
✅ **配额计数器**：portalocker 文件锁 + 原子写入
✅ **健康状态缓存**：60 秒 TTL
✅ **进程级缓存**：LRU 淘汰 + TTL 过期

### Phase 1 — 执行引擎增强
✅ **重试逻辑**：RetryableError 重试 3 次，指数退避
✅ **三轮递进检索**：精准→泛搜→兜底，提前终止
✅ **query_template 占位符**：精准轮加引号
✅ **结构化日志**：A4 标准
✅ **性能监控**：_perf_data 进程级内存

### Phase 2 — 智能路由、质量评分、LLM 查询改写

#### LLM Query Agent（Phase 2 R1）
- **可选组件**：默认 disabled，需用户显式启用
- **功能**：对原始 query 做 LLM 意图理解，生成多版本优化查询
- **provider_scores**：LLM 评估每个 provider 的适配度
- **site_restrictions**：政策类查询自动建议 site:gov.cn 等
- **降级策略**：LLM API 失败时自动降级，不影响搜索主流程
- **缓存**：相同 query 在 cache_ttl 内命中

#### Result Quality Scorer（Phase 2 R2）
- **总是启用**：所有搜索结果自动按质量评分排序
- **三个维度**：
  - 权威性（authority）：基于 URL 域名评估可信度（gov.cn=1.0, edu.cn=0.8, ...）
  - 时效性（freshness）：基于发布日期评估信息新鲜度（30天内=1.0, ...）
  - 相关性（relevance）：基于关键词在 title/snippet 中的覆盖度
- **可配置权重**：通过 ScorerConfig 调整各维度权重
- **稳定排序**：评分相同时保持原顺序

#### Adaptive Provider Router（Phase 2 R3）
- **可选组件**：默认 disabled，需用户显式启用
- **功能**：根据历史成功率+延迟+LLM provider_scores 动态选择 provider
- **评分公式**：score = success_rate × success_weight + latency_score × latency_weight + llm_score × llm_score_weight
- **持久化**：性能数据写入 `_runtime/router-perf.json`
- **静态回退**：无历史数据或数据不足时使用默认顺序
- **意图隔离**：不同意图的性能数据分开记录

#### 组件协同

三个 Phase 2 组件可选程度不同：
- **Result Quality Scorer**：始终启用，无需配置
- **LLM Query Agent**：需设置环境变量 + 修改配置启用
- **Adaptive Router**：需修改 router-config.yaml 启用

当 LLM Agent 和 Adaptive Router 同时启用时：
1. LLM 分析 query → 生成 provider_scores 和改写 query
2. Adaptive Router 结合历史数据 + LLM scores 选择最优 provider
3. 搜索执行后，Scorer 对结果排序

当任何组件失败时：
- LLM Agent 失败 → 降级到原始 query + 静态路由
- Adaptive Router 失败 → 降级到静态 preferred_providers
- Scorer 异常 → 保持原顺序（不降级，因为总是启用）

## CLI 使用

### 列出所有 provider

```bash
python3 -m orchestrator.cli list-providers
```

### 列出所有意图模式

```bash
python3 -m orchestrator.cli list-intents
```

### 探测环境

```bash
python3 -m orchestrator.cli probe
```

### 查看状态（Phase 2）

```bash
# 查看 Adaptive Router 性能数据
python3 -m orchestrator.cli status
```

输出示例：
```
{
  "router": {
    "enabled": false,
    "data_points": 0,
    "providers": {}
  },
  "scorer": {
    "weights": {"authority": 0.5, "freshness": 0.3, "relevance": 0.2}
  }
}
```

### 执行搜索（模拟模式）

```bash
# 基础搜索（JSON 输出）
python3 -m orchestrator.cli search "Python 异步编程"

# 指定意图
python3 -m orchestrator.cli search "Python 异步编程" --intent INFO

# 串行执行（使用 fallback 链）
python3 -m orchestrator.cli search "Python 异步编程" --serial

# 限制 provider 数量
python3 -m orchestrator.cli search "Python 异步编程" --max-providers 2

# 限制结果数量
python3 -m orchestrator.cli search "Python 异步编程" --num-results 5

# 易读格式输出
python3 -m orchestrator.cli search "Python 异步编程" --pretty
```

## 配置文件

### Provider 配置 (providers/*.yaml)

每个 provider 包含：
- `name`: Provider 唯一标识
- `type`: mcp 或 http
- `mcp_server`: MCP 服务器名称
- `mcp_tool_name`: MCP 工具名称
- `call.parameters`: 参数名映射和类型转换
- `call.result_mapping`: 结果字段映射
- `quota_limit`: 配额上限
- `quota_window`: 配额时间窗口（秒）
- `timeout`: 请求超时（秒）

### 意图模式配置 (intent-modes.yaml)

每个意图模式包含：
- `query_strategy`: precise 或 broad
- `cache_ttl`: 缓存存活时间（秒）
- `preferred_providers`: 首选 provider 列表
- `enable_fallback`: 是否启用 fallback
- `query_strategy_config`: 三轮递进配置（可选）

### Fallback 链配置 (fallback_order.yaml)

包含：
- `chain`: Provider 优先级列表
- `trigger_on_status`: 触发条件
- `max_depth`: 最大 fallback 深度

### Scorer 配置 (scorer-config.yaml)

```yaml
weights:
  authority: 0.5
  freshness: 0.3
  relevance: 0.2
authority_tiers:
  - pattern: "*.gov.cn"
    score: 1.0
  - pattern: "*.edu.cn"
    score: 0.8
freshness_cutoffs:
  - days: 30
    score: 1.0
  - days: 90
    score: 0.8
```

### Router 配置 (router-config.yaml)

```yaml
adaptive_router:
  enabled: false        # 默认关闭
  max_providers: 3
  min_history: 5
  scoring:
    success_weight: 0.5
    latency_weight: 0.3
    llm_score_weight: 0.2
  persistence:
    enabled: true
    file: "_runtime/router-perf.json"
```

## 作为库使用

```python
from orchestrator import (
    SearchEngine,
    SearchRequest,
    ConfigLoader,
    McporterMCPClient,
    StateManager,
    CacheManager,
)

# 创建组件
config_loader = ConfigLoader()
config_loader.load_all()

mcp_client = McporterMCPClient()
state_manager = StateManager()
cache_manager = CacheManager()

# 创建搜索引擎
engine = SearchEngine(
    config_loader=config_loader,
    mcp_client=mcp_client,
    state_manager=state_manager,
    cache_manager=cache_manager,
)

# 执行搜索
request = SearchRequest(
    query="Python 异步编程",
    intent="INFO",
    num_results=10,
)

result = await engine.search(
    request=request,
    parallel=True,
    max_providers=3,
)

print(f"状态: {result.status.value}")
print(f"结果数: {len(result.items)}")
```

### 启用 LLM Query Agent

```python
from orchestrator.llm_agent import LLMQueryAgent
from orchestrator.schema import LLMConfig

# 创建 LLM Agent（需要设置 LLM_API_KEY 环境变量）
llm_config = LLMConfig(enabled=True)
llm_agent = LLMQueryAgent(config=llm_config)

engine = SearchEngine(llm_agent=llm_agent)
```

### 启用 Adaptive Router

```python
# 方法 1: 修改 router-config.yaml，设置 adaptive_router.enabled=true

# 方法 2: 创建后覆盖
from orchestrator.router import AdaptiveRouter
from orchestrator.schema import RouterConfig

engine = SearchEngine()
router_config = RouterConfig(enabled=True, min_history=5)
engine.router = AdaptiveRouter(router_config)
```

## 验证

✅ 所有模块可导入：`python3 -c "import orchestrator; print('OK')"`
✅ CLI 命令正常工作
✅ 配置文件加载成功
✅ 类型注解完整
✅ 单元测试：224 项全部通过
✅ LLM Query Agent 测试覆盖 build_prompt / parse / cache / degradation
✅ Result Scorer 测试覆盖 authority / freshness / relevance / sort
✅ Adaptive Router 测试覆盖 selection / record / persistence / integration
