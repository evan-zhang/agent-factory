## 审查结论

**总体评级**：CONDITIONAL PASS
**置信度**：0.84
**审查对象**：B 类（方案类）— stock-picking Node 0「外部触发入口」基线方案（S2 节点评审稿）
**审查时间**：2026-06-23 22:36 CST
**使用模型**：newapi-openai/MiniMax-M3
**审查依据**：
- 被审上下文 `projects/stock-picking/node-0-trigger-entry-review-context.md`
- 现行基线 `projects/stock-picking/src/SKILL.md`（旧 v2.0 单体）
- 需求稿 `projects/stock-picking/REQ-01.md` 节点 0 段落
- 编排计划 `projects/stock-picking/PLAN.md`

---

## 一句话总评

边界判断正确，调度从 skill 内部抽离的方向对；输入契约基本够用但还缺 4–5 个高价值字段；多市场/多策略的拆分语义需要写进契约而不是放进执行黑盒；dry_run 默认值方向对，但 `dry_run=false` 的语义在 Node 0 这一层没定义清楚。可在补齐 §四 列出的条件项后，作为 S2 基线放行。

---

## 维度评分

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 边界正确性 | 4 | 「调度属 Gateway，契约属 skill」方向正确，需补「推荐 cadence 是建议不是执行」 |
| 输入契约完整性 | 3 | 6 字段可用，但缺 `strategy_version`、`timezone / market_session`、`universe`、`correlation_id`、`priority` |
| 多市场/多策略语义 | 3 | 「外层多、内层拆」正确，但需要从契约层禁掉歧义，不是依赖执行层好习惯 |
| dry_run 策略 | 3 | 默认 true 对；`dry_run=false` 在 Node 0 这一层没定义边界，且与未来 execution gateway 概念耦合 |
| 可行性 | 4 | 没有任何字段是当前 runtime 做不到的；纯契约层修改 |
| 与 REQ-01 一致性 | 4 | 节点 0 段落、PLAN.md 关键决策、新流程图都支持该方案 |
| 验收标准可测试性 | 3 | 缺：拒绝多市场 / 拒绝 mixed 策略 / 字段缺失返回 4xx / 幂等键 / 日志格式 |
| 风险识别 | 4 | 编排者识别了「mixed 黑盒」「卖出零人工干预」两个主要风险，方向对 |

---

