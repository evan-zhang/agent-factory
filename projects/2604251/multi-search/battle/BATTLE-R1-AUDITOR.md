# BATTLE-R1 — 审查裁决报告（Red / Auditor）

**审查者**：探针（Probe）

**审查标的**：搜索编排器（Search Orchestrator）架构方案
**审查范围**：12 个待决问题的架构合理性、工程可行性、可维护性

**总评**：方案方向 APPROVE，但半数问题的实现建议需要调整。核心问题是架构层级的定位不够清晰——编排器给"基础设施层"增加了决策逻辑，改变了 multi-search 的职责边界。以下逐个细审。

---

## Q1 编排器运行时 — REJECT 方向，APPROVE 修正方案

**问题**：编排器以 Python 脚本 / MCP Server / OpenClaw Skill 函数 哪种形态存在？

**盲点/遗漏**：
- MCP Server 本身是*被编排的对象*，让它做编排是反模式的。MCP Server 孵化其他 MCP Server 需要手动管理子进程，既不可靠也不可观测。
- OpenClaw Skill 函数只能通过 SKILL.md 的工作流定义调用，不具备常驻进程能力，无法做健康检查或配额追踪。

**裁决**：REJECT 以上三种形态。编排器不应该是一个"服务"。

**结论**：编排器以 **Python 异步库 + CLI 入口** 形态存在。

具体方案：
- 核心逻辑是 `orchestrator/` 目录下的 Python 模块
- 对外暴露一个 CLI 入口 `search`（类似 `zero-search` 的模式）
- SKILL.md 中的搜索调用从"直接调用 MCP tool"改为"调用 `search` CLI"
- 不常驻，每次搜索调用是单次进程
- 健康检查和配额追踪通过 `orchestrator probe` 子命令实现（按需执行，不持续）

选择 Python 而非 MCP Server 的理由：
1. 编排器需要调用多个 MCP Server，Python 的 asyncio + subprocess 天然适合
2. 不增加常驻进程，与现有 mcporter 架构一致
3. SKILL.md 在 OpenClaw 和 Hermes 上都可以通过脚本调用

---

## Q2 结果格式统一 — APPROVE，但需要版本化

**问题**：不同 MCP Server 返回不同结构，编排器的统一输出格式是什么？

**盲点/遗漏**：
- 只考虑了"统一"，没有考虑兼容性和演进。如果 Brave 发新版改变字段结构，硬编码的 schema 会断裂。
- 没有区分 "搜索结果"和"页面抓取结果"——前者是条目列表，后者是全文。

**裁决**：APPROVE 方案方向，补充细节。

**结论**：统一格式为以下几种之一，由 caller 指定：

```python
# 搜索结果格式
OrchestratorSearchResult:
  version: "1.0"           # schema 版本号，兼容演进
  provider: str             # 实际提供结果的 provider 名称
  query: str                # 实际执行的查询（可能被改写）
  items: [SearchItem]
  metadata:                 # 来源元数据
    engines_tried: [str]    # 尝试了哪些引擎
    engines_succeeded: [str]
    total_latency_ms: int
    quota_impact: dict      # 本次消耗的配额

SearchItem:
  title: str
  url: str
  snippet: str
  source_engine: str        # 来自哪个引擎
  published_date: str?      # 如果有
  score: float?             # 如果有排序分
  content_type: str?        # "policy" | "news" | "general"
```

关键设计决策：
- `version` 字段必须存在，默认 `"1.0"`，schema 变更时 `s/1.0/1.1/` 不影响旧消费者
- `source_engine` 保留原始来源，避免去重后丢失 provenance
- normalize 策略：优先保留最丰富的字段（Tavily > MiniMax > Brave），缺失的字段标记为 null

---

## Q3 搜索需求分类 — REJECT

**问题**：路由依赖识别场景（中国政策 vs 英文文档 vs 新闻）。谁来做分类？

**盲点/遗漏**：
- 让编排器做语义分类是过度设计。分类需要理解业务上下文，而编排器只应该做路由决策。
- 引入 LLM-based 分类器增加了延迟、成本和出错点。
- 即使是简单的关键词匹配（`site:gov.cn` → 中文政策），也会因为搜索词本身的多样性而误判。

**裁决**：REJECT。编排器不做语义分类。

**结论**：分类由**调用方（Caller）明确的参数**指定，编排器只按参数路由。

```
search(query="社保缴费比例", intent="chinese-policy")
search(query="LLM architecture paper", intent="english-academic")
search(query="NVIDIA stock", intent="news")
search(query="如何办理居住证", intent="general")
```

