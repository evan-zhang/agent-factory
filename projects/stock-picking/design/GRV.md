# stock-picking GRV

- 项目：stock-picking
- 文档编号：P-GRV-01
- 创建时间：2026-06-24
- 状态：Draft for Battle v2
- 当前判定：可进入 S3 设计；不可直接进入 Ralph Loop / S4 实施

## G - 目标

把旧 `stock-picking-v2` 从单体选股 skill 重构为模块化 SOP 编排层，让策略、复选、追踪、建仓衔接、持仓对账、风控监控、证据库都能独立演进，并在真实交易动作前建立可审计的人工确认和执行闸门。

v1.0.0 的目标不是“一次性自动交易系统”，而是一个可审计、可 dry-run、可逐模块验证的股票研究与候选生命周期系统。

## 评审吸收矩阵

本节是 Battle 输入的入口闸门。S2 节点评审中的 finding 必须在 GRV 中显式标记吸收状态，否则不得进入 Ralph Loop。

状态词：
- `absorbed`：已进入 R / V / milestone / acceptance。
- `deferred`：明确延期，且有理由。
- `open`：未解决；存在 open 时不得进入 Ralph Loop。

| ID | 来源 | Finding | 吸收状态 | 落点 |
|---|---|---|---|---|
| N0-01 | Node 0 | cron 属于 Gateway/外部调度，不属于 skill 内部逻辑 | absorbed | R1, V3 |
| N0-02 | Node 0 | 入口必须是单市场、单策略、单 run mode 的 atomic request | absorbed | R1, R2 |
| N0-03 | Node 0 | 多市场/多策略/full workflow 必须由外层拆分并用 `correlation_id` 串联 | absorbed | R1, R2 |
| N0-04 | Node 0 | v1 拒绝 `mixed/full/monitor/dry_run=false` 进入下游 | absorbed | R1, R5 |
| N0-05 | Node 0 | `custom` 策略不能接受自由文本，必须有可解析引用 | absorbed | R3 |
| N0-06 | Node 0 | 每次运行必须带 request/correlation/caller/market/strategy/run_mode/dry_run 审计字段 | absorbed | R1, R2, R6 |
| N1-01 | Node 1 | Node 1 输出统一 `run_context`，不是策略内的交易日判断 | absorbed | R1, R2 |
| N1-02 | Node 1 | 输出必须有 `decision: proceed/skip/needs_override/fail` | absorbed | R2 |
| N1-03 | Node 1 | closed/holiday/weekend 不得调用下游策略 | absorbed | R1, R2 |
| N1-04 | Node 1 | 日历 unknown 时 manual/sop 需要 override，cron fail closed | absorbed | R2 |
| N1-05 | Node 1 | 半日市规则必须结构化并写入 warning / policy | absorbed | R2, R4a |
| N1-06 | Node 1 | 下游模块不得重复实现交易日判断，只消费 `run_context` | absorbed | R1, R2, R4a |
| N2-01 | Node 2 | Node 2 是 registry selector，不执行策略 | absorbed | R3 |
| N2-02 | Node 2 | Node 2 只输出 `strategy_dispatch` envelope | absorbed | R3 |
| N2-03 | Node 2 | cron/sop 必须精确 semver；v1 不支持 `latest` | absorbed | R3 |
| N2-04 | Node 2 | 不允许 fallback 到 TAROC 或其他策略 | absorbed | R3 |
| N2-05 | Node 2 | registry 必须有版本、snapshot/hash、schema validation | absorbed | R3, R4b |
| N2-06 | Node 2 | Chokepoint v1 为 experimental + manual only | absorbed | R3 |
| N4-01 | Node 4 | Chokepoint v1 限定 US/manual/discovery | absorbed | R3 |
| N4-02 | Node 4 | Chokepoint 先产 `theme_research.v1`，满足证据门槛再升 draft | absorbed | R3, R6 |
| N4-03 | Node 4 | `theme_research.v1` 必须带 `upgrade_triggers` | absorbed | R3, R6 |
| N4-04 | Node 4 | lead-scanner 共识线索只能 observe，不能直接 draft | absorbed | R3 |
| N4-05 | Node 4 | Serenity 战绩/履历只作 framework reference，不进 registry/dispatch/权重 | absorbed | R3, R6 |
| N4-06 | Node 4 | 单路径依赖、微型股流动性、幸存者偏差、技术路径误判必须显式暴露 | absorbed | R3, R6 |

当前 `open` finding：无。

## R - 成果

### R1：SOP 编排层（P0）

交付物：
- 重写后的 `src/SKILL.md`
- `src/flows/*.md` 的流程说明
- 外部 Gateway cron 调用建议，不写入 skill 运行逻辑

验收标准：
- 不包含内嵌 cron schedule。
- 明确 Node 0-13 的调用顺序、输入输出和 skip/fail 行为。
- 外部触发只接受单市场、单策略、单 run_mode 的 atomic request。
- 多市场/多策略由外层拆成多次 atomic run，并用 `correlation_id` 串联。
- `run_context.decision != proceed` 时，不得进入策略节点。

