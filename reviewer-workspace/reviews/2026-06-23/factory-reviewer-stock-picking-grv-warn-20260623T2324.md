# Review Report — stock-picking GRV (Battle 模式)

**总体评级**：WARN
**置信度**：0.82
**审查对象**：B 类（方案/GRV）— `stock-picking` 项目 GRV（Goal/Results/Vision）+ REQ-01 全量
**审查时间**：2026-06-23 23:24 CST
**使用模型**：newapi-openai/MiniMax-M3（factory-reviewer）
**被审文件**：
- `projects/stock-picking/REQ-01.md`（1330 行，S2 讨论基线）
- `projects/stock-picking/design/GRV.md`（115 行，Draft for Battle）
**配套参考**：
- `projects/stock-picking/PLAN.md`（基线计划）
- `projects/stock-picking/DISCUSSION-LOG.md`（节点 0-13 评审会记录）
- `projects/stock-picking/intelligence-brief.md`（已读）
- 已审节点 0/1/2/4 评审报告（CONDITIONAL_PASS / WARN / CONDITIONAL_PASS / WARN）
- `packs/general.md`（通用评审维度）
- `REVIEWER_GUIDE.md`（WARN 模式：每条发现附修复建议）

---

## 一句话结论

GRV 的"目标—成果—举措—约束—风险—里程碑"骨架完整，与 REQ-01 的三层架构、S2 节点评审结论（节点 0-13 全部确认）方向一致；GRV 的 R1-R6 与 REQ-01 的核心数据契约、registry 设计、approval/execution guard 边界对齐良好；**但存在 1 个 blocker（GRV 缺失对未消化评审发现的"承接"声明）和 5 个 major 问题（GRV 把所有 R 推为 v1.0.0 同时完成、execution guard 缺最小骨架、R3 中 Chokepoint 退出条件被 R3 验收吞掉、Risk 章节"应对"不闭合、里程碑 M3-M4 缺独立 review 闸门）**，补齐后可升 PASS。

---

## 维度评分

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 目标清晰度（G） | 5 | 一句话把"单体 skill → 模块化 SOP 编排层"说清楚，定位准确；与 REQ-01 "一句话定位"完全一致 |
| 成果可验收性（R） | 3 | R1-R6 都有交付物 + 验收标准，但 R3 验收被简化、R5 只到"修复清单"层级、R6 的 migration plan 在 V 阶段没显式动作 |
| 举措可执行性（V） | 3 | V1-V9 顺序合理，但 V5（拆 TAROC/Chokepoint）与 V6（事件存储替换 day1/day2/day3）之间没有明确里程碑闸门 |
| 约束完整性 | 4 | 不重启 Gateway、不自动买卖、Evan 人工确认、不重写所有 quant 路径、保留 v2 入口直到验收通过——5 条全清晰 |
| 风险与缓解 | 3 | 风险表 5 条都列了"应对"，但第 1 条"CSV migration 兼容投影"对应 R6 的 migration plan 没有具体落点；第 4 条"Evidence store 设计过重"的应对"v1 JSON/JSONL + 索引"是已经在做的设计选择，不是真正缓解措施 |
| 里程碑闭环性 | 3 | M1-M5 顺序合理，但 M3/S3 设计完成后**没有 review 闸门**；M4/Ralph Loop 实施没有 review 闸门；只有 M2/Battle 审查是一次闸门 |
| 与 REQ-01 一致性 | 4 | 与三层架构、节点 0-13 评审结论对齐；与已审 node 0/1/2/4 评审的 finding **没有显式声明"已吸收/有分歧"** |
| 边界明确性 | 4 | "不做什么" + 约束条件 + 风控红线 + 风险 4 都把自动卖出、execution guard、CSV 物理落盘等排除；和 REQ-01 保持一致 |
| 战斗准备度（Battle） | 3 | GRV 自标"draft for Battle"，但没回答"我方推荐/反方质疑/裁决议题"三段式；M2 是评审，M3/M4 没有同等审查节点 |
| 安全/审计默认 | 4 | dry_run 默认 true；execution guard 默认关闭；CSV reason 不作唯一证据；approval artifact 强约束；与 REQ-01 完全一致 |

---

