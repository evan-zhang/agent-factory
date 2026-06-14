# Core BP Rules

## 1. Organization Chain

The BP system covers the full chain:

`集团 -> 中心/业务公司 -> 部门 -> 关键岗位个人`

Each organization level has a responsible owner. A level's target is achieved by the contribution set of its responsible person and key individuals.

## 1.2 BP Object Granularity

"One BP object" has different meanings at different levels. This must be confirmed before locking (see SKILL.md Step 0 and state `material_received`).

| Level | One BP object equals |
|---|---|
| 集团 | One group objective, e.g., G-7 (with its outcomes and initiatives) |
| 中心 / 业务公司 | One center objective, e.g., A3-1 (with its outcomes and initiatives) |
| 部门 | One department's full BP (all objectives for that department) |
| 关键岗位个人 | One individual's full BP (all objectives for that person) |

When the user provides a full center BP document (e.g., all 10 center objectives), ask which objective to process first before locking. Never audit multiple objectives in one cycle unless the user explicitly asks for a batch summary.

## 2. Standard Semantic Chain

Use one semantic structure across levels, but vary depth by management need:

`目标 -> 成果 -> 衡量标准/最终验收物 -> 关键举措 -> 主责主体 -> 承接方式 -> 下级承接对象 -> 过程证据/AI判灯依据`

| Layer | Meaning | Control Point |
|---|---|---|
| 目标 | Annual result state this level must form | Must be a result state, not an action list |
| 成果 | Key results proving target achievement | KR layer; controls final delivery |
| 衡量标准/最终验收物 | Criteria or final acceptance object for judging成果 | Must be judgeable and source-backed |
| 关键举措 | Path supporting成果 achievement | Primary downstream handoff point |
| 主责主体 | Single accountable organization or person | Must not be blurred with协同 |
| 承接方式 | How the initiative continues downstream | Complete BP, light tracking, result responsibility, collaboration trace, or no split |
| 下级承接对象 | Lower-level BP object when complete BP承接 is selected | Only filled for complete BP承接 |
| 过程证据/AI判灯依据 | Monthly natural evidence used by AI to judge progress | Not the same as final验收物 |

成果层负责交付验收，举措层负责过程推进。

### 成果输出对象 8 类（v1.5 §三 / R36）

每个成果必须标注一个主输出对象，归入以下 8 类之一：

1. **经营结果**：收入、利润、现金流、市场份额、费用率、回款质量、断货率等可量化的经营指标
2. **规则机制**：经确认的规则、制度、流程、决策机制、评价机制、分配机制
3. **业务模型**：跑通的新业务模式、产品模型、渠道模型、商业化模型
4. **系统能力**：上线并验收的系统、数据贯通、AI诊断、知识库能力
5. **数据/知识资产**：可复核的数据资产、资料资产、规则库、诊断库、证据库
6. **组织机制**：关键岗位机制、骨干队伍机制、协同机制、激励机制
7. **合作成果**：已签署或进入实质执行的合作、准入、注册、转移生产、商业化承接
8. **复盘结论**：集团确认的正式复盘结论，用于下一轮决策、纠偏或规则迭代

**主输出对象规则（R37）**：
- 一个成果原则上只设一个主输出对象
- 多个独立验收物应拆分成果，或明确主输出 + 辅助输出
- 不得把过程证据（会议纪要、台账、月报、审批进度）误写为成果输出对象
- 缺成果输出对象 → 维度 3 ❌；暂未确定 → 写"待确认"并说明缺口

### AI 数字化/系统类目标写法（v1.5 §9.2 / R25/R26）

集团层 AI 数字化类成果应写清：
1. 支撑哪个管理闭环
2. 打通哪些数据、文档、证据或知识资产
3. 重构哪些重点业务工作流
4. 如何支持判断、复盘、纠偏和责任追溯
5. 哪些内容需要下沉为信息化专项/中心BP/项目计划

不宜写法（❌）：用系统名称替代成果 / 用模块清单替代管理目标 / 用看板上线替代数据贯通 / 用 AI 工具清单替代工作流重构 / 把所有 AI 应用都上提为集团级目标。

AI 工作流样板 6 要素：管理对象 / 流程节点 / 数据与证据来源 / AI 应用方式 / 责任主体 / 复盘回流。

### 外来概念本地化（v1.5 §9.1 / R27）

不应机械引用外部术语作为正式BP标题：
- FDE 骨干队伍 → 适应管理升级、业务流程重塑和AI数字化运行要求的业务骨干与关键人才
- AI Agent 项目 → AI 驱动的重点业务工作流重构
- Dashboard 上线 → 数据贯通、证据链和管理评价能力形成

