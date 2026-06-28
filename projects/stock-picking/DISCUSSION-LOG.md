# DISCUSSION-LOG.md — stock-picking 项目

---

## 2026-06-23 Session 1：收编讨论 + 架构拆解

**参与者**：Evan、chat-main-agent
**时长**：约 30 分钟（21:18 - 21:59）

---

### 议题 1：是否将 stock-picking-v2 纳入 Factory 管理

**结论**：是。

- stock-picking-v2 是成熟的多文件 skill（11 个文件，1200+ 行），符合 Factory SOP S0 的建 Skill 标准
- 当前位置 `~/.agents/skills/stock-picking-v2/` 不规范，源码应纳入 Factory 项目目录管理
- 新 GitHub 私有仓库：`evan-zhang/stock-picking`（去掉 -v2 后缀）
- 收编后重新编号，纳入 Factory semver 体系，首版 v1.0.0

### 议题 2：项目目录确定

**结论**：
```
domains/agent-factory/projects/stock-picking/
├── src/          # skill 源码（唯一真相源）
├── design/       # 设计档案
├── REQ-01.md
├── DISCUSSION-LOG.md（本文件）
└── ...
```

- 源码必须在项目目录内，确保完整性和可恢复性
- `~/.agents/skills/` 等位置只是部署目标
- GitHub 仓库是分发渠道

### 议题 3：是否合并 serenity-skill（卡脖子选股框架）

**分析**：
- serenity-skill 路径：`/Users/evan/.openclaw/gateways/life/domains/quant/skills/serenity-skill/`
- 13 个文件，包含核心方法论、逆向引擎、线索扫描、实战范例、产业地图、风险分析、战绩记录
- 与 stock-picking-v2 是互补关系：serenity 找研究线索，stock-picking 把线索变成交易
- 重叠点：R 阶段验证逻辑相似，都要求强制搜负面

**结论**：纳入，但不简单合并。作为独立的策略插件。

### 议题 4（关键决策）：架构重构

**Evan 指出问题**：
> 每日的定时触发不应该在 skill 里。选股是可以的。三天复选、四周追踪、建仓、持仓监控、移动止损，每一部分都应该可以单独拎出来。用一个 SOP 流程把它们串在一起。选股这块将来可以选用不同的策略。

**确认的新架构（三层）**：

#### Layer 1 — SOP 编排层
`stock-picking` master skill，定义完整生命周期：
```
选股 → 复选确认 → 追踪 → 建仓 → 持仓监控 → 止损/清仓
```
只做流程编排，不含策略实现和执行逻辑。

#### Layer 2 — 独立能力模块（可插拔）

| 模块 | 职责 | 策略相关 |
|------|------|---------|
| `taroc-strategy` | TAROC 五步选股 | ✅ 可替换 |
| `chokepoint-strategy` | 卡脖子选股（来自 serenity-skill） | ✅ 可替换 |
| `selection-validation` | 3天2次复选入池 | ❌ 通用 |
| `position-tracker` | 四周追踪+周复盘 | ❌ 通用 |
| `position-monitor` | 持仓监控+移动止损+组合风控 | ❌ 通用 |

#### Layer 3 — 共享基础设施
- `holidays/` 交易日历
- `data-schema` CSV 数据结构定义
- `scripts/` 可执行脚本

**关键设计原则**：
1. 选股策略可替换：TAROC、Chokepoint、未来更多策略
2. 持仓监控/止损独立，任何策略产出 candidates 后都能接入
3. 复选/追踪统一，不管哪条策略选出的股
4. cron 调度由 Gateway 管，skill 只定义"被调用时做什么"

---

### 待办（下一步）

- [x] 重写 REQ-01，按三层架构重新定义需求范围
- [ ] S3 方案设计：详细设计每个模块的接口和边界
- [ ] 确定 serenity-skill 拆解为 `chokepoint-strategy` 的具体方案
- [ ] 确定 cron 调度从 skill 中剥离后的 Gateway 配置方案

### 2026-06-23 22:02 续作记录

Evan 要求“继续”。已按上一轮确认的方向更新 `REQ-01.md`：

- 将定位从“三市场独立选股系统”改为“模块化选股与持仓流程 SOP”
- 明确 `stock-picking` 只做编排层，不再承载 cron、策略实现、持仓风控全部职责
- 将 TAROC 与 Chokepoint 定义为平级策略模块
- 将复选、四周追踪、持仓监控、移动止损定义为通用模块
- 新增项目级 `PLAN.md`，用于后续 Factory L2 流程交接

