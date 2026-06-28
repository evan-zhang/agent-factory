# BATTLE-R2 — 第二轮深度审查报告（Red / Auditor）

**审查者**：Red（独立审查）
**审查标的**：BATTLE-R1 最终修订版（BATTLE-R1-EXECUTOR.md）
**审查范围**：7 个新发现的工程落地问题 + 额外架构盲点
**审查方式**：独立审查，不参考 Executor 的预判

**总评**：R1 方案在接受 12 条裁决后，架构方向正确（Python 异步库 + CLI + YAML provider descriptor 模式）。但**7 个新问题中有 6 个需要修正**，方案在"从设计到落地"的工程细节上还有显著缺失。另发现 5 个额外盲点，其中 2 个是重大隐患。

---

## 一、7 个新问题逐条裁决

---

### Issue 1：MCP 参数映射缺失

**问题**：Provider YAML 描述符没有定义参数映射规则。Brave 的 `brave_web_search` tool 要求传 `country`/`search_lang`/`count`，MiniMax 只传 `query`，Tavily 有自己的参数结构。编排器的核心是"调用 MCP Server"，不定义参数映射就无法自动化调用。

**审查**：

当前 Provider YAML 模板（BATTLE-R1-EXECUTOR.md §3.4）：

```yaml
call:
  timeout_ms: 30000
  retry: 2
  required_env: [BRAVE_API_KEY]
```

没有 `parameters`、`args_mapping` 或 `normalize` 相关的任何字段。这意味着编排器的执行引擎在调用 provider 时，只能对所有 provider 传入同一组参数——但这组参数对不同 MCP tool 来说可能是错误的/多余的。

**具体影响**：
- Brave 需要 `query` + `count` + `country` + `search_lang` + `freshness`。如果只传 `query`，结果质量大打折扣（返回无关地区的内容）。
- MiniMax 如果收到 `country=CN` 参数，它的 MCP 可能忽略或者报错。
- Tavily 有 `search_depth` 参数控制搜索深度，不传的话用默认值，可能不够深入。

这不是小问题——**编排器的核心职责就是"调用 MCP tool"，如果连参数都拼不对，整个路由机制没有意义**。

**裁决**：REJECT

**建议方案**：在 Provider YAML 中添加 `parameters` 节，定义 normalized parameter → MCP tool parameter 的映射关系：

```yaml
# providers/brave.yaml
call:
  timeout_ms: 30000
  retry: 2
  required_env: [BRAVE_API_KEY]
  parameters:
    # normalized → MCP tool parameter mapping
    query:
      mcp_param: "query"        # normalized query → MCP "query"
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
      default: null             # 不传
```

```yaml
# providers/minimax.yaml
call:
  timeout_ms: 30000
  retry: 2
  required_env: [MINIMAX_API_KEY]
  parameters:
    query:
      mcp_param: "query"
      required: true
    # MiniMax 不需要 count/country/search_lang/freshness
    # 这些参数在调用时自动忽略
```

执行引擎的逻辑：
1. 接收 normalized 参数（`query`, `count`, `country`, `search_lang` ...）
2. 查询 provider YAML 的 `parameters` 映射
3. 对每个 provider，只传 mapped 的参数，忽略未定义的
4. required 参数缺失时抛出明确错误

如果认为加 YAML 字段太重，也可以用简单规则：`include: ["query", "count"]` 白名单模式，或 `exclude_field: []` 黑名单模式。**关键是这个能力必须存在，不能默认所有 MCP tool 参数一致**。

---

### Issue 2：安装分发链缺失

**问题**：编排器是 Python 异步库放在 `orchestrator/` 目录下，但 calling agent（调用方 agent）怎么找到 `search` 命令？绝对路径？pip 全局安装？uvx？

**审查**：

BATTLE-R1-EXECUTOR.md 定义了目录结构（§3.6）：

```
orchestrator/
├── __init__.py
├── cli.py          # CLI 入口（search, probe 子命令）
├── engine.py
├── ...
```

但没有任何关于 "这个 `search` 命令怎么装、在哪里、calling agent 怎么找到它" 的说明。