检测到未本地化的外部术语 → 维度 2 ⚠️，要求改写为公司内部可理解、可执行、可评价的业务管理语言。

## 3. Level Boundary

### 集团-中心边界上提触发（v1.5 §5.1.2 / R19）

满足以下任一条件才允许写入集团BP：
1. 集团冻结目标（年度硬承诺、财务数字、战略基线）
2. 跨中心协同（多中心共同完成，不写集团层会责任断裂）
3. 无人负责风险（不在集团层指定可能没人负责）
4. 重大决策权（CEO/管委会/投决机制）
5. 重大风险控制（集团级合规/资金/供应/资本回收）

### 集团-中心边界分流条件（v1.5 §5.1.3 / R18/R42）

满足以下任一条件原则上不进集团BP：
1. 中心工作法（专业路径）
2. 内部流程（SOP/台账/会议）
3. 部门分工（中心内部部门或岗位承办）
4. 具体项目动作（单项目/单产品/单合作方）
5. 工具建设细节（系统/看板/模板）
6. 过程复盘动作（内部复盘/日常检查/问题关闭）

集团BP只写：战略方向 / 最低交付 / 结构要求 / 承接入口。不写中心内部过程：月报怎么做、会议怎么开、项目怎么归档、风险预警怎么设计、SOP 怎么编、人员怎么排班、项目节点表怎么维护。

### Group BP

Group BP writes only:

| Type | Meaning |
|---|---|
| 战略方向 | Annual strategic state the group must form |
| 最低交付 | Minimum delivery baseline required by group |
| 结构要求 | Business, product, capability, organization, or risk structure required by group |
| 承接入口 | Which center/business company must receive and decode the requirement |

Group BP must not write center internal process actions such as monthly meeting mechanics, SOP details, project filing, risk alert mechanism design, or detailed node tables.

### Center / Business Company BP

Center or business company BP decodes group requirements and adds:

| Type | Meaning |
|---|---|
| 放大目标 | Not lower than the upstream baseline; may set floor/base/excellent/challenge levels |
| 专业路径 | Professional path designed by the center |
| 部门分工 | Split to departments, modules, projects, or key roles |
| 过程管理 | Project list, monthly review, alert, meeting, SOP, evidence archive |
| 能力建设 | Organization, talent, system, process, mechanism capability goals |

### Department BP

Department BP is valid only when the department has real management increment:

1. multiple outcomes or workstreams;
2. multiple key roles to manage;
3. independent annual result commitment;
4. not merely executing a single already-defined center task.

### Key Individual BP

Personal BP covers key roles only, not every participant. It is valid only when the person has a distinct annual result commitment and evidence responsibility.

## 4. Differentiated Depth

| Organization Type | Recommended Structure |
|---|---|
| 专业责任中心 | 中心完整BP + 部门/个人责任卡 + 日常证据/AI判灯 |
| 经营责任中心 | 集团战略基线 + 经营责任中心完整BP + 区域/部门BP + 关键岗位个人BP |
| 混合型中心 | Decide by object: complete BP for multi-line capability, light tracking for single tasks, split business input and professional conversion when needed |

### 经营责任中心 vs 经营管理中心（v1.5 §7.4 / R40/R41）

- **经营责任中心** = 深康 / 德镁 / 维盛 / 院外业务中心（承担业务事实和经营结果）
- **经营管理中心** = 经营规则/诊断/审核/统筹/复盘（职能中心，不承担经营结果）
- 混淆时归维度 6（单主责）或维度 1（层级边界）问题。
- 完整复盘版、关闭版、总复盘版必须反写占位词，过程稿可临时使用。

## 5. Downstream Handoff

关键举措 is the primary lower-level承接入口. 成果 proves the target, but is often still too broad for direct downstream ownership.

Use five承接方式:

| 承接方式 | Use When |
|---|---|
| 完整BP承接 | Lower level needs its own target, multiple outcomes, and multiple initiatives |
| 任务/举措轻量跟踪 | It is a concrete task without independent BP tree value |
| 成果责任派发 | A result is naturally owned by one module/person but does not need another target tree |
| 协同留痕 | It is support, input, review, or dependency, not vertical ownership |
| 不下拆 | Current level can execute and evidence it directly |

### 完整BP承接 5 必要条件（v1.5 §4.3.1 / R46）

