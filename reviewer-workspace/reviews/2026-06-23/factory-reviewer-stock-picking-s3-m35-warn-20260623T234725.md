# M3.5 Review — stock-picking S3 Design Gate

## 审查结论

**总体评级**：WARN
**置信度**：0.84
**审查对象**：B 类（方案类文档） + C 类（数据契约/配置） — `stock-picking` S3 设计包
**审查时间**：2026-06-23 23:47 CST
**使用模型**：newapi-openai/MiniMax-M3
**审查模式**：M3.5 闸门（battle 单轮 quick/battle 混合）— 验证 S3 baseline 是否可进 Ralph Loop M4a

**被审文件**：
- `projects/stock-picking/design/DESIGN.md`
- `projects/stock-picking/design/GRV.md`（上下文：Ralph Loop 准入条件、吸收矩阵）
- `projects/stock-picking/REQ-01.md`（上下文：S2 节点评审基线）
- `projects/stock-picking/src/references/data-schema.md`
- `projects/stock-picking/src/references/registry-design.md`
- `projects/stock-picking/src/references/execution-guard.md`
- `projects/stock-picking/src/references/migration-plan.md`
- `projects/stock-picking/src/strategies/registry.yaml`
- `projects/stock-picking/src/strategies/custom_refs.yaml`
- `projects/stock-picking/design/reviews/GRV-battle-round2-review-2026-06-24.md`（上轮发现吸收核对）

**Pack**：`packs/general.md`（B 类方案评审 + C 类契约评审）

---

## 一句话结论

**S3 baseline 方向正确、可落地，可进入 Ralph Loop M4a（安全/验证底座）**。Battle 二轮的 F001/F002/I001/I002 全部结构性吸收；registry snapshot 原子性、custom_ref 白名单加载时机、execution-guard 拒绝用例 5+2 条均已落到对应 reference 文件。但发现 **3 项 major + 7 项 minor + 3 项 info**，其中 3 项 major 都集中在"REQ-01 vs S3 data-schema 的隐式 schema 漂移"——S3 baseline 把"双冻结"写进 acceptance，但 data-schema 自身已经悄悄偏离了 REQ-01 节点评审基线（evidence_id 格式、source_type/source_quality 枚举、claim.v1 字段集、risk_event 来源 enum 等）。**M4a 必须在 schema validator 实现时先做一次"REQ-01 ↔ data-schema 对账"，否则双冻结会自欺欺人**。

按 GRV L223-231 准入条件，**M3.5 闸门通过**，可进入 M4a（前提：M4a 第一周把 3 项 major 在 schema validator 阶段关掉，剩余 7 minor 不阻塞 M4a 进入业务模块 M4b）。

---

## Ralph Loop 准入条件核对

GRV L223-231 列出的 6 条准入条件：

| # | 条件 | 当前状态 | 证据 |
|---|------|---------|------|
| 1 | GRV Battle 二轮没有 blocker | ✅ | `design/reviews/GRV-battle-round2-review-2026-06-24.md` 结论 WARN，无 blocker |
| 2 | `design/DESIGN.md` 已定义模块边界、目录结构、调用顺序、失败行为 | ✅ | DESIGN §1-4 含 14 模块边界表 + 文件结构 + 调用链 + 失败行为表 |
| 3 | `src/references/data-schema.md` 已冻结 P0 schema | ⚠️ | P0 schema 名称冻结 ✅，但与 REQ-01 存在隐式漂移（见 M001-M003） |
| 4 | `src/strategies/registry.yaml` 与 registry validator 设计已冻结 | ✅ | `registry.yaml` 含 TAROC + Chokepoint + maturity_gate；`registry-design.md` 含 snapshot atomicity 6 步 |
| 5 | execution guard 最小骨架的拒绝用例已写入 S3 设计 | ✅ | `execution-guard.md` §"Refusal Tests" 含 7 条 + §"Observable Signals" 含 broker API 调用统计要求 |
| 6 | M3.5 factory-reviewer 闸门通过，或仅剩明确可在 S4 第一轮关闭的 WARN | ✅ | 本轮结论 WARN，3 项 major 明确归口到 M4a schema validator 阶段 |