**具体影响**：
- OpenClaw 的 SKILL.md 需要配置一个命令或脚本路径。如果 `search` 不是/usr/local/bin/search，SKILL.md 怎么写？
- Hermes 平台有自己的脚本调用方式，路径规则不同。
- 本地开发时是 `python -m orchestrator` 还是 `./orchestrator/cli.py` 还是 `search`？
- 如果 calling agent 通过 `exec` 或 `subprocess` 调用 `search`，环境 PATH 是否包含 orchestrator 目录？

**裁决**：REJECT

**建议方案**：参照 `zero-search` 的模式，明确安装分发链：

**方案 A：作为 skill 内嵌脚本（推荐）**
- `search` 命令不做为全局可执行文件
- 在 SKILL.md 中通过函数定义调用 orchestrator：`python3 {skill_dir}/orchestrator/cli.py search [...]`
- SKILL.md 在安装时自动设置 `SKILL_DIR` 环境变量
- 不污染全局 PATH，依赖 skill 内的相对路径

**方案 B：pip install -e 本地安装**
- 在 orchestrator/ 下放 setup.py/pyproject.toml
- 安装时执行 `pip install -e {orchestrator_dir}`
- `search` 命令变成全局可执行文件

**方案 C：uvx 临时执行**
- 需要发布到 PyPI 或本地可访问的仓库
- `uvx search-provider ...` 或 `uv run -p {path} search ...`

**必须明确的点**：
- calling agent 调用 `search` 时，实际执行的 shell 命令是什么？需要具体到 `python3 /path/to/orchestrator/cli.py` 还是 `search` 还是 `uvx ...`
- 这个路径在安装时如何确定？
- 旧 SKILL.md 的兼容性——升级后 calling agent 是否需要改调用方式？

---

### Issue 3：配额计数器竞态条件

**问题**：本地 JSON 文件 `_runtime/quota-state.json`，两个 agent 同时写会覆盖对方更新。标记为"近似值"可接受还是需要锁？

**审查**：

BATTLE-R1-EXECUTOR.md 回应："本地文件足以，不引入跨进程同步"。

**分析**：

并发写入方：
- 多个 calling agent 可以同时发起 `search` 调用
- 每个调用是独立进程
- 两个进程同时读写 `_runtime/quota-state.json`

竞态条件：
```
进程 A: read → {"brave": {"used": 100, ...}}      # used=100
进程 B: read → {"brave": {"used": 100, ...}}      # used=100
进程 A: write → {"brave": {"used": 101, ...}}      # used=101 (inc +1)
进程 B: write → {"brave": {"used": 101, ...}}      # used=101 (也 inc +1，覆盖了 A)
```
最终：used=101，应该 102。丢失了 1 次计数。

**影响评估**：
- 这是近似计数器，丢失几次计数不影响路由正确性（配额会用得更慢，但不会更快）
- 更严重的问题是**文件损坏**：如果进程 A 写了一半被中断（SIGKILL），留下半截 JSON → 下次读入解析失败
- 文件损坏的后果：所有 provider 配额不可知 → 路由不应用配额过滤 → 实际等于没做配额追踪

**裁决**：APPROVE（方向正确，但需补充细节）

**条件**：
1. 必须使用**原子写入**：先写临时文件，再 rename 覆盖。`write temp → os.rename(temp, quota-state.json)`。避免写半截导致 JSON 损坏。
2. **写入时加文件锁（file lock）**：Python 的 `fcntl.flock` 或 `portalocker`，避免丢失更新。单个文件锁的开销远小于跨进程同步。
3. **读取失败时降级**：如果 JSON 解析失败（文件损坏），记录警告后重置为初始空状态（used=0）。降级后所有 provider "看起来配额充足"，不会阻断搜索但配额过滤失效。
4. 明确文档：**此计数器仅用于路由决策，不用于计费。并发写入可能丢失少量计数，属于可接受范围。**

**不需要的**：数据库、Redis、分布式锁、信号量。

---

### Issue 4：三轮递进策略丢失

**问题**：原有搜索最核心的三轮递进（精准→泛搜→兜底）在新方案里没被明确安置。它和路由正交——路由选引擎，三轮递进构造查询。谁来负责？

**审查**：

当前设计中的搜索执行路径：
1. 调用方传入 `intent` + `query`
2. 编排器根据 intent 映射到 provider 列表
3. 按策略（serial/parallel/hybrid）执行
4. 聚合去重后返回

