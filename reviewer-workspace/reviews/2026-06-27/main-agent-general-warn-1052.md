# 08-Reviewer 审查与引进方案

> 审查对象：`mattpocock/skills 评估结论 → OpenClaw Life Gateway 引进/改造方案`  
> 审查时间：2026-06-27  
> 审查角色：factory-reviewer  
> 审查范围：TPR Framework、Agent Factory SOP、factory-reviewer 与 `knowledge/2026/06/mattpocock-skills/` 7 篇评估文档  
> 总体结论：**有条件通过（WARN / CONDITIONAL PASS）**

---

## 一、审查结论摘要

主 Agent 提出的三项引进动作总体方向正确：它没有尝试整套照搬 mattpocock/skills，而是提取其中最适合 OpenClaw 的方法论原语（追问、交接、双轴评审）并嵌入现有 TPR / agent-factory-sop / reviewer 体系。这符合 `07-企业适配建议.md` 的总结判断：核心价值不在具体 Skill 实现，而在「追问先于行动、统一语言减少成本、小步快跑验证反馈、深层模块设计」。

但当前方案仍偏概念性，存在三个需要修正的点：

1. **动作 1（grilling → TPR Discovery）可行且高 ROI，但必须做“阶段化裁剪”**：不能把无限追问原样放入 DISCOVERY，否则会冲突 TPR 的阶段停止规则和用户确认节奏。
2. **动作 2（handoff → Skill 工厂多 session 协作）必要性最高，应作为第一优先级**：Agent Factory SOP 已经存在 S0-S8 长流程和三道评审关卡，最容易发生上下文断裂；handoff 应落成标准交接包，而不是临时总结。
3. **动作 3（review 双轴 → factory-reviewer）方向正确，但表述不准**：factory-reviewer 现有 AGENTS.md 已不只是“单轴代码质量”，它已经覆盖 A/B/C/D/E 五类审查；真正缺口是 **C 类代码审查没有强制绑定原始需求 / GRV / issue / DESIGN baseline 做符合度审查**。

建议最终采用：

> **P0：先做 handoff 标准化 → P1：升级 reviewer 的需求符合度轴 → P2：把 grilling 裁剪后嵌入 TPR Discovery。**

原因是：handoff 和 reviewer 都是基础设施型改造，能立即降低现有工厂流程风险；grilling 属于交互体验改造，需要更多试点和节流规则。

---

## 二、各维度评审结论

| 维度 | 结论 | 评分 | 简评 |
|---|---|---:|---|
| 可行性 | 有条件通过 | 4/5 | 三个动作都可在 OpenClaw 现有文件型 Skill / subagent / reviewer 体系内落地，无明显技术障碍；但都需要本地化为 OpenClaw 机制，不能照搬 slash-command 语义。 |
| 必要性 / ROI | 有条件通过 | 4/5 | handoff 与 reviewer ROI 高；grilling ROI 高但要控制追问成本。 |
| 风险评估 | 有条件通过 | 3/5 | 方案识别了不直接照搬项，但对流程副作用、token 消耗、用户确认节奏、审查职责膨胀说明不足。 |
| 遗漏检查 | 有条件通过 | 3/5 | 漏掉了 `domain-modeling` / `codebase-design` / `diagnosing-bugs` / `to-prd → to-issues` 的部分高价值模式，至少应进入后续路线图。 |
| 优先级建议 | 有条件通过 | 4/5 | 三个动作都值得做，但顺序应调整：handoff 优先于 grilling；review 双轴应在工厂评审链路中先落地。 |

**最终评级：WARN / 有条件通过**  
**放行条件**：按本文第七节的优先级和实施步骤收敛范围，不直接照搬 mattpocock 的 Skill 文件和触发机制。

---

## 三、动作 1 审查：把 grilling 方法论写进 TPR Discovery

### 3.1 结论

**结论：有条件通过。**

将 grilling 的「一次一个问题 + 推荐答案 + 沿设计树追问」嵌入 TPR 的 DISCOVERY 阶段是合理的。TPR Framework 的 DISCOVERY 本来就是 T + P 阶段，目标包括识别核心假设、验证路径和用户确认；grilling 可以提升 DISCOVERY 对模糊需求的穿透力。

### 3.2 证据