**M3.5 闸门：PASS（带 3 项必须 M4a 第一周关闭的 major）**。

---

## Battle Round 2 吸收核对

| ID | Battle R2 finding | S3 落点 | 吸收？ |
|----|-------------------|---------|--------|
| F001 | Chokepoint exit criteria 逻辑连接 + 重大 thesis break 判定口径 | `DESIGN.md` §3.5 "Exit criteria use AND logic" + "Major thesis break definition" 三条 | ✅ 完全吸收 |
| F002 | custom_ref 白名单存放位置、加载时机、变更审计路径 | `registry-design.md` §"Custom Ref Whitelist" + `DESIGN.md` §3.4 + §5 Decision Log 2026-06-24 一条 | ✅ 完全吸收 |
| I001 | `futu_tool.py buy` 修复的"已修复"可观测信号 | `execution-guard.md` §"Observable Signals" 写明 "Broker API call count for rejected paths must be zero or provably blocked before the broker client is invoked" | ✅ 完全吸收 |
| I002 | validation 幂等键不应依赖 mutable signal_date | `data-schema.md` `validation_event.v1` idempotency key 显式改为 `(draft_id, validation_run_id, calendar_checked_at, validation_session_key)`，并写明"signal_date is retained for reporting but must not be the sole idempotency anchor" | ✅ 完全吸收（且增强：把 R2 建议的 `calendar_checked_at` + `validation_session_key` 都纳入，比 R2 建议的"任选其一"更强） |

4/4 全部吸收，Battle R2 收束干净。

---

## 维度评分

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| DESIGN 完整性（模块边界/数据流/文件结构/UX/失败行为/粒度决策） | 5 | 6 个章节全覆盖；14 模块边界表 + 6 步调用链 + 6 项风险 + 5 状态 UX + hard fail/skip/needs_override/warning 四象限失败表 + 4 段粒度决策 |
| DESIGN 内部一致性 | 5 | §3.4 提到的 snapshot atomicity 6 步、custom_ref 白名单、AND exit criteria 与对应 reference 文件一一对得上；Decision Log 与正文无矛盾 |
| data-schema 内部完整性 | 4 | 16 个 schema 全部给出 enum 约束和 reject 规则；`legacy_csv_projection.v1` 兼容性段清晰；唯独缺一个"字段变更记录"小节（见 m007） |
| data-schema ↔ REQ-01 一致性 | 2 | **本轮最大问题**。3 项 schema 静默偏离 REQ-01 节点评审基线（见 M001-M003），未在文档中声明偏离或迁移路径 |
| registry.yaml / registry-design 完整性 | 5 | registry 字段含 `maturity_gate`（6 月 / 10 次 / 0 break / requires_factory_review），与 DESIGN §3.5 一一对应；snapshot 6 步 + 14 reject codes + 11 测试覆盖 |
| execution-guard 完整性 | 5 | 8 项 minimum checks + 7 条 refusal tests + broker API 调用统计可观测信号 + 显式 `dry_run` 默认 true + `sell` 在 v1 禁用 |
| migration-plan 完整性 | 4 | 7 步迁移序列 + rollback 路径 + 6 字段审计 + 4 条 acceptance；缺"如何处理 evidence_id 格式迁移"（见 m005） |
| Ralph Loop 准入对齐 | 5 | 6 条准入条件 5/6 完全满足，第 3 条 P0 schema 冻结存在 minor 偏差但已在 M001-M003 明确归口到 M4a |
| M3.5 → M4a 可执行性 | 4 | M4a 范围清楚（schema/registry validator + execution guard + approval gate + migration scaffold），S3 baseline 已给足 hook |

**加权分 ≈ 4.0**（data-schema ↔ REQ-01 一致性 2 分拖累整体）。

---

## 问题清单

