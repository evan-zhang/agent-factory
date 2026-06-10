# AI Knowledge Maintenance Rules  
AI 必须确保文档始终与代码一致。

本文件定义“何时更新哪些文档”，以及文档与代码之间的映射方式。

> **Spec-Lite 单文件模式适配 (v1.1)**：本规则同时支持 Spec-Lite 的单文件 `rt-lite.md` 模式和 Spec-Full 的多文件模式。处理 Spec-Lite RT 时，请将 `rt-lite.md §N` 视为对应章节的文档来源。

---

## 1. 总原则

1. 文档是系统的一等公民，必须与代码一起演化；
2. 任何重要改动都必须在相关文档中有所体现；
3. AI 在执行任何非琐碎修改后，应主动检查并更新相关文档；
4. 如果文档与代码不一致，AI 应优先尝试修正不一致，而不是忽略。

---

## 2. 文档类别

### 2.1 全局文档（Global）

位于 `.aodw-next/` 或 `docs/` 下，用于整个系统：

- `.aodw-next/01-core/aodw-constitution.md`  
- `.aodw-next/06-project/ai-overview.md`  
- `.aodw-next/03-standards/ai-coding-rules.md`  
- `.aodw-next/01-core/ai-knowledge-rules.md`  
- 模块 README（如 `docs/modules/users.md`、`docs/modules/orders.md` 等）  
- 数据与合约文档（如 `data-model.md`、`contracts/*.md` / `contracts/*.yaml`）

**当发生以下情况时，AI 必须更新相关全局文档：**

- 整体架构变化（例如引入新子系统、拆分服务、替换核心中间件）；
- 模块职责变化（例如将一部分业务从 A 模块迁移到 B 模块）；
- 数据模型变化（增加 / 删除 / 修改实体或字段含义）；
- 对外接口或协议变化（API、消息格式等）；
- AODW 流程规则本身发生修改。

---

### 2.2 RT 专属文档（Local per RT）

每个 RT 都有自己的知识库目录，包括核心文档和过程文档。

**目录结构**：详见 `.aodw-next/02-workflow/rt-manager.md` 第 2 节"目录与分支创建"。

**核心文档**：位于 RT 目录根目录，记录 RT 全生命周期信息（intake、decision、spec、plan、impact、invariants、tests、changelog 等）。

**过程文档**：位于 `RT/RT-XXX/docs/` 目录，记录执行过程中的分析、调研、决策。详细规则见第 7 节。

---

## 3. 何时更新哪些文档

### 3.1 Intake 阶段后

在 RT-Manager 完成本 RT 的 Intake（立项）后：

- 必须创建 / 更新：
  - `RT/RT-XXX/intake.md`
  - `RT/RT-XXX/decision.md`

`intake.md` 应包含：

- 原始用户描述；
- AI 提出的问题与用户回答的简要记录；
- 对需求 / 问题的归类（Feature / Bug / Enhancement / Refactor / Research 等）；
- 初步范围与风险评估。

`decision.md` 应包含：

- 为何选择 Spec-Full 或 Spec-Lite；
- 若存在备选流程（如纯 Research），记录为何未采用；
- 如用户强行指定流程，记录 AI 的原始建议与用户的选择。

---

### 3.2 Spec 阶段后（Spec-Full / Spec-Lite）

**Spec-Full：**

- AI 必须创建 / 更新：
  - `RT/RT-XXX/spec.md`
  - `RT/RT-XXX/clarifications`（可在 spec 中以章节形式存在）

Spec 内容应包括：

- 背景与目标；
- 用户故事 / 功能需求；
- 非功能需求（性能、安全、可用性等）；
- 成功标准；
- 需要澄清的历史问题记录（Q&A）。

**Spec-Lite：**

- AI 必须创建 / 更新：
  - `RT/RT-XXX/rt-lite.md`（**单文件模式**，包含所有过程文档内容）

`rt-lite.md §1 背景与目标` 至少需要填写：
- 当前问题描述；
- 目标行为（修复后 / 改进后的预期效果）；
- 影响范围的文字说明；
- 可验证的成功标准。

> ⚠️ Spec-Lite 不再创建独立的 `spec-lite.md` 文件，全部内容整合在 `rt-lite.md` 中。

---

### 3.3 Plan 阶段后

**Spec-Full：**

- AI 必须创建 / 更新：
  - `RT/RT-XXX/plan.md`
  - `RT/RT-XXX/data-model.md`（如涉及数据模型变更）
  - `RT/RT-XXX/contracts/`（如涉及对外接口变更）
  - `RT/RT-XXX/research.md`（如有前期调研与决策）

**Spec-Lite：**

- `rt-lite.md §2 方案设计` 已包含 Plan 内容（修改点、方案描述、最小必要改动）。
- 不再创建独立的 `plan-lite.md`。

---

### 3.4 修改代码前

在实现前，AI 必须创建 / 更新：

- `RT/RT-XXX/impact.md`  
  - 当前问题是如何触发的；
  - 哪些模块 / 功能直接受到影响；
  - 哪些模块可能被间接影响；
- `RT/RT-XXX/invariants.md`  
  - 在本次改动中必须保持不变的行为；
  - 不允许被破坏的数据与接口约束。

这些文档是 **变更的约束条件**。如之后发现方案与 invariants 冲突，AI 应向用户明确指出，并建议走 Spec-Full 或修订 invariants。

---

### 3.5 修改代码后

在实现完成后，AI 必须：

1. **更新 tests.md**

   - 列出新增的测试用例及其覆盖的场景；
   - 列出建议回归的关键用例；
   - 如存在未自动化但应进行手动验证的场景，也应列出。

