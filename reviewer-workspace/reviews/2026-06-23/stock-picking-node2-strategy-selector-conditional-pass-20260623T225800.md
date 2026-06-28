# Review Report — Node 2 策略选择器

**总体评级**：CONDITIONAL PASS
**置信度**：0.81
**审查对象**：B 类方案稿 — Node 2 边界/契约提案（stock-picking S2 节点评审）
**审查时间**：2026-06-23 22:58 CST
**使用模型**：newapi-openai/MiniMax-M3
**被审文件**：`projects/stock-picking/node-2-strategy-selector-review-context.md`
**配套参考**：
- `projects/stock-picking/REQ-01.md`（节点 2 段落、全流程图、Layer 分层）
- `projects/stock-picking/PLAN.md`
- `projects/stock-picking/DISCUSSION-LOG.md`（22:55 节点 1 确认结论）
- `projects/stock-picking/node-0-trigger-entry-review-context.md`（已审，CONDITIONAL PASS）
- `projects/stock-picking/node-1-market-context-review-context.md`（已审，WARN）
- `projects/stock-picking/intelligence-brief.md`（TAROC 与 Chokepoint 原始形态）
- `packs/general.md`（通用方案评审维度）

---

## 一句话结论

**主方案方向正确**：Node 2 是"策略注册表 + 路由器"，不做策略实现、不做融合/排序/兜底，这一条边界划得很清楚。契约骨架基本可落地，但**有 1 个 blocker 契约缺口、4 个 major 风险点、2 个与 Node 0/Node 1 契约不一致项**，必须先补齐再进 S3 方案设计。

---

## 维度评分

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 边界清晰性 | 5 | "Node 2 是注册表 + 路由器，不是策略引擎"是这次评审里边界最清楚的一节。 |
| 契约完整性 | 3 | 17 字段够用，但缺 `request_id / correlation_id / run_id` 透传、缺 `expected_strategy_version` 校验语义、缺 `custom_strategy_ref` 解析规则。 |
| 与 Node 0 / Node 1 一致性 | 3 | 与 Node 0 的 `custom` 策略引用语义未对齐；与 Node 1 的 `decision=proceed` 前置条件没写进契约。 |
| 注册表设计 | 4 | 字段够用；与 Layer 3 共享基础设施归属没说；`entrypoint` 的具体形态（path / skill_ref / 命令行）未定义。 |
| 失败/拒绝语义 | 4 | 7 个 reject_reason 枚举可用；但 deprecated 策略对 cron/sop caller 的行为没说；silent fallback 已经被禁止，方向对。 |
| 可落地性 | 3 | 依赖 Layer 3 的 `strategies/registry.yaml` 是否存在、归谁维护、版本策略未说。 |
| 风险识别 | 4 | 编排者主动列出"不要静默回退到 TAROC"是最大亮点；缺策略爆炸、版本漂移、custom 注入风险。 |
| 验收标准可测试性 | 3 | 给了 7 条验收，但缺负向用例（重复 strategy_id、版本不匹配、registry 缺字段）。 |

---