- 调用方在调用时声明 `intent`，默认为 `"general"`
- 编排器内置 `intent → [provider candidates]` 映射表：
  - `chinese-policy` → MiniMax → Brave → web_fetch
  - `english-academic` → Brave → Tavily → heventure
  - `news` → Brave news → MiniMax → Tavily
  - `general` → 全部候选，按成本排序
- 映射表通过配置文件维护，调用方或管理员可以重载

不引入语义分类器，降低架构复杂度。

---

## Q4 Provider 最小单元 — APPROVE，YAML 描述符

**问题**：每个搜索方案的最小单元是什么？

**盲点/遗漏**：
- MCP 配置片段（mcporter.json 条目）不适合在编排器中直接引用——编排器不应关心 MCP 底层实现
- SKILL.md 太重，不是配置级单位

**裁决**：APPROVE YAML provider descriptor 方案。

**结论**：每个 provider = 一个 `providers/<name>.yaml` 文件：

```yaml
# providers/brave.yaml
name: brave
type: mcp
tool: brave_web_search
description: Brave Search API，覆盖网页/新闻/图片
cost_tier: 1               # 0=免费无限 1=免费限配额 2=付费
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

新增 provider = 新增 YAML 文件 + 配置对应 MCP Server。无需改代码。

---

## Q5 打分机制 — REJECT 静态评分，APPROVE 多维状态

**问题**：打分怎么执行、维护、反映到路由？

**盲点/遗漏**：
- "打分"暗示了数值化、可比较的质量评分。这在搜索领域不成立——不同 provider 在不同场景下各有优劣，不存在一个"全局质量分"。
- 手动评分必然过时，自动评分需要大量标数据，当前规模不到这个阶段。

**裁决**：REJECT 全局评分概念。APPROVE 多维状态跟踪。

**结论**：用 4 个布尔状态替代数值评分：

| 维度 | 含义 | 来源 |
|------|------|------|
| alive | 进程存活，响应正常 | 健康检查（每 10 次调用探一次） |
| capable | 对该 intent 有可用结果 | 实际搜索的成功/失败比率 |
| quota_ok | 配额未用尽 | 本地计数器 + provider 重置周期 |
| latency_ok | 平均延迟在阈值内 | 运行时统计（P95 < 5s） |

路由决策规则：
1. 过滤掉任意维度为 false 的 provider
2. 剩余 provider 中按 cost_tier 升序排列
3. 同 tier 内随机（避免都打到第一个）

不需要打分。静态可维护，无需训练数据。

---

## Q6 免费额度追踪 — APPROVE 局部计数器方案

**问题**：MiniMax 周配额、Brave 月配额。编排器如何知道当前剩余？

**盲点/遗漏**：
- 依赖 provider API 返回配额信息不可靠——大部分搜索 API 不返回剩余配额
- 实时查询配额 API 会增加额外的调用延迟

**裁决**：APPROVE 本地近似计数器方案。

**结论**：编排器维护一个本地 JSON 文件 `_runtime/quota-state.json`：

```json
{
  "brave": {
    "type": "monthly",
    "limit": 2000,
    "used": 347,
    "reset_at": "2026-07-01T00:00:00Z",
    "last_updated": "2026-06-06T09:15:00Z"
  },
  "minimax": {
    "type": "weekly",
    "limit": 500,
    "used": 123,
    "reset_at": "2026-06-08T00:00:00Z",
    "last_updated": "2026-06-06T09:15:00Z"
  }
}
```

- 每次调用后计数器 +1（近似值）
- 重置时间到了自动归零
- 不对 provider 做精确查询
- 只用于路由决策（"配额满了就跳过"），不用于计费

**不引入**：定时任务、配额 API 探测、跨进程同步。本地文件足以。

---

## Q7 新旧架构关系 — APPROVE 共存模式

**问题**：线性降级链（现存）和场景路由（新方案）如何共存？

**盲点/遗漏**：
- 方案没有说明用户视角是否感知到变化——如果调用方 API 变了，就是破坏性变更
- 没有迁移路径

**裁决**：APPROVE 共存模式，明确迁移路径。

**结论**：

**Phase 1（兼容期）**：
- 旧 `search(query)` 走线性降级链，不变
- 新 `search(query, intent="...")` 走编排器路由
- 两者共存，调用方自己选

**Phase 2（统一）**：
- `search(query)` 内部自动走编排器，意图 = `"general"`
- 旧线性降级链成为编排器兜底策略（Q9 的失败处理）
- 删除旧专用的 `search-fallback.md`，内容合并到编排器文档

**路由最终形态**：
```
搜索调用
  │
  ├─ 带 intent → Orchestrator → 并行/串行调用 2-3 provider → 聚合去重 → 返回
  └─ 不带 intent → Orchestrator(general) → 同上

