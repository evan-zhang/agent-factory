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

## 3. Level Boundary

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

Every BP object MUST be audited against the following 7 dimensions. No dimension may be skipped. The audit must be exhaustive and produce a judgment (✅ Pass / ⚠️ Need confirmation / ❌ Fail / 📊 Data missing) for each dimension before any confirmation question is asked (see SKILL.md Step 4.5 and state `dimension_audited` in `interactive_state_machine.md`).

| # | Dimension | What to check | Judgment criterion |
|---|---|---|---|
| 1 | 层级边界 (Level boundary) | Does each objective belong to the correct organization level (group/center/department/individual)? Are boundaries between levels clean? | Objectives align with the level's responsibility scope; no cross-level leakage. |
| 2 | OKR 语义 (OKR semantics) | Are objectives, key results, and initiatives written following the standard semantic chain (target → outcome → measure → initiative → owner → cascade → downstream → evidence)? | Each level uses the correct depth; semantic chain is intact. |
| 3 | 成果验收 (Outcome acceptance) | For each outcome, is there an explicit measurable acceptance criterion (threshold, value, timing, deliverable)? | Every outcome has a numeric threshold or verifiable deliverable. |
| 4 | 口径对齐 (Definition alignment) | Are scoring rules, time windows, denominators, and reference targets (e.g., "75分位", "YTD") explicitly defined? | No ambiguous or undefined口径 references. |
| 5 | 证据路径 (Evidence path) | Does each key KR / initiative have a process evidence path so AI判灯 can determine status (red/yellow/green)? | Every key item has evidence source and frequency. |
| 6 | 单主责 (Single owner) | Does each key KR / initiative have exactly one主责主体 (no co-primary ownership)? | Single named owner; co-owners are协办 not co-主责. |
| 7 | 冻结规则 (Freeze rules) | Does the BP object violate any of the 10 freeze rules in § 6? (No placeholders, no empty thresholds, no "待完善" metrics, no "?" metrics, no typos, no numbers without口径, no key initiatives without owner, no key initiatives without cascade, no key initiatives without evidence, no unconfirmed facts.) | Zero violations. |

If any dimension is judged ⚠️ or ❌, the corresponding issues MUST be entered into the question queue and asked one by one (see `interactive_state_machine.md` § 3 Question Rules).

A dimension with insufficient data to judge MUST be marked 📊 Data missing, NOT left blank. Data missing itself becomes a question for the user.