## 问题清单

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| B001 | blocker | 审计/可追溯 | GRV 全文 | 已审节点评审（node 0/1/2/4 共 24 条 finding：2+3+2+1=8 blocker/major、16 minor/info）**在 GRV 全文中没有任何"评审吸收声明"**。Ralph Loop 实施时无法判断"哪条 finding 已在 V/R 里消化、哪条没消化、哪条要回炉"。S2 评审会跑了一圈，但 GRV 入口处没有"评审吸收矩阵"或链接 | 4 份评审报告共 24 条 finding；GRV 全文搜不到"AC-"、"B00"、"M00"、"finding"等关键词 | 在 GRV 顶部加一节"评审吸收矩阵"（表格），列出已审 finding ID、对应 REQ-01 章节、对应 GRV 条款、消化状态（已吸收/部分吸收/未消化/有分歧）。这是 Battle 阶段 GRV 的"必填项" |
| M001 | major | 成果可落地性 | GRV R1-R6 + V1-V9 | R1-R6 全部目标都打包进 v1.0.0 一次性交付，但 V1-V9 的执行顺序并没有把这些 R 拆成 milestone 内的"硬里程碑"。M3 完成后同时进 R1-R6 设计、M4 完成后同时进 R1-R6 实施 — 这是 6 条平行 R 撞车，Ralph Loop 在 M4 阶段会**多线并行**，context 切换成本极高 | GRV 全文未对 R 排优先级；V1-V9 9 个举措里 6 个对应 6 个 R | (a) 把 R 按价值/风险/依赖排顺序：R5（交易安全）> R2（数据契约）> R3（策略边界）> R6（Evidence Store）> R4（候选生命周期）> R1（SOP 重写）；(b) 每个 R 在 M4 拆成独立 sub-Ralph Loop 子任务；(c) 在 GRV 里程碑表加一列"该 milestone 涵盖的 R 子集" |
| M002 | major | 安全/最小骨架 | GRV R5 | R5 验收标准只到"修复清单"层级（"futu_tool.py buy 不允许裸调"是修复项而不是成果），execution guard **没有最小骨架定义**。V7 写"设计 approval/execution guard"是设计工作不是落地工作，缺少：(a) approval state machine 转移表；(b) execution guard 拦截位点（CLI wrapper / library import / API gateway 至少选一个）；(c) dry-run 对照与 audit 字段 | REQ-01 §节点 10/§节点 12 已定义 approval + risk event schema；GRV R5 没继承 | R5 拆成 R5a（buy-approval-gate，含 approval state machine + 拦截位点）和 R5b（execution-guard 占位，默认 closed）。R5a 必须有最简 CLI wrapper 把 `futu_tool.py buy` 包起来，无 approval 时 hard error。R5b 写明"v1 不开发，仅留接口" |
| M003 | major | 策略边界完整性 | GRV R3 验收 | R3 验收写"cron/sop 必须精确 semver；不支持 latest"，但**未写已审 node 2 评审的 M001/M003/M005 三条 major**（custom ref 白名单 + checksum + 路径约束；状态机单向；schema_version 与 strategy_version 双冻结）。更关键的是 **REQ-01 §节点 4 已加 `experimental_exit_criteria` 字段要求（已审 node 4 评审 M002）**，但 GRV R3 验收没继承 | REQ-01 §节点 4 末尾 + 已审 node 2/4 评审 | (a) R3 验收补三条：custom ref 白名单 + checksum + 路径约束；状态机 active→experimental→deprecated→disabled 单向；schema_version 与 strategy_version 双冻结；(b) Chokepoint v0.1.0 registry 条目必须包含 `experimental_exit_criteria`（≥10 次 manual + 0 次 critical thesis_break + evidence 覆盖率 ≥60% + 团队评审通过日期） |
| M004 | major | 风险缓解闭合 | GRV "风险"段第 1/4 条 | 风险 1 "旧 CSV 与新事件模型迁移不完整" 应对写"先做只读兼容投影，再迁移写路径" — 这是 V8 的目标而不是"如何降低风险"的具体措施；风险 4 "Evidence store 设计过重会阻碍落地" 应对写"v1 JSON/JSONL + 索引，不做图数据库/RAG" — 这是已经定好的设计选择，不是缓解措施 | GRV 风险段 5 条逐条核对 | 风险 1 应对改为："v1 migration 必须配套 rollback plan + 兼容窗口（建议 2 周）+ 旧 CSV 写路径冻结日期；S4 第一个 sub-task 单独出 migration plan 文档"。风险 4 应对改为："evidence store v1 schema validator 必须在第一个 R6 sub-task 落地后 1 周内完成；schema 不通过时 R6 整体 block" |
| M005 | major | 里程碑闸门 | GRV 里程碑 M3/M4 | M3=S3 设计（DESIGN.md + data-schema.md），M4=S4 实施（Ralph Loop）。**M3 和 M4 之间没有 review 闸门**。M2（Battle 审查）只覆盖 GRV + REQ；M3 完成后直接进 M4。一旦 S3 设计有缺漏（按已审 node 1/2 经验，复杂契约评审通常会发现 blocker），就会带着 bug 跑 Ralph Loop 几周 | PLAN.md "下一步"列表：M2 → M3 → M4 连续无 review | (a) 在 M3 之后、M4 之前加 **M3.5：S3 方案 Battle 审查**（reviewer 出 S3-PASS/WARN/FAIL）；(b) M4 拆成 M4a（数据契约 + 策略边界 R2/R3 实施）和 M4b（候选生命周期 + 交易安全 R4/R5 实施），M4a 后再加 M4.5 审查；(c) 每个 R 完成后做 R-Level self-review（dofflemeyer 式 checklist） |
| m001 | minor | 命名一致性 | GRV 文档编号 P-GRV-01 | 文档自标"文档编号：P-GRV-01"，但 REQ-01 自标"编号 REQ-01"，DISCUSSION-LOG/PLAN 均无统一编号规则。Factory 内部文档编号是 GRV 第一个该有的章节，但缺少"文档编号规则"段 | GRV 顶部 + REQ-01 顶部对比 | 在 GRV 顶部加一节"编号规则"：`P-GRV-NN` = Project/GRV/序号；`P-REQ-NN` = Project/REQ/序号；`P-DSG-NN` = Project/Design/序号；`P-RVW-NN` = Project/Review/序号。后续 S3 设计的 DESIGN.md 应编为 `P-DSG-01` |
| m002 | minor | 命名一致性 | GRV R1-R6 vs REQ-01 节点 0-13 | GRV 的 R 是"按模块/能力"切的（编排层/数据契约/策略插件/候选生命周期/交易安全/Evidence Store），REQ-01 的节点是"按流程"切的（节点 0-13）。两个切法不能一一对应：R1 = 节点 0/1/2 的 orchestration 段；R2 跨节点 5-13 的数据契约；R3 = 节点 2-4；R4 = 节点 5-8；R5 = 节点 9-12；R6 = 节点 13。**没有映射表，V/R 的实施项会跟节点 0-13 评审发现错位** | GRV R/R 列表 vs REQ-01 节点 0-13 | 在 GRV 加一节"R 与节点映射表"，明确 R1↔{节点 0,1,2}、R2↔{节点 5,6,7,8 + 13 数据契约段}、R3↔{节点 2,3,4}、R4↔{节点 5,6,7,8}、R5↔{节点 9,10,11,12}、R6↔{节点 13}。后续 Ralph Loop 子任务命名沿用 R1-R6 + 节点号双标 |
| m003 | minor | 完整性 | GRV R4 | R4 验收写"AI 只能写 promote_suggested/remove_suggested，最终 removed 必须 human"，但没写 **"removed 必须 human" 如何在 schema validator 层强制**（已审 node 7 评审对应）。REQ-01 §节点 7 已写明"schema validator 必须拒绝 actor != human 的 removed 写入"，GRV R4 没继承 | REQ-01 §节点 7 + 已审节点 0/1/2 评审的同样模式 | R4 验收补一条："candidate_record.v1 schema validator 在 S3 阶段实现，强制拒绝 `actor != human` 的 `state=removed` 写入" |
| m004 | minor | 完整性 | GRV R6 + V8 | R6 验收有"支持 source dedup、snapshot、source quality、status lifecycle"，V8 写"design evidence store 与旧 CSV/Markdown 的 migration 方案"，但 R6 验收没写 **"v1 dedup 键是什么"**。REQ-01 §节点 13 写 `(source_url + claim_hash)` 是默认建议，但 GRV 没固化 | REQ-01 §节点 13 + GRV R6 + V8 | R6 验收补一条："v1 dedup 键为 `(source_url, content_hash)`（同 URL 同正文视为同一 evidence，不重复入库）"。V8 的 migration 文档必须包含"旧 CSV `reason` 字段如何映射到 `claim.v1` 的 claim_text + evidence_id[]" |
| m005 | minor | 风险识别 | GRV 风险表 | 风险表没列"多模块拆分后调用链变复杂"的应对细节。已审 node 2 评审和 node 4 评审都把"审计链 / evidence_ref 闭环 / correlation_id 透传"列为核心风险 | GRV 风险第 5 条 + 已审 node 0/1/2 评审 B 类 24 条 | 风险 5 应对补一条："dispatch / strategy_run / validation / tracking / risk 事件统一写入 `audit/<component>_audit_YYYY-MM.jsonl`；S3 阶段由一个独立 audit-format-check 工具断言每个事件的 request_id + correlation_id 不为空" |
| m006 | minor | 可测试性 | GRV 验收标准 R1-R6 | 6 条 R 的验收没有一条是"可机器验证的"。比如 R3 验收"TAROC 只输出 draft，不写 CSV" — 这是设计选择不是验收；"cron/sop 必须精确 semver" — 需要 test case 描述 | GRV 验收段 | 每个 R 验收补 ≥2 条"可执行验收"：(a) 命令/脚本能跑；(b) 期望 stdout/exit code/输出文件路径；(c) 与 baseline 对比。Battle 阶段不需要每条都写完整测试，但至少要给出"哪条验收是 unit-testable、哪条是 review-checkable" |
| m007 | minor | 与已审 finding 的关系 | GRV V9 | V9 "用 factory-reviewer 做 Battle 审查" — 措辞过于轻。"Battle 审查"应该是 multi-round（3 轮对抗 / 用户裁决）而不是单次评审。已审 node 0/1/2/4 全部是单次 review，GRV 应该把 multi-round 评审机制说清楚 | V9 单条 + 已审评审模式 | V9 改写："V9a: factory-reviewer 第一次评审 → 输出 issue list；V9b: 主 agent 修订 GRV；V9c: factory-reviewer 二次评审（Battle 二轮）；V9d: 仍未收敛时升级 Evan 裁决（Battle 三轮）。最终 PASS/WARN/BLOCK 由评审员在 V9c 或 V9d 给出" |
| I001 | info | 文档结构 | GRV 标题/章节 | GRV 没有"不做什么"专门章节（REQ-01 有），但 GRV 有"约束条件"段。建议显式加"不做什么"段，避免和"约束"混淆 | GRV 全文 | 加一节"不做什么"：不实现具体选股策略 / 不内置 cron / 不自动买卖 / 不自动卖出 / 不重写 quant 全部路径 / 不替代 serenity-skill 的方法论知识 / 不消费任何业绩数据作为信号 |
| I002 | info | 一致性 | GRV "约束条件" vs REQ-01 "约束条件" | GRV 约束 5 条，REQ-01 约束 9 条（含数据源/Gateway/交易日/Discord 输出格式等）。GRV 没吸收 REQ-01 的"数据源优先 longbridge"、"Discord 输出不用 Markdown 表格，摘要简短" | GRV 约束段 vs REQ-01 约束段 | 补两条：(a) 数据源优先复用 longbridge 系列 skill/CLI，新闻/政策/产业链证据走联网搜索；(b) Discord 输出不用 Markdown 表格，摘要简短（≤200 字） |
| I003 | info | 风险 | GRV 风险段 | 风险表 5 条都聚焦"实施风险"，没列"人员/认知风险"：(a) 主 agent 一个人跑全部 S3/S4，认知负载风险；(b) Ralph Loop 单 agent 跑多模块易丢上下文 | 隐含 | 加一条："主 agent 单人长跑 S3+S4 易失焦，应每完成一个 R 做一次 self-review + 状态总结写回 DISCUSSION-LOG.md" |
| I004 | info | 触发词 | GRV 全文 | GRV 没有"触发词"段（REQ-01 有"选股 / stock-picking / sp / TAROC 选股 / 卡脖子选股"） | REQ-01 触发词段 vs GRV 全文 | 补一段"触发词"，与 REQ-01 对齐。Battle 阶段 GRV 不仅是实施基线，也是后续注册到 Gateway 的入口元数据 |
| I005 | info | 已知问题 | GRV 全文 | GRV 没有"已知问题与修复方向"段（REQ-01 有 9 条）。其中至少 4 条（futu_tool.py buy 裸调、position-monitor 硬编码、target_pool 空字段、pending dry-run 过期）应作为 R5 的子项显式列出 | REQ-01 "已知问题与修复方向"段 vs GRV R5 | R5 验收补"已知问题承接"段，把 4 条高优先级 known issue 显式列为 sub-R |
| I006 | info | 版本规划 | GRV 全文 | GRV 没有"版本规划"段。REQ-01 末尾写"首个 Factory 管理版本 v1.0.0，但目标从收编旧 skill 改为建立模块化 SOP 与最小可运行模块边界" | REQ-01 版本规划 vs GRV | 补一段"版本规划"：v0.9.0 = S3 设计 + schema frozen；v1.0.0 = M4 完成后第一版可 dry-run 的 SOP；v1.1.0 = 真实 buy approval gate 验证 + 1 次完整 dry-run round-trip；v1.2.0 = 第一次人工买入确认端到端跑通（不真实下单） |
| I007 | info | 路由定位 | GRV 全文 | GRV 没有"路由定位/前后置 skill"段（REQ-01 有）。这是 Battle 阶段 GRV 必需章节 — 决定 R1 的 SOP 编排层怎么注册到 Gateway、怎么和 longbridge / taroc-strategy / chokepoint-strategy 协同 | REQ-01 路由定位段 vs GRV | 补一段"路由定位"：前置 skill (longbridge-* / internet-search / taroc-strategy / chokepoint-strategy)、后置 skill (selection-validation / position-tracker / ...)、重叠 skill (stock-picking-v2 / longbridge-* / my-positions / quant-tpr-rough-loop) |

