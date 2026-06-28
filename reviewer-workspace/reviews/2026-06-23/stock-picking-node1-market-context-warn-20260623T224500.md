# Review Report — Node 1 交易日与运行上下文检查

**总体评级**：WARN
**置信度**：0.78
**审查对象**：B 类方案稿 — Node 1 边界/契约提案（stock-picking S2 节点评审）
**审查时间**：2026-06-23
**使用模型**：newapi-openai/MiniMax-M3
**被审文件**：`projects/stock-picking/node-1-market-context-review-context.md`
**配套参考**：`projects/stock-picking/REQ-01.md`、`PLAN.md`、`DISCUSSION-LOG.md`、`node-0-trigger-entry-review-context.md`

---

## 一句话结论

主方案方向正确（Node 1 负责"市场日期 + 会话上下文"两道闸门，交易日历下沉为共享基础设施），契约骨架基本可落地；但**存在 3 个 blocker 级别契约缺口和 2 个 major 风险点**，必须先补齐才能进 S3 方案设计。

---

## 维度评分

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 边界清晰性 | 4 | "Node 1 拥有 pre-run 规范化、上下文闸门；不拥有日历数据维护"这条线划得不错，但与 Node 0 入口校验的职责边界有重叠风险。 |
| 契约完整性 | 2 | 5 个关键字段/场景缺失：`universe` 在 Node 1 几乎无意义却被列为输入；缺 `input_calendar`（信号日使用的旧日历快照）；缺 override 过期与撤销语义；缺会话切换的时区解释规则。 |
| 风险与失败处理 | 3 | closed/half_day/unknown 三态分支已列，但 cron 兜底、override 滥用、跨日多时区并发等场景无具体处理。 |
| 一致性 | 4 | 与 REQ-01.md 中"holidays 抽成 market-calendar 共享基础设施"一致；与 Node 0"v1 拒绝 monitor/full/dry_run=false"对齐。 |
| 可落地性 | 3 | 依赖一个尚未存在的 `market-calendar` 共享基础设施，v1 落地路径不清。 |

---

