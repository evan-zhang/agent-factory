---
id: aodw-spec-lite
version: 2.0.0
category: aodw/execution-profile
trigger: "当 RT-Manager 决策 profile=Spec-Lite 时自动加载"
replaces: "spec-lite-profile.md (v1.x，原 6 文档模式)"
description: >
  AODW Spec-Lite 执行 Skill。适用于小范围变更（bug 修复、单模块改进、低风险增强）。
  核心变化：将原来的 6 个独立文档合并为单个 rt-lite.md，降低 AI 认知负担与 Token 消耗。
gate_hooks:
  - gate: 3
    name: 计划批准
    action: "展示 rt-lite.md §1-§4 摘要，等待用户批准"
  - gate: 4
    name: 提交确认
    action: "展示 git diff，等待用户确认提交"
  - gate: 5
    name: 完成确认
    action: "展示完成摘要，等待用户确认后移交 git-discipline"
token_budget: "~2KB (自身) + rt-lite.md 读取 (~1KB)"
---

# Skill: aodw-spec-lite
AODW Spec-Lite 执行规范 v2.0（单文档模式）

适用于：bug 修复 / 单个模块的小改进 / 简单 UI 或交互调整 / 不涉及数据结构与 API 契约变更的工作。

---

## 1. 核心原则

**六合一（6-in-1）**：以下原 6 个文档的内容，全部统一写入单个 `RT/RT-XXX/rt-lite.md` 文件：

| 原文档 | 迁移至 rt-lite.md 的章节 |
|--------|--------------------------|
| spec-lite.md | § 1. 背景与目标 |
| plan-lite.md | § 2. 方案设计 |
| impact.md | § 3. 影响分析 |
| invariants.md | § 4. 不可破坏边界 |
| tests.md | § 5. 验证计划 |
| changelog.md | § 6. 变更记录 |

---

## 2. 执行流程（8 步）

### Step 0：分支确认（强制）
```bash
git branch --show-current
# 必须输出 feature/RT-XXX，否则立即停止
```
- ✅ 确认在 feature 分支上后方可继续
- ❌ 如在 main/master 上：**立即停止，严禁写入任何文件**

### Step 1：生成 rt-lite.md (§1-§4)
- AI 根据 intake.md 自动生成背景与目标章节（§ 1）
- AI 设计技术方案并填写方案设计章节（§ 2）
- AI 填写影响分析（§ 3）和不可破坏边界（§ 4）
- **必须包含"实现前对齐"四要素**：关键假设 / 歧义点 / 最小改动 / 可验证成功标准

> **设计理由**：§3（影响分析）和 §4（不可破坏边界）是方案的一部分，移到 Gate 3 之前生成，
> 确保用户审批时有完整信息——不仅是"做什么"（§1-§2），还有"会影响什么"（§3）和"不能碰什么"（§4）。

### Step 2：内联格式验证（非审计）
> AI 检查 §1-§4 的字段完整性（非空验证）。
> - [ ] §1 背景与目标属性是否全部填写？
> - [ ] §2 方案是否满足非空要求？
> - [ ] 是否填写了关键假设与歧义？
> - [ ] 成功标准是否已列出？
> - [ ] §3 影响范围是否已列出（受影响和不受影响的部分）？
> - [ ] §4 不可破坏边界是否已列出？
>
> 若有字段为空，先填写再继续。此步骤不替代 `aodw-auditor` 的批判性审计，仅确保文档可被后续流程解析。

### Step 3：Claude Code 方案审查（Gate 3 前置）

在向用户展示方案前，先由 Claude Code 独立审查：