- `tpr-framework/SKILL.md` 中 DISCOVERY 阶段产出为 `DISCOVERY.md`，认知重心是 `T + P`；DISCOVERY 完成条件包括“核心假设全部识别 + 至少 1 个验证路径 + 用户确认理解正确”。这与 grilling 的需求澄清定位一致。
- `04-Productivity Skills 评估.md` 对 grilling 的评价指出，其关键机制是“一次只问一个问题”“为每个问题提供推荐答案”“如果能通过探索代码库回答，就去探索代码库”。
- `07-企业适配建议.md` 将 grilling 列为高价值移植对象，称其为“追问式需求澄清的底层引擎”。

### 3.3 可行性

技术上可行，因为 TPR 是 Markdown Skill 指令体系，DISCOVERY 阶段可以增加一段流程规则，不需要新增运行时能力。OpenClaw 已支持 subagent、文件写入、reviewer 等机制，grilling 不依赖特殊工具。

但必须做三点裁剪：

1. **从无限追问改为有限追问**：每个 DISCOVERY 主题最多 3-5 个关键问题，避免无止境深入。
2. **从“每次只问一个问题”改为“复杂问题一次一问，简单信息可批量最多 3 问”**：否则与 agent-factory-sop S1 的“每次最多问 3 个问题”风格不一致，也会拖慢项目启动。
3. **必须产出结构化记录**：grilling 原版偏对话，不强制落盘；TPR 的红线是“没有记录没有发生”，因此每轮追问结果必须写入 `DISCOVERY.md` 的假设、风险、验证路径中。

### 3.4 必要性 / ROI

ROI 较高，尤其适用于：

- 用户初始问题模糊，只给方向不给边界；
- GRV 前需要识别隐藏约束；
- Battle 前需要先把争议点拆清楚；
- 业务/战略/产品方案容易被“听起来合理”的假设带偏。

但它不应该成为所有 TPR 的强制长流程。TPR 已有“简单问题不用全流程”“纯执行任务直接执行”的排除规则；grilling 也应只在 DISCOVERY 中触发，而非全阶段常驻。

### 3.5 风险与副作用

| 风险 | 影响 | 缓解 |
|---|---|---|
| 追问过度 | 用户疲劳，TPR 启动成本升高 | 设置问题预算；每轮只追问最高不确定性假设 |
| 推荐答案形成锚定 | 用户可能默认接受 Agent 的建议 | 推荐答案必须标注为“建议基线”，并提供“也可以反对”的提示 |
| 与主动推进风格冲突 | TPR 要求能推断意图时先给草案，grilling 可能过度等待用户 | 采用“先给草案，再追问关键缺口”的混合模式 |
| 记录缺失 | 追问结果留在聊天里，不进入 TPR 文件 | DISCOVERY 模板增加“追问记录 / 关键假设 / 用户确认”小节 |

### 3.6 建议改法

不要写成“使用 grilling”，而应写成 TPR 原生规则：

> **DISCOVERY Grilling Loop**：对每个高不确定性主题，Agent 先给出当前理解和推荐答案，再一次只追问一个阻塞性问题；若信息可通过文件、代码或知识库验证，则先验证再问用户；每轮追问必须更新 `DISCOVERY.md` 的假设、风险和验证路径。达到问题预算或用户确认后停止。

---

## 四、动作 2 审查：把 handoff 机制引入 Skill 工厂多 session 协作

### 4.1 结论

**结论：通过，且应作为最高优先级。**

这是三个动作中最必要、风险最低、收益最确定的一项。Agent Factory SOP 的 L2 流程从 S0 到 S8，包含需求澄清、需求固化、设计、开发、验证、发布、验收、归档；其中 S3 baseline review、S5 code review、S7 acceptance 都可能跨 session / subagent / reviewer 发生。如果没有标准化交接包，最容易出现“审查者不知道原始需求”“开发者不知道评审意见是否已修复”“发布者不知道测试基准”的断裂。

### 4.2 证据