---

## B 类（方案/GRV）专项

### 可行性
- **好**：三层架构清晰、模块边界在 REQ-01 已逐节点锁死、R1-R6 与节点 0-13 评审结论一致。
- **弱**：execution guard（R5）只有"修复清单"没有"最小骨架"；Evidence Store（R6）只有"两层 schema"没有"dedup 键/索引细节"；候选生命周期（R4）只有"事件存储"没有"状态机强制"。

### 完整性
- **缺**：评审吸收矩阵（B001）、R 与节点映射表（m002）、触发词、版本规划、路由定位、已知问题承接。
- **好**：目标/约束/风险/里程碑骨架完整。

### 风险识别
- **好**：识别了 CSV 迁移 / execution guard 过早开放 / Chokepoint 执行成本 / Evidence Store 设计过重 / 拆分后调用链复杂 5 条。
- **弱**：每条应对措施偏抽象、不可机器执行；没列"认知负载"类软风险。

### 边界明确性
- **好**：约束条件 5 条 + 不做自动买卖/卖出 + 保留 v2 入口直到验收 — 与 REQ-01 完全一致。
- **弱**：没有显式"不做什么"段（REQ-01 有），约束和不做什么混在一个段。

### 一致性
- **好**：与 REQ-01 三层架构、节点 0-13 评审结论对齐。
- **弱**：与已审 4 份评审报告（24 条 finding）没有显式承接/消化矩阵 — Battle 阶段 GRV 的最大缺口。