## 问题清单

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| B001 | blocker | 契约冗余/职责泄漏 | "Recommended input" 段 | `universe`（market/sector/watchlist/candidates）被列为 Node 1 输入，但 Node 1 不消费 universe 做任何判定；这是把 Node 0/SOP 编排层的职责错放到 Node 1。 | 输入表第 9 行 `universe`；Node 0 入口契约里已经包含 universe。 | 把 `universe` 从 Node 1 输入中移除，由下游策略模块按需读取；Node 1 透传 `request_id/correlation_id/market/run_date/signal_date/timezone/caller/run_mode` 即可。 |
| B002 | blocker | 关键字段缺失 | "Recommended output" 段 | 缺 `session_open_at`（会话开盘时间）。当前只有 `session_close_at`，但 half_day 场景下"还有多久开盘"和"现在处于哪个时段"无法表达。 | 输出 schema 11 个字段，对照 REQ-01 第 1 节要求"market_session 包含 premarket/regular/postmarket"。 | 新增 `session_open_at: ISO8601 \| null`，与 `next_open_at` 区分（前者是当前 session 起点，后者是下一个 session 起点）。 |
| B003 | blocker | 缺语义/口径定义 | "Recommended output" 段 `market_session` | `market_session` 与 `calendar_status` 的语义边界没定义：`half_day` 时 market_session 是什么？`closed` 时能不能也是 `regular`？ | 文档未说明。 | 文档补充约束：`market_session` 仅在 `calendar_status=open \| half_day` 时取具体值；`closed` 时强制 `closed`；`unknown` 时强制 `unknown`。 |
| M001 | major | 共享依赖未定义 | "Recommended boundary" 段 | 主方案要求 `market-calendar` 作为共享基础设施，但该模块 v1 是否存在、归属 Layer 3 还是 Layer 2、谁负责维护、版本号策略，文档全部未提。 | 整段只提一句 "preferably `market-calendar`"。 | 在 v1 边界里明确：v1 阶段允许 Node 1 自带薄包装的 calendar 适配器（failover 到内部表），同时把 `market-calendar` 作为 Layer 3 共享模块在 S3 设计文档里立项。给出"v1 双轨：内置 + 外部依赖"的过渡方案。 |
| M002 | major | override 滥用风险 | "Recommended behavior" 段 `unknown` 分支 | 手动 caller 在 calendar unknown 时可以"显式 override 后继续"；但未定义 override 的有效期、审计要求、可撤销性、是否进入 v1。 | "if `calendar_status=unknown` ... manual caller: allow only with explicit override"，但没有 override_id 校验细节。 | 明确：(a) override 必须含 `override_id`+`override_reason`+`override_expires_at`；(b) override 事件必须进入 `trade_log` 或独立 `override_audit`；(c) v1 是否启用手动 override 必须在 3 个问题里给出明确选择。 |
| M003 | major | 半日市/调休日行为不一致 | "Recommended behavior" 段 `half_day` 分支 | "allow discovery/validation/tracking but tag `context_warnings`" 这条与"closed 返回 HEARTBEAT_OK"逻辑层级不同：half_day 没有明确的 skip 路径，只打 warning 继续走。 | 同上。 | 补一条契约：`half_day` 模式下，run_mode 必须是 `discovery/validation/tracking` 三选一；`run_mode=monitor` 在 half_day 仍按"暂停"处理（与 Node 0 一致：v1 monitor 模式本身就被拒）。 |
| M004 | major | 跨时区并发未覆盖 | "Recommended behavior" `signal_date` 段 | `signal_date` 可能与 `run_date` 不同（跨时区美股跑批），但 Node 1 没有规则说明：当 signal_date 所在市场已休市、但 run_date 市场未休市时，是否允许运行？ | 单句 "may differ from `run_date` for cross-timezone US runs"，无规则。 | 增加规则：signal_date 的市场日历若不可用（unknown/closed），Node 1 必须把 signal_data 标为 `stale` 并写入 `context_warnings`；不允许"假装新鲜"。 |
| m001 | minor | 命名冲突 | output `skip_reason` | `skip_reason` 与 Node 0 评审中提到的"已通过/未通过"语义不同；在 Node 1 它表示"为什么不开市"，在下游可能误读为"为什么跳过这个 run"。 | 字段名 `skip_reason` 单一含义。 | 重命名为 `calendar_skip_reason` 或在契约里写明 "该字段描述 calendar 跳过原因，与 run 级别 skip_reason 不同"。 |
| m002 | minor | 缺版本字段 | input 段 | 输入没有 `calendar_source_version` 而输出有；无法做幂等/回放校验。 | 对照输出第 11 字段。 | 在输入补 `expected_calendar_source_version`（可选），用于 Node 1 校验 caller 期望的日历版本。 |
| m003 | minor | "SOP caller" 概念未定义 | behavior 段 | "SOP caller" 在 Node 0 入口契约里没有；Node 0 v1 只接受 `manual \| cron \| sop`，`sop` 已经在 Node 0 出现。 | 上下文对照 Node 0 review。 | 把"sop" 与"manual/cron" 同列；不要单独叫 SOP caller，避免分类冲突。 |
| m004 | minor | 缺时区校验细则 | behavior 段 `timezone` 句 | "If `timezone` does not match `market`, fail before downstream work" 没有给出"匹配"的判定规则。 | 单句规则。 | 给出对照表：US→`America/New_York`、HK→`Asia/Hong_Kong`、CN→`Asia/Shanghai`；任何其他时区或缺失时区必须 fail。 |
| I001 | info | 问题 1/2/3 未给出推荐答案 | Questions 段 | 三个问题（manual override v1、validation/tracking 是否在 closed 跑、market_session 粒度）都只是问句，提案没有给出推荐选项。 | 文档末尾三个 Questions 段。 | 主方案应对每个问题给出推荐答案+理由，让评审会聚焦"是否同意推荐"而非"选项有哪些"。 |

---

## 推荐边界（我方建议）

**主方案边界基本可接受，补充如下**：