- `agent-factory-sop/SKILL.md` 明确 L2 是 `S0 → S8` 的 Skill 产品生命周期，并且每步完成后必须用户确认才能进入下一步。
- 同文件 S3 要求 `design/DESIGN.md` 做 B 类方案评审；S5 要求硬门槛、用户本地测试和 C 类代码评审；S6/S7 又涉及版本、发布和验收。流程长、交接点多。
- `04-Productivity Skills 评估.md` 指出 handoff 的核心是“引用而非重复”“建议 Skill”“脱敏处理”，正适合降低长会话上下文衰减。
- `07-企业适配建议.md` 建议将 handoff 改造为通用版，输出目标回顾、已完成事项、关键决策、待办列表、推荐下一步，并存入企业知识库。

### 4.3 可行性

技术上完全可行。OpenClaw 已经具备：

- 文件系统作为阶段产物载体；
- subagent 编排与自动结果返回；
- Skill Workshop / reviewer 等生命周期工具；
- TPR 与 factory SOP 的“文件记录为事实源”原则。

因此不需要引入 mattpocock 的临时目录策略；应改造成 **工厂内部交接包**，写入项目工作区，例如：

```text
.factory/handoffs/
  S2-to-S3.md
  S3-review-to-S4.md
  S4-to-S5-review.md
  S5-to-S6-release.md
```

或在 Skill 项目目录下：

```text
design/HANDOFF.md
reviews/HANDOFF-FIXES.md
release/HANDOFF.md
```

### 4.4 必要性 / ROI

ROI 很高，原因：

1. **降低多 session 断裂**：尤其是开发 → 审查 → 修复 → 发布链路。
2. **提升 reviewer 质量**：reviewer 可以直接读取交接包知道审查基准。
3. **减少重复说明**：用户不必每次向新 Agent 重新解释背景。
4. **提升归档质量**：S8 归档可直接汇总 handoff 与决策记录。

### 4.5 风险与副作用

| 风险 | 影响 | 缓解 |
|---|---|---|
| handoff 变成重复文档 | 与 REQ、DESIGN、ReviewReport 内容重复，增加维护成本 | 强制“引用而非复制”：只写路径、状态、差异、未落盘信息 |
| 泄露敏感信息 | 交接包可能包含凭证、PII、商业机密 | 模板加入脱敏检查；禁止写 API Key、token、患者数据 |
| 状态源冲突 | handoff 与 DESIGN / REQ 表述不一致 | 规定 REQ/DESIGN/ReviewReport 是事实源，handoff 只是索引和下一步说明 |
| 流程负担 | 每步都写 handoff 可能拖慢 | 只在跨角色、跨 session、跨审查关卡时强制写 |

### 4.6 建议改法

在 agent-factory-sop 中增加“阶段交接包”规则：

> 当工作从一个角色 / session / 审查关卡转移到另一个角色 / session / 审查关卡时，必须生成 `HANDOFF.md`。该文件只包含：目标、事实源路径、已完成事项、关键决策、未解决问题、下一角色任务、建议使用的 Skill、风险与脱敏确认。不得重复粘贴已有产物全文。

---

## 五、动作 3 审查：把 review 双轴模式升级 factory-reviewer

### 5.1 结论

**结论：有条件通过。**

方向正确，但当前理由“从单轴代码质量变双轴”不够准确。factory-reviewer 当前已经在 AGENTS.md 中定义了 A/B/C/D/E 五类审查对象，并不是单纯代码质量审查；真正问题是 **C 类代码 / 脚本审查维度中，没有把“需求符合度”作为强制维度**。

### 5.2 证据

- `AGENTS.md` 中 C 类代码 / 脚本维度包括：正确性、安全性、健壮性、可维护性、测试覆盖。
- 同一文件 E 类交付验收才包含“功能符合需求”“质量门控全过”“文档完整”“版本号一致”“安装与使用说明可用”。
- `agent-factory-sop/SKILL.md` S5 的 C 类评审发生在发布前，通常应对照 `REQ-01.md`、`design/DESIGN.md` 和用户测试结果审查；如果 C 类只审代码质量，可能漏掉“实现质量好但不是用户要的东西”。
- `07-企业适配建议.md` 将 mattpocock 的 `review` 评价为“规范 + 需求”的双轴评审，适合改造为企业代码审查流程。

### 5.3 可行性

可行。只需更新 factory-reviewer 的审查模板和调用任务要求，不需要改变工具能力。关键是：reviewer 在审 C 类代码时必须能读到“需求基准”。

建议将 C 类代码审查从 5 维升级为 6 维：

