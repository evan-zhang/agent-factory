# BATTLE-R1 — 执行者回应与修订方案（Blue / Executor）

**执行者**：方案设计者（Executor）
**审查者**：探针（Probe）
**状态**：R1 审查 → 逐一回应 → 输出最终修订版

---

## 一、逐条回应审查裁决

### Q1 编排器运行时 — ACCEPT

审计者裁定：编排器不应以 MCP Server 或 OpenClaw Skill 函数形态存在，应为 Python 异步库 + CLI 入口。

**接受理由**：审计者的分析指出 MCP Server 是"被编排的对象"而非编排者，这是正确的架构原则。OpenClaw Skill 函数确实不具备常驻进程能力。Python 异步库 + CLI 入口形态与 `zero-search` 模式一致，避免了额外常驻进程，与现有 mcporter 架构兼容。

**修订方案**：
- 核心逻辑为 `orchestrator/` 目录下的 Python 异步模块
- 对外 CLI 入口 `search`（可独立执行，也可被 SKILL.md 调用）
- 每次搜索为单次进程调用，不留常驻进程
- 健康检查通过 `orchestrator probe <name>` 子命令按需执行
- SKILL.md 中搜索调用从"直接调用 MCP tool"改为"调用 `search` CLI"

### Q2 结果格式统一 — ACCEPT，采纳补充

审计者裁定：统一格式方向 APPROVE，但需要补充 `version` 字段和 `source_engine` 字段。

**接受理由**：`version` 字段确保 schema 可演进，`source_engine` 保留 provenance 数据，都是合理且必要的补充。

**修订方案**：
- 统一结果格式增加 `version: "1.0"` 顶层字段
- 每个 SearchItem 增加 `source_engine: str` 保留原始来源
- schema 变更时通过 version 号管理兼容性

### Q3 搜索需求分类 — ACCEPT

审计者裁定：编排器不做语义分类，由调用方通过 `intent` 参数声明。

**接受理由**：引入 LLM 分类器增加了不必要的延迟、成本和出错点。编排器作为基础设施层，不应理解业务上下文。调用方最清楚自己的搜索意图，应由调用方显式传递。

**修订方案**：
- 删除编排器内置的语义分类能力
- 调用方调用时声明 `intent` 参数，默认为 `"general"`
- 编排器维护 `intent → [provider candidates]` 静态映射表（YAML 配置文件维护）
- 映射表可被管理员或调用方重载

### Q4 Provider 最小单元 — ACCEPT

审计者裁定：YAML provider descriptor 方案 APPROVE。

**接受理由**：YAML 描述符方案是原方案的一部分，审计者认可此方向。

**修订方案**：
- 每个 provider 对应一个 `providers/<name>.yaml` 文件
- 描述符定义：name, type, tool, cost_tier, capabilities, health_check, quota, call
- 新增 provider = 新增 YAML + 可选配置 MCP Server，不改代码

### Q5 打分机制 — ACCEPT

审计者裁定：REJECT 全局数值评分，APPROVE 4 维布尔状态。

**接受理由**：审计者正确指出"全局质量分"在搜索领域不成立——不同 provider 在不同场景下各有优劣。手动评分必然过时，自动评分需要大量标注数据，当前规模不具备条件。4 维布尔状态（alive, capable, quota_ok, latency_ok）更简单、可维护、无需训练数据。

**修订方案**：
- 删除所有数值评分概念
- 引入 4 维布尔状态：alive、capable、quota_ok、latency_ok
- 路由规则：过滤掉任意维度为 false 的 provider，剩余按 cost_tier 升序，同 tier 随机
- 不需要评分模型，不需要训练数据，不需要人工维护评分

### Q6 免费额度追踪 — ACCEPT

审计者裁定：本地近似计数器方案 APPROVE。

**接受理由**：无需依赖不可靠的配额 API，不引入额外的调用延迟。本地 JSON 文件足以用于路由决策。

**修订方案**：
- 维护 `_runtime/quota-state.json` 作为本地近似计数器
- 每次调用后计数器 +1（近似值）
- 按 provider 配置的 reset 周期自动归零
- 仅用于路由决策（"配额满则跳过"），不用于计费
- 不引入定时任务、配额 API 探测、跨进程同步

### Q7 新旧架构关系 — ACCEPT

审计者裁定：共存模式 + 明确迁移路径 APPROVE。

**接受理由**：审计者指出需要明确的 Phase 1 / Phase 2 迁移路径，这是原方案缺失的部分。共存方案确保非破坏性迁移。