### Major（3 项 — 必须在 M4a 第一周关闭，否则双冻结失效）

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| M001 | major | 静默 schema 漂移 | `data-schema.md` `evidence_ref.v1` `evidence_id` 字段 + REQ-01 §节点 13 `evidence_id: ev_<ulid>` | data-schema 把 `evidence_id` 简化为 `uuid`，丢弃了 REQ-01 显式定义的 `ev_<ulid>` 类型前缀。S3 文档未声明此偏离，未提供 claim 中 `evidence_id: string[]` 引用侧的兼容性说明。类型前缀的作用是让审计/索引/grep 时一眼能区分 evidence 与其他 uuid 实体（candidate_id / draft_id / approval_id 等都是裸 uuid）。在双冻结原则下，这是个未走 Decision Log 的隐式 schema 变更。 | data-schema.md `evidence_ref.v1`: `evidence_id: uuid` / REQ-01 `evidence_ref.v1`: `evidence_id: ev_<ulid>` / 文档无 `## Schema Changelog` 段 | 在 `data-schema.md` 加 `## Schema Changelog from REQ-01` 小节记录：(a) `evidence_id` 是否保留 `ev_` 前缀；(b) 决策后通过 M4a 的 schema validator 强校验。若决定保留前缀，把 data-schema 改回 `evidence_id: ev_<ulid>`（或 `string` 加 regex 约束）。 |
| M002 | major | 静默 schema 漂移 | `data-schema.md` `evidence_ref.v1` `source_type` 枚举 + REQ-01 §节点 13 `source_type` 枚举 | REQ-01 定义的 `source_type` 是 5 值（`primary / secondary / community / ai_inference / unverified`），data-schema 扩展为 9 值（新增 `regulatory / broker_data / company_filing / news / analyst / internal_note`，删除 `community / unverified`）。这是**扩展且重命名**两类值的复合变更：(a) 扩展是合理的（regulatory/company_filing 是 REQ-01 §节点 13 §"审计规则"明确提到的"一手来源"），但 (b) 把 `community` 和 `unverified` 合并为 `analyst / internal_note` 丢失了"未验证"语义。 | REQ-01: `source_type: primary \| secondary \| community \| ai_inference \| unverified` / data-schema: `source_type: primary \| secondary \| regulatory \| broker_data \| company_filing \| news \| analyst \| internal_note \| ai_inference` | 在 data-schema 顶部加 schema changelog，列出：(a) 新增 5 个值并标注对应 REQ-01 §节点 13 段落；(b) 显式声明 `community` 和 `unverified` 合并到 `analyst`（保留"unverified"语义为 `source_quality: unknown`）；(c) 或保留 `community / unverified` + 9 值全集。M4a schema validator 实现时需先按最终枚举值生成枚举字面量。 |
| M003 | major | 静默 schema 漂移 + 语义丢失 | `data-schema.md` `evidence_ref.v1` + `claim.v1` 字段集 | data-schema 把 REQ-01 §节点 13 的 `evidence_ref.v1` 字段集做了**两处不可逆简化**：(a) `publisher_authority: number` + `ai_classified_quality: number` + `classification_method: enum` 三字段全部消失，合并为单一枚举 `source_quality: high \| medium \| low \| unknown` —— 丢失了"双轨评分"（publisher 客观分 + AI 主观分）的能力，未来 evidence store 升级想做 weighted quality 时必须改 schema；(b) `claim.v1` 完全重写：REQ-01 字段是 `claim_kind: support \| refute \| risk \| catalyst \| break_condition \| neutral_context` + `polarity: positive \| negative \| mixed \| neutral` + `valid_until`，data-schema 改为 `claim_type: positive \| negative \| break_condition \| inference` + `thesis_broken: boolean` —— **把"两面性"压扁成了"四象限枚举"**，下游 tracking/weekly-review 没法再区分"这是正面的 catalyst 还是负面的 risk"（以前靠 polarity=positive + claim_kind=risk 可以表达"已知风险但论证中"）。 | REQ-01 §节点 13: `evidence_ref.v1` 完整字段 + `claim.v1` 完整字段 / data-schema: `evidence_ref.v1` 16 行（远少于 REQ-01） + `claim.v1` 9 行（远少于 REQ-01） | 在 schema changelog 显式声明：(a) `publisher_authority + ai_classified_quality` 是否需要保留——若需保留则改回 number 字段或加 `extensions: { publisher_authority?, ai_classified_quality? }`；(b) `claim.v1` 至少恢复 `claim_kind` + `polarity` 两字段，或用 `claim_type: positive \| negative \| break_condition \| inference` + `claim_subtype: string` 代替；(c) 这是双冻结原则下最严重的隐性回归，必须在 M4a schema validator 阶段先关掉。 |