完整BP承接须同时满足：
1. 下级承担年度结果责任
2. 下级需把上级关键举措转写为本级年度目标
3. 下级需继续拆出多个成果或关键举措
4. 下级存在真实管理增量（多部门/多项目/多流程/多岗位/多工作流）
5. 月报、证据、灯色沿纵向链路上卷

缺少任一条件 → 不得写"完整BP承接"。

反例（v1.5 §4.3.1 示例）：
- "建立产品资产基线达成的集团级确认和例外裁决机制" → 不下拆/集团裁决机制（最终裁决权留在 CEO/管委会）
- "由财经中心提供 NPV 测算和产品力得分" → 协同留痕（只提供输入）或成果责任派发（需交正式规则卡）

If complete BP承接 is selected, the downstream object must rewrite the initiative into its own annual result-state target. It must not mechanically copy the upstream initiative wording.

## 6. Ownership

Each key initiative has one主责主体. If two real owners exist, split the row or define one主责 and one协同主体.

主责主体 answers "who is accountable for success or failure." 承接方式 answers "whether and how this continues downstream." Do not merge them.

## 7. One-To-Many Decomposition

A healthy BP cascade should usually form:

`one target -> multiple outcomes -> multiple initiatives -> lower-level one-to-many continuation`

If one target has one outcome and one initiative, consider aggregating it into one task object. Do not create formal hierarchy without management increment.

## 8. Amplification

Upstream targets are minimum baselines, not simple arithmetic totals. Lower levels should not reduce upstream targets. Centers may amplify via floor/base/excellent/challenge levels; departments and key individuals should provide coverage redundancy.

## 9. Freeze Rules

Do not freeze formal BP text containing:

1. placeholders or stars;
2. empty thresholds;
3. "待完善" as a final metric;
4. question-marked metrics;
5. obvious typos;
6. numbers without口径;
7. key initiatives without主责主体;
8. key initiatives without承接方式;
9. key initiatives without process evidence or AI判灯 basis;
10. unconfirmed facts, ownership, or business rules.


## 10. Seven Audit Dimensions (Mandatory Exhaustive Check)

Every BP object MUST be audited against the following 7 dimensions. No dimension may be skipped. The audit must be exhaustive and produce a judgment (✅ Pass / ⚠️ Need confirmation / ❌ Fail / 📊 Data missing) for each dimension before any confirmation question is asked (see SKILL.md Step 5 and state `dimension_audited` in `interactive_state_machine.md`).

字段级操作核查动作（必查字段、归类边界）见 `references/dimension_audit_checklist.md`。该文件从属于本节，冲突时以本节为准。

| # | Dimension | What to check | Judgment criterion |
|---|---|---|---|
| 1 | 层级边界 (Level boundary) | Does each objective belong to the correct organization level (group/center/department/individual)? Are boundaries between levels clean? | Objectives align with the level's responsibility scope; no cross-level leakage. |
| 2 | OKR 语义 (OKR semantics) | Are objectives, key results, and initiatives written following the standard semantic chain (target → outcome → measure → initiative → owner → cascade → downstream → evidence)? | Each level uses the correct depth; semantic chain is intact. |
| 3 | 成果验收 (Outcome acceptance) | For each outcome, is there an explicit measurable acceptance criterion (threshold, value, timing, deliverable)? | Every outcome has a numeric threshold or verifiable deliverable. |
| 4 | 口径对齐 (Definition alignment) | Are scoring rules, time windows, denominators, and reference targets (e.g., "75分位", "YTD") explicitly defined? | No ambiguous or undefined口径 references. |
| 5 | 证据路径 (Evidence path) | Does each key KR / initiative have a process evidence path so AI判灯 can determine status (red/yellow/green)? | Every key item has evidence source and frequency. |
| 6 | 单主责 (Single owner) | Does each key KR / initiative have exactly one主责主体 (no co-primary ownership)? | Single named owner; co-owners are协办 not co-主责. |
| 7 | 冻结规则 (Freeze rules) | Does the BP object violate any of the 10 freeze rules in § 9? (No placeholders, no empty thresholds, no "待完善" metrics, no "?" metrics, no typos, no numbers without口径, no key initiatives without owner, no key initiatives without cascade, no key initiatives without evidence, no unconfirmed facts.) | Zero violations. |

If any dimension is judged ⚠️ or ❌, the corresponding issues MUST be entered into the question queue and asked one by one (see `interactive_state_machine.md` § 3 Question Rules).

A dimension with insufficient data to judge MUST be marked 📊 Data missing, NOT left blank. Data missing itself becomes a question for the user.
