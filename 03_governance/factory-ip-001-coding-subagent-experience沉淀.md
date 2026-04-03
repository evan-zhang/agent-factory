# Factory Improvement Proposal #001 (Revised)

**编号**：FIP-001-R
**标题**：Sub-Agent 过程经验沉淀机制
**类型**：执行层流程改进
**日期**：2026-04-03
**状态**：ACCEPTED
**提案人**：ops-agent（原始）→ Orchestrator + 独立架构评审（修订）
**修订原因**：三方 PK 后统一方案

---

## 现状问题

- Sub-agent 完成任务即销毁，过程中积累的经验全部丢失
- 下一次同类任务从头摸索，效率低且质量不稳定
- 跨阶段信息断裂：Agent A 在设计阶段发现的约束，Agent B 在开发阶段不知道

## 修订后方案

### 载体：项目级累积式 `EXPERIENCE.md`

每个项目维护一个 `projects/{project-id}/EXPERIENCE.md`，追加式累积，不按任务拆文件。

### 格式（每条 ≥100 字）

```markdown
## [日期] [Sub-Agent类型] [任务摘要]
- 难点：
- 决策：(必须含"没选X是因为Y"的否定式记录)
- 前车之鉴：
- 上下文：(项目约束、技术栈版本等关键前提)
```

### 覆盖范围：所有 sub-agent

不区分 coding/interview/validator/generator/assembler/reviewer。
经验不分类型，决策过程都有价值。

### 强制程度

| 条件 | 要求 |
|------|------|
| 任务执行 >10 分钟，或产生非平凡决策 | **强制写入** |
| 任务简单、决策直观 | 鼓励但不强制 |

### 读取规则（V1 最简）

后续 sub-agent 启动时：
1. 检查当前项目是否有 `EXPERIENCE.md`
2. 如有，读取最近 5 个条目
3. 同类型 sub-agent 的条目优先读取

不建索引、不建检索系统、不建向量库。

### 质量控制

- 每条最少 100 字（防敷衍）
- "决策"字段必须包含否定式记录（"没选X是因为Y"）
- 不做 Validator 审核，靠格式约束和使用反馈自然筛选

### 留给后续迭代的

- 检索/发现机制（V2）
- 经验过期/清理规则（V2）
- 跨项目经验复用（V3）
- 与现有知识体系的整合（自然演进）

## 执行步骤

1. ✅ Evan 确认
2. 更新 coding-agent task 模板，加入 EXPERIENCE.md 写入要求
3. 更新 Orchestrator AGENTS.md，所有 sub-agent spawn 时传入读取指令
4. 下次 sub-agent 任务时验证

## 评审记录

- ops-agent 原始提案 → Orchestrator 五点评审 → 独立架构评审 PK → 统一方案
- 核心修订：范围从 coding 扩大到全 sub-agent，载体从碎片文件改为累积式，检索从"引用前3个"改为"读最近5条"