```bash
# 将方案内容写入审查文件
cat > /tmp/claude-review-g3.md << 'EOF'
# 方案审查（Gate 3）

你是独立审查员。请审查以下 RT 的技术方案，关注：
1. 方案合理性 — 是否能达成目标？
2. 影响范围 — 是否充分评估了影响？
3. 风险点 — 是否有遗漏的风险或边界情况？
4. 与不可破坏边界的一致性

RT 信息：
（将 rt-lite.md §1-§4 核心内容粘贴至此）
EOF

# Claude Code 审查（后台）
exec background:true workdir:<项目目录> \
  command:"claude --print --permission-mode bypassPermissions '读取 /tmp/claude-review-g3.md，审查方案并输出报告到 /tmp/claude-review-g3-report.md'" \
  timeout:300
```

等待 Claude Code 完成后，读取审查报告，连同 rt-lite.md §1-§4 摘要一起展示给用户。

### Step 4：🛑 Gate 3 — 计划批准（强制暂停）

> **AI 必须此处暂停，展示以下内容并等待用户确认：**
> 1. rt-lite.md §1-§4 摘要（约 300 字，覆盖方案、影响、边界）
> 2. **Claude Code 方案审查报告**
> 3. 计划修改的文件列表
> 4. 预计影响范围
> 5. 不可破坏边界摘要
>
> 询问："方案审查完成，是否批准执行？"
> **严禁在用户批准前修改任何业务文件。**

### Step 3.5：任务追踪（按需）
> 如果 §2 方案中的实现步骤 > 3，AI 必须创建 `RT/RT-XXX/task.md` 用于进度追踪。
> 格式要求：`[x]` 已完成 / `[/]` 进行中 / `[ ]` 待执行。
> 每完成一个阶段或提交代码前必须更新 task.md。
> 详见 rt-manager.md §8。

### Step 4：实现代码
- 在 feature 分支上修改业务代码
- 遵守项目编码规范（如需：加载对应 Tech-Stack Skill）
- 每条修改不超出 §2 方案范围（最小改动）
- 不破坏 §4 中列出的任何 invariant

### Step 5：外部审计钩子（可选触发）
> 如果用户在 Gate 3 或 Gate 4 时输入"审计"，则触发 `aodw-auditor` Skill 进行深度质检。
> 否则，以 Step 2 的内联自审计为准。

### Step 6：Claude Code 代码审查（Gate 4 前置）

在向用户展示 diff 前，先由 Claude Code 独立审查代码变更：

```bash
cat > /tmp/claude-review-g4.md << 'EOF'
# 代码审查（Gate 4）

你是独立审查员。请审查以下代码变更，关注：
1. 逻辑正确性 — 实现是否符合方案设计？
2. 代码质量 — 可读性、可维护性、边界处理
3. 安全性 — 是否有安全隐患？
4. 性能 — 是否有性能问题？
5. 与不可破坏边界的一致性

变更内容：
（将 git diff 核心内容粘贴至此）
EOF

# Claude Code 审查（后台）
exec background:true workdir:<项目目录> \
  command:"claude --print --permission-mode bypassPermissions '读取 /tmp/claude-review-g4.md，审查代码并输出报告到 /tmp/claude-review-g4-report.md'" \
  timeout:300
```

等待 Claude Code 完成后，读取审查报告，连同 git diff 一起展示给用户。

### Step 7：🛑 Gate 4 — 提交确认（强制暂停）

> **AI 必须此处暂停，展示以下内容并等待用户确认：**
> 1. `git status` 输出
> 2. 关键文件的 `git diff` 摘要
> 3. **Claude Code 代码审查报告**
>
> 询问："代码审查完成，是否提交？"
> **严禁在用户确认前执行 git commit。**

### Step 8：Claude Code 验收审查（Gate 5 前置）

在向用户展示完成摘要前，先由 Claude Code 独立验收：

```bash
cat > /tmp/claude-review-g5.md << 'EOF'
# 验收审查（Gate 5）

你是独立审查员。请审查本次 RT 的验证计划和变更记录，关注：
1. 验证计划 — 测试用例是否充分覆盖了变更点？
2. 变更记录 — 变更摘要是否准确反映了用户可感知的变化？
3. 风险确认 — 是否存在未经验证的潜在风险？

验证计划与变更记录：
（将 §5 + §6 核心内容粘贴至此）
EOF

# Claude Code 验收审查（后台）
exec background:true workdir:<项目目录> \
  command:"claude --print --permission-mode bypassPermissions '读取 /tmp/claude-review-g5.md，审查验收材料并输出报告到 /tmp/claude-review-g5-report.md'" \
  timeout:300
```