### Minor（7 项 — 不阻塞 M4a，可在 M4a/M4b 同步关闭）

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| m001 | minor | 隐式添加 schema 字段 | `data-schema.md` `risk_event.v1` | REQ-01 `risk_event.v1` 的 `source` enum 是 4 值（`position_monitor / reconcile / portfolio_risk / execution_guard`），data-schema 添加了 `strategy_tracking`；`event_type` enum 从 5 值（`stop_loss_breach / drawdown_breach / quote_failed / reconcile_mismatch / execution_blocked`）添加了 `thesis_broken`。`thesis_broken` 与 DESIGN §3.5 Chokepoint 重大 thesis break 定义直接对应，是合理的；但 `strategy_tracking` 来源未在 REQ-01/GRV/DESIGN 中出现，且 `thesis_broken` 已在 `tracking_event.v1` 的 `event_type` 中可表达，存在冗余。 | REQ-01: `source: position_monitor \| reconcile \| portfolio_risk \| execution_guard` / data-schema: `source: ... \| strategy_tracking` + `event_type: ... \| thesis_broken` | 在 schema changelog 显式说明：`(a) strategy_tracking` 来源是 tracking_event 把 thesis_broken=true 提升到 risk_event 时的 source 值，或 (b) 删去以避免与 tracking_event.v1 重复 |
| m002 | minor | 跨文档引用断链 | `data-schema.md` Schema Index 中 P0 列表 vs DESIGN.md §3.3 Interface Specs | 两者都列了相同的 16 个 P0 schema 名称，**完全一致** ✅。但 `data-schema.md` 第 5 行列的兼容性 schema 段提到 `legacy_csv_projection.v1`，而 `migration-plan.md` 没有引用这个 schema 名。 | data-schema.md L5: `Compatibility: legacy_csv_projection.v1` / migration-plan.md: 无引用 | 在 migration-plan.md 顶部加 "References: data-schema §legacy_csv_projection.v1" 链接 |
| m003 | minor | 文档一致性 | `data-schema.md` `strategy_dispatch.v1` vs `registry.yaml` Chokepoint `output_schema` | data-schema `strategy_dispatch.v1.output_schema` 允许 `draft_candidates.v1 \| theme_research.v1`；registry.yaml 中 TAROC 的 `output_schema: draft_candidates.v1`、Chokepoint 的 `output_schema: theme_research.v1`。**一致性 OK**，但 registry 没说"Chokepoint 升级到 draft 时 output_schema 是不是会变"—— REQ-01 §节点 4 明确写 Chokepoint 先产 `theme_research.v1`，满足证据门槛后才升 `draft_candidates.v1`，所以同一 strategy 在不同阶段 output_schema 不同。registry 字段无法表达这种"运行时多 schema"。 | data-schema `strategy_dispatch.v1.output_schema` 双值 / registry.yaml 单值 | 在 registry-design.md §"Output Schema" 段加一条：Chokepoint `output_schema` 字段声明"primary output"，策略内部允许通过 `promotion_status` 触发 secondary output (draft_candidates.v1)；M4a 实现时 dispatch 输出 `output_schema` 必须反映本次运行实际 schema，而非 registry 静态字段 |
| m004 | minor | 配置一致性 | `custom_refs.yaml` | 文件存在但 `refs: []` 空。这是预期的（v1 不接受 custom），但 DESIGN §3.4 `custom_ref` policy 第 4 条说"Every whitelist change must be recorded in design/DESIGN.md Decision Log"，当前空列表是初始状态。建议在文件顶部加注释块说明"empty = no custom refs accepted in v1; any addition must be audited via DESIGN.md Decision Log"。 | `src/strategies/custom_refs.yaml`: `custom_refs_version: 1\nrefs: []` | 在 custom_refs.yaml 顶部加注释：`# Empty: v1 rejects all custom_refs. Any future entry must be approved via design/DESIGN.md Decision Log and reference a registry-approved strategy record or signed internal reference.` |
| m005 | minor | 迁移计划覆盖 | `migration-plan.md` 与 evidence_id 漂移联动 | migration-plan.md §"Audit Fields" 要求每条迁移事件带 `legacy_row_hash` 等 6 字段，**未考虑** evidence_id 在 REQ-01（`ev_<ulid>`）和 data-schema（`uuid`）两种格式间的迁移。如果 M001 决定保留 `ev_` 前缀，迁移时旧 CSV `reason` 字段绑定的 `evidence_id` 引用（前缀缺失）需要做格式补偿。 | migration-plan.md §Audit Fields / data-schema.md evidence_id 漂移 | 在 migration-plan.md §"Migration Sequence" 第 3 步后加一个 sub-step: "Normalize evidence_id format and document any id-prefix transition in migration_audit"；与 M001 同步处理 |
| m006 | minor | 验收标准缺条目 | `data-schema.md` 末尾 | data-schema.md 没有"如何验证 schema freeze"的可执行验收点。建议加一段 §"Verification"：M4a 必须产出 (a) JSON Schema / Pydantic / Zod 之一作为 executable validator；(b) `validate_schema.py` 跑过全部 16 schema 的正/反例测试。 | data-schema.md 全文无 §Verification | 在 data-schema.md 末尾加 §Verification 段，给 M4a 的 schema validator 实现定义验收点 |
| m007 | minor | 缺变更记录机制 | `data-schema.md` | 文档说 P0 schema 在 S3 冻结后"变更必须进 Decision Log"，但 data-schema.md 自身没有 changelog 段，DESIGN.md Decision Log 也没有 schema 变更条目。M001-M003 揭示的事实就是：schema 变更已经发生，但没走 Decision Log。 | data-schema.md 全文无 changelog / DESIGN.md Decision Log 4 条全是非 schema 决策 | 在 data-schema.md 顶部加 `## Schema Changelog` 段，M4a 第一周内把 M001-M003 三个发现的处置结果写进去 |