2. **更新 changelog.md**

   - 以简洁的方式概述本次 RT 对系统行为的改动；
   - 如有潜在影响范围（例如“可能对历史数据产生影响”），加以说明；
   - 标注与其他 RT 或模块的依赖关系。

3. 如涉及数据模型或对外接口更改，必须更新：

   - `data-model.md`；
   - `contracts/` 中的相关说明；
   - 相关模块 README；
   - 必要时更新 `ai-overview.md`（例如新增了新的核心模块）。

---

## 4. 文档与代码的映射（Frontmatter Mapping）

为了帮助 AI 找到与某段代码相关的文档，建议在文档顶部使用 Frontmatter：

```yaml
---
rt: RT-001
related_files:
  - apps/api/src/orders/**
  - apps/api/src/orders/order_service.ts
  - apps/web/src/features/orders/**
---
```

或在模块 README 中：

```yaml
---
module: orders
files:
  - apps/api/src/orders/**
  - apps/web/src/features/orders/**
---
```

AI 在进行修改时，必须执行 **Mapping Check**：

1.  **查索引**：读取 `.aodw-next/06-project/modules-index.yaml`，获取所有模块的 `root` 路径。
2.  **匹配路径**：检查本次修改的文件路径是否落在某个模块的 `root` 下。
3.  **定位文档**：如果匹配，读取对应的 `path`（即模块 README）。
4.  **验证 Frontmatter**：进一步检查模块 README 中的 `files` 字段是否包含该文件。
5.  **更新文档**：确认匹配后，必须审查该文档，并将本次 RT 的变更同步更新进去。

**如果找不到匹配的模块**：
- 考虑是否需要创建一个新模块？
- 或者该文件属于公共基础设施（需更新全局文档）？

---

## 5. 文档一致性检查

在 RT 实现流程的最后（合并 / 完成之前），AI 应进行一次快速一致性检查：

**核心文档检查**：
- 当前改动是否改变了数据模型？如果是，`data-model.md` 是否反映了这一点？
- 当前改动是否改变了对外接口？如果是，`contracts/` 是否已更新？
- 当前改动是否改变了模块职责？如果是，相关 README 是否已更新？
- 当前 RT 的：
  - `spec` / `spec-lite`
  - `plan` / `plan-lite`
  - `impact`
  - `invariants`
  - `tests`
  - `changelog`

  是否完整地记录了从"问题 → 方案 → 实现 → 测试 → 结果"的过程？

**目录结构检查**：
- 检查过程文档是否在正确位置（应在 `RT/RT-XXX/docs/` 目录下，详见第 7 节）
- 检查核心文档是否完整（meta.yaml、intake.md、decision.md、spec/plan、impact、invariants、tests、changelog）

如发现明显不一致，AI 应主动修订文档或提示用户。

---

## 6. 版本控制与标签

所有文档都应纳入 Git 版本控制。

当一个 RT 完成时，推荐在：

- 代码分支合并后打上 tag（例如 `done-RT-XXX`）；
- 在 RT 的 `changelog.md` 中记录最终状态；
- 如果本次 RT 涉及 AODW 制度本身的更新（例如修改了 `aodw-constitution.md`），应特别标注。

---

## 7. 过程文档管理规则

过程文档是指在 RT 执行过程中产生的、用于记录分析、调研、决策等过程的文档。

**存储位置**：必须存放在 `RT/RT-XXX/docs/` 目录下，禁止与核心文档混放在根目录。

**命名规范**：使用小写字母和连字符（如 `dependency-installation-strategy.md`），避免使用序号前缀。

**何时创建**：进行策略分析、技术调研、设计决策、问题诊断、修复总结时。

**与核心文档的关系**：过程文档是对核心文档的补充和细化，不应替代核心文档。

---

## 8. 当信息缺失或不确定时

如果 AI 判断文档中存在以下情况：

- 信息缺失；
- 描述明显过时；
- 与代码行为明显矛盾；

则 AI 应：

1. 在当前 RT 中开辟一小节（可放在 `changelog.md` 或 `docs/` 目录下的单独文档中）记录发现的问题；
2. 尝试基于当前代码自动修正文档；
3. 在不确定时向用户提出明确问题，获取确认后再更新文档。

AI 不应在发现明显不一致时保持沉默。

---
---

## 9. RT 元数据与索引维护规则

**元数据优先级**：`RT/RT-XXX/meta.yaml` 是权威来源，`RT/index.yaml` 是全局汇总。如不一致，以 meta.yaml 为准。

**何时更新 meta.yaml**：RT 创建、类型/Profile/状态/模块/工具/负责人变更、RT 结束时。

**何时更新 index.yaml**：新建 RT、meta.yaml 发生变更时同步更新。详细操作规范见 `.aodw-next/02-workflow/rt-manager.md` 第 9 节。

**一致性检查**：RT 进入 `done` 状态前，检查 meta.yaml 与 index.yaml 是否一致。

---

## 9.5 时间字段获取规则

⚠️ **重要**：所有时间字段必须使用系统真实时间，严禁 AI 自行推断或使用假时间。

**详细规则**：请参考 `.aodw-next/02-workflow/rt-manager.md` 第 10 节"时间字段获取规则（强制要求）"。

**关键要求**：
- 必须通过系统命令或 API 获取真实时间
- 禁止使用 AI 训练数据、对话上下文或自行推断的时间
- 时间格式：ISO8601（如 `2025-11-28T11:54:45Z`）
- 适用范围：`meta.yaml`、`RT/index.yaml`、`AODW_Governance/version.md` 等所有时间字段
