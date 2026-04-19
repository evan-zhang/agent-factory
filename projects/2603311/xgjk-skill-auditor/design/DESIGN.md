# xgjk-skill-auditor 设计档案

## 核心定位

工厂专属 Skill 质检工具。对 Skill 进行 5 维度评分，给出 PASS/REVISE 判定 + 具体改进方向。

## 功能范围

- 发布前质检
- 修改后验证
- 安全合规扫描
- 生成评分报告（附 file:line 问题定位）

## Skill 类型

工作流类 — 多步骤评审流程，无外部 API 依赖

## 审核维度

| 维度 | 权重 | 说明 |
|------|------|------|
| D1 结构质量 | 20% | SKILL.md 行数、frontmatter、目录结构 |
| D2 触发质量 | 25% | description 触发词、覆盖度 |
| D3 内容质量 | 25% | 关键步骤完整性、示例质量 |
| D4 安全合规 | 15% | 凭证处理、敏感词扫描 |
| D5 发布合规 | 15% | slug、版本号、changelog |

## 判定规则

PASS：总分 ≥ 7.5 AND D4 ≥ 6
REVISE：否则

## 依赖资源

- `references/factory-weights.md` — Skill 类型分类 + 权重矩阵
- `references/scoring-rubric.md` — D1-D5 详细 checklist
- `references/security-patterns.md` — CRITICAL/严重/轻微 grep pattern

---

*创建时间：2026-04-05*