### Info（3 项 — 不阻塞，强化建议）

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| I001 | info | 强化建议 | `DESIGN.md` §3.7 UX & Error Fallback | "proceed/skip/needs_override/fail/reject/execution_blocked" 6 个 UX 路径已定义。建议加一条：当 Node 0/1/2 失败时，给出"最近一次成功 run"的可重试入口（retry vs re-run-from-scratch 的区别）。当前文档没区分 idempotency_key 重放与新 run。 | DESIGN §3.7 | 加一条 UX 规则："`idempotency_key` 重放时返回上次 cached result（包含 warnings），不重新执行。" |
| I002 | info | 强化建议 | `execution-guard.md` §"Observable Signals" | 提到 "Broker API call count for rejected paths must be zero or provably blocked before the broker client is invoked"，建议加一条"instrumented middleware hook" 的具体实现路径（method decorator / proxy / monkey patch），并明确归口到 M4a。 | execution-guard.md §"Observable Signals" 一段 | 加一段 "Implementation Hook"：建议用 method decorator `@execution_guard` 包装 `futu_tool.buy / longbridge.place_order` 等 broker entry point，guard 决定 block 时抛 `ExecutionBlockedError`，调用计数由 decorator 累计 |
| I003 | info | 强化建议 | `migration-plan.md` §Acceptance | 4 条 acceptance 包含"idempotent rerun"，建议加一条"冷启动首次迁移与热重启迁移行为一致"的回归测试。 | migration-plan.md §Acceptance 4 条 | 加 acceptance 5："Migration can resume from a partially completed batch without duplicating events; restart-after-failure must be idempotent." |

