# Battle 机制与状态机

> 本文档只回答一个问题：**Battle 怎么跑。**
> 包含状态机定义、规则、触发条件和 Battle 专属红线。

---

## Battle 的认知定位

Battle 是 TPR 中 **Probe + Review 强化** 的制度化实现。

- **审查层**：承担 Probe 角色，主动挑战、证伪、补证，暴露方案盲点
- **执行层**：接受挑战，回应、修订，用事实答复
- **编排者**：维护流程节奏，不参与 Battle 内容

Battle 的目标不是"通不通过"，而是"有没有看到盲区"。

### Battle 中的 Best-Minds 专家思维

**审查层必须以该领域最挑剔的评审者身份进行挑战。** 不是泛泛找茬，而是以专家的 rigor 审视：
- 架构设计是否经得起同行评审？
- 方案是否遗漏了该领域已知的常见陷阱？
- 是否与业界最佳实践一致？如不一致，偏离的理由是否充分？
- 是否有该领域经典论文/案例可以佐证或反驳？

**执行层回应时也必须以专家身份。** 不是"我改了"，而是"基于 XX 原理/XX 实践，修订如下，理由是..."

---

## Battle 触发条件

以下场景需要进入 Battle：

| # | 场景 | 说明 |
|---|------|------|
| 1 | GRV 起草完成 | 策划层 → 审查层审 GRV |
| 2 | 方案制定完成 | 执行层方案 → 审查层审方案（白头 Battle）|
| 3 | 执行成果完成 | 执行层执行结果 → 审查层审核 |

**不需要 Battle 的场景**：
- 极简模式项目（项目分级为 Simple）跳过 Battle
- DISCOVERY 阶段不需要 Battle

---

## Battle 状态机

```
GRV_DRAFT
    ↓ 提交审查
AUDITOR_REVIEWING
    ↓ 审查层给出结论
    ├── APPROVE → GRV_APPROVED
    ├── CONDITIONAL → PENDING_APPROVAL（需甲方介入）
    └── REJECT → EXECUTOR_REVISING

EXECUTOR_REVISING（对应轮次 +1）
    ↓ 修订完成
AUDITOR_REVIEWING（重新审核）

若3轮内无法达成一致
    → 编排者汇总争议提交甲方裁决
```

---

## 编排者行为约束

| 当前状态 | 编排者禁止行为 |
|---------|--------------|
| AUDITOR_REVIEWING | 禁止向甲方汇报审查层结论 |
| EXECUTOR_REVISING | 禁止跳过执行层修订直接汇报 |
| GRV_APPROVED | 才能向甲方汇报 Battle 结果 |

**REJECT 处理流程**：审查层 REJECT 后，编排者不得在执行层完成修订并提交审查层重审之前，向甲方汇报审查层的结论。必须等待完整的"修订 → 重审"循环完成。

---

## 并行限制

审查层和执行层 **不得并行运行**，必须串行：

1. 审查层先审 → 出结论
2. 若 REJECT → 执行层修订（不并行）
3. 执行层修订完成 → 提交审查层重审
4. 重复直到 APPROVE 或达轮次上限

---

## Battle 规则

### 轮次限制

- 最多 3 轮 Battle
- 3 轮内无法达成一致 → 汇总争议点交甲方决策
- 甲方决定：继续 Battle 3 轮，或强制推进

### 审查层行为规范

作为 Probe 的制度化承担者，审查层在 Battle 中必须严格执行**主客观分流审查 (Objective vs Strategic Judgement)**：

1. **客观类错误（确定性 Issue）**：如接口报错、交付物缺失、格式违背模板要求。查出此类问题直接将其记入项目根目录 `issues.md` 待办池并给执行层抛出 REJECT 自动发回重写，**严禁将此类琐碎错误发给甲方请示**。
2. **主观类争议（方向性 Issue）**：如模型选型可能超支、核心架构过于超前。只有这类依靠直觉经验的争议，才允许输出在 BATTLE 审查报告中，并引发甲方的介入裁定。
3. **提出 3-5 个实质性异议**，不是仅做拼写检查的形式审查。
4. **每个异议必须**：引用具体章节、说明为什么有问题、提出具体修改建议。
5. **给出明确结论**：APPROVE / REJECT / CONDITIONAL。
6. **不做和稀泥式审查** — "总体不错但有些地方可以改进"不算审查，必须非黑即白。
7. **领域认知完整性审查**：
   - GRV 是否体现了领域共识对约束条件的影响？
   - GRV 的风险章节是否覆盖了已知分歧？
   - 对每个分歧的立场选择是否有充分理由？
   - 分歧是否是真正的分歧（而非稻草人）？
   - 如发现策划层遗漏的重要分歧，应补充并要求策划层回应
   - **不强求补充数量**——如果策划层已覆盖所有重要分歧，无需额外编造

### 执行层行为规范

1. **逐条回应审查层异议**：明确接受/拒绝，给出理由
2. **接受的修改必须体现在修订版 GRV 中**
3. **拒绝的理由必须有事实/证据支撑**

### CONDITIONAL 处理

审查层给出 CONDITIONAL 时：
- 进入 PENDING_APPROVAL 状态
- 编排者将条件清单发给甲方
- 甲方决定：接受条件继续推进，或要求修订

---

## 用户介入条件

以下情况必须通知用户介入：

| 条件 | 用户行为 |
|------|---------|
| Battle 3 轮未达成一致 | 决定继续 Battle 或强制推进 |
| 审查层给出 CONDITIONAL | 决定接受条件或要求修订 |
| GRV 通过 Battle | 做最终确认 |
| 执行层执行完成 | 确认或打回 |

---

## Battle 专属红线（Layer 3）

| # | 规则 |
|---|------|
| B1 | 审查层 REJECT 后，编排者不得在修订-重审循环完成前向甲方汇报 |
| B2 | 审查层和执行层不得并行运行，必须串行 |
| B3 | 最多 3 轮，超过交甲方裁决 |
| B4 | CONDITIONAL 需甲方介入决策 |
| B5 | 只有 GRV_APPROVED 后才能向甲方汇报 Battle 结果 |

---

## Sub-agent 派遣模板

### 审查层（审查方）

```
task: You are 审查侧 (Auditor), the critical reviewer in a TPR Battle.
Your role is Probe: actively challenge assumptions, find evidence gaps, expose blind spots.

Review the GRV document at {project}/GRV.md.
Raise 3-5 substantive objections. For each:
- Cite the specific GRV section
- Explain why it is problematic
- Propose a concrete fix

After presenting objections, report your verdict: APPROVE / REJECT / CONDITIONAL.
Write your review to {project}/battle/BATTLE-R{round}-AUDITOR.md
```

### 执行层（应答方）

```
task: You are 执行侧 (Executor), the implementer and defender in a TPR Battle.
The GRV is at {project}/GRV.md.
Auditor has raised these objections (read {project}/battle/BATTLE-R{round}-AUDITOR.md).

Respond to each objection with:
- Accept (with what will change) or Reject (with evidence-based rationale)

Write your response to {project}/battle/BATTLE-R{round}-EXECUTOR.md
If you accepted changes, also update GRV.md accordingly.
```

---

*版本：2.2.0*
*更新：2026-05-13*