---

## 与主方案的分歧

| 编号 | GRV 当前表述 | 本审查建议 | 理由 |
|------|------------|------------|------|
| D1 | V1-V9 平铺所有 R | 按价值/风险/依赖排 R 优先级，并把 M4 拆 M4a/M4b | 6 条 R 并行会让 Ralph Loop context 切换爆炸 |
| D2 | R5 验收只到"修复清单" | 拆 R5a（buy-approval-gate 最小 CLI wrapper）+ R5b（execution-guard 占位） | 没最小骨架就没法验证"futu_tool.py buy 不裸调" |
| D3 | R3 验收不写 custom ref / 状态机 / 双冻结 | 补三条（来自已审 node 2 评审 M001/M003/M005） | 已审 finding 不吸收等于评审会白开 |
| D4 | 风险段 5 条应对偏抽象 | 风险 1/4 改写为可执行步骤（migration plan + 旧 CSV 写路径冻结日期；schema validator 1 周内完成） | 风险应对不可执行等于没应对 |
| D5 | M3 后直接 M4，无 review 闸门 | M3 后加 M3.5（S3 Battle 审查）；M4 拆 M4a/M4b + 中间 M4.5 审查 | 复杂契约评审一次性放过风险高 |
| D6 | V9 单次 Battle 审查 | 改 multi-round 评审机制（V9a-d） | Battle 模式设计本就要求多轮 |
| D7 | 缺评审吸收矩阵 | 顶部加"评审吸收矩阵"表格 | Battle GRV 必填项，决定 v1.0.0 是否能落地 |