## 问题清单

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| B001 | blocker | 契约字段缺失 | Recommended output | 输出缺 `request_id` 和 `correlation_id`，无法与 Node 0/Node 1 透传的审计链对齐。SOP 编排层做 fan-out 时无法把"选了哪个策略版本"和"上层 trigger"对应起来。 | 对照 Node 0/Node 1 评审稿，二者均强制 `request_id` + `correlation_id`。 | 输出契约必须包含 `request_id: uuid` 和 `correlation_id: uuid`（透传上游值，不重生成）。 |
| B002 | blocker | 契约校验语义缺失 | Recommended input + `strategy_version` | "if omitted in a manual call, Node 2 may resolve to registry default"这条没有给出**解析时机**（调用前解析？解析失败怎么办？）和**resolver 的幂等性**保证。`run_context.decision=proceed` 是从 Node 1 来的，但契约没明确 Node 2 收到 `decision≠proceed` 时的处理。 | Recommended behavior 第 4 条只说"may resolve"；契约里没出现 `run_context.decision`。 | 契约补两条：(a) Node 2 输入必须包含 Node 1 的 `run_context.decision`，Node 2 在 `decision≠proceed` 时直接 `dispatch_decision=reject, reject_reason=upstream_not_ready`；(b) `strategy_version` 解析必须发生在 Node 2 内部原子事务里——一旦解析成功即冻结，registry 后续变更不影响本次 dispatch。 |
| M001 | major | 一致性 / 契约空缺 | `custom` 策略 | "custom" 在 Node 0 评审里定义为"可解析的策略引用"，但 Node 2 的契约里没有 `custom_strategy_ref` 字段，只有 `strategy_id: ... | custom`。`custom` 的具体形态（路径？skill_ref？git url？）没有解析规则，也没有"白名单/审批过的引用"判定标准。 | Node 0 review F001/F005、Node 2 input 段。 | (a) 把 `custom_strategy_ref: string` 显式列为 Node 2 输入必填（当 `strategy_id=custom` 时）；(b) 给出 ref 解析规则：`{layer2_module_path}@{version}` 或 `{git_url}@{sha256_prefix}` 二选一；(c) 解析失败 → `reject_reason=custom_ref_invalid`；(d) ref 必须出现在 registry 或本地白名单中，禁止任意路径。 |
| M002 | major | 共享依赖未定义 | Recommended registry fields + Key question 4 | "registry.yaml 放在哪"被列为开放问题。v1 阶段该文件不存在会直接卡住 Node 2 落地。 | Key question 4：「Should a strategy registry live in `src/strategies/registry.yaml`, or in the SOP text first?」 | 给出 v1 双轨方案：v1 把 registry 嵌入 `src/strategies/registry.yaml`（与 `holidays/` 同级），S3 阶段考虑抽成 `strategy-registry` Layer 3 模块（与 `market-calendar` 对称）。 |
| M003 | major | 失败语义空缺 | Recommended behavior | "deprecated strategies may run for manual caller with warning" 但没说：(a) 何时升级为 `disabled`；(b) cron/sop caller 遇到 deprecated 是 reject 还是 warning-only；(c) 警告是否会触发自动升级。 | Recommended behavior 第 5 条。 | 明确：(a) 状态机 `active → experimental → deprecated → disabled` 单向，`disabled` 不可恢复；(b) deprecated 策略只对 `caller=manual` 允许 dispatch，对 `caller=cron` 和 `caller=sop` 一律 `reject + reject_reason=strategy_disabled`（或新增 `strategy_deprecated`）；(c) `last_reviewed_at` 超期（如 180 天）必须把 `active` 降为 `experimental` 并发出 selector_warning。 |
| M004 | major | 与 Node 0 契约不一致 | Recommended input + `run_mode` | Node 0 v1 已限定 `run_mode ∈ {discovery, validation, tracking}` 并拒绝 `full / monitor`。Node 2 的 input 段也复述了这个枚举，但 `supported_run_modes` 字段是 per-strategy 列表——如果 TAROC 只支持 `discovery / validation`，Chokepoint 只支持 `discovery`，注册表怎么写？v1 时 Chokepoint 还不存在，v1 阶段注册表是否预置？ | Node 0 评审稿 + Node 2 registry fields。 | 文档明确：(a) v1 registry 只预置 `taroc`；(b) `chokepoint` 在 v1 写明 `status=experimental` 且不进入 dispatch 流程（即使注册也不可调用）；(c) `custom` 在 v1 不接受自由注册，必须人工审批后写进 `local-overrides.yaml`。 |
| M005 | major | 跨版本一致性 / 漂移风险 | Recommended behavior + `output_schema_version` | registry 里 `output_schema_version: semver` 与 `strategy_version: semver` 是两个不同维度的版本号。契约没说明：当 schema 升级而 strategy 不升级时（反之亦然），Node 2 是否做兼容性校验？下游消费者怎么识别？ | Registry fields 第 7、9 项。 | 明确：(a) Node 2 dispatch 时把 `strategy_version` 与 `output_schema_version` 同时输出到 selector 响应；(b) 兼容性策略：`output_schema_version` 的 major 与 strategy 输出的 draft schema 必须一致，不一致时 `reject_reason=schema_mismatch`；(c) 下游复选/追踪模块通过 `expected_output_schema: draft_candidates.v1` 字段做版本断言。 |
| m001 | minor | 命名一致性 | output `expected_output_schema` | 与 `output_schema_version` 在 registry 里同名不同义；建议把"schema 名称"和"schema 版本"分开。 | Registry fields + output schema。 | registry 加 `output_schema_name: draft_candidates`，version 字段独立。 |
| m002 | minor | 命名一致性 | `dispatch_decision` 枚举 | `dispatch \| reject \| needs_review` 中 `needs_review` 与 Node 1 的 `needs_override` 是平行概念，建议对齐命名。 | Recommended output。 | 改为 `dispatch \| reject \| needs_review`，并定义：needs_review 在 Node 2 仅用于 `caller=manual` 遇到 `experimental` 策略时，要求人工 ack。 |
| m003 | minor | 字段约束 | `universe` 在 Node 2 的语义 | Node 2 的 input 列了 `universe`，但 Node 1 评审已经把 universe 移出契约（因为 Node 1 不消费）。Node 2 消费 universe 吗？如果消费，应该透传到下游 strategy；如果不消费，应该移除。 | Node 2 input 段 + Node 1 review B001。 | 明确 Node 2 必须透传 `universe` 到 strategy 入口，不在本节点做任何筛选或校验。 |
| m004 | minor | 行为未定义 | `selector_warnings` 用途 | "selector_warnings: string[]" 是自由文本，但没说什么算 warning、什么算 error；下游可能误把 warning 当 error。 | Recommended output。 | 定义 `selector_warnings` 至少含三类枚举：`version_implicit_default`、`deprecated_strategy_in_use`、`schema_version_drift`，其他用自由文本。 |
| m005 | minor | 调度边界 | entrypoint 形态 | `entrypoint: path_or_skill_ref` 没区分：(a) Node 2 怎么找到它；(b) Node 2 是否负责加载它的依赖；(c) entrypoint 失败时 Node 2 报哪个 reject_reason。 | Registry fields。 | 增加 entrypoint 子结构：`{kind: skill_ref | path | url, value: string, checksum?: string}`，并定义 dispatch 失败时统一报 `strategy_unavailable`（建议加到 reject_reason 枚举）。 |
| m006 | minor | 一致性 | `run_mode: discovery | validation | tracking` 的归属 | Key question 2 问 "validation 和 tracking 是 strategy 内部 run mode 还是后续通用模块"——这是 Node 6/Node 8 的问题，不该挂在 Node 2 上。 | Key question 2。 | Node 2 不回答 Q2，只透传 `run_mode` 到 strategy。文档加一句："run_mode 在 strategy 模块内如何解释由各 strategy 决定，不在 Node 2 决策范围。" |
| m007 | minor | 行为 / 安全 | `custom` 策略注入风险 | "ref 必须出现在 registry 或本地 config"——如果本地 config 是用户可写文件，等于绕过白名单。 | Recommended behavior 第 3 条。 | 明确：(a) `custom_strategy_ref` 必须出现在**受版本控制的** registry 或白名单文件中，不接受用户运行时临时写入；(b) 任何 ref 加载执行前必须做 `checksum` 校验；(c) ref 路径必须在仓库工作目录内，禁止 `..` 和绝对路径。 |
| I001 | info | 关键问题未给推荐 | Key questions 1–4 | 主方案 4 个 key questions 都是问句，没给推荐答案。Node 1 评审 D5 已经批评过这种做法。 | 全文末 Questions 段。 | 主方案必须给推荐答案：(Q1) 严格 semver；(Q2) run_mode 透传；(Q3) Chokepoint v1 写为 `experimental` 且不进入 dispatch；(Q4) registry 在 v1 落地为 `src/strategies/registry.yaml`。 |
| I002 | info | 缺少 fan-out 编排语义 | Recommended boundary | "Multi-strategy orchestration remains outside Node 2" 正确，但没说 SOP 编排层怎么 fan-out、怎么聚合 draft。 | Recommended boundary 第 4 条。 | 在 S3 阶段 SOP 编排层设计中补充：fan-out 由 SOP 编排层产生 N 个 Node 2 调用，共享 `correlation_id`，每个返回独立 draft，下游复选模块做聚合。 |
| I003 | info | 审计/可观测性 | Recommended output | 输出没有 `selector_audit` 事件结构。registry 暴露 metadata 给 observability，但 dispatch 事件本身没说要进 `strategy_audit` 日志。 | Recommended behavior 第 8 条。 | 建议在 dispatch 成功时输出 `selector_audit` 事件：`{request_id, correlation_id, strategy_id, strategy_version, dispatch_decision, dispatched_at, dispatch_latency_ms}`，与 Node 0/Node 1 审计链对齐。 |
| I004 | info | 与 REQ-01 对齐 | REQ-01 §节点 2 | REQ-01 节点 2 的"改进建议"说"输出 draft 列表 / 拆 score / 强制负面搜索"，但这些是 strategy 模块职责，不是 Node 2 职责。 | REQ-01 §节点 2 第 1、2 段。 | 修订 REQ-01 §节点 2 的"改进建议"段，明确：draft 输出由 strategy 模块负责，Node 2 只负责 dispatch。 |
| I005 | info | 维度缺失 | Key question 1 "latest" | 评审只问 `strategy_version=latest` 是否支持，缺 `^`/`~` 范围语法、缺"两个 minor 之间的可重现性"约束。 | Key question 1。 | 文档补一句："v1 严格 semver，不支持 latest、^、~、范围语法；registry 的 default 字段是唯一允许的隐式版本。" |