**修订方案**：
- Phase 1（兼容期）：旧 `search(query)` 走线性降级链不变；新 `search(query, intent=...)` 走编排器路由；两者共存
- Phase 2（统一期）：`search(query)` 内部自动编排器，intent=`"general"`；旧线性降级链成为编排器兜底策略；删除旧专用 fallback 文件
- 最终形态：带 intent → Orchestrator；不带 intent → Orchestrator(general)；全部失败 → 旧线性降级链兜底

### Q8 Provider 生命周期 — ACCEPT

审计者裁定：按需探测 + 60s 缓存 APPROVE。

**接受理由**：常驻健康检查在 provider 扩展到 8+ 时造成不必要的 MCP 连接开销。按需探测 + 短时缓存更合理。mcporter 已有进程管理，编排器不需要重复发明。

**修订方案**：
- 按需探测策略：调用前检查缓存，1 分钟内复用，5 分钟内上次失败则仍标记不可用
- 探测方式：调用 MCP 的 tools/list（超时 5s）
- 不引入守护进程/定时任务
- 依赖 mcporter 的进程自愈能力

### Q9 失败处理策略 — ACCEPT

审计者裁定：有损降级策略 APPROVE。

**接受理由**：审计者补充了更清晰的场景分类（全部失败 / 部分成功 / 0 结果）和"成功"的定义标准，这是原方案缺乏的细化。

**修订方案**：
- 场景 A（全部失败）：回退到旧线性降级链逐个尝试；全部失败 → 返回 empty + gap note
- 场景 B（部分成功）：返回聚合结果；metadata 标注失败 provider 及原因
- 场景 C（0 结果非失败）：视为"无匹配"，只聚合有结果的
- 成功率定义：HTTP 200 + 结构完整 = 成功；超时/异常/配额 = 失败；0 结果 ≠ 失败

### Q10 并行 vs 串行 — ACCEPT

审计者裁定：默认并行、按 intent 约束 APPROVE。

**接受理由**：审计者补充了关键规则：全局超时管理（不是各 provider 超时的和）、同一底层引擎不并行、最快结果优先策略。这些都是正确的工程实践。

**修订方案**：
- 默认并行执行，按 intent 可配置 serial/parallel/hybrid 策略
- 全局超时 10-15s（不是 provider 超时的和）
- 最快 N 个结果优先，超时结果丢弃
- 同底层引擎 provider 不并行
- 配置于 `orchestrator/intent-modes.yaml`

### Q11 成本预算意识 — ACCEPT

审计者裁定：4 级 cost_tier 模型 APPROVE，不引入复杂优化。

**接受理由**：搜索场景的 cost 敏感度很低（一次搜索最贵几分钱）。配额耗尽 ≠ 成本。静态优先级已足够，不需要线性规划或机器学习。

**修订方案**：
- 4 级 cost_tier：0=免费无限、1=免费有限额、2=付费、3=高价格
- 同一 intent 内优先低 tier 的 provider
- 同 tier 内按健康状态选择
- 配额耗尽 = 等价于 tier 提升
- 不引入实时竞价、线性规划、机器学习

### Q12 注册流程 — ACCEPT

审计者裁定：目录自动发现 APPROVE，补充了完整注册流程。

**接受理由**：审计者完善了从 MCP 部署到编排器识别的完整链路。Step 1-4 的明确划分有助于团队理解职责边界。

**修订方案**：
- 完整注册流程纳入文档：Step 1 部署 MCP → Step 2 创建 provider 描述符 → Step 3 加入 intent 映射 → Step 4 验证
- 编排器启动时扫描 `orchestrator/providers/` 目录动态加载
- 不存在则自动跳过
- 不改代码 = 仅需 Step 2（+ 可选 Step 3）

---

## 二、审计者风险点回应

### 风险 1：职责边界膨胀

**回应**：ACCEPT，明确标记。编排器确实从"工具"进入了"中间件"领域。这是合理的演进——multi-search 从单一路径升级为多路径路由引擎，必然需要中间件层的决策逻辑。在文档中明确标注编排器为"搜索中间件层"，不是纯基础设施工具。同时严格保持"不做业务语义理解"的边界（调用方传 intent）。

### 风险 2：双运行时兼容性

**回应**：ACCEPT，纳入架构要求。编排器的 Python 异步实现需要在 OpenClaw 和 Hermes 上都能运行。MCP 调用层需要抽象：定义 `MCPClient` 接口，OpenClaw 用 mcporter 子进程通信，Hermes 用直接 MCP stdio 通信。具体抽象层设计归入 Phase 0 基础设施。

### 风险 3：数据落盘变更

