# tpr-framework Discussion Log

## 2026-04-01 — 质检驱动重构

**背景**：xgjk-skill-auditor 审计 D1 得 4/10（189行超标），D3 大量 NEVER 无解释，D5 design/ 缺失。

**决策**：
- Bindings Management + Sub-agent Spawning 两章推入 references/
- Critical Rules 补"为什么"说明
- 补建 design/ 档案
- 发布到 ClawHub（tpr-framework）

**产出**：SKILL.md 189→57行，references/ 新建 spawning-guide.md + bindings-guide.md