### 2026-06-23 22:13 基线讨论方式修正

Evan 指出：不能直接要求确认基线，应先在基线文档中画出完整流程图，然后基于流程图逐节点讨论。

已据此更新 `REQ-01.md`：

- 新增完整 Mermaid 流程图：外部触发 → 交易日检查 → 策略选择 → draft → 复选 → candidates → 四周追踪 → target pool → 人工买入确认 → positions → 持仓监控 → 风控事件 → trade log
- 新增“节点逐项评审”：每个节点分别写明当前做法、优点、缺点、改进建议
- 将 `REQ-01.md` 状态改为“S2 讨论版：流程图与节点评审待逐项确认”
- 更新 `PLAN.md`：下一步不是进入 S3，而是先按流程图逐节点收集 Evan 反馈

### 2026-06-23 22:43 节点 0 评审会确认

Evan 确认采用“主方案 + 独立方案 + Factory Review + 合并结论”的逐节点评审会模式。

节点 0（外部触发入口）结论：

- 只接受“单市场 + 单策略 + 单运行模式”的原子请求。
- 多市场、多策略、完整流程由 SOP 编排层拆成多个原子请求，用 `correlation_id` 串联。
- Node 0 只负责入口契约、参数校验、幂等、审计，不负责 cron 调度、市场日历、策略实现或交易执行。
- v1 拒绝 `market: [US, HK]`、`strategy_id: mixed`、`run_mode: full`、`run_mode: monitor`、`dry_run: false`。
- `custom` 策略必须提供可解析的策略引用，不能接受自由文本策略。

下一步进入节点 1：交易日与运行上下文检查。

### 2026-06-23 22:55 节点 1 评审会确认

Evan 确认采用节点 1（交易日与运行上下文检查）的收紧版结论。

节点 1 结论：

- Node 1 不是简单判断“今天是否开市”，而是生成统一 `run_context`，供后续策略、复选、追踪模块消费。
- Node 1 负责市场本地日期、时区、交易日、休市、半日市、临时停市判断，以及结构化运行决策。
- Node 1 不负责 cron 调度、策略选择、universe 解释、日历数据长期维护、个股停牌判断或交易执行。
- v1 先采用“内置薄包装 + 内部日历表/override 表”的可落地实现；S3 再决定是否抽成 Layer 3 的 `market-calendar`。
- 输出必须有 `decision: proceed | skip | needs_override | fail`，不能只靠 `is_runnable` 推断行为。
- 周末、假日、已知休市返回 `skip` / `HEARTBEAT_OK`，不调用下游策略节点。
- 半日市 v1 默认允许 `discovery`、`validation`、`tracking` 继续运行，但必须写入 warning。
- 日历 unknown 时，manual/sop 进入 `needs_override`，cron fail closed。
- 时区不匹配、market 不支持、日期格式错误为 hard fail。

下一步进入节点 2：策略选择器。

### 2026-06-23 23:08 节点 2 评审会确认

Evan 授权后续节点不再逐项等待确认，由主 agent 全程编排推进；仍保留“主方案 + 独立方案 + Factory Review + 合并结论”的评审会模式，并将结论写入文件。

节点 2（策略选择器）结论：

- Node 2 是纯策略注册表选择器，不是策略执行器。
- Node 2 只在 Node 1 `run_context.decision=proceed` 后工作；否则结构化拒绝，不进入下游。
- Node 2 负责 registry lookup、版本解析、market/run_mode/caller/dry_run/schema/custom_ref 校验，以及生成 `strategy_dispatch` envelope。
- Node 2 不执行策略、不融合多策略、不排序候选、不兜底切换 TAROC、不处理 portfolio 或交易动作。
- 多策略编排仍在 SOP 外层完成；每个 atomic run 只 dispatch 一个明确策略版本。
- v1 不支持 `latest`；cron/sop 必须传精确 semver。
- manual 可在 registry 有明确 default 时省略版本，但必须写入 warning。
- `custom` 不接受自由文本；`custom_ref` 必须来自白名单或 registry。
- Chokepoint v1 先标记为 `experimental`，仅允许 `manual` 调用。
- registry 版本解析必须来自同一份 snapshot，并在 dispatch 输出 registry version/hash，保证审计可追溯。

下一步继续节点 3：TAROC Strategy。后续节点默认由主 agent 持续推进，完成整套新方案后再进入开发方式决策。

### 2026-06-23 23:18 节点 3 评审会确认

节点 3（TAROC Strategy）结论：