---

## 推荐边界（我方建议）

**主方案边界基本可接受，补充如下**：

1. **属于本节点**：策略注册表（registry）维护、`strategy_id` + `strategy_version` 解析、market/run_mode 兼容性校验、entrypoint 加载前的版本冻结、dispatch 决策的原子事务、registry metadata 暴露给 observability。
2. **不属于本节点**：策略实现本身、draft 候选生成、证据链解释、score 排序、跨策略融合、fallback 替换、universe 解释、cron 调度、市场日历、交易执行。
3. **关键调整**：
   - 透传 `request_id` / `correlation_id` / `decision=proceed`，不重生成。
   - 解析必须原子：一旦 dispatch 成功，registry 后续变更不影响本次。
   - 状态机单向：`active → experimental → deprecated → disabled`，disabled 不可恢复。

---

## 推荐输入/输出契约变更

### 输入（建议加 1、明确 2）

```yaml
request_id: uuid                  # 新增：透传 Node 0
correlation_id: uuid              # 新增：透传 Node 0
run_context:                       # 透传 Node 1 输出
  decision: proceed | skip | needs_override | fail
  market: US | HK | CN
  run_date: YYYY-MM-DD
  signal_date: YYYY-MM-DD
  timezone: America/New_York | Asia/Hong_Kong | Asia/Shanghai

strategy_id: taroc | chokepoint | custom     # 必填
strategy_version: semver                     # 必填；可省略但需 resolver 锁定默认
custom_strategy_ref: string | null           # 新增：strategy_id=custom 时必填
market: US | HK | CN
run_mode: discovery | validation | tracking  # 透传，Node 2 不解释
universe: market | sector:{name} | watchlist:{name} | candidates:{market}  # 透传
dry_run: true
```