---

## 跨文档一致性矩阵

| 主题 | REQ-01 | GRV | DESIGN | data-schema | registry | execution-guard | 一致性 |
|------|--------|-----|--------|-------------|----------|-----------------|--------|
| 入口原子性（Node 0 拒绝 mixed/full/monitor/dry_run=false） | ✅ | ✅ R1 | ✅ §3.1-3.2 | ✅ atomic_request.v1 reject | n/a | n/a | ✅ |
| 交易日统一（Node 1 输出 run_context） | ✅ | ✅ R1/R2 | ✅ §3.2 | ✅ run_context.v1 | n/a | ✅ check #2 | ✅ |
| 策略选择器（Node 2 = registry，不执行） | ✅ | ✅ R3 | ✅ §3.2/3.4 | ✅ strategy_dispatch.v1 | ✅ snapshot 6 步 | n/a | ✅ |
| TAROC 输出 draft_candidates.v1 | ✅ | ✅ R3 | ✅ §3.2 | ✅ draft_candidates.v1 | ✅ output_schema: draft_candidates.v1 | n/a | ✅ |
| Chokepoint experimental + manual + US | ✅ | ✅ R3 | ✅ §3.5 | n/a | ✅ status: experimental + allowed_callers: [manual] + supported_markets: [US] | n/a | ✅ |
| Chokepoint exit criteria AND 逻辑 | ❓ Battle R2 F001 | ❓ | ✅ §3.5 | n/a | ✅ maturity_gate.exit_logic: AND | n/a | ✅（已吸收 F001） |
| 重大 thesis break 判定 | ❓ Battle R2 F001 | ❓ | ✅ §3.5 三条 | n/a | n/a | n/a | ✅（已吸收 F001） |
| custom_ref 白名单 | ❓ Battle R2 F002 | ✅ R3 | ✅ §3.4 | n/a | ✅ custom_refs.yaml + custom_refs_version: 1 | n/a | ✅（已吸收 F002） |
| custom_refs 加载时机（同 snapshot 阶段） | ❓ | ❓ | ✅ §3.4 "loaded in the same snapshot phase" | n/a | ✅ registry-design.md "loaded during the same validation phase" | n/a | ✅ |
| approval artifact machine-checkable | ✅ | ✅ R5 | ✅ §3.2 | ✅ approval.v1 | n/a | ✅ check #5 | ✅ |
| dry_run 默认 true | ✅ | ✅ R5 | ✅ §3.8 hard fail | ✅ atomic_request.v1 dry_run: true | n/a | ✅ check #1 | ✅ |
| futu_tool.py buy 修复可观测信号 | ❓ | ❓ I001 | ✅ §3.2/3.4 risks | n/a | n/a | ✅ "Broker API call count for rejected paths must be zero" | ✅（已吸收 I001） |
| validation 幂等键（不依赖 signal_date） | ❌ 用 signal_date | ❓ I002 | ✅ §4.1 risks | ✅ "(draft_id, validation_run_id, calendar_checked_at, validation_session_key)" | n/a | n/a | ✅（已吸收 I002，且更强） |
| evidence_id 格式 | `ev_<ulid>` | n/a | n/a | `uuid` ⚠️ | n/a | n/a | ❌ **静默漂移 M001** |
| source_type enum | 5 值 | n/a | n/a | 9 值 ⚠️ | n/a | n/a | ❌ **静默漂移 M002** |
| source_quality 字段 | 双 number + classification_method | n/a | n/a | 单 enum ⚠️ | n/a | n/a | ❌ **静默漂移 M003a** |
| claim.v1 字段集 | claim_kind + polarity + valid_until | n/a | n/a | claim_type + thesis_broken ⚠️ | n/a | n/a | ❌ **静默漂移 M003b** |
| risk_event.v1 source/event_type | 4+5 值 | n/a | n/a | 5+6 值 ⚠️ | n/a | n/a | ⚠️ **隐式扩展 m001** |