1. **需求符合度**：是否实现 REQ / GRV / DESIGN / issue 中承诺的行为；是否遗漏非目标边界；是否引入未授权范围。
2. 正确性。
3. 安全性。
4. 健壮性。
5. 可维护性。
6. 测试覆盖。

同时，在 JSON schema 中增加：

```json
"requirement_alignment": {
  "score": 1,
  "basis_files": [],
  "matched_requirements": [],
  "missing_requirements": [],
  "scope_creep": []
}
```

### 5.4 必要性 / ROI

ROI 高。原因是 AI 编码最大的失败模式之一不是“代码写不出来”，而是“写出了质量不错但偏离需求的代码”。双轴 review 可以直接拦截：

- 漏做验收标准；
- 做了未授权扩展；
- 修改破坏既有边界；
- 测试覆盖了实现细节但没覆盖用户行为；
- 代码通过但无法发布。

### 5.5 风险与副作用

| 风险 | 影响 | 缓解 |
|---|---|---|
| reviewer 职责膨胀 | 每次代码审查都变成完整验收，成本上升 | 按风险级别启用：工厂 S5 强制，日常小改可 quick |
| 需求基准不清 | reviewer 无法判断符合度 | 调用 reviewer 时必须传 `REQ-01.md` / `DESIGN.md` / issue / GRV 路径 |
| 与 E 类验收重复 | C 类和 E 类都看需求 | C 类看“代码是否实现需求”；E 类看“交付物是否可安装/发布/使用” |
| 过度阻塞 | 小偏差都 fail | 严重度分级：阻塞只限核心需求缺失、安全问题、验收标准失败 |

### 5.6 建议改法

factory-reviewer 增加如下规则：

> C 类代码审查默认采用“双轴”：Implementation Quality（实现质量）+ Requirement Alignment（需求符合度）。若调用方未提供需求基准文件，reviewer 必须将需求符合度标为“无法判断”，并降低 confidence；在 agent-factory-sop S5 中，缺少需求基准应视为调用错误。

---

## 六、遗漏检查：是否漏掉高价值 Skill / 设计模式

当前三个动作抓住了 mattpocock/skills 的三块高价值能力，但仍有若干遗漏。建议分为“应立即纳入路线图”和“暂缓观察”。

### 6.1 应纳入路线图的遗漏

#### 1. domain-modeling：不应完全被 MEMORY.md 替代

原方案认为 CONTEXT.md 领域语言“已有 MEMORY.md 体系，因此不直接照搬”。这个判断只对一半。

MEMORY.md / wiki 更像跨会话长期记忆；mattpocock 的 CONTEXT.md 更像**项目内的领域术语表与禁用替代词**。两者作用不同：

- MEMORY.md：记录偏好、历史事实、跨项目长期记忆；
- CONTEXT.md：约束当前项目的术语、边界、命名一致性；
- ADR：记录难逆转、未来会困惑、有真实权衡的决策。

建议不照搬 `CONTEXT.md` 文件名，但把“项目术语表 + 禁用替代词 + 轻量 ADR”纳入 TPR / Agent Factory 的可选产物。尤其在 ERP、医药、投研、复杂产品方案中价值很高。

#### 2. codebase-design：适合成为架构评审词汇表

`07-企业适配建议.md` 将 codebase-design 列为高价值，并指出其 deep module、seam、adapter、leverage 等词汇适合 ERP/BP 模块边界讨论。当前三动作没有覆盖这部分。

建议后续为 OpenClaw 增加“架构词汇参考”而不是完整 Skill：用于 GRV 技术方案、B 类方案评审和代码重构评审。

#### 3. diagnosing-bugs：适合日常项目开发

用户定义的三条主线中第三条是“日常项目开发 — 编码、调试、架构重构”。当前引进动作偏 TPR 和工厂，对日常调试没有覆盖。

`03-Engineering 质量与架构评估.md` 对 diagnosing-bugs 评价很高，尤其是 feedback loop、假设排序、DEBUG 标签清理。这对 OpenClaw 日常调试非常直接。

建议后续增加“结构化调试循环”到日常开发 Skill 或 code-agent orchestration 中。

#### 4. to-prd / to-issues 的垂直切片拆分

