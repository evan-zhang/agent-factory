# tpr-framework 设计档案

## 产品概述
- **Slug**：tpr-framework
- **当前版本**：v1.0.1
- **定位**：工厂多 Agent 协作工作流框架，强制角色边界，防止调度员越界执行

## 核心设计决策

### D-01：为什么要三省分离
AI 在单 Agent 场景下很容易"自问自答"——起草了 GRV 又自己审查，立场天然趋同。三省制强制把起草/审查/执行拆给不同 sub-agent，批判性审查才有意义。

### D-02：Battle 为什么必须用真实 sub-agent
自己扮演 Menxi 和 Shangshu 时，两个角色共享同一个上下文窗口，审查会无意识偏向起草立场。真实 sub-agent 有独立上下文，立场更中立。

### D-03：Orchestrator "Brain Only, No Hands" 原则
一旦 Orchestrator 开始亲手执行，角色边界彻底崩溃，后续所有角色分工都名存实亡。429/失败 → 重派，不自己动手。

## 版本历史
| 版本 | 日期 | 摘要 |
|------|------|------|
| v1.0.0 | 2026-03 | 初版：四阶段流程 + 三省角色表 + Critical Rules |
| v1.0.1 | 2026-04-01 | SKILL.md 重构（189→57行），新增 references/，补 design/ 档案 |