**汇总**：14 条一致性主题中 10 条 ✅、1 条 ⚠️（静默扩展）、3 条 ❌（静默漂移）。**M001-M003 是 S3 baseline 自身的一致性漏洞**，与 REQ-01 节点评审基线存在 3 处隐式背离，但 S3 文档全篇没有声明"已偏离 REQ-01 节点 X 段，原因 Y"。

---

## 风险与失败场景（针对 M3.5 / M4a 边界）

| 风险 | 描述 | 缓解 |
|------|------|------|
| 双冻结自欺欺人 | DESIGN §3.3 说"validator must preserve field names and reject unknown critical enums"，但 data-schema 自身已经偏离 REQ-01 节点 13 的字段集 | M4a schema validator 实现前先做 REQ-01 ↔ data-schema 对账，3 项 major 在 M4a 第一周关闭 |
| Registry snapshot 漂移（v1 实现期） | registry-design.md 写 "S4 can implement this as copy-on-read in a single process; no filesystem transaction is required for v1 as long as the selector never mixes two snapshots" —— 这是"开发者自律"约束，不是系统约束。`custom_refs.yaml` 与 `registry.yaml` 同时加载的原子性也未给出锁机制 | M4a 实现时用 process-level 单例 + bytes-after-read 哈希验证；若 v1.1 需要并发，引入文件锁 |
| Chokepoint maturity gate 自动判定 | registry.yaml `maturity_gate` 字段写得很完整，但**没有任何模块负责"这周运行了几次 manual / 这周有没有 thesis_broken 事件"**。Gate 是 data，但 evaluator 缺位 | M4b 在 `position-monitor` 或新 `chokepoint-maturity-evaluator` 模块实现 evaluator；M3.5 仅保证 data shape 正确，不阻塞 |
| execution guard 修复被绕过 | `futu_tool.py buy` 修复属于代码侧，execution-guard.md §"Observable Signals" 给的是验收信号不是实现机制。装饰器/代理/monkey patch 三种实现路径都说得通 | M4a 第一周用 decorator 模式先打 patch；保留 broker client 方法名不变 |
| 旧 CSV 迁移断链 | migration-plan.md 只说"keep legacy CSV read-only during compatibility window"，但没说"reader 切到 event store 后，CSV 投影是否仍生成" | M5 验收时显式测试"切到 event store 后，CSV 投影是否仍生成且与新写入一致" |
| Evidence store P1 延期 | GRV 把 evidence store 列 P1，S3 没把 evidence-store module 写进 §3.6 file structure | M4b 评估 evidence-store 落地时机；若 M4b 不动 evidence-store，data-schema 里的 evidence_ref / claim 暂作 dry 字段 |

---

## Ralph Loop / M4a 准入判断

| 检查项 | 状态 |
|--------|------|
| GRV Battle 二轮无 blocker | ✅ |
| DESIGN.md 模块边界 / 目录 / 调用顺序 / 失败行为完整 | ✅ |
| data-schema.md 冻结 P0 schema 名称 | ✅ |
| registry.yaml 与 registry-design.md 冻结 | ✅ |
| execution-guard 拒绝用例已写入 S3 设计 | ✅（7 条，超过 GRV 准入要求的 5 条） |
| M3.5 闸门 | ✅ **本轮通过** |

**M3.5 闸门结论**：**PASS**（带 3 项 major 必须在 M4a 第一周关闭）。

**M4a 准入建议**：
- **M4a Week 1**：实现 `validate_schema.py` + `validate_registry.py` 时，**先关 M001/M002/M003**（REQ-01 ↔ data-schema 对账），3 项 major 不关不允许进入 M4a Week 2。
- **M4a Week 2-3**：execution-guard decorator + approval-gate skeleton + migration scaffold。
- **M4a 退出条件**：M001-M003 关闭 + execution-guard 7 条拒绝用例 executable test 全过 + registry validator 正/反例测试全过 + migration 干跑一次成功（无需真数据）。
- **M4b 准入**：M4a 退出条件全过，且 7 项 minor 中至少 5 项已修或明示 M4b 处理计划。