### R2：统一数据契约（P0）

交付物：
- `src/references/data-schema.md`
- JSON schema 或等价 schema validator 的最小骨架
- 旧 CSV 兼容投影说明

验收标准：
- 覆盖 `atomic_request.v1`、`run_context.v1`、`strategy_dispatch.v1`、`draft_candidates.v1`、`theme_research.v1`、`validation_event.v1`、`candidate_record.v1`、`tracking_event.v1`、`target_pool.v1`、`approval.v1`、`reconcile_report.v1`、`risk_event.v1`、`evidence_ref.v1`、`claim.v1`。
- 所有候选生命周期都能追溯 `draft -> validation_event -> candidate -> tracking_event -> evidence`。
- CSV 只作为投影或兼容层，不能把 free-text reason 当唯一证据。
- schema validator 必须拒绝：`removed` 非 human 写入、缺 `origin_draft_id`、缺 evidence 引用、缺 `registry_record_hash` 的 dispatch。

### R3：策略插件边界（P0）

交付物：
- `src/strategies/registry.yaml`
- strategy registry schema 与 selector 设计
- TAROC / Chokepoint 插件规范
- Chokepoint `theme_research.v1` 到 draft 的 promoter 规则

验收标准：
- Node 2 只 dispatch，不执行策略。
- registry 支持 `registry_version`、per-record hash、defaults、allowed callers、status、output schema。
- cron/sop 必须精确 semver；manual 省略版本时只能使用唯一 default 并写 warning；不支持 `latest`。
- unknown strategy、unsupported market/run_mode、disabled strategy、cron 调用 experimental Chokepoint 必须结构化拒绝。
- `custom_ref` 必须来自白名单或 registry；自由文本、路径穿越、临时脚本全部拒绝。
- TAROC 只输出 draft，不写 CSV、不推消息、不建仓。
- Chokepoint v1 仅 US/manual/discovery，先产 `theme_research.v1`，满足证据门槛后再升 draft。
- Chokepoint exit criteria：至少 6 个月、manual 调用不少于 10 次、无重大 thesis break 后，才评审是否开放 HK/CN、tracking 或 sop。

### R4a：候选生命周期模块（P0）

交付物：
- `selection-validation` 设计与最小接口
- `position-tracker` 设计与最小接口
- `target-pool-manager` 设计与最小接口
- candidate/tracking/target pool 状态机说明

验收标准：
- validation 按交易 session 计算，半日市默认 exclude。
- promotion 幂等，不重复产生 candidate。
- Node 7 状态机单向受控；`removed` 必须 human。
- AI 只能写 `promote_suggested/remove_suggested`，不能直接删除或建仓。
- target pool 的 active build-ready 行必须有 entry、stop、target、size、deadline。
- 多策略命中同一 ticker 时保留各自 `source_drafts[]` 和 confidence，不做虚假综合置信度。

### R4b：验证与迁移底座（P0）

交付物：
- schema validator
- registry validator
- event store append-only 写入规则
- 旧 CSV migration plan

验收标准：
- registry 有 schema validation 测试，dispatch hash 可稳定复算。
- candidate lifecycle schema 与 evidence schema 双冻结；S4 不得边实现边改字段。
- 旧 CSV 迁移有兼容窗口、回滚方案、迁移审计。
- per-market JSONL 写入 v1 采用串行；未来并发必须引入文件锁。

### R5：交易安全与风控底座（P0）

交付物：
- `buy-approval-gate` 设计
- `position-reconcile` 设计
- `position-monitor` 设计
- `execution-guard` 最小骨架
- `futu_tool.py buy` 裸调用修复

验收标准：
- 真实 buy 必须读取 approval artifact；无 approval 时 hard error。
- `futu_tool.py buy` 不允许裸调券商 API；必须经过 execution guard 或被显式禁用。
- 最小 `execution-guard` 骨架必须包含：approval artifact 校验、pretrade check 引用、dry-run 默认、market/run_context 校验、broker action allowlist、audit log、hard-error path。
- 最小验证用例必须覆盖：无 approval 拒绝、过期 approval 拒绝、非 Evan approval 拒绝、pretrade check 缺失拒绝、dry_run false 但无 guard 拒绝。
- reconcile 区分 API broker 和手工 ledger，输出 resolution 生命周期。
- v1 默认只生成 risk event，不自动下单。

### R6：Evidence Store（P1）

交付物：
- `evidence-store` schema
- 路径布局、索引、审计规则
- migration plan

验收标准：
- 支持 `evidence_ref.v1 + claim.v1` 两层模型。
- 支持 source dedup、snapshot、source quality、status lifecycle。
- 正面证据、负面证据、break condition 同级保存。
- AI inference 不能伪装成事实来源。
- `theme_research.v1` 必须有 `upgrade_triggers`，并写入 theme index。
- `source_url + claim_hash` 重复写入时必须 dedup。

## V - 关键举措