---

## 最重要的一条建议

**在 GRV 顶部加"评审吸收矩阵"（B001）**。已审 4 份评审报告共 24 条 finding（8 blocker/major + 16 minor/info），如果 GRV 入口处不显式声明"哪条已吸收、哪条未消化、哪条有分歧"，Ralph Loop 在 M4 阶段无法判断"评审会发现被谁解决"。S2 评审会的全部价值会在 M3/M4 阶段蒸发。

---

## Acceptance Criteria（建议 Battle 通过前必须满足）

AC-1. **评审吸收矩阵**：GRV 顶部加一节"评审吸收矩阵"表格，列出已审 finding ID（4 份评审报告的 F/B/M/I 编号）、对应 REQ-01 章节、对应 GRV 条款、消化状态（已吸收/部分吸收/未消化/有分歧）。消除 B001。
AC-2. **R 优先级与里程碑映射**：M 列加"该 milestone 涵盖的 R 子集"；R 排序为 R5 > R2 > R3 > R6 > R4 > R1；M4 拆 M4a（R2+R3 实施）+ M4b（R4+R5+R6 实施）。消除 M001。
AC-3. **R5a 最小骨架**：R5 拆 R5a（buy-approval-gate，含 approval state machine + CLI wrapper 把 futu_tool.py buy 包起来，无 approval 时 hard error）+ R5b（execution-guard 占位，v1 不开发）。消除 M002。
AC-4. **R3 验收补三条**：custom ref 白名单 + checksum + 路径约束；状态机 active→experimental→deprecated→disabled 单向；schema_version 与 strategy_version 双冻结。Chokepoint v0.1.0 registry 条目必须包含 experimental_exit_criteria（≥10 次 manual + 0 次 critical thesis_break + evidence 覆盖率 ≥60% + 团队评审通过日期）。消除 M003。
AC-5. **风险段可执行化**：风险 1 应对补 migration plan + 兼容窗口 + 旧 CSV 写路径冻结日期；风险 4 应对补 schema validator 1 周内完成 + R6 整体 block 条件。消除 M004。
AC-6. **M3 后加 M3.5 闸门**：S3 设计完成后必须 factory-reviewer 再审一次；M4a/M4b 之间加 M4.5 闸门。消除 M005。
AC-7. **R 与节点映射表**：明确 R1↔{节点 0,1,2}、R2↔{节点 5-8 + 13 数据契约段}、R3↔{节点 2,3,4}、R4↔{节点 5,6,7,8}、R5↔{节点 9,10,11,12}、R6↔{节点 13}。消除 m002。
AC-8. **R4 补 schema validator 强制**：R4 验收加"candidate_record.v1 schema validator 强制拒绝 actor != human 的 state=removed 写入"。消除 m003。
AC-9. **R6 补 dedup 键**：v1 dedup 键为 `(source_url, content_hash)`；V8 migration 文档必须包含"旧 CSV reason 字段如何映射到 claim.v1"映射规则。消除 m004。
AC-10. **风险 5 应对补 audit 闭环**：dispatch / strategy_run / validation / tracking / risk 事件统一写 audit 日志；S3 阶段由独立 audit-format-check 工具断言 request_id + correlation_id 不为空。消除 m005。
AC-11. **V9 改 multi-round 评审**：V9a 一次评审 → V9b 主 agent 修订 → V9c 二次评审 → V9d Evan 裁决（仍未收敛时）。消除 m007。
AC-12. **补"不做什么"段**：把 GRV 约束条件拆出"不做什么"段。消除 I001。
AC-13. **补 2 条约束**：数据源优先 longbridge；Discord 输出不用 Markdown 表格、摘要简短。消除 I002。
AC-14. **补触发词段**：与 REQ-01 对齐（选股 / stock-picking / sp / TAROC 选股 / 卡脖子选股）。消除 I004。
AC-15. **补已知问题承接段**：把 REQ-01 的 4 条高优先级 known issue 列为 R5 sub-R。消除 I005。
AC-16. **补版本规划段**：v0.9.0（设计 + schema frozen）→ v1.0.0（第一版可 dry-run）→ v1.1.0（buy approval + dry-run round-trip）→ v1.2.0（人工买入确认端到端）。消除 I006。
AC-17. **补路由定位段**：前置/后置/重叠 skill 列表。消除 I007。
AC-18. **补"认知负载"风险**：主 agent 单人长跑 S3+S4 风险 + 每 R 完成后 self-review + 状态总结回写 DISCUSSION-LOG.md。消除 I003。
AC-19. **验收可执行化**：每个 R 至少 2 条验收是 unit-testable 或 review-checkable。消除 m006。
AC-20. **文档编号规则**：GRV 顶部加编号规则段（P-GRV-NN / P-REQ-NN / P-DSG-NN / P-RVW-NN）。消除 m001。