当前方案把 tdd vertical slice 归为“仅对编码有用”，这个判断偏窄。`to-issues` 的垂直切片不仅是编码策略，也是项目拆解策略：每个切片 narrow but complete、可独立验证。这与 TPR 的 Implementation 阶段和 Agent Factory 的验收标准可以结合。

建议不照搬 GitHub issue 发布机制，但把“垂直切片拆解原则”纳入：

- GRV 的举措拆解；
- DESIGN 的里程碑；
- Agent Factory S4/S5 的开发与测试计划。

### 6.2 可暂缓的内容

| Skill / 模式 | 暂缓原因 |
|---|---|
| writing-great-skills 的 invocation 机制 | OpenClaw 已有 Skill 列表注入、版本哈希和按需读取；可吸收理论，不必改运行时。 |
| ask-matt router | OpenClaw 技能已有系统级路由；当用户侧 Skill 数量进一步膨胀时再考虑“人工入口导航”。 |
| teach | 价值高但不是当前三条主线核心，适合企业培训或个人学习场景后续单独评估。 |
| improve-codebase-architecture HTML 报告 | 架构评审价值高，但依赖代码扫描和可视化，实施成本高于前三项。 |
| loop-me | 自主循环风险高，需要安全边界，不建议当前引入。 |

---

## 七、最终引进 / 改造方案

### 总体原则

1. **取方法论，不搬运行时**：不复制 mattpocock 的 slash-command、plugin.json 或安装机制。
2. **嵌入 OpenClaw 现有事实源**：TPR 以 DISCOVERY/GRV/BATTLE 文件为准；Factory 以 REQ/DESIGN/ReviewReport/HANDOFF 为准。
3. **所有新机制必须有停止条件**：追问、交接、审查都要避免无限扩张。
4. **先改基础设施，后改交互体验**：handoff 和 reviewer 优先，grilling 试点后推广。

---

## 八、优先级与实施步骤

### P0：建立 Agent Factory Handoff 标准（最高优先级）

**目标**：解决 Skill 工厂跨阶段、跨 session、跨 reviewer 的上下文断裂。

**改动位置**：`agent-factory-sop`。

**实施步骤**：

1. 在 SOP 中新增“阶段交接包”章节。
2. 定义 `HANDOFF.md` 模板：
   - 当前阶段与下一阶段；
   - 目标摘要；
   - 事实源路径（REQ / DESIGN / ReviewReport / 测试记录）；
   - 已完成事项；
   - 关键决策；
   - 未解决问题；
   - 下一角色任务；
   - 建议使用的 Skill / reviewer 类型；
   - 脱敏确认。
3. 规定强制生成场景：
   - S2 → S3；
   - S3 baseline review → S4；
   - S4 → S5 code review；
   - S5 conditional pass 修复后 → 复审；
   - S6 → S7 验收；
   - 任意跨 session 继续。
4. 规定禁止项：不得复制已有文档全文；不得写入凭证、PII、患者数据；不得把 handoff 当事实源覆盖 REQ/DESIGN。

**验收标准**：

- 任一 reviewer 可以只读 `HANDOFF.md + 事实源路径` 理解审查基准；
- S8 归档能直接引用 handoff 还原阶段流转；
- 不出现同一结论在 REQ/DESIGN/HANDOFF 中三处不一致的情况。

---

### P1：升级 factory-reviewer 为需求符合度 + 实现质量双轴（第二优先级）

**目标**：避免“代码质量合格但需求偏离”的漏审。

**改动位置**：`factory-reviewer` 的 C 类代码审查流程与输出 schema。

**实施步骤**：

1. 在 C 类审查维度中新增“需求符合度”。
2. reviewer task 调用规范中要求传入需求基准：
   - `REQ-01.md`；
   - `design/DESIGN.md`；
   - GRV / issue / 用户验收标准；
   - 相关 handoff。
3. Markdown 报告新增“双轴评分”：
   - Requirement Alignment；
   - Implementation Quality。
4. JSON 报告新增字段：
   - `basis_files`；
   - `matched_requirements`；
   - `missing_requirements`；
   - `scope_creep`；
   - `untestable_requirements`。
5. 更新 severity 规则：
   - 核心需求缺失 → major / blocker；
   - 未授权扩展影响边界 → major；
   - 需求基准缺失 → confidence 降低，工厂流程中视为调用错误。

**验收标准**：