## 问题清单

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| F001 | major | 完整性 | 输入契约 | 缺 `strategy_version`，与 `strategy_id` 是两个不同维度。版本号缺失会让 draft 难以复现和审计「同一 thesis 不同版策略」 | node-0-trigger-entry-review-context.md「Suggested input fields」段 | 增加 `strategy_version: semver`，要求与策略模块内 VERSION 一致 |
| F002 | major | 一致性 | 输入契约 | 缺 `timezone` 或 `market_session` 提示。CN 9:30 / HK 9:30 / US 9:30 ET 是三个不同时区，复盘时「同一交易日」极易误判 | node-0-trigger-entry-review-context.md「Suggested input fields」段 | 增加 `market_session: pre \| regular \| after_hours \| closed`，或至少 `timezone: Asia/Shanghai\|Asia/Hong_Kong\|America/New_York` |
| F003 | major | 一致性 | 输入契约 | 缺 `correlation_id` / `parent_run_id`。编排者明确说多市场要拆成多次独立 run，调度层需要把这些 run 串成同一次 SOP 触发 | node-0-trigger-entry-review-context.md「Initial recommended stance」第 1 条 | 增加 `correlation_id: uuid` 作为外层 SOP 单次触发的关联键，每次 fan-out 共享 |
| F004 | major | 完整性 | 多市场语义 | `market` 字段是否允许多值在契约里没写。文档用「多市场可允许」又说「内层拆分」，但契约层没规定「单 market」是硬约束 | node-0-trigger-entry-review-context.md「multi-market」问 | 把 `market` 强制单值，文档明确「多市场由调度层 fan-out，不在本节点契约范围内」 |
| F005 | major | 完整性 | 多策略语义 | `strategy_id: mixed` 是「在 SOP 层拆多个策略调用」，但契约字段直接允许它，会让策略选择器变成隐式黑盒。编排者说「不应是隐藏黑盒」，但契约没做强制 | node-0-trigger-entry-review-context.md「Initial recommended stance」第 2 条 | v1 直接从枚举中删除 `mixed`；若需 SOP 编排，由调用方做多次调用并共享 `correlation_id` |
| F006 | major | 完整性 | dry_run 语义 | `dry_run=false` 的语义在 Node 0 这一层没定义。Node 0 是研究/选股入口，不存在真实下单；这会让 `false` 看起来「能下单」而实际啥也不会发生 | node-0-trigger-entry-review-context.md「Initial recommended stance」第 3、4 条 | 明确 v1 阶段 `dry_run` 仅控制「是否写 trade_log / risk_event 的执行态字段」，与下单无关；真实下单网关是后续独立节点 |
| F007 | minor | 完整性 | 输入契约 | 缺 `universe` 提示。同一策略对「全市场 / 行业 / 自选股 / 已有 candidates 复选」成本差异巨大 | node-0-trigger-entry-review-context.md「Suggested input fields」段 | 增加 `universe: market \| sector:{name} \| watchlist:{name} \| candidates:{market}` |
| F008 | minor | 完整性 | 输入契约 | 缺 `priority` / `deadline`。当 cron 在市场开盘前触发失败需要重试，或用户手动请求高于 cron 时，需要调度层做取舍 | node-0-trigger-entry-review-context.md「Suggested input fields」段 | 增加 `priority: low \| normal \| high`（v1 可选，但留位） |
| F009 | minor | 完整性 | dry_run 语义 | 编排者说「涉及真实交易动作必须显式配置」，但 `trigger_source: manual\|cron\|sop` 与「是否走真链路」的对应关系没说 | node-0-trigger-entry-review-context.md「Initial recommended stance」第 3 条 | 文档明确：v1 阶段 trigger_source 只用于审计和 SLA，不影响 dry_run；未来 execution gateway 才用它做二次确认 |
| F010 | minor | 完整性 | dry_run 语义 | 缺 `audit` 字段。trigger 入口的审计元数据是契约的一部分，至少要有 `request_id`、`caller`、`requested_at` | node-0-trigger-entry-review-context.md「Initial recommended stance」段 | 增加 `request_id: uuid`、`requested_at: ISO8601`、`caller: string`；`trigger_source` 退化为 `caller` 的语义分类 |
| F011 | minor | 风险识别 | dry_run 策略 | 编排者把「未来 risk-execution gateway」混进 Node 0 的讨论。Node 0 是研究/选股入口，execution 是独立节点；混着讨论会让 S2 基线飘移到还没决定的领域 | node-0-trigger-entry-review-context.md「Initial recommended stance」第 4 条 | 文档明确 Node 0 不讨论 execution；execution 留到 S3 / S4 单独评审 |
| F012 | minor | 一致性 | 验收标准 | 缺「拒绝多市场 / mixed 策略 / 缺字段」三类负向验收 | 隐含在 review context 问 3、4 | 验收清单必须包含：① 单 market 强制；② `mixed` 拒绝；③ 缺必填字段返回结构化错误；④ `correlation_id` 必填 |
| F013 | minor | 完整性 | 验收标准 | 缺「幂等 / 重放」语义。同 `(market, strategy_id, strategy_version, run_date)` 二次触发是「重新跑」「续跑」还是「拒绝」没说 | 隐含 | 增加 `idempotency_key` 或明确规定重放策略；至少 v1 写明「同 key 二次触发 = 拒绝 + 返回上次 run_id」 |
| F014 | info | 边界 | 边界 | 「建议 cadence」与「调度计划」之间需要明确边界：skill 可以给「推荐频率」建议，但不应在文档里写「每周一 8:30 跑」 | 旧 SKILL.md 16-22、43-50 段 | 节点 0 文档用「建议频率」一节替代具体时间表，例：`"discovery": "trading_day, market_open-30m"` |
| F015 | info | 一致性 | 命名 | `run_mode` 含 `full`，但下游节点 0 不应触发「full」一次性把 discovery→tracking→monitor 全跑完——`full` 是 SOP 编排层的概念，不是 Node 0 入口的概念 | node-0-trigger-entry-review-context.md「run_mode」字段 | `run_mode` 限定为 discovery \| validation \| tracking 三选一；`full` 改为 SOP 编排层概念，节点 0 拒绝 |
| F016 | info | 完整性 | 验收标准 | 缺「结构化日志」验收：每次 trigger 入口必须记录 request_id、caller、market、strategy、run_mode、dry_run、入参 hash、回参摘要 | review context「audit metadata」段 | 验收清单补一条：「Node 0 必须输出可被审计的结构化触发日志，字段如上」 |
| F017 | info | 一致性 | 命名 | `run_date` 含义不清：是「调度执行日期」还是「数据 as-of 日期」？对「用 2026-06-20 数据重新跑 2026-06-23 的策略」这种场景，调用方需要区分 | node-0-trigger-entry-review-context.md「run_date」字段 | 拆为 `signal_date`（数据 as-of）+ `run_date`（触发日期），或文档明确 v1 假定二者相同 |
| F018 | info | 一致性 | REQ-01 对齐 | REQ-01.md 第 9、12 段提到「必须人工确认」「自动卖出能力必须有 dry-run 和双重确认」，Node 0 的 dry_run 策略需要和这些红线对齐声明 | REQ-01.md 9-12 段、node-0-trigger-entry-review-context.md | 节点 0 文档加一句「本节点 dry_run 与人工确认红线解耦；Node 0 不发起交易」 |

---

## 与编排者立场的差异