1. Node 1 拥有：日期/会话判定、时区校验、override 校验、上下文规范化（market + date + session 三元组）。
2. Node 1 **不拥有**：交易日历数据维护、cron 调度、策略决策、universe 解释。
3. **关键调整**：
   - 把 `universe` 从 Node 1 输入里移除（职责错位）。
   - 把 `market-calendar` 共享基础设施的 v1 落地路径写明（先内置再外迁）。
   - override 必须有审计和有效期。
   - half_day 与 closed 行为路径必须对称（都是"跳过"或"tag 继续"二选一，不能各走一派）。

---

## 推荐输入/输出契约变更

### 输入（建议删 1、加 0）

```yaml
request_id: uuid
correlation_id: uuid
caller: manual | cron | sop
market: US | HK | CN
run_date: YYYY-MM-DD          # 市场本地交易日
signal_date: YYYY-MM-DD       # 信号源日期，可与 run_date 不同
timezone: America/New_York | Asia/Hong_Kong | Asia/Shanghai
run_mode: discovery | validation | tracking
```

**删除**：`universe`（不在 Node 1 决策链上）。

### 输出（建议加 1、补充语义 2）

```yaml
request_id: uuid
correlation_id: uuid
market: US | HK | CN
run_date: YYYY-MM-DD
timezone: IANA

calendar_status: open | closed | half_day | unknown | overridden
market_session: premarket | regular | postmarket | closed | unknown
is_runnable: true | false
skip_reason: holiday | weekend | emergency_closure | outside_session | calendar_unavailable | invalid_context | none
session_open_at: ISO8601 | null        # 新增：当前 session 起点
session_close_at: ISO8601 | null
next_open_at: ISO8601 | null
calendar_source: string
calendar_source_version: string
override_id: string | null
override_expires_at: ISO8601 | null    # 新增：override 有效期
context_warnings: string[]             # 含 stale_signal_data, half_day_limited 等
```

**语义约束**（必须文档化）：
- `market_session` 与 `calendar_status` 联合约束，详见 B003。
- `is_runnable=false` 等价于 `calendar_status ∈ {closed, unknown, overridden-failed}`。
- `is_runnable=true` 时 `market_session ∈ {premarket, regular, postmarket}`。
- `skip_reason=none` 仅在 `is_runnable=true` 时合法。

---

## 失败/跳过行为（推荐版）

| calendar_status | caller=manual | caller=cron | caller=sop |
|----------------|---------------|-------------|------------|
| `open` | run | run | run |
| `closed` | HEARTBEAT_OK + `skip_reason` | HEARTBEAT_OK + `skip_reason` | HEARTBEAT_OK + `skip_reason` |
| `half_day` | run + `context_warnings: ["half_day_session"]` | run + warnings | run + warnings |
| `unknown` | NEEDS_OVERRIDE | FAIL_CLOSED（HEARTBEAT_FAIL） | NEEDS_OVERRIDE |
| `overridden` (有效) | run | run + audit | run + audit |
| `overridden` (过期/无效) | 重回 `unknown` 分支 | 同上 | 同上 |

**关键改动**：
1. `unknown` 状态 cron 必须 **fail closed**（防止 cron 在日历源挂掉时无脑跑错日期）。
2. `overridden` 必须区分"有效"和"失效"两态，失效后回到 `unknown` 重新走分支。
3. 任何 `overridden` 状态必须写入 `override_audit` 事件，含 `override_id`、`override_by`、`override_reason`、`override_expires_at`、`actual_calendar_status`。

---

## 风险与缺失场景