### 输出（建议加 3、改 1）

```yaml
request_id: uuid
correlation_id: uuid
strategy_id: string
strategy_version: semver
strategy_entrypoint:
  kind: skill_ref | path | url
  value: string
  checksum: string | null
strategy_status: active | experimental | deprecated | disabled
dispatch_decision: dispatch | reject | needs_review
reject_reason: none | strategy_not_found | unsupported_market | unsupported_run_mode | version_not_found | strategy_disabled | strategy_deprecated | custom_ref_invalid | schema_mismatch | strategy_unavailable | upstream_not_ready
expected_output_schema:
  name: draft_candidates              # 拆分 name + version
  version: semver
selector_warnings: string[]            # 至少含 version_implicit_default / deprecated_strategy_in_use / schema_version_drift
selector_audit:                        # 新增：dispatch 事件
  dispatched_at: ISO8601
  dispatch_latency_ms: number
  registry_version: semver            # 新增：本次解析时使用的 registry 版本号
```

**语义约束（必须文档化）**：
- `dispatch_decision=dispatch` 当且仅当 `strategy_status=active` 且所有校验通过。
- `dispatch_decision=needs_review` 仅对 `caller=manual` + `strategy_status=experimental` 合法。
- `reject_reason=upstream_not_ready` 当 `run_context.decision ≠ proceed`。
- `selector_warnings` 不影响 dispatch 决策；`reject_reason` 不影响 warning。
- `selector_audit.registry_version` 冻结本次解析的 registry 版本，registry 后续变更不追溯。

---

## 失败/拒绝行为（推荐版）

