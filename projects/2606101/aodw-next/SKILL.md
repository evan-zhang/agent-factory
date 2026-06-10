---
name: aodw
version: "0.5.1"
description: AODW (AI-Orchestrated Development Workflow) — 完整的 AI 协作开发工作流体系。当用户涉及以下任意场景时必须加载本 skill：新建 RT / 需求 / 功能 / 任务、立项、分支管理、worktree 创建与清理、Spec-Full / Spec-Lite 开发流程、代码提交与合并、RT 审查与完成、AODW 规范检查。关键触发词：RT、立项、新需求、开发任务、feature 分支、worktree、spec、intake、决策、实现、验收。本 skill 管理从立项到合并的完整开发生命周期。
---

# AODW — AI 编排开发工作流 (v0.5.1)

用 **RT（Request Ticket）** 追踪每个开发任务，通过文档驱动、分支隔离、Gate 检查点和确认门控执行。

## 加载顺序（渐进式披露，优先读 summary）

1. **总是加载**：`01-core/aodw-constitution-summary.md`（最高行为准则）
2. **按场景追加**（优先读 `*-summary.md`，需要细节时再读完整版）：

| 场景 | 追加加载 |
|------|---------|
| 立项 / 创建 RT | `rt-manager-summary.md` + `ai-interaction-rules-summary.md` + `rt-id-generation-rules.md` |
| Spec-Lite 执行 | `spec-lite-profile-summary.md` + `git-discipline-summary.md` |
| Spec-Full 执行 | `spec-full-profile-summary.md` + `ai-coding-rules.md`（按技术栈） |
| Git 操作 / 合并 | `git-discipline.md`（完整版） |
| 审计 | `04-auditors/aodw-requirement-auditor-rules.md` |
| 交叉审核（Spec-Full） | `04-auditors/cross-model-review.md` |
| 知识同步 | `ai-knowledge-rules-summary.md` |

## 核心概念

- **RT 生命周期**：`created → intaking → decided → in-progress → reviewing → done`
- **一个 RT = 一个 Worktree = 一个 Feature 分支**（`feature/RT-XXX-name`）
- **Spec-Full**：跨模块/数据模型/API 变更/高风险 → 完整 spec+plan+审计
- **Spec-Lite**：单模块/bug 修复/低风险 → 单文件 `rt-lite.md`
- **确认门控**：commit/merge/push/worktree 操作前必须向用户确认
- **规则索引**：详见 `manifest.yaml`
- **新项目安装**：详见 `README.md`
