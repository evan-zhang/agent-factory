# RT-Manager Specification

统一请求票编排器（Request Ticket Manager）

RT-Manager 是 AODW 的核心组件，负责：
- RT 编号管理
- 立项流程
- Full / Lite（Spec-Full / Spec-Lite）流程分流
- RT 目录和分支的创建与约束

---

## 0. 核心原则

**简洁至上**：保持简单清晰的流程，避免复杂度
**自动化优先**：自动化可自动化的操作（RT-ID 生成、目录创建）
**分支隔离**：每个 RT 独立工作分支，避免相互干扰

---

## 1. 工作前强制检查

AI 在执行任何文件修改操作前，必须先执行以下检查序列：

### Step 1: 验证 RT 是否已创建
- 检查 `RT/RT-XXX/` 目录是否存在
- 检查 `meta.yaml` 和 `intake.md` 是否已创建

### Step 2: 验证 feature 分支是否已创建并切换
执行 `git branch --show-current`，检查结果：
- ✅ 如果显示 `feature/RT-XXX-xxx`：继续工作
- ❌ 如果显示 `main` 或 `master`：**立即停止**，提示用户并创建分支

**🚨 强制规则**：AI 在开始任何代码工作前，必须先创建并切换到 feature 分支！
严禁在 `main`/`master` 分支上直接修改业务代码。

---

## 2. 流程状态机

```
created → intaking → decided → in-progress → reviewing → done
```

RT-Manager 统一管理全局状态机更新。

---

## 3. Intake（立项）流程

### 3.1 触发条件
用户表达以下意图时：
- 新功能
- Bug 修复
- 需求
- 改进
- 重构

### 3.2 执行步骤
1. 生成 RT-ID（使用本地生成或远程获取）
2. 创建 RT 目录结构
3. 执行交互式澄清（选项化提问）
4. 记录立项信息到 `intake.md`
5. 决定使用 Spec-Full 还是 Spec-Lite profile

---

## 4. 流程分流决策

### 4.1 Spec-Full 适用场景
- 跨模块影响
- 数据模型/schema 变更
- 外部 API/协议变更
- 高风险或高复杂度变更

### 4.2 Spec-Lite 适用场景
- Bug 修复
- 单模块小改进
- 简单 UI 或交互调整
- 不涉及数据结构与 API 契约变更的工作

### 4.3 Spec-Autonomous 适用场景
- 目标明确、验收标准清晰
- 需要 AI 全程自主完成、不需人工协作
- 中小型功能模块
- 用户仅在启动时确认目标，执行中不干预

---

## 5. 目录结构

```
RT/RT-XXX/
  meta.yaml          ← RT 元数据
  intake.md          ← 立项记录
  decision.md        ← Profile 决策
  spec.md            ← Spec-Full 完整需求
  plan.md            ← Spec-Full 技术方案
  impact.md          ← 影响分析
  invariants.md       ← 不可破坏边界
  tests.md           ← 验证计划
  task.md           ← AI 任务追踪（仅 Spec-Full）
  changelog.md        ← 变更记录
  
  或（Spec-Lite）：
  rt-lite.md         ← 单文件整合所有内容
```

---

## 6. 分支命名与隔离策略

**分支命名**：`feature/RT-XXX-short-name`
**工作区隔离**：每个 RT 对应一个独立的 Git worktree

**🚨 关键规则**：一个 RT = 一个 Worktree = 一个 Feature 分支

---

## 7. Profile 调用规范

AI 根据决策结果，加载对应的 Profile：

- Spec-Autonomous → 加载 `02-workflow/spec-autonomous-profile.md`
- Spec-Full → 加载 `02-workflow/spec-full-profile.md`
- Spec-Lite → 加载 `02-workflow/spec-lite-profile.md`

---

## 8. 集成规范

与以下规范配合使用：
- `01-core/git-discipline.md`（分支与提交规范）
- `01-core/ai-interaction-rules.md`（交互规范）
- `01-core/ai-knowledge-rules.md`（知识同步规范）