| 触发条件 | dispatch_decision | reject_reason | 备注 |
|---------|-------------------|---------------|------|
| Node 1 `decision≠proceed` | reject | upstream_not_ready | 强制前置 |
| `strategy_id` 不在 registry | reject | strategy_not_found | |
| `strategy_id=custom` 但缺 `custom_strategy_ref` | reject | custom_ref_invalid | |
| `custom_strategy_ref` 不在白名单/registry | reject | custom_ref_invalid | |
| `custom_strategy_ref` 含 `..` / 绝对路径 / checksum 不匹配 | reject | custom_ref_invalid | |
| `market` 不在 `supported_markets` | reject | unsupported_market | |
| `run_mode` 不在 `supported_run_modes` | reject | unsupported_run_mode | |
| `strategy_version` 不存在 | reject | version_not_found | |
| `output_schema_version` major 不匹配 | reject | schema_mismatch | |
| `strategy_status=disabled` | reject | strategy_disabled | 所有 caller |
| `strategy_status=deprecated` + `caller∈{cron, sop}` | reject | strategy_deprecated | 仅 manual 允许 |
| `strategy_status=experimental` + `caller=manual` | needs_review | none | 需人工 ack |
| `strategy_status=experimental` + `caller∈{cron, sop}` | reject | strategy_deprecated | 等同 deprecated 处理 |
| `last_reviewed_at` 超期（>180 天） | dispatch | none | 自动降为 experimental 并 warning |
| `entrypoint` 加载失败（运行时） | reject | strategy_unavailable | |
| `strategy_version` 省略 | dispatch | none | warning: version_implicit_default |

**关键改动**：
1. `upstream_not_ready` 新增，防止 Node 2 越过 Node 1 直接 dispatch。
2. `experimental` 策略在 cron/sop caller 下与 deprecated 同等对待。
3. `last_reviewed_at` 超期自动降级为 `experimental` + warning。
4. registry_version 冻结，保证 dispatch 可重放。

---

## 风险与缺失场景

| 风险 | 描述 | 缓解 |
|------|------|------|
| 策略爆炸 | 新增策略随意，registry 膨胀 | `status=disabled` 单向、`last_reviewed_at` 强制 review、registry 加 `owner` 字段定责 |
| 版本漂移 | `strategy_version` 与 `output_schema_version` 不同步 | dispatch 时同时冻结两个版本，下游用 `expected_output_schema` 断言 |
| Custom 注入 | `custom_strategy_ref` 被利用执行任意代码 | 强制白名单 + checksum + 路径约束（禁止 `..` 和绝对路径） |
| Registry 单点失败 | registry.yaml 不存在或解析失败 | v1 内置默认 registry + 加载时 checksum 校验；S3 立项 `strategy-registry` Layer 3 模块 |
| 静默 fallback | 缺策略时回退到 TAROC | 主方案已禁止；建议在 reject_reason 中加 `strategy_unavailable` 让 silent fallback 无处藏身 |
| 调度与契约分离 | SOP 编排层 fan-out 时怎么传 correlation_id | Node 2 透传 `correlation_id`，由 SOP 编排层在 fan-out 时复制 |
| 审计链断裂 | Node 0/Node 1/Node 2/Strategy 各有日志 | 统一 `selector_audit` 事件结构，与 Node 0 `request_id` + Node 1 `run_context.decision` 串成一条链 |
| Registry 升级时旧 dispatch 失效 | registry 改了，但已派发的 strategy 还在跑 | dispatch 解析时记录 `registry_version`，strategy 跑完前该版本不可变 |
| `caller=manual` 滥用 needs_review | 永远用 manual 触发 experimental 策略 | needs_review 必须记录 `approved_by` + `approved_at`，与 Node 0 触发日志对齐 |
| 旧 TAROC v1 与新 v2 混用 | registry 出现两个 version | `strategy_version` 严格 semver；同 strategy_id 不允许 major=0 与 major=1 同时 active |

---

## 验收标准（建议加入 S2 baseline）

