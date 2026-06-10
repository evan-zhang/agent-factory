---
id: aodw-spec-full
version: 2.0.0
category: aodw/execution-profile
trigger: "当 RT-Manager 决策 profile=Spec-Full 时自动加载"
replaces: "spec-full-profile.md (v1.x，无 Skill 封装版)"
description: >
  AODW Spec-Full 执行 Skill。适用于复杂功能、高风险改动、多模块变更、数据模型或 API 变更。
  核心变化（v2.0）：Skill 化封装，审计器统一调用 aodw-auditor Skill（mode 参数区分阶段）。
gate_hooks:
  - gate: 1
    name: 需求确认
    action: "展示 spec.md 摘要，等待用户确认"
  - gate: 3
    name: 计划批准
    action: "展示 plan.md 摘要，等待用户批准"
  - gate: 4
    name: 提交确认
    action: "展示 git diff，等待用户确认提交"
  - gate: 5
    name: 完成确认
    action: "提供收尾脚本，等待最终确认"
token_budget: "~10KB (自身完整流程文档）"
---

# Spec-Full Profile Specification

**适用场景**：新功能、大范围改动、跨模块影响、数据模型或 API 变更、高风险改动。

**不适用场景**：Bug 修复、单模块小改进、UI 微调（应使用 Spec-Lite）。

---

## 1. 文件结构

在 `RT/RT-XXX/` 目录下：

```
RT/RT-XXX/
  spec.md         ← 完整需求说明
  plan.md         ← 技术实现方案
  data-model.md   ← 实体与关系
  impact.md       ← 影响分析
  tests.md        ← 验证计划
  changelog.md    ← 行为变更总结
```

---

## 2. 流程概览

```
Intake → Spec/Plan (AI 生成) → 计划批准 → 实现 → 审计 → 验证 → 完成 → Git 提交
```

---

## 3. 核心 Spec (spec.md)

AI 根据用户描述和澄清问题自动生成，必须包含：

### 3.1 背景与动机
- 为什么需要这个特性
- 业务目标是什么

### 3.2 目标与非目标
- 明确列出本次 RT 的目标范围
- 明确哪些是**不处理**的内容

### 3.3 技术约束
- 性能要求
- 兼容性要求
- 安全要求

### 3.4 验收标准
- 功能验收标准
- 代码质量验收标准
- 测试覆盖率要求

---

## 4. 技术方案 (plan.md)

AI 生成的技术实现方案，必须包含：

### 4.1 技术选择
- 使用的框架、库、工具
- 技术选择的理由

### 4.2 架构设计
- 组件关系图（可选，用 Mermaid 或 ASCII）
- 分层设计
- 数据流设计

### 4.3 实现步骤
按优先级排列的具体步骤
- 每个步骤包含：子任务、负责人（可选）、预计时间

### 4.5 数据模型变更（如涉及）
- Schema 变更说明
- 迁移策略

### 4.6 API 变更（如涉及）
- 新增端点
- 修改的端点
- 废弃的端点

---

## 5. 影响分析 (impact.md)

必须分析对现有功能的影响，包括：

### 5.1 兼容性影响
- 向后兼容的保证
- 迁移需求

### 5.2 性能影响
- 预期性能变化
- 优化措施

### 5.3 安全影响
- 安全风险评估
- 缓解措施

### 5.4 依赖影响
- 第三方依赖的变更
- 内部模块的依赖变更

---

## 6. 测试计划 (tests.md)

验证规格和方案是否实现正确：

### 6.1 单元测试
- 新代码必须有单元测试
- 测试覆盖率要求

### 6.2 集成测试
- API 集成测试
- 端到端测试

### 6.3 手动测试场景
- 关键用户路径测试
- 边界条件测试

---

## 7. 行为变更总结 (changelog.md)

记录本次 RT 的所有变更，格式：

### 7.1 功能变更
- 新增功能
- 功能改进

### 7.2 Bug 修复
- 修复的 Bug 编号
- 修复描述

### 7.3 代码重构
- 重构的模块
- 重构原因

### 7.4 配置变更
- 配置文件变更
- 环境变量变更

---

## 8. 不可破坏边界 (invariants.md)

必须明确不可破坏的原则和边界：

### 8.1 API 契约
- 不得破坏现有 API 契约
- 向后兼容的保证

### 8.2 数据完整性
- 不得破坏数据完整性
- 迁移过程中的数据保护

### 8.3 性能指标
- 不得降低关键性能指标
- 性能回退策略

---

## 9. Gate 检查点（含 Claude Code 独立审查）

每个 Gate 在向用户展示前，必须先由 **Claude Code 独立审查**，审查报告连同内容一起交给用户最终决策。

| Gate | 检查点 | Claude Code 审查内容 | 向用户展示 |
|------|---------|---------------------|------------|
| 1 | 需求确认 | 需求完整性、验收标准可验证性、遗漏场景 | spec.md 摘要 + 审查报告 |
| 3 | 计划批准 | 方案合理性、风险评估充分性、与约束一致性 | plan.md 摘要 + 审查报告 |
| 4 | 提交确认 | 逻辑正确性、代码质量、安全性、与方案一致性 | git diff + 审查报告 |
| 5 | 完成确认 | 验证计划充分性、变更记录准确性、风险确认 | 完成摘要 + 审查报告 |

### Claude Code 审查调用方式

```bash
# Gate 1: 需求审查
exec background:true workdir:<项目目录> \
  command:"claude --print --permission-mode bypassPermissions '审查 spec.md 需求说明，关注完整性/验收标准/遗漏场景，输出报告到 /tmp/claude-review-g1-report.md'" \
  timeout:300

# Gate 3: 方案审查
exec background:true workdir:<项目目录> \
  command:"claude --print --permission-mode bypassPermissions '审查 plan.md 技术方案，关注合理性/风险评估/与约束一致性，输出报告到 /tmp/claude-review-g3-report.md'" \
  timeout:300

# Gate 4: 代码审查
exec background:true workdir:<项目目录> \
  command:"claude --print --permission-mode bypassPermissions '审查 git diff 代码变更，关注逻辑正确性/代码质量/安全性/与方案一致性，输出报告到 /tmp/claude-review-g4-report.md'" \
  timeout:300

# Gate 5: 验收审查
exec background:true workdir:<项目目录> \
  command:"claude --print --permission-mode bypassPermissions '审查验证计划和变更记录，关注测试充分性/变更准确性/风险确认，输出报告到 /tmp/claude-review-g5-report.md'" \
  timeout:300
```

### 审查报告格式

Claude Code 审查报告必须包含：
- **Critical**：必须修复才能继续
- **Important**：建议修复
- **Minor**：可选优化

---

## 10. 审计要求

**必须审计**（使用 `aodw-requirement-auditor-rules.md`）：
- Spec 完整性
- Plan 可行性
- Impact 分析充分性

**必须通过审计后才能**：
- 开始代码实现
- 提交到 feature 分支

---

## 11. 文档同步

完成后必须：
- 更新模块索引（`modules-index.yaml`）
- 更新相关模块 README
- 记录新 API 到文档

---

## 12. 引用规范

必须与以下规范配合：
- `aodw-next/03-standards/ai-coding-rules.md`（编码规范）
- `aodw-next/01-core/git-discipline.md`（Git 规范）
- 对应技术栈的编码规范文件