Orchestrator 全部失败 / 不可用时:
  → 旧线性降级链（MiniMax → Tavily → Exa → web_fetch）  # 一个 provider 一个
  → 全部失败 → 标注缺口
```

---

## Q8 Provider 生命周期 — APPROVE 按需探测

**问题**：MCP Server 进程可能挂掉。编排器如何感知可用性？

**盲点/遗漏**：
- 常驻健康检查（每 N 分钟遍历所有 provider）在只有 2-3 个 provider 时 OK，扩展到 8+ 时造成不必要的 MCP 连接开销
- mcporter 本身已经有进程管理，编排器不需要重复发明

**裁决**：APPROVE 按需探测 + 缓存结果。

**结论**：

```python
# 按需探测策略
check_available(provider_name: str) -> bool:
    now = time()
    cache = load_cache()
    last_check = cache.get(provider_name, {}).get("last_check", 0)
    last_ok = cache.get(provider_name, {}).get("ok", False)

    if now - last_check < 60:           # 1分钟内复用上次结果
        return last_ok
    if now - last_check < 300:           # 5分钟内上次失败则仍标记不可用
        if not last_ok:
            return False

    # 执行探测：调用 MCP 的 tools/list
    ok = try_mcp_tools_list(provider_name, timeout=5000)
    cache[provider_name] = {"ok": ok, "last_check": now}
    return ok
```

- 不引入守护进程 / 定时任务
- 利用 mcporter 已有的进程重启能力：mcporter 会自愈挂掉的 MCP 子进程
- 编排器的探测只是确认 MCP 进程是否响应

---

## Q9 失败处理策略 — APPROVE 有损降级

**问题**：3 个 provider 全部失败怎么办？部分成功怎么办？

**盲点/遗漏**：
- 没有定义"失败"和"成功"的量化标准——搜索返回 0 结果算失败还是成功？
- 没有区分 provider 级失败和单条请求级失败

**裁决**：APPROVE 有损降级策略。

**结论**：

```
场景 A：全部 3 个 provider 都失败
  → 回退到旧的线性降级链，按顺序逐个尝试
  → 全部失败 → 返回 empty result + gap note

场景 B：部分成功（1-2 个 provider 成功）
  → 返回成功的聚合结果
  → 在 metadata 中标注哪些 provider 失败，原因

场景 C：部分 provider 返回 0 结果（非失败）
  → 视为"该 provider 对此查询无匹配"，不算失败
  → 只聚合有结果的
```

**成功率定义**：
- provider 成功 = HTTP 200 + 返回了列表结构 | 搜索结果条数不确定，有响应结构就算"成功"
- 搜索结果 0 条 = 该 provider 对此查询无匹配，不影响 provider 的健康状态
- 超时 / 异常 / 配额耗尽 = provider 失败，计入健康统计

---

## Q10 并行 vs 串行 — APPROVE 默认并行，按 intent 约束

**问题**：3 个 provider 全部并行/全部串行/混合？谁来决定？

**盲点/遗漏**：
- 假设 3 个 provider 都适合并行执行——但 exa 调 brave 的底层都和 Brave API 有关联？如果多个 provider 共享同一个底层引擎，并行会竞争同一资源。
- 没有考虑编排器的超时管理——3 个并行，最慢的卡 30s，整个调用就卡 30s

**裁决**：APPROVE 默认并行，按场景约束。

**结论**：

```yaml
# 执行模式配置文件 (orchestrator/intent-modes.yaml)
intent_modes:
  chinese-policy:
    strategy: serial          # 政策搜索需要精准，先用最好的
    providers: [minimax, brave, web_fetch]
    parallel_groups: []       # 全部串行
  english-academic:
    strategy: parallel
    providers: [brave, tavily, heventure]
    external_timeout_ms: 10000   # 总超时 10s，不是 3*30s=90s
  news:
    strategy: parallel
    providers: [brave_news, minimax]
    external_timeout_ms: 8000
  general:
    strategy: hybrid           # 并行与串行混合
    parallel_groups: [[brave, tavily], [heventure]]  # 前两个并行，第三个串行
    external_timeout_ms: 15000