从来没有任何地方提到：
- "精准搜索"时是否调整 query 参数（如加引号、site: 限定）
- "泛搜"时是否需要 query 变体（同义词、拆词、去修饰词）
- "兜底"时是否放宽条件（降门槛、扩 range）
- 这三轮是串行执行（先精准，不够再加泛搜）还是并行（同时发起，取结果更全的）？

**为什么这不只是"实现细节"**：
- 三轮递进是当前 multi-search 的核心价值之一——它使得搜索不仅是"发请求"而是"策略式搜索"
- 路由解决的是"选谁"的问题，三轮递进解决的是"怎么搜"的问题
- 两者是正交的，但都需要在编排器中定义

**裁决**：REJECT

**建议方案**：在 intent-modes.yaml 中为每个 intent 添加 `query_strategy` 定义：

```yaml
intent_modes:
  chinese-policy:
    strategy: serial
    providers: [minimax, brave, web_fetch]
    external_timeout_ms: 15000
    query_strategy:
      rounds:
        - mode: precise           # 精准：原样 query
          count: 5
          timeout_ms: 8000
        - mode: broaden           # 泛搜：扩展 query，适当放宽
          count: 10
          timeout_ms: 10000
        - mode: fallback          # 兜底：全量搜索
          count: 15
          timeout_ms: 12000
      round_termination:          # 何时终止后续轮次
        min_results: 3            # 精准轮搜到 3 条就够，不执行后续轮次
```

或者简化版——如果不想过度设计，至少在设计文档中明确回答：
1. 三轮递进是编排器职责还是调用方职责？
2. 如果是编排器职责，定义在 provider YAML 还是 intent-modes.yaml 还是专门的 query-planner 模块？

**当前最现实的方案**：将三轮递进的责任放在编排器的执行引擎内，对每个 intent 定义 `query_strategy.rounds`，由引擎管理轮次执行和终止条件。

---

### Issue 5：结果格式缺少 error/status 字段

**问题**：全部 provider 失败时 `items=[]` 无法区分"搜到了0条"和"全部失败"。

**审查**：

当前统一结果格式（BATTLE-R1-EXECUTOR.md §3.5）：

```yaml
OrchestratorSearchResult:
  required: [version, provider, query, items, metadata]
  properties:
    items:                    # 搜索结果条目
    metadata:
      engines_succeeded: []
      engines_failed: []
```

当全部 provider 失败时：
- `items: []`
- `engines_succeeded: []`
- `engines_failed: [{engine: "brave", reason: "timeout"}, ...]`

调用方代码需要写两层判断：
```python
result = call_search(...)
if not result.items and result.metadata.engines_failed:
    # 全部失败
elif not result.items and not result.metadata.engines_failed:
    # ??? 不可能的场景
```

这是不直观的。调用方应该通过一个**顶层字段**就能判断搜索结果的整体质量状态，而不是解析 metadata 的子结构。

**裁决**：REJECT

**建议方案**：在顶层添加 `status` 字段：

```yaml
OrchestratorSearchResult:
  required: [version, status, provider, query, items, metadata]
  properties:
    status:
      type: string
      enum: [ok, partial, no_match, all_failed, error]
      description: |
        ok: 至少一个 provider 返回了结果
        partial: 部分 provider 失败但仍有结果
        no_match: 所有 provider 都返回了 0 结果（网络正常但无匹配）
        all_failed: 所有 provider 都失败了（超时/异常/配额）
        error: 编排器自身出错（配置错误 / CLI 异常）
    error:
      type: string
      description: 仅在 status=error 时存在，说明错误原因
      nullable: true
```

| status | items | 含义 |
|--------|-------|------|
| ok | 有结果 | 正常，至少一个 engine 返回了结果 |
| partial | 有结果 | 部分成功，metadata.engines_failed 不为空 |
| no_match | [] | 所有 provider 正常但无匹配 |
| all_failed | [] | 所有 provider 失败，调用方可判断是否需要回退 |
| error | [] | 编排器自身出错，调用方应降级处理 |