1. Node 2 文档明确声明"不实现策略、不融合、不排序、不兜底、不解释 universe"。
2. 输入契约包含 `request_id`、`correlation_id`、`run_context.decision=proceed` 必填校验。
3. 输出契约包含 `request_id`、`correlation_id`、`selector_audit.registry_version`、`strategy_entrypoint.kind`。
4. `dispatch_decision` 与 `reject_reason` 联合约束文档化（见上表）。
5. v1 registry 只预置 `taroc`（`active`）；`chokepoint` 写为 `experimental` 且 v1 不进入 dispatch；`custom` 不接受自由注册。
6. `strategy_status=disabled` 一律 reject，无 caller 例外。
7. `strategy_status=deprecated` 仅对 `caller=manual` 允许 dispatch。
8. `custom_strategy_ref` 必须经白名单 + checksum + 路径约束三重校验。
9. `strategy_version` 严格 semver，不支持 `latest` / `^` / `~` / 范围。
10. dispatch 时同时冻结 `strategy_version` + `output_schema_version` + `registry_version`，写入 `selector_audit`。
11. Node 2 单元测试覆盖：Node 1 失败时 reject、registry 缺字段时 reject、版本不匹配时 reject、experimental 策略在 cron 下 reject、custom ref 含 `..` 时 reject、同 idempotency_key 二次 dispatch 返回首次结果。
12. 与 Node 0 v1「拒绝 mixed / full / monitor / dry_run=false」契约对齐；与 Node 1 v1「decision=proceed 才进入」对齐。
13. 4 个 key questions 必须给出推荐答案。
14. 文档明确 Node 2 不回答「validation / tracking 是 strategy 还是后续模块」问题（Q2 推到 S3）。
15. registry 归属 v1 路径为 `src/strategies/registry.yaml`，S3 阶段考虑抽成 Layer 3 `strategy-registry` 模块。

---

## 与主方案的分歧

| 编号 | 主方案 | 我方建议 | 理由 |
|------|--------|----------|------|
| D1 | 输出不含 `request_id` / `correlation_id` | **强制透传** | 审计链必须贯穿 Node 0 → Node 1 → Node 2 → strategy；缺这俩字段无法追溯 |
| D2 | `Node 1 decision=proceed` 作为前置条件未写进契约 | **契约必填校验** | 防止 Node 2 越过 Node 1 自行 dispatch |
| D3 | `strategy_version` 省略时 "may resolve to default" | **明确 resolver 原子事务 + 冻结** | 否则 registry 升级时已派发的 strategy 失效 |
| D4 | `custom` ref 接受"registry 或本地 config" | **仅接受受版本控制的白名单** | 本地 config 可写等于绕过白名单 |
| D5 | `deprecated` 策略 manual 允许 dispatch | **cron/sop 一律 reject** | 与 Node 0/Node 1 强调的"不静默 continue"对齐 |
| D6 | v1 registry 是否预置 Chokepoint 未说 | **v1 写为 experimental 且不进入 dispatch** | 与"未正式接入"现状对齐，避免 v1 出现 active=chokepoint 误导 |
| D7 | `expected_output_schema` 一个字段含 name+version | **拆 name + version** | 与 registry 的 `output_schema_version` 严格对应 |
| D8 | `output_schema_version` major 不匹配未规定 reject 行为 | **major 不一致直接 reject** | schema 不兼容比版本不匹配更严重 |
| D9 | registry 归属作为开放问题 | **v1 落地为 `src/strategies/registry.yaml`** | v1 必须有可运行文件 |
| D10 | `universe` 透传未明确 | **明确透传不消费** | 与 Node 1 评审 B001 对齐 |
| D11 | `entrypoint` 是 path_or_skill_ref 字符串 | **拆 kind + value + checksum** | 区分加载方式 + 防止注入 |
| D12 | 4 个 key questions 留空 | **提案给推荐答案** | 与 Node 1 评审 D5 一致 |

---

## 最重要的一条建议

**强制透传 `request_id` / `correlation_id` / `run_context.decision=proceed`，并把 dispatch 解析做成原子事务**。Node 2 是"分叉点"——同一个上游请求会从这里派发到一个具体策略；一旦审计链断了、或 registry 在 dispatch 过程中变更了，整个 S2 基线就在这一步失控。透传是审计的最低要求，原子事务是 dispatch 可重放的最低要求。

---

## 评级理由

- **不给 PASS**：B001（缺 `request_id`/`correlation_id` 透传）、B002（Node 1 `decision=proceed` 前置条件未进契约）两个 blocker 必须先补。
- **不给 WARN**：因为 4 个 major 风险点（custom 注入、registry 归属、状态机、版本漂移）任一不补都会导致 v1 落地时不可控。
- **给 CONDITIONAL PASS**：主方案方向对、边界清楚、silent fallback 已禁、registry 字段够用，修订成本低；补完 12 条 finding（含 2 blocker + 4 major）即可进 S3 方案设计，不需要重新评审边界。
