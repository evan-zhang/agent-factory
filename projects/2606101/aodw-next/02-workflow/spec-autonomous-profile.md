---
id: aodw-spec-autonomous
version: 1.0.0
category: aodw/execution-profile
trigger: "当 RT-Manager 决策 profile=spec-autonomous 时自动加载"
description: >
  AODW 自主执行模式。AI 全程自主闭环，仅在启动时与用户确认目标，
  执行过程中不需人工干预。通过 Ralph Loop 机制确保 AI 持续运行，
  多 Agent 协同交叉验证（Claude Code / Codex）。
gate_hooks: []
---

# Skill: aodw-spec-autonomous
AODW 自主执行模式 v1.0

适用于：明确了目标和验收标准、需要 AI 全程自主完成的开发任务。

**核心变化：去除了所有人工 Gate，仅在启动时与用户确认目标。**

---

## 0. 设计理念

- **用户只做一次决策**：确认目标和验收标准
- **AI 自主循环**：Codex 通过 Ralph Loop 驱动，Claude Code 辅助执行和审查
- **多 Agent 协同**：按能力分工，Codex 协调，Claude Code 审查/实现
- **异常上抛**：无法自主解决的问题 → 通知用户决策

---

## 1. Agent 分工定义

| Agent | 能力特性 | 职责 |
|-------|---------|------|
| **Codex（GLM 5）** | 方案设计、协调、进度追踪 | Ralph Loop 主控、整体协调、进度追踪 |
| **Claude Code（Opus 4）** | 深度推理、代码审查、复杂逻辑 | 代码审查、关键模块实现、架构设计 |
| **OpenAI Codex** | 高速机械实现、大量模板代码 | 批量代码生成、简单模块实现 |

---

## 2. 执行流程

### Phase 0：启动确认（唯一人工环节）

**目标**：与用户确认三件事：
1. **目标** — 做什么？
2. **验收标准** — 怎么算完成？
3. **不可破坏边界** — 什么不能碰？

输出：写入 `RT/RT-XXX/rt-lite.md` 的 §1 + §4 + §5

用户确认后，Codex 全程自主接管。

---

### Phase 1：方案设计（Codex 主导）

1. Codex 阅读设计方案参考文件（如有）
2. 生成 `rt-lite.md` §2（方案设计）
3. **Claude Code 方案审查**：
   - Codex 调用 `agent_launch` → Claude Code 审查方案
   - 审查通过 → 进入 Phase 2
   - 审查发现问题 → Codex 修订方案 → 重新审查（最多 3 轮）

---

### Phase 2：代码实现（Codex Ralph Loop 自主循环）

**使用 `goal_launch` 启动 Ralph Loop**：

```
goal: "完成 RT-XXX 全部代码实现"
verifier_commands:
  - "cd projects/task-platform && npm run build && echo PASS || echo FAIL"
  - "find server/ -name '*.py' | xargs python3 -m py_compile 2>&1 | grep -q Error && echo FAIL || echo PASS"
mode: ralph
```

**Loop 内部分工（Codex 协调）：**

1. **代码实现**
   - 主模块：Claude Code（复杂逻辑）
   - 简单模块：OpenAI Codex（高速生成）
   - 或：Codex 直接实现

2. **代码审查**（每完成一个子模块）
   - Claude Code 审查：`logic correctness + code quality + security + performance`
   - Critical 问题 → Codex 修复 → 重新审查
   - Important 问题 → 记录到 §6，继续
   - Minor 问题 → 忽略

3. **进度追踪**
   - 更新 `RT/RT-XXX/task.md`（如步骤 > 3）
   - verifier_commands 通过 → 下一阶段

---

### Phase 3：测试与验证（Codex 主导）

1. **单元测试**
   - 执行测试命令
   - 失败 → 自动修复（最多 3 轮）
   - 3 轮后仍失败 → 通知用户

2. **端到端验证**
   - 启动服务
   - 调用 API 验证
   - 失败 → 自动排查修复（最多 3 轮）
   - 3 轮后仍失败 → 通知用户

3. **审查验证**（Claude Code）
   - 验证 §5（验收标准）是否满足
   - 全部通过 → 填写 §6（变更记录）

---

### Phase 4：交付通知

- Codex 输出完整交付报告
- 包含：实现文件列表 + 测试结果 + 审查报告 + 变更记录
- **通知用户**：结果已就绪，用户可事后 review

---

## 3. 异常处理机制

| 情况 | 处理方式 |
|------|---------|
| 方案审查失败（3 轮） | 通知用户，暂停，等待决策 |
| 代码审查 Critical（3 轮） | 通知用户，暂停，等待决策 |
| 测试失败（3 轮） | 通知用户，暂停，等待决策 |
| 子 Agent 超时 | 重试一次，仍失败通知用户 |
| 不确定决策 | 通知用户，不要假设 |

---

## 4. verifier_commands 设计原则

verifier_commands 是 Ralph Loop 的"退出条件"，必须满足：
- 每个 command 必须是确定性的（通过/失败明确）
- 失败时输出 `FAIL`，通过时输出 `PASS`
- 至少包含：编译检查 + 核心功能测试
- 不依赖外部服务（如数据库未启动则提前检查）

---

## 5. rt-lite.md 结构（spec-autonomous 专用）

```markdown
# RT-Lite: [RT-ID] - [任务标题]

> profile: spec-autonomous | status: in-progress | branch: feature/RT-XXX

---

## § 1. 背景与目标

### 1.1 目标（Goal）
<!-- 简洁描述最终要达成的状态 -->

### 1.2 验收标准（Success Criteria）
<!-- 可验证的检查项，每个都是明确的 True/False -->
- [ ] 标准1
- [ ] 标准2

### 1.3 不可破坏边界（Hard Constraints）
<!-- 必须遵守的约束 -->
- 约束1
- 约束2

---

## § 2. 方案设计
<!-- 完整的技术方案 -->

## § 3. 影响分析

## § 4. 不可破坏边界

## § 5. 验证计划
<!-- verifier_commands 的来源，对应每个验收标准 -->

## § 6. 变更记录
```

---

## 6. 与 Spec-Lite 的对比

| 方面 | Spec-Lite（人工审批） | Spec-Autonomous（自主） |
|------|----------------------|------------------------|
| Gate 3 | 人工审批方案 | Claude Code 审查（自动） |
| Gate 4 | 人工审批代码 | Claude Code 审查（自动） |
| Gate 5 | 人工验收 | verifier_commands 验证 |
| 用户交互 | 3 次（Gate 3/4/5） | 1 次（启动时） |
| 失败处理 | 用户决策 | 3 轮自动修复，仍失败通知 |
| 适用场景 | 高风险/大范围变更 | 明确目标的中小型任务 |