**回应**：ACCEPT，更新落盘规范。编排器的结果包含 `orchestrator` 层信息（engines_tried、engines_succeeded、total_latency_ms 等），需要更新 multi-search 数据落盘 schema。格式随 `version` 字段演进。

---

## 三、最终修订版设计

### 3.1 架构总图

```
┌──────────────────────────────────────────────────────────────┐
│                        调用方（Caller）                        │
│   search(query="...", intent="chinese-policy")               │
└────────────────────────┬─────────────────────────────────────┘
                         │ CLI / SKILL.md 调用
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    Search Orchestrator                        │
│                                                              │
│  ┌────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │ CLI 入口    │  │ 执行引擎        │  │ 结果聚合器         │   │
│  │ search     │─▶│ 并行/串行调度   │─▶│ 去重 + 格式化     │   │
│  └────────────┘  └───────┬───────┘  └─────────┬─────────┘   │
│                          │                     │             │
│  ┌────────────┐  ┌───────┴───────┐  ┌─────────┴─────────┐   │
│  │ 配置加载器   │  │ Provider 池   │  │ 状态管理器         │   │
│  │ YAML 目录   │  │ 各 provider   │  │ 健康 + 配额缓存    │   │
│  └────────────┘  │ 的 MCP 调用   │  └───────────────────┘   │
│                   └───────┬───────┘                         │
└───────────────────────────┼─────────────────────────────────┘
                            │ MCP 协议（抽象层）
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  MCP Server  │  │  MCP Server  │  │  MCP Server  │
│  Brave       │  │  MiniMax     │  │  Tavily      │
│  (mcporter)  │  │  (mcporter)  │  │  (mcporter)  │
└──────────────┘  └──────────────┘  └──────────────┘

┌──────────────────────────────────────────────────────────────┐
│ 存储层                                                       │
│  orchestrator/providers/    ← provider YAML 描述符目录      │
│  orchestrator/intent-modes.yaml  ← 意图映射配置             │
│  _runtime/quota-state.json ← 本地配额计数器                 │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 组件职责边界

| 组件 | 职责 | 不做 |
|------|------|------|
| **CLI 入口** (`search`) | 解析参数（query, intent, timeout），调用执行引擎，输出结果 | 不做配置管理、不做持久化 |
| **配置加载器** | 扫描 `providers/*.yaml` 加载 provider 描述符；加载 `intent-modes.yaml` | 不做配置校验（YAML schema 由外部 validator 处理） |
| **执行引擎** | 根据 intent 确定 provider 列表和执行模式（serial/parallel/hybrid）；设定全局超时；发起调用 | 不做语义分析、不做结果排序 |
| **Provider 池** | 管理各 provider 的 MCP 客户端实例；提供 `call(provider, query) → raw_result` 接口 | 不做结果去重、不做状态缓存 |
| **结果聚合器** | 去重（URL 判重）、统一格式化（含 source_engine）、metadata 填充 | 不做结果排序、不做摘要生成 |
| **状态管理器** | 维护 provider 健康状态（4 维布尔）和配额计数器 | 不做计费、不做跨进程同步 |
| **抽象 MCP 层** | `MCPClient` 接口：OpenClaw 实现（mcporter 子进程）、Hermes 实现（直接 stdio） | 不做进程管理（由 mcporter 负责） |

### 3.3 12 个问题的最终定案

| # | 问题 | 最终方案 | 状态 |
|---|------|---------|------|
| Q1 | 编排器运行时 | Python 异步库 + CLI 入口 `search`，不常驻 | ✅ 定案 |
| Q2 | 结果格式统一 | 统一 JSON schema v1.0，含 version、source_engine、metadata | ✅ 定案 |
| Q3 | 搜索需求分类 | 调用方传 `intent` 参数，编排器映射到 provider 列表 | ✅ 定案 |
| Q4 | Provider 最小单元 | YAML 描述符文件 `providers/<name>.yaml` | ✅ 定案 |
| Q5 | 打分机制 | 4 维布尔状态（alive/capable/quota_ok/latency_ok），无数值评分 | ✅ 定案 |
| Q6 | 免费额度追踪 | 本地 JSON 近似计数器，+1 递增，按周期归零 | ✅ 定案 |
| Q7 | 新旧架构关系 | Phase 1 共存 → Phase 2 统一，旧链成为兜底 | ✅ 定案 |
| Q8 | Provider 生命周期 | 按需探测 + 60s 缓存，依赖 mcporter 自愈 | ✅ 定案 |
| Q9 | 失败处理策略 | 有损降级（全部失败→旧链兜底，部分成功→聚合，0 结果→不算失败） | ✅ 定案 |
| Q10 | 并行 vs 串行 | 默认并行，intent 配置 serial/parallel/hybrid，设全局超时 | ✅ 定案 |
| Q11 | 成本预算意识 | 4 级 cost_tier 静态优先级，无复杂优化 | ✅ 定案 |
| Q12 | 注册流程 | 目录自动发现 + 4 步标准注册流程 | ✅ 定案 |

### 3.4 Provider 注册模板（YAML）

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
  method: mcp_list_tools    # 通过 MCP 的 tools/list 确认
  timeout_ms: 5000

quota:
  type: monthly             # monthly / weekly / pay_per_call
  limit: 2000
  reset_day: 1

call:
  timeout_ms: 30000
  retry: 2
  required_env: [BRAVE_API_KEY]
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
  reset_day: 1               # 每周一重置

call:
  timeout_ms: 30000
  retry: 2
  required_env: [MINIMAX_API_KEY]
```

### 3.5 统一结果格式（JSON Schema）

```yaml
# 编排器统一输出格式 v1.0
OrchestratorSearchResult:
  type: object
  required: [version, provider, query, items, metadata]
  properties:
    version:
      type: string
      description: Schema 版本号，默认为 "1.0"，变更时递增次版本
      example: "1.0"

    provider:
      type: string
      description: 名义 provider 名称（聚合结果时为 "orchestrator"）
      example: "orchestrator"

    query:
      type: string
      description: 实际执行的查询（可能被改写，但当前版本不做查询改写）
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
            description: 结果链接
            format: uri
          snippet:
            type: string
            description: 结果摘要
          source_engine:
            type: string
            description: 原始来源引擎名称（去重后仍保留 provenance）
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
      required: [engines_tried, engines_succeeded, total_latency_ms]
      properties:
        engines_tried:
          type: array
          description: 尝试了哪些引擎
          items:
            type: string
          example: ["brave", "minimax", "tavily"]

        engines_succeeded:
          type: array
          description: 成功返回结果的引擎
          items:
            type: string
          example: ["brave", "minimax"]

        engines_failed:
          type: array
          description: 失败（超时/异常/配额）的引擎
          items:
            type: object
            properties:
              engine:
                type: string
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
          description: 本次调用对各 provider 配额的消耗情况
          additionalProperties:
            type: integer
          example:
            brave: 1
            minimax: 0
            tavily: 0

        intent:
          type: string
          description: 本次搜索的意图（由调用方传入）
          example: "chinese-policy"

        strategy:
          type: string
          description: 执行策略
          enum: [serial, parallel, hybrid]
          example: "hybrid"

### 3.6 目录结构

```
orchestrator/
├── __init__.py             # 模块入口
├── cli.py                  # CLI 入口（search, probe 子命令）
├── engine.py               # 执行引擎（调度 provider 调用）
├── aggregator.py           # 结果聚合去重
├── config.py               # 配置加载器（扫描 YAML 目录）
├── state.py                # 状态管理器（健康 + 配额缓存）
├── mcp_client.py           # MCP 调用抽象层（接口 + OpenClaw 实现）
├── providers/              # Provider YAML 描述符目录
│   ├── brave.yaml
│   ├── minimax.yaml
│   ├── tavily.yaml
│   ├── exa.yaml
│   ├── web_fetch.yaml
│   └── heventure_ddg.yaml
├── intent-modes.yaml       # 意图映射配置
└── _runtime/               # 运行时状态（gitignored）
    └── quota-state.json    # 本地配额计数器
```

### 3.7 实施顺序（采纳审计者建议）

```
Phase 0（基础设施）：
  ├─ Python 异步库框架 + CLI 入口（search, probe）
  ├─ provider YAML 描述符目录 + 配置加载器
  ├─ 统一结果格式 v1.0
  ├─ 按需健康探测 + 60s 缓存
  └─ MCPClient 抽象层（先实现 mcporter 版本）

Phase 1（功能）：
  ├─ intent 映射表 + intent-modes.yaml
  ├─ 并行/串行执行引擎（含全局超时管理）
  ├─ 结果聚合去重
  ├─ 失败处理 + 回退策略（旧线性链兜底）
  └─ Phase 1→Phase 2 共存配置

Phase 2（运维）：
  ├─ 配额本地追踪 + quota-state.json
  ├─ provider 状态缓存持久化
  ├─ 调试日志（谁调了什么、耗时、结果、决策链路）
  ├─ Hermes MCPClient 实现
  └─ 数据落盘 schema 更新
```
