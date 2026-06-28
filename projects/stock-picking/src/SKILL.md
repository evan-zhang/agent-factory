---
name: stock-picking
description: "编排股票研究候选生命周期，触发词：选股、sp2、复选、候选池、周复盘。只做研究/候选/审批/风控事件，不自动交易；行情与账户查询转 longbridge，真实持仓对账转 my-positions。"
aliases: [sp2, stock-picking, stock-picking-v2]
---

# Stock Picking SOP

`stock-picking` 是股票研究与候选生命周期的 SOP 编排层。它把一次选股请求拆成可审计事件：请求、交易日上下文、策略调度、研究输出、候选验证、目标池、审批、对账、风险事件和证据引用。

它不是自动交易系统，也不是 TAROC 单策略脚本。策略只产研究输出；任何 broker-affecting action 必须先过 execution guard。

## 何时触发

- 用户说“选股”“sp2”“跑一下今日候选”，需要生成结构化 draft candidates。
- 用户说“复选”“验证候选”“候选池更新”，需要检查已有 draft 是否还能成立。
- 用户说“周复盘”“四周追踪”“清理建议”，需要生成 tracker 建议和风险事件。
- 用户说“加入目标池”“准备买入审批”，需要生成 target pool item 和 approval request。
- 用户说“持仓对账”“风险监控”，且上下文属于本 SOP 的候选或目标池生命周期。

不要在以下场景触发：

- 只问单只股票实时行情、盘口、K 线、财报、新闻，转 `longbridge` 或其子 skill。
- 查询 Evan 真实持仓、账户资产、跨券商对账，转 `my-positions`。
- 一次性投资建议、宏观闲聊、教学解释，不写入候选生命周期。
- 用户要求真实下单但没有审批 artifact，不执行，返回 execution blocked。

## 执行流程

### 1. 生成 atomic request

把自然语言请求归一成 `atomic_request.v1`。一次请求只允许一个 market、一个 strategy、一个 run mode。

默认值：

- `dry_run=true`
- `caller=manual`
- `strategy_id=taroc`
- `run_mode=discovery`

拒绝：

- 多市场混跑
- `run_mode=full` 或 `monitor`
- `dry_run=false`
- 未白名单 `custom_ref`

### 2. 检查运行上下文

生成 `run_context.v1`。市场关闭、周末、节假日、未知日历、无效 timezone、unsupported market 都不得进入策略调度。

cron 不属于 skill 内部职责。外部 Gateway cron 只负责触发，skill 内部仍按 atomic request 与 run context 审计。

### 3. 选择策略

调用 `src/scripts/validate_registry.py` 的同等逻辑：

- 读取 `src/strategies/registry.yaml` 一次并计算 snapshot hash。
- 在同一份内存快照中解析 exact version 或 manual default。
- 计算 selected record hash。
- 输出 `strategy_dispatch.v1`。

不得 fallback 到 TAROC 或其他策略。

### 4. 执行研究策略

TAROC 与 Chokepoint 平级，但 maturity 不同：

- TAROC：默认 active，支持 US/HK/CN 的 discovery 与 validation。
- Chokepoint：experimental，只允许 manual + US + discovery。

策略输出必须含 `strategy_id`、`strategy_version`、`registry_record_hash`、`source_evidence`、`negative_evidence_searched` 和 `next_step`。

本地最小干跑入口：

```bash
python3 src/scripts/dry_run_orchestrator.py --event-root /tmp/stock-picking-events discovery
python3 src/scripts/dry_run_orchestrator.py --event-root /tmp/stock-picking-events validation
```

该入口只写 append-only JSONL 事件，不联网、不查询账户、不触达券商。

### 5. 候选生命周期

按 flow 文档处理：

- `flows/discovery.md`
- `flows/validation.md`
- `flows/weekly-review.md`
- `flows/target-pool.md`
- `flows/approval.md`
- `flows/reconcile.md`
- `flows/risk-monitor.md`

CSV 只能作为 legacy projection 或迁移输入；canonical 记录是事件 schema。

### 6. 证据与 claim

所有投资判断必须引用 `evidence_ref.v1` 或明确标记为 AI inference。claim 使用 `claim_kind + polarity` 双轴模型，不使用旧 `claim_type`。

## 安全边界

- 真实 buy 需要 `approval.v1`：`approval_state=approved`、`approved_by=Evan`、未过期、匹配 `pool_item_id`、pretrade check pass。
- 真实 sell 在 v1 禁用，只能生成 blocked recommendation 或 risk event。
- `execution_guard.py` 必须在 broker client 调用前执行；拒绝路径 broker API call count 必须为 0。
- risk event 的 `execution_allowed` 恒为 false。
- AI 可以建议移除候选，不能代表 human 写最终 removed。

## 配置与授权

必填配置：

- Longbridge 行情能力：优先使用已有 `longbridge-*` skills 或 CLI 环境。
- OpenClaw message/cron：由 Gateway 提供；cron 配置在 skill 外部维护。
- 数据根目录：后续 S4 数据实现必须明确 event store 根路径，不能隐式写当前目录。

可选配置：

- TradingAgents：仅用于 TAROC C 阶段多空辩论；不可用时降级为同 LLM 正反抗辩。
- Chokepoint custom refs：只允许 `src/strategies/custom_refs.yaml` 白名单项。

不得把券商 token、OpenClaw token、Telegram token 写入本 skill 仓库。

## 示例

用户：“sp2 今天跑一下美股初选”

执行：

1. 生成 US discovery atomic request。
2. 检查美股日历与 session。
3. registry dispatch 到 TAROC exact/default version。
4. 生成 `draft_candidates.v1`，附 evidence refs 与 negative evidence search 状态。
5. 返回候选摘要、证据覆盖、warnings 和下一步。

用户：“把 AAPL 加入目标池，准备买”

执行：

1. 检查该候选是否来自有效 candidate/validation event。
2. 生成 `target_pool_item.v1`。
3. 生成 `approval.v1` request。
4. 不调用券商；等待 Evan 审批 artifact。

## 问题反馈

记录问题时附上：

- `request_id`
- `correlation_id`
- schema name
- reject code 或 execution guard decision id
- 触发用语

Factory 项目内问题先写入 `DISCUSSION-LOG.md`；发布后再指向对应 GitHub Issue。