| 风险 | 描述 | 缓解 |
|------|------|------|
| 日历源单点失败 | `market-calendar` 共享基础设施未立，v1 没有 failover 路径 | v1 内置薄包装 + 内置表；S3 阶段把 `market-calendar` 立项为 Layer 3 模块 |
| 跨时区信号过期 | signal_date 与 run_date 不同时，stale signal 被当成新鲜数据 | `context_warnings: ["stale_signal_data"]` + 禁止用 stale signal 进入 strategy 阶段（策略模块读 warnings 决定是否降级） |
| Override 滥用 | 手动 override 绕过日历校验，可能在台风/黑雨日错开交易 | override 必须有 expires_at（最长 24h）+ 强制 audit log + 后续可回溯 |
| 调休日/半日市漂移 | 每个 Node 各自判定交易日，行为不一致 | Node 1 单点判定 + 显式 `is_runnable`，下游不重判 |
| Node 0/Node 1 职责重叠 | Node 0 也做参数校验，时区校验该归谁 | Node 0 只校验"形参合法性"（字段类型/枚举），Node 1 校验"业务一致性"（timezone↔market、run_date↔signal_date） |
| 港股台风/黑雨半日 | 临时休市无法被静态日历覆盖 | override 入口 + 临时 `holiday_overrides.yaml`（Layer 3 共享） |
| 美股 DST 切换 | 夏令时切换当天 session 时间偏移 | `market-calendar` 内部处理，Node 1 只消费结果 |

---

## 验收标准（建议加入 S2 baseline）

1. Node 1 文档明确声明"不拥有日历数据维护"和"不解释 universe"。
2. 输入契约不含 `universe`，输出契约包含 `session_open_at` 和 `override_expires_at`。
3. `market_session` 与 `calendar_status` 联合约束写明。
4. `unknown` 状态下，cron caller 必须 fail closed，不允许静默 continue。
5. Override 必须有 `override_id` + `override_reason` + `override_expires_at`，且进入 `override_audit` 事件流。
6. 时区与市场匹配规则有明确对照表（US→NY、HK→HK、CN→SH）。
7. `market-calendar` 在 S3 阶段立项为 Layer 3 共享模块，v1 给出内置 fallback 路径。
8. 三个未决问题（manual override v1、validation/tracking on closed、market_session 粒度）必须给出推荐答案。
9. Node 1 单元测试覆盖：常规交易日、周末、法定假日、调休日、半日市、unknown 降级、override 有效/失效、时区不匹配、跨时区 signal_date。
10. 文档明确写出 Node 1 不重判交易日（防止下游模块各自再判）。

---

## 与主方案的分歧

| 编号 | 主方案 | 我方建议 | 理由 |
|------|--------|----------|------|
| D1 | `universe` 列为 Node 1 输入 | **删除** | Node 1 不消费 universe，列出只会让下游误以为 Node 1 会基于 universe 预筛。 |
| D2 | `market-calendar` 是"preferred"依赖 | **强制 v1 落地路径**："v1 内置薄包装 + 外部 market-calendar 立项" | 否则 v1 没有可运行的日历源。 |
| D3 | `unknown` 状态 manual 可 override 后继续 | **必须配 override 审计和过期时间** | 不加审计和过期，override 会被无脑使用。 |
| D4 | `half_day` 走 "tag warning 继续" 路径 | **明确 run_mode 限制**：`monitor` 在 half_day 仍按 closed 处理 | 与 Node 0 的"v1 拒 monitor"对齐。 |
| D5 | 三个 Questions 留空 | **提案必须给出推荐答案** | 否则评审会变成"选项列举会"，不是决策会。 |
| D6 | `next_open_at` 与 `session_close_at` 都给，但不给 `session_open_at` | **补 `session_open_at`** | `next_open_at` 表达"下一个 session"，但 `half_day` 场景下"当前 session 是什么时候"无法表达。 |
| D7 | `caller` 在 behavior 段被细分为 manual/cron/SOP caller | **统一用 Node 0 的 `caller: manual\|cron\|sop` 三元组** | 避免新分类法与 Node 0 冲突。 |

---

## 最重要的一条建议

**把 v1 落地路径写明白再进 S3**：Node 1 强依赖一个尚未存在的 `market-calendar` 共享基础设施。v1 必须明确"内置薄包装 + 内置交易日表"的过渡方案，否则 Node 1 在 S3 设计阶段会因为"依赖未立项"而卡住。

---

## 评级理由

- **不给 PASS**：3 个 blocker（契约冗余 `universe`、缺 `session_open_at`、缺 `market_session` 语义约束）必须先补。
- **不给 FAIL**：主方案方向、boundary 划分、与 Node 0 的对齐都合理，修订成本低。
- **给 WARN**：补完 blocker 即可进 S3 方案设计，不需要重新评审边界。