```

并行执行的关键规则：
- 编排器设定全局超时（10-15s），不是各个 provider 超时的和
- 最快返回的 2 个结果优先，最慢的即使返回也丢弃（控制延迟）
- 同底层引擎的 provider 不并行（避免竞争）

---

## Q11 成本预算意识 — APPROVE 简单层级模型

**问题**：不同 provider 成本不同，编排器如何做成本优化？

**盲点/遗漏**：
- 方案暗示了"成本优化"是一个复杂的问题，搜索场景的 cost 敏感度很低——一次搜索最贵也就几分钱
- 配额耗尽 ≠ 成本，这是两个不同的问题

**裁决**：APPROVE 简单成本层级，不引入复杂优化算法。

**结论**：成本建模不需要实时优化，用静态优先级即可。

```yaml
cost_tiers:
  0:  # 免费无限量
    - heventure_ddg       # Docker 或 uvx，零成本
    - web_fetch           # OpenClaw 内置
  1:  # 免费有限额
    - brave               # 2000次/月免费
    - minimax             # Token Plan 配额
    - tavily              # 1000次/月免费
  2:  # 付费
    - exa                 # Exa AI pay-per-call
    - brave_pro           # Brave Pro plan
  3:  # 价格高/不可控
    - bright_data_serp    # Bright Data 按量付费
```

路由规则（不包含复杂优化）：
1. 同一 intent 内，Tier 0 的 provider 优先于 Tier 1，Tier 1 优先于 Tier 2
2. 同 tier 内的多个 provider 按健康状态选择
3. 配额耗尽等同于 Tier 提升——Brave 用完了就"升"到 Tier 2 去用 Exa

不需要线性规划、不需要实时竞价、不需要机器学习。

---

## Q12 注册流程 — APPROVE 目录自动发现

**问题**：新增 provider 不改原有代码。注册方式？

**盲点/遗漏**：
- 只提到了"不改代码"，但没有说明新增 provider 的完整流程——从 MCP Server 部署到编排器识别的完整链路
- 没有考虑登录/密钥管理

**裁决**：APPROVE 目录自动发现方案。

**结论**：完整注册流程：

```
Step 1: 部署 MCP Server
  → mcporter add <provider> 或手动写入 mcporter.json
  → 确保 MCP 进程启动并可响应 tools/list

Step 2: 创建 provider 描述符
  → 在 orchestrator/providers/<name>.yaml 新增文件
  → 定义: name, tool, cost_tier, capabilities, health_check, quota

Step 3: 加入 intent 映射（如果需要被特定的 intent 匹配到）
  → 修改 orchestrator/intent-modes.yaml，在对应 intent 下加入 provider 名称

Step 4: 验证
  → orchestrator probe <name>     # 确认 MCP 连接正常
  → search "test" --intent xxx    # 确认路由正确
```

**在不改代码的情况下新增 provider** = 只需要 Step 2（修改配置）+ 可选 Step 3。Step 1 是 MCP 基础设施操作，不属于编排器范畴。

编排器启动时扫描 `orchestrator/providers/` 目录，动态加载所有描述符。不存在则自动跳过。

---

## 架构总评

### 风险点

1. **职责边界膨胀**：multi-search 当前是"基础设施层不包含业务逻辑"。编排器加入了路由决策、意图映射、结果聚合——这些已经超出了"工具"的范畴，进入了"中间件"的领域。这是合理的演进，但需要明确标记。

2. **双运行时兼容性**：编排器的 Python 异步实现需要在 OpenClaw 和 Hermes 上都能运行。Hermes 的 MCP 通信方式与 OpenClaw 的 mcporter 不同，编排器需要抽象 MCP 调用层。

3. **数据落盘变更**：当前 multi-search 的数据落盘定义 `_data/multi-search/{session-id}/`，编排器的结果来源会包含 `orchestrator` 层的信息，需要更新落盘规范。

### 建议的实施顺序

```
Phase 0（基础设施）：
  ├─ Python 异步库框架 + CLI 入口
  ├─ provider YAML 描述符目录
  ├─ 统一结果格式 v1.0
  └─ 按需健康探测

Phase 1（功能）：
  ├─ intent 映射表 + 执行模式配置
  ├─ 并行/串行执行引擎
  ├─ 结果聚合去重
  └─ 失败处理 + 回退策略

Phase 2（运维）：
  ├─ 配额本地追踪
  ├─ provider 状态缓存
  └─ 调试日志（谁调了什么、耗时、结果）
```

### 红线提醒

这是基础设施层的 skill，它的调用者（如 2606152 的监管业务 Agent）依赖它的稳定性和可预测性。编排器引入的**不确定性**（哪个 provider 被选中、结果如何聚合）需要通过以下方式管理：
1. Provider 选择对调用方透明——输出中明确 `source_engine`
2. 失败时可追溯——输出中有 `engines_tried` 和 `engines_succeeded`
3. 调试模式下输出完整决策链路
