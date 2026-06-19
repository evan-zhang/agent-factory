# Sub-Agent 模板参考

## 模板清单（`specs/agents/`）

| 模板 | 文件 | 适用场景 |
|------|------|----------|
| Interview | interview.md | L2 S1-S2：需求引导、业务摘要结构化 |
| Analyst | analyst.md | L2 S3：文档解析、能力盘点、缺口分析 |
| Generator | generator.md | L2 S3：生成 Agent/Skill/API 规范文档 |
| Validator | validator.md | 每步完成后：质量门控 PASS/FAIL |
| Assembler | assembler.md | L2 S5-S6：组装 workspace、追溯矩阵 |
| Reviewer | reviewer.md | 独立外部评审（审计独占） |
| Governance Officer | governance-officer.md | 治理合规检查 |
| Orchestrator | link-archivist-orchestrator.md | Depth 1：编排链接归档 Phase 1-5 |
| Worker | link-archivist-worker.md | Depth 2 叶子：抓取/调研/归档 |

## 可用 Skill

| Skill | 项目 | 用途 |
|-------|------|------|
| tpr-framework | 2604011 | TPR 三省制工作流 |
| coding-agent | — | 代码任务委托（本地） |

工厂不引用第三方 Skill，所有基础能力自研。新增时更新 `_runtime/governance/factory-task-index.md`。