- TAROC 保留 T/A/R/O/C 方法论，但只作为可插拔策略插件存在。
- TAROC 只消费 Node 1 `run_context` 与 Node 2 `strategy_dispatch`，输出 `draft_candidates.v1`。
- TAROC 不负责交易日判断、cron、CSV 落盘、消息推送、复选入池、候选追踪、仓位金额、买入确认、持仓监控或移动止损执行。
- 原 `discovery.md` 中写 drafts CSV 与 Telegram 推送的职责迁出到 SOP 层。
- 原 TAROC 方法论中的具体仓位金额迁出到风险预算 / position-sizer 模块。
- A 阶段赛道分与 C 阶段总确信度分必须分开命名；对外输出 `subscores + aggregate_score + conviction.level`。
- T 阶段广度搜索与垂直专业源必须统一为“候选信号源”，所有信号都要经过专业价值判断和大众认知滞后评估。
- 强制负面搜索必须 fail-loud：未执行负面搜索或无记录时，不得产出合格 draft。
- Phase 4 / crowdedness 高的主题默认只进入 watch，不直接进入 validation。

节点 3 最高优先级是冻结 `draft_candidates.v1`，因为它同时约束 TAROC、Chokepoint、Draft、Validation 和后续候选生命周期。

### 2026-06-23 23:25 节点 4 评审会确认

节点 4（Chokepoint Strategy）结论：

- Chokepoint v1 是实验性策略插件，默认仅 `market=US`、`caller=manual`、`run_mode=discovery`。
- Chokepoint 不进入 cron/sop，不输出买卖建议，不写 candidates，不做仓位、止损或持仓监控。
- Chokepoint 输出拆成两层：
  - `theme_research.v1`：主题/产业链研究线索，写入 `data/research/_themes/`。
  - `draft_candidates.v1`：满足证据门槛后，由 `draft-promoter` 升级为统一 draft。
- `lead-scanner`、`reverse-engine`、主六步框架都先产 research/thesis；不能直接绕过证据门槛进入 draft。
- `theme_research.v1` 必须带 `upgrade_triggers`，避免研究主题无限堆积。
- `lead-scanner` 的共识线索降级为 observe，不可直接进入 draft。
- `reverse-engine` 发现的邻居节点必须回到 theme research。
- Serenity 的方法论可作为 framework reference；公开战绩、履历、具体 call 不进入 registry、dispatch 或默认信号。
- Node 4 必须显式暴露单路径依赖、微型股流动性踩踏、不可验证履历、幸存者偏差、技术路径误判等框架固有风险。
- v1 至少运行 6 个月、manual 调用不少于 10 次、无重大 thesis break 后，才评审是否开放 HK/CN、tracking 或 sop。

### 2026-06-23 23:45 节点 5-8 评审会确认

节点 5-8（候选生命周期）采用 WARN 后收紧版：

- Node 5 统一 draft 只描述策略输出，不保存复选过程；必须有 `draft_id`、`strategy_run_id`、`correlation_id` 与证据链。
- `confidence` 是策略自评，不允许跨策略聚合成单一分数。
- Node 6 复选按交易 session 计算；半日市默认不计入复选窗口，除非显式允许。
- Node 6 必须输出 `validation_event`，并用 `validation_run_id` 做幂等，不能重复 promotion。
- Node 7 候选记录必须有 `origin_draft_id`，保证 `candidate -> draft -> strategy_run` 审计链。
- `aggregate_thesis` 必须声明 `concatenation | summary`，v1 默认 concatenation。
- Node 8 追踪事件必须冗余 `origin_draft_id`；AI 只能写 `promote_suggested/remove_suggested`，最终 removed 必须 human 确认。
- 事件存储 v1 采用 per-market 串行写入，JSONL 按 market/week 分片；旧 CSV 迁移需另出 migration plan。

### 2026-06-23 23:58 节点 9-12 评审会确认

节点 9-12（行动与风险层）已结合 `/Users/evan/.openclaw/gateways/life/domains/quant/` 真实文件核对后写入 `REQ-01.md`：