---

## verdict 决策依据

- **没有事实错误/幻觉**（评分 4）→ 不上 BLOCK/FAIL。
- **缺 1 个 B 类必填项**（评审吸收矩阵）→ B001 是 blocker。
- **5 个 major**（R 优先级/最小骨架/策略边界/风险应对/里程碑闸门）任一不补都会让 v1.0.0 落地时失控。
- **其他 16 条 minor/info** 是结构/编号/可执行性增量修补。
- **AC-1 ~ AC-6**（B001 + 5 major）必须在 PASS 前补完。
- **综合**：**WARN**（补完 B001 + 5 major 后可升 PASS；Battle 阶段尚可继续推进 S3 方案设计，但 Ralph Loop 实施必须等 Battle 二轮通过）。

---

## 关键引用（评审证据链）

- `projects/stock-picking/REQ-01.md` 节点 0-13 全部评审会确认（2026-06-23 22:43 ~ 2026-06-24 00:10）
- `projects/stock-picking/DISCUSSION-LOG.md` Session 1 + 节点 0-13 续作
- `projects/stock-picking/PLAN.md` 当前状态与下一步
- 已审评审报告：
  - `reviews/2026-06-23/main-agent-stock-picking-node0-trigger-entry-CONDITIONAL_PASS-223625.md`（Node 0 触发入口）
  - `reviews/2026-06-23/stock-picking-node1-market-context-warn-20260623T224500.md`（Node 1 交易日上下文）
  - `reviews/2026-06-23/stock-picking-node2-strategy-selector-conditional-pass-20260623T225800.md`（Node 2 策略选择器）
  - `reviews/2026-06-23/stock-picking-node4-chokepoint-warn-20260623T2309.md`（Node 4 Chokepoint）
- `packs/general.md` B 类方案评审维度
- 评审员个人参考（已审 4 份 B 类评审）

---

## 评级理由（与工厂评审口径一致）

- **不给 PASS**：B001 + 5 major 未消化前，v1.0.0 落地不可控；Battle 二轮前不应放行。
- **不给 FAIL**：GRV 整体方向对、与 REQ-01 节点 0-13 评审结论一致、风险与约束已识别主框架、修订成本低。
- **给 WARN**：补完 B001 + AC-1 ~ AC-6 即可升 PASS；Battle 阶段可继续推进 S3 方案设计（但不进入 Ralph Loop 实施）。
- **置信度 0.82**：B001 是单点高置信问题；major 5 条已逐条核对 REQ-01 章节与已审评审 finding；minor/info 16 条是结构/编号/可执行性增量，不阻塞主结论。