调用方一行代码决定后续逻辑：
```python
match result.status:
    case "ok" | "partial":  process_items(result.items)
    case "no_match":        broaden_query(query)
    case "all_failed":      fallback_to_old_chain()
    case "error":           log_and_alert(result.error)
```

---

### Issue 6：intent 列表对调用方不可见

**问题**：调用方传 `intent` 但不知道有哪些可选，也没有 `list-intents` 命令。

**审查**：

BATTLE-R1-EXECUTOR.md 定义了 `search` CLI 入口，含 `probe` 子命令。但没有任何子命令或机制让调用方查询可用的 intent。

调用方（业务 Agent）需要知道：
1. 当前有哪些 intent 可用？
2. 每个 intent 的语义是什么（适合什么场景）？
3. 新增 intent 后，现有 calling agent 如何感知？

这是**信息不对称**问题：intent 的定义在 orchestrator 的配置中，但调用方没有办法动态获取。

**裁决**：REJECT

**建议方案**：在 `search` CLI 中添加 `list-intents` 子命令：

```
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

调用方在初始化时调用 `search list-intents`，缓存结果，按需选择。这样可以：
- 新增 intent 后 calling agent 自动感知
- 调用方可以在用户交互时展示可选意图
- 降低调用方和编排器之间的耦合

---

### Issue 7：旧线性降级链没写成可执行代码

**问题**：新方案说"全部失败→回退旧链"，但旧链只是 SKILL.md 里的描述性规则（MiniMax → Tavily → Exa → web_fetch 逐个尝试），没有可调用的代码实现。

**审查**：

BATTLE-R1-EXECUTOR.md §3.3 Q7 中说：

> Phase 2（统一期）：旧线性降级链成为编排器兜底策略

§3.3 Q9 中说：

> 场景 A（全部失败）：回退到旧线性降级链逐个尝试

但实际上：
- 旧链存在于 SKILL.md 中，是描述性的："如果 MiniMax 失败则尝试 Tavily，再失败则尝试 Exa..."
- 编排器没有实现"串行 retry with priority list"的代码
- 如果编排器全部失败，编排器自己打算怎么"回退到旧链"？再启动一个进程调用旧的搜索方式？

**核心矛盾**：编排器就是来替代旧链的，但现在说"编排器回退到旧链"——旧链要么不存在（未实现），要么不在编排器的控制范围内（在 SKILL.md 里）。

**裁决**：REJECT

**建议方案**：

**方案 A：旧链作为编排器的内置 fallback（推荐）**
- 在 orchestrator 中实现一个 `fallback_chain` 模块
- `fallback_chain.py` 实现串行调用，按优先级顺序逐个 provider
- 优先级顺序：配置在 provider YAML 中或专门的 `fallback_order.yaml` 中
- 旧 SKILL.md 的描述降级为"参考文档"，执行逻辑由编排器本身负责

**方案 B：旧链保留为独立脚本**
- 保留独立的 `search-fallback.sh` 或 `search-fallback.py`
- 编排器全部失败时 subprocess 调用此脚本
- 坏处：两份实现、两份维护、编排器不可用时 fallback 可用（但编排器不掌控 fallback）

**方案 C：删除旧链概念**
- 承认旧链已不存在
- 全部失败时直接返回 `status: all_failed` + 空 items
- 调用方自己决定如何处理

**推荐方案 A**。旧链不应该是一个外部依赖，而应该是编排器的内置能力。在 orchestrator 中实现 `fallback_chain`，使用已有的 provider YAML 信息，优先级由添加 provider 的顺序决定。

---

## 二、额外发现的架构盲点

### Blind Spot 1（重大）：输入参数接口未定义

**问题**：调用方通过 CLI 调用 `search`，但 CLI 的完整参数列表、默认值、类型约束都没有定义。

当前只定义了 `query` 和 `intent`，但搜索还需要：
- `count`：返回结果数（Brave 默认 10，MiniMax 默认 5）
- `offset`：分页（部分 provider 支持）
- `freshness`：时效性（day/week/month/year）
- `country` / `region`：地域限定
- `safe_search`：安全搜索级别
- `format`：输出格式（json / yaml / text）
- `timeout`：超时
- `debug`：调试模式开关

SKILL.md 需要用确定的 `command_template` 来拼接调用，如果 CLI 参数不完整，SKILL.md 也无法定义。

**裁决**：补充设计，在 CLI schema 中定义完整的参数列表和默认值。至少需要 `query`、`intent`、`count`、`max_timeout` 四个核心参数。

---

### Blind Spot 2（重大）：Provider YAML 加载容错未定义

**问题**：编排器启动时扫描 `orchestrator/providers/` 动态加载所有 YAML。但如果：
- 某 YAML 语法错误 → 全部加载失败？部分加载？
- 某 provider 引用了不存在的 MCP tool → 怎么报错？
- 某 provider 缺少 `call` / `name` 等必填字段 → 怎么处理？

BATTLE-R1-EXECUTOR.md 中说"不存在则自动跳过"，但"不存在"和"存在但格式错误"是两回事。

**影响**：如果 6 个 YAML 中 1 个格式错误，当前的"静默跳过"策略会导致：编排器认为你有 5 个 provider，但运维人员不知道有个 provider 没加载。

**裁决**：补充设计。加载逻辑应为：
1. 对每个 YAML 文件独立加载
2. 格式错误 → 记录警告 + 跳过该 provider
3. 缺少必填字段 → 记录警告 + 跳过
4. 最终输出：`Loaded 5/6 providers, 1 skipped (brave.yaml: invalid YAML syntax)`
5. 必填字段应有一个 YAML schema（可用 JSON Schema 或简单校验）

---

### Blind Spot 3（中等）：结果聚合策略未定义

**问题**：多个 provider 返回结果后，聚合去重只是按 URL 判重。但：

- 结果排序：按 provider 优先级？按时间倒序？按评分？
- 去重判据：仅 URL 还是 URL + title + snippet？
- 同一个 provider 返回了重复结果怎么办？
- Brave 返回 10 条 + MiniMax 返回 5 条 → 输出 15 条去重后的？还是截断到 N 条？
- 一条结果的优先级：来自便宜 provider vs 贵 provider vs 某个 provider 对这个 intent 更擅长？

BATTLE-R1-EXECUTOR.md §3.2 说"不做结果排序"——那聚合后的顺序是什么？provider 1 的结果全在前面，provider 2 的结果全在后面？调用方收到后自己重排？

**裁决**：补充至少一个聚合策略定义。最简单的方案：按 provider 在 intent 配置中的顺序排列结果，同 provider 内按原始顺序。或者按 `published_date` 倒序（如果有）。明确说"暂不排序"和"暂不排序，按 provider 顺序"是两种不同的清晰度。

---

### Blind Spot 4（中等）：Phase 0 未定义 MCP 客户端抽象层

**问题**：BATTLE-R1-AUDITOR.md 明确指出双运行时兼容性要求（OpenClaw 的 mcporter vs Hermes 的直接 stdio），执行者也接受了这个风险并要求在 Phase 0 做 MCPClient 抽象。

但 BATTLE-R1-EXECUTOR.md 的最终版只说了"定义 MCPClient 接口"，**没有给出接口定义**（方法签名、参数、返回值等）。Phase 0 的实施顺序中也没有明确列出"MCPClient 抽象层"。

**影响**：如果编码开始时没有接口定义，可能出现：
- 只实现了 mcporter 版本，Hermes 版本后补（但你后补改接口 → 两边都改）
- 接口耦合了 mcporter 实现细节（子进程通信），Hermes 适配时发现不兼容

**裁决**：要求在 Phase 0 明确输出 MCPClient 的接口定义（至少是 Python protocol class），接口不依赖具体运行时实现细节。

---

### Blind Spot 5（中等）：意图与 provider 能力的语义匹配缺失

**问题**：当前设计说"编排器维护 intent → [provider candidates] 静态映射表"。但 provider 有 `capabilities`（languages, content_types, regions, special），intent 理论上也需要对应的 `requirements`。

当前两个配置是割裂的：
- Provider YAML 定义了 capabilities（如 brave: languages=[en, multi], regions=[global]）
- Intent-modes.yaml 硬编码了 provider 列表（如 chinese-policy: [minimax, brave, web_fetch]）

这两者没有关联——如果你加了新的 provider，需要手动把它加入 intent 列表。但如果新 provider 的 capabilities 自动匹配某个 intent，不会自动生效。

**这不是必须解决的问题**，静态映射在现阶段完全够用。但在设计文档中指出这个局限性，避免以后有人期望"自动匹配"。

**裁决**：不需要改方案，但需要在设计文档中明确标注："当前 intent→provider 是静态映射，不与 provider capabilities 自动匹配。未来添加 provider 后需要手动更新 intent 映射表。"

---

## 三、7 个问题裁决汇总

| # | 问题 | 裁决 | 优先级 | 修复量级 |
|---|------|------|--------|---------|
| 1 | MCP 参数映射缺失 | **REJECT** | P0（阻塞） | 中 | Provider YAML 加 parameters 节 |
| 2 | 安装分发链缺失 | **REJECT** | P0（阻塞） | 小 | 明确 `search` 的调用路径 |
| 3 | 配额计数器竞态条件 | **APPROVE** 附条件 | P2（低优） | 小 | 加文件锁 + 原子写入 |
| 4 | 三轮递进策略丢失 | **REJECT** | P1（重要） | 中 | intent-modes.yaml 加 query_strategy |
| 5 | 结果格式缺少 error/status | **REJECT** | P1（重要） | 小 | 顶层加 status + error 字段 |
| 6 | intent 列表不可见 | **REJECT** | P1（重要） | 小 | CLI 加 list-intents 子命令 |
| 7 | 旧链无可执行实现 | **REJECT** | P1（重要） | 中 | orchestrator 内实现 fallback_chain |

**P0（阻塞）**：不改无法编码，编码即错误路径。必须修复后才能进入 Phase 0 实施。

**P1（重要）**：影响功能完整性和调用方体验。应在 Phase 0 或 Phase 1 中修复。

**P2（低优）**：存在潜在问题但影响可控，可在 Phase 2 中修复。

---

## 四、额外盲点汇总

| # | 盲点 | 严重程度 | 说明 |
|---|------|---------|------|
| 1 | 输入参数接口未定义 | **重大** | 完整的 CLI 参数和默认值未定义 |
| 2 | Provider YAML 加载容错未定义 | **重大** | 格式错误的 YAML 静默跳过 |
| 3 | 结果聚合策略未定义 | 中等 | 去重后的排序/截断策略空白 |
| 4 | MCPClient 抽象接口未定义 | 中等 | Phase 0 缺少接口定义 |
| 5 | Intent→Capabilities 自动匹配缺失 | 中等 | 需标注此局限性 |

**建议**：盲点 1 和 2 应该纳入 Phase 0 的基础设施清单中，作为前置条件。
盲点 3-5 在 Phase 1 补全设计，不影响 Phase 0 编码启动。

---

## 五、整体方案健康度评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构方向 | ★★★★☆ | Python 异步库 + CLI + YAML 描述符，方向正确 |
| 12 个原问题 | ★★★★★ | 全部被妥善处理，Auditor 判决被完整接受 |
| 7 个新问题 | ★★☆☆☆ | 6/7 需要修改，暴露了"设计→实现"之间的落地空白 |
| 文档完整性 | ★★★☆☆ | 组件边界清晰，但输入/输出/分发链不完整 |
| 可编码性 | ★★☆☆☆ | 缺 input schema / install chain / parameter mapping 三类信息 |

**总体裁决**：架构方向 **APPROVE**，但工程落地 **CONDITIONAL**。

7 个问题中有 6 个 REJECT，但都是"补全"而非"推翻"。不存在架构层面的方向性错误。

**进入 Phase 0 编码的前提条件**（修正上述问题后）：
1. ✅ Provider YAML 增加 parameters 映射定义
2. ✅ 明确 `search` CLI 的完整输入参数规范
3. ✅ 明确安装分发链（search 命令的实际调用路径）
4. ✅ 明确 Phase 0 MCPClient 的接口定义
5. ✅ Provider YAML 加载容错机制

当以上 5 项在设计层面明确后，Phase 0 可以开始编码。
Phase 1 开始前需修正：Issue 4（三轮递进）、Issue 5（status 字段）、Issue 6（list-intents）。

---

*审查完毕。建议 Executor 在进入编码前先解决 P0 和 P1 问题，总工作量约 3-5 个字段扩展 + 1 个 CLI 子命令。*