- C 类 review 能明确回答“是否实现了用户要的东西”；
- E 类验收与 C 类审查边界清晰；
- Agent Factory S5 的 review 结果可直接指导修复。

---

### P2：将 Grilling Loop 裁剪后嵌入 TPR Discovery（第三优先级）

**目标**：提高 TPR DISCOVERY 的追问深度，同时不破坏阶段节奏。

**改动位置**：`tpr-framework` 的 DISCOVERY 规则与模板。

**实施步骤**：

1. 在 DISCOVERY 阶段增加“高不确定性假设追问”流程。
2. 对每个主题执行：
   - 写出当前理解；
   - 给出推荐答案；
   - 只问一个阻塞性问题；
   - 若可通过文件/代码/知识库验证，则先查证；
   - 更新 DISCOVERY 记录。
3. 增加停止条件：
   - 核心假设已识别；
   - 至少 1 个验证路径；
   - 用户确认理解正确；
   - 达到问题预算；
   - 用户要求停止。
4. 增加反锚定提示：推荐答案只是基线，不代表最终判断。
5. 对简单任务、紧急救火、纯执行任务默认不启用。

**验收标准**：

- DISCOVERY.md 中能看到假设、问题、推荐答案、用户确认、验证路径；
- 用户交互轮次没有显著增加到不可接受；
- GRV 阶段的返工率降低。

---

### P3：后续路线图（不纳入本轮三动作）

| 后续项 | 建议动作 | 优先级 |
|---|---|---|
| 项目术语表 / 轻量 ADR | 在 TPR 和 Agent Factory 中增加可选 `GLOSSARY.md` / ADR 机制，不替代 MEMORY.md | 中 |
| codebase-design 词汇表 | 做成 reviewer / GRV 技术方案的参考词汇，不做强制流程 | 中 |
| structured debugging | 把 diagnosing-bugs 的 feedback loop、假设排序、DEBUG 标签引入日常开发 | 中高 |
| vertical slice 拆解 | 把 to-issues 的 narrow but complete 原则引入 Implementation 计划 | 中 |
| Router Skill | 当 OpenClaw 用户可见 Skill 过载时，再引入统一导航入口 | 低 |

---

## 九、问题清单

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|---|---|---|---|---|---|---|
| F001 | major | 优先级 | 三动作总体方案 | 当前方案未明确实施顺序，容易先做交互型 grilling，反而延迟基础设施收益 | Agent Factory SOP 的 S0-S8 与多审查关卡显示 handoff 是最迫切断点 | 调整为 P0 handoff、P1 reviewer、P2 grilling |
| F002 | major | 表述准确性 | 动作 3 | “factory-reviewer 从单轴变双轴”表述不准；现有 reviewer 已覆盖 A/B/C/D/E 多类 | AGENTS.md 已列出五类审查对象；C 类缺需求符合度 | 改成“C 类代码审查增加需求符合度轴” |
| F003 | major | 流程风险 | 动作 1 | grilling 原样引入可能造成无限追问和用户疲劳 | grilling 原版缺少明确终止条件；TPR 有阶段停止规则 | 加问题预算、停止条件、记录落盘 |
| F004 | minor | 遗漏 | 不直接照搬项 | CONTEXT.md 被简单归因为 MEMORY.md 已覆盖，忽略项目术语表的局部价值 | 06 文档说明 CONTEXT.md 是项目级统一语言，MEMORY.md 是 OpenClaw 长期记忆 | 引入可选项目术语表，不替代 MEMORY.md |
| F005 | minor | 遗漏 | 日常项目开发 | 三动作未覆盖 diagnosing-bugs 结构化调试模式 | 03 文档对 diagnosing-bugs 评价高，且用户主线包含编码调试 | 放入 P3 后续路线图 |
| F006 | minor | 风险 | 动作 2 | handoff 如果无模板，可能变成冗余总结 | 04 文档指出 handoff 原版缺少格式模板 | 在 SOP 中定义强模板和“引用而非复制”规则 |

---

## 十、最终建议一句话

**不要把 mattpocock/skills 当作可安装包引入 OpenClaw；应把它当作一组工程纪律原语：先用 handoff 修补工厂链路断点，再用双轴 reviewer 守住需求符合度，最后把 grilling 作为有限追问循环嵌入 TPR Discovery。**