### Step 9：🛑 Gate 5 — 完成确认（强制暂停）

- 填写验证计划（§ 5）和变更记录（§ 6）
- 向用户展示完成摘要 + **Claude Code 验收审查报告**，等待确认
- 用户确认后，移交 `git-discipline.md` 执行收尾（合并 / 打 Tag / 更新状态）

---

## 3. rt-lite.md 标准模板

> **AI 创建 rt-lite.md 时必须严格按照以下结构**，审计官通过标题锚点定位各章节。

```markdown
# RT-Lite: [RT-ID] - [任务标题]

<!-- 元数据行（单行，勿删） -->
> profile: Spec-Lite | status: in-progress | branch: feature/RT-XXX

---

## § 1. 背景与目标 (Context & Goal)

### 1.1 问题描述
<!-- 当前存在的问题或需求 -->

### 1.2 目标
<!-- 本次改动希望达成的效果（用户视角） -->

### 1.3 影响范围
<!-- 涉及的模块/文件；明确不受影响的部分 -->

### 1.4 实现前对齐 (Implementation Alignment)
- **关键假设**：
- **歧义点与推荐选项**：
- **最小必要改动**：（为何不是更大方案）
- **可验证成功标准**：

---

## § 2. 方案设计 (Solution & Design)

### 2.1 修改点
<!-- 计划修改的具体文件路径 -->

### 2.2 方案描述
<!-- 技术方案简述：调整哪一层逻辑，是否引入新组件/函数 -->

### 2.3 风险与注意事项
<!-- 边界情况、与其他模块的隐含耦合 -->

---

## § 3. 影响分析 (Impact Analysis)

### 3.1 直接影响
<!-- 受影响的模块和具体行为 -->

### 3.2 间接影响
<!-- 上下游依赖模块 -->

### 3.3 风险评估
<!-- 数据/安全/性能/用户体验风险 -->

---

## § 4. 不可破坏边界 (Invariants)

### 4.1 业务行为边界
<!-- 不改变的业务规则和用户流程 -->

### 4.2 接口边界
<!-- 不改变的 API 路径、请求/响应格式、错误码 -->

### 4.3 技术结构边界
<!-- 不允许绕过的中间层或架构约束 -->

---

## § 5. 验证计划 (Verification Plan)

### 5.1 本次新增测试
- [ ] 测试用例 1：
- [ ] 测试用例 2：

### 5.2 回归测试
- [ ] 回归场景 1：

### 5.3 手动验证步骤
- [ ] 手动步骤 1：

---

## § 6. 变更记录 (Changelog)

### 6.1 变更摘要

### 6.2 用户可感知变化

### 6.3 内部重要变化
```

---

## 4. 禁止行为（Red Lines）

- 🚫 **Never Code on Main**：绝不在 main/master 上修改业务代码
- 🚫 **Never Skip Gate 3**：在计划批准前不得修改任何业务文件
- 🚫 **Never Skip Gate 4**：在用户确认前不得执行 git commit
- 🚫 **Never Skip Gate 5**：RT 完成前必须等待用户确认
- 🚫 **Never Add Unplanned Scope**：禁止引入 § 2 范围外的任何修改
- 🚫 **Never Create 6 Files**：禁止退化回旧版 6 文档模式

---

## 5. Skill 升级路径

- **如遇以下情况，立即建议升级至 `aodw-spec-full`**：
  - 影响数据模型或对外 API
  - 跨越 3 个以上模块
  - § 4 中存在无法满足的 Invariant

- **升级方法**：将 `rt-lite.md` 中各章节内容拆分至对应的独立文档，并更新 `meta.yaml` 的 profile 字段。