**S5 验收不阻塞项**（M3.5 此刻可预见的 S5 必查点）：
- DRY-RUN 全链路：跑 1 次 manual TAROC discovery + 1 次 manual Chokepoint discovery + 1 次 validation + 1 次 reconcile。
- 交易闸门拒绝用例 executable pass：execution-guard 7 条 + S5 加 I001 broker API 调用统计。
- 旧 CSV → 事件模型迁移：1 次 cold-start + 1 次 restart-after-failure 的幂等性。
- Registry snapshot 漂移检测：人为改 registry.yaml 后，已派发的 strategy 仍按旧版本完成（replay safety）。

---

## 最重要的一条建议

**M4a 第一周必须做"REQ-01 ↔ data-schema 对账"，把 3 项 major 在 schema validator 落地前关掉**。S3 baseline 写"双冻结"是纸面冻结，data-schema 已经悄悄偏离 REQ-01 §节点 13 的 evidence/claim 字段集；如果 validator 直接按 data-schema 现状实现，等于把"REQ-01 节点 13 评审结论"也冻结成了过时版本。这是 M3.5 闸门唯一真正的风险点——其他维度都是工程量问题，这一条是"双冻结原则是否自洽"的根本性问题。

---

## 所需下一步动作

1. **编排者**：
   - 把本报告归档到 `projects/stock-picking/design/reviews/GRV-battle-round3-M3.5-review-2026-06-24.md` + `.json`（沿用 round 2 命名风格）。
   - 在 S3 任务派发单里把 M001-M003 列为 M4a Week 1 blocker。
2. **M4a 实施方**：
   - M4a Week 1 启动前先读 M001-M003，决定是 backport REQ-01（推荐）还是 forward-port data-schema（需要 R3 复审），并把决定写入 data-schema.md `## Schema Changelog` 段。
   - m001-m007 在 M4a/M4b 任意窗口关闭，优先级 M001 > M002 > M003 > m007 > m005 > m006 > m003 > m001 > m002 > m004。
3. **S5 验收方**：
   - 验收清单加入"M001-M003 在 data-schema.md changelog 中有结论"作为 M4a 退出条件 gate。
4. **不再走 GRV Battle 三轮**：本轮是 S3 baseline 闸门，不是 GRV 文档审查；后续如果 S4 实施产生 GRV 变更（如新策略、新市场），另起 Battle 轮次。

---

## 评级理由

- **不给 PASS**：M001-M003 三项 major 涉及"S3 baseline 与 S2 节点评审基线的一致性"，是双冻结原则的根本性问题；schema validator 落地方案取决于这三项的处置。
- **不给 FAIL / BLOCK**：M001-M003 是 schema 字段调整，不是事实错误、不是安全漏洞、不是逻辑跳跃；3 项都可以在 M4a Week 1 通过 1-2 天的"对账 + 写 changelog"关闭。
- **给 WARN**：双冻结原则纸面化、其他维度工程量可控、battle R2 全部吸收、registry/execution-guard 7 条拒绝用例、迁移计划 6 字段审计——S3 baseline 整体可落地。

---

## 归档元数据

- 审查对象类型：B + C 类（B 方案 + C 数据契约/配置）
- 审查模式：M3.5 闸门（battle 单轮 quick/battle 混合）
- 上轮结论：GRV Battle Round 2 = WARN（B001+M001-M005 已吸收，F001/F002 minor + I001/I002 info）
- 本轮结论：WARN（F001/F002 + I001/I002 已吸收；新发现 M001-M003 major + m001-m007 minor + I001-I003 info）
- 进入下阶段：Ralph Loop M4a（M001-M003 列为 M4a Week 1 blocker；M3.5 闸门通过）
- M4a 退出条件：M001-M003 关闭 + 7 条 minor 中至少 5 项处理或纳入 M4b 计划