- V1：冻结 S2 基线，把 `REQ-01.md` 从讨论稿整理为实现基线。
- V2：补齐 `src/references/data-schema.md`，将所有 Node contract 结构化。
- V3：重写 `src/SKILL.md` 为 master SOP，不再承载策略实现和 cron。
- V4：建立 `src/strategies/registry.yaml` 与 strategy dispatch 规则。
- V5：拆 TAROC 与 Chokepoint 的策略接口，保留旧逻辑为兼容 reference。
- V6：实现或定义候选生命周期事件存储，替换 day1/day2/day3 写回 draft 的模式。
- V7：设计 approval/execution guard，并把 `futu_tool.py buy` 裸调用列为首个安全修复。
- V8：设计 evidence store 与旧 CSV/Markdown 的 migration 方案。
- V9a：Battle 一轮审查 GRV + REQ，吸收 blocker / major。
- V9b：Battle 二轮复审 GRV，确认可进入 S3。
- V9c：S3 设计完成后增加 M3.5 闸门审查，再决定是否进入 Ralph Loop。

## 约束条件

- 不重启、不杀 Life Gateway。
- 不自动买入，不自动卖出。
- 真实交易动作必须 Evan 人工确认。
- v1 优先保证可审计和安全，不追求一次性自动化全部流程。
- 保留旧 `stock-picking-v2` 的可用入口直到新 SOP 通过验收。
- 所有涉及 quant 数据路径的实现必须先读 `DATA-PATHS.md`，不硬编码新路径。
- Chokepoint v1 不进入 cron/sop。
- schema 与 registry 在 S3 冻结后，S4 实施只允许通过变更记录调整，不允许隐式漂移。

## 不做什么

- 不做自动交易系统。
- 不把 cron 调度写进 skill。
- 不把 TAROC 设为不可替换默认策略。
- 不把 Chokepoint 的公开战绩、履历、粉丝量作为策略信号。
- 不把 CSV 当 canonical event store。
- 不让 strategy plugin 直接写 candidates、target pool、positions 或 broker order。
- 不在 v1 做图数据库、RAG、实时 webhook、自动卖出。

## 风险

- 旧 CSV 与新事件模型迁移不完整，导致历史候选断链。
  - 真正缓解：先做只读兼容投影，再出 migration plan；迁移必须有审计和回滚。
- execution guard 设计不足，导致文档写了人工确认但代码入口仍可裸买。
  - 真正缓解：R5 先交付最小 guard 骨架与拒绝用例，再碰 broker buy。
- Chokepoint 方法论执行成本高，容易拖慢每日流程。
  - 真正缓解：v1 manual only + US only + 搜索预算 + theme research 先行。
- Evidence store 设计过重会阻碍落地。
  - 真正缓解：v1 JSON/JSONL + 索引，不做图数据库/RAG。
- 多模块拆分后调用链变复杂。
  - 真正缓解：每个节点保留 request_id/correlation_id，并用 schema validator 做链路检查。
- S3 设计缺陷若直接进入 Ralph Loop，会被放大成多周返工。
  - 真正缓解：新增 M3.5 reviewer 闸门；未过不得进 M4。

## 里程碑

- M1：S2 基线冻结：`REQ-01.md`、`DISCUSSION-LOG.md`、`PLAN.md` 更新完成。
- M2：Battle 审查：factory-reviewer 对 GRV 和 REQ 做 WARN/BLOCK/PASS。
- M3：S3 设计：创建 `design/DESIGN.md`、`src/references/data-schema.md`、registry/schema validator 设计。
- M3.5：S3 闸门审查：factory-reviewer 审查 DESIGN + schema + registry + execution guard skeleton plan。
- M4a：Ralph Loop 安全底座：schema/registry validator、execution guard、approval gate、migration scaffold。
- M4b：Ralph Loop 业务模块：SOP、TAROC/Chokepoint、validation/tracker/target-pool/evidence-store。
- M5：S5 验收：旧入口兼容、新 SOP dry-run 跑通、交易安全闸门验证通过。

## Ralph Loop 准入条件

进入 Ralph Loop / S4 前必须全部满足：
- GRV Battle 二轮没有 blocker。
- `design/DESIGN.md` 已定义模块边界、目录结构、调用顺序、失败行为。
- `src/references/data-schema.md` 已冻结 P0 schema。
- `src/strategies/registry.yaml` 与 registry validator 设计已冻结。
- execution guard 最小骨架的拒绝用例已写入 S3 设计。
- M3.5 factory-reviewer 闸门通过，或仅剩明确可在 S4 第一轮关闭的 WARN。

## 开发方式建议

采用 TPR 全流程 + Ralph Loop 持续执行，但顺序必须是：

1. GRV Battle 二轮：修掉 blocker / major。
2. S3 方案设计：落 `DESIGN.md`、data schema、registry、guard skeleton plan。
3. M3.5 审查：防止 S3 bug 带进多周实现循环。
4. M4a 先做安全与验证底座。
5. M4b 再做业务模块拆分。
6. S5 用 dry-run 全链路和交易闸门拒绝用例验收。

不建议直接一次性 coding：
- 容易把新 SOP 又写回单体。
- 容易遗漏 approval/execution guard 这类安全红线。
- CSV migration 和 evidence store 需要分阶段验证。