| 主题 | 编排者立场 | 本审查意见 | 理由 |
|------|-----------|------------|------|
| 多市场 | 外层允许，内层拆 | 同意，但建议在契约层禁掉 `market` 多值 | 契约层硬约束比依赖调度层好习惯更可靠 |
| `mixed` 策略 | SOP 层编排，不是黑盒 | 同意，但建议 v1 直接从枚举中删 | 字段允许 = 调用方会传，契约字段存在即会污染 |
| dry_run 默认 | selection/validation/tracking 默认 true | 同意；建议明确「`dry_run=false` 在 Node 0 无业务效果」 | 防止 `false` 被误解为「可以下单」 |
| 未来 risk-execution gateway | 提及作为后续独立模块 | 同意；建议 Node 0 文档完全不讨论 execution | 避免 S2 基线被未来未决定的设计带跑 |

---

## 推荐基线（修订后）

### 节点 0 边界

- **属于本节点**：触发参数解析、必填校验、市场/策略/模式路由到下游节点、结构化触发日志、Idempotency 处理、休市日初判（如果本节点就拒绝，则不进下游）。
- **不属于本节点**：cron / 调度计划本身（Gateway 运维配置）、具体策略实现、复选逻辑、持仓监控、下单、止损执行、真实券商对接。

### 推荐输入契约（v1）

```
{
  "request_id":       "<uuid>",            // 必填，审计键
  "correlation_id":   "<uuid>",            // 必填，fan-out 共享
  "caller":           "manual|cron|sop",   // 必填，trigger_source 字段并入
  "requested_at":     "<ISO8601>",         // 必填
  "market":           "US|HK|CN",          // 必填，单值
  "strategy_id":      "taroc|chokepoint|<custom>",  // 必填，v1 不含 mixed
  "strategy_version": "<semver>",          // 必填，与策略模块 VERSION 一致
  "run_mode":         "discovery|validation|tracking",  // 必填，v1 不含 full/monitor
  "universe":         "market|sector:{name}|watchlist:{name}|candidates:{market}",  // 可选
  "signal_date":      "YYYY-MM-DD",        // 可选，默认 = run_date
  "run_date":         "YYYY-MM-DD",        // 必填
  "timezone":         "Asia/Shanghai|Asia/Hong_Kong|America/New_York",  // 可选，从 market 推导
  "dry_run":          true,                // 必填，默认 true；v1 false 在本节点不触发交易
  "priority":         "low|normal|high",   // 可选，默认 normal
  "idempotency_key":  "<string>"           // 可选；缺失时由 request_id+run_date+strategy 派生
}
```

### 推荐默认与拒绝规则

- `dry_run: true` 是唯一允许的默认值；调用方传 `false` 必须显式。
- `market` 多值 → 400；`strategy_id: mixed` → 400；`run_mode: full|monitor` → 400。
- 缺 `request_id` / `correlation_id` / `strategy_version` → 400。
- 同一 `idempotency_key` 二次触发 → 返回首次 `run_id` + 状态，不重新执行（v1）。

### 验收标准（必过项）

1. Node 0 文档中不出现任何具体 cron 时间表，只出现「推荐频率（建议，非执行）」。
2. 调度配置（实际 cron）以 Gateway 运维文档形式独立存在，不在 skill 内。
3. `market` 强制单值，文档明确「多市场由外层 fan-out」。
4. `strategy_id` v1 不含 `mixed`；`run_mode` v1 不含 `full` / `monitor`。
5. `dry_run: true` 是默认；`dry_run: false` 在 Node 0 不触发任何交易动作，文档明确。
6. 缺必填字段返回结构化错误（`error_code` + `field` + `message`），不静默回退。
7. 幂等：同 `idempotency_key` 二次触发返回上次 `run_id`，不重复执行。
8. 每次触发输出结构化审计日志：`request_id`、`correlation_id`、`caller`、`market`、`strategy_id + version`、`run_mode`、`dry_run`、`入参 hash`、`回参摘要`。
9. 节点 0 文档明确「不讨论 execution / 下单 / 自动卖出」；execution 由后续独立节点评审。
10. 与 REQ-01.md 第 9、12 段「买入人工确认 / 卖出 dry-run + 双重确认 / 止损不可跳」红线声明对齐。

---

## 实施顺序建议

1. 修订 `REQ-01.md` 节点 0 段落，把上述 18 条 finding 吸收进基线（优先 F001–F006 + F011）。
2. 在 `src/SKILL.md` 重写版（v1.0.0）首节定义 `TriggerRequest` schema（JSON 形式或 TS-style interface），与上面契约一一对应。
3. 在 `flows/` 下加 `trigger.md`，写明拒绝规则与错误码。
4. 旧 `stock-picking-v2/SKILL.md` 中 cron 表与持仓监控频率段整体迁出至 Gateway 运维文档（不归 skill 内部）。
5. 把 §验收标准 1–10 写成「Node 0 准入 checklist」，后续 factory review 节点 N 时复用同一份对照表。

---

## 最重要的一条建议

**把「`mixed` 策略」「多市场」「`full` 模式」从 v1 契约中直接删除**——契约字段存在就会被使用，靠文档「应该不会传」是防不住的；让 fan-out 和多策略编排回到 SOP 调度层，而不是藏在 skill 内部黑盒。