- Node 9 target pool 是建仓前唯一 gated queue；status 固定为 `active/deferred/rejected/built/expired`。
- `active` 且 build-ready 的 target pool 行必须有 entry、stop、target、position amount 和 deadline；`position_amount=0` 只能表示 awaiting sizing。
- Node 10 买入确认必须是 machine-checkable approval artifact；真实 buy 入口无 approval 时 hard error。
- 现有 `futu_tool.py buy` 可直接触达券商 API，进入 S4 高优先级修复清单。
- Node 11 将 `positions.csv` 定位为 shadow book；HK/US 以 API broker 为真，`guosen`/A 股手工账户按 ledger-only 处理。
- Reconcile 只读 positions，并输出运行日志、risk event 与 resolution 生命周期。
- Node 12 默认只产生 risk event 和建议动作，不直接下单；未来自动卖出必须通过 execution guard。
- `position-monitor.py` 的硬编码路径、shell 拼接和规则写死进入 S4 修复清单。

### 2026-06-24 GRV Battle 一轮 WARN 吸收

factory-reviewer 对 `REQ-01.md` + `design/GRV.md` 做 GRV Battle 一轮审查，结论为 WARN：可进入 S3 设计，但不可直接进入 Ralph Loop / S4。

已吸收的必修问题：

- B001：在 GRV 顶部新增“评审吸收矩阵”，显式消化 Node 0/1/2/4 的 24 条 finding。
- M001：给 R 增加 P0/P1 优先级，并将 M4 拆为 M4a 安全/验证底座与 M4b 业务模块。
- M002：R5 从“修复清单”升级为 execution guard 最小骨架与拒绝用例。
- M003：R3/R4 明确 custom ref 白名单、状态机单向、schema/registry 双冻结、Chokepoint exit criteria。
- M004：风险应对从“已定设计选择”改为真正缓解措施。
- M005：新增 M3.5 reviewer 闸门，S3 未审查不得进入 Ralph Loop。

当前动作：已更新 `design/GRV.md` 与项目 `PLAN.md`，并启动 GRV Battle 二轮复审。若二轮无 blocker，则进入 S3 设计；仍不直接进入 S4。

### 2026-06-24 00:10 节点 13 评审会确认

节点 13（Research Evidence Store）采用共享基础设施定位：

- Node 13 是 Layer 3 证据底座，不是普通 SOP 执行节点。
- 它负责 evidence refs、claim、索引、快照、来源质量、生命周期与审计。
- TAROC、Chokepoint、Validation、Tracker、Target Pool、Reconcile/Risk 都只引用 evidence ids，不把 free-text reason 当唯一证据。
- v1 采用 `evidence_ref.v1 + claim.v1` 两层模型：证据对象和 thesis-relative assertion 分开。
- Markdown 只是人工阅读投影；canonical record 用 JSON/JSONL 保存。
- 写入规则为 creator write-once，后续 append-only；证据撤回或降级通过 lifecycle audit 暴露，不删除旧记录。
- AI 推理只能标记为 `ai_inference`，不能伪装成 primary/secondary 事实来源。
- 负面搜索即使没有发现反证，也必须保存查询、时间和结果。
- S3 需要为 evidence store 单独落 data-schema 与 migration plan。

### 2026-06-24 S3 方案设计启动

GRV Battle 二轮复审结论为 WARN，但无 blocker / major；B001 与 M001-M005 全部结构性吸收。允许进入 S3 设计，不允许直接进入 Ralph Loop / S4。

S3 已创建或更新：

- `design/DESIGN.md`：S3 baseline，覆盖模块边界、数据流、文件结构、失败行为、UX 兜底和粒度判断。
- `src/references/data-schema.md`：P0 schema baseline，替换旧 CSV 字段定义；旧 CSV 降级为 `legacy_csv_projection.v1`。
- `src/strategies/registry.yaml`：TAROC active，Chokepoint experimental/manual-only。
- `src/references/registry-design.md`：registry snapshot 原子性、版本策略、拒绝码、custom_ref 白名单。
- `src/references/execution-guard.md`：execution guard 最小骨架、拒绝用例、`futu_tool.py buy` 可观测验收信号。
- `src/references/migration-plan.md`：旧 CSV 迁移、兼容投影、回滚和审计字段。

已吸收 Battle 二轮新发现：

- F001：Chokepoint exit criteria 明确为 AND，并定义 major thesis break。
- F002：`custom_ref` 白名单固定为 `src/strategies/custom_refs.yaml`，加载时机与审计路径写入设计。
- I001：`futu_tool.py buy` 修复验收要求 broker API rejected path 调用次数为 0 或在 broker client 前阻断。
- I002：validation 幂等键不再只依赖 `signal_date`，改为包含 `calendar_checked_at` 与 `validation_session_key`。

当前动作：已启动 M3.5 factory-reviewer 闸门审查。M3.5 未通过前，不进入 Ralph Loop / M4a。
