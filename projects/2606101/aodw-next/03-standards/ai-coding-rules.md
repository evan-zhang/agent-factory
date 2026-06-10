# AI Coding Rules  
适用于 Cursor / Claude / Codeium 等所有 AI 工具。

本文件定义 AI 在修改代码前后必须遵守的行为规范。  
任何 AI 开发助手在本仓库中工作时，都应视本文件为“行为准则”。

---

## 0. 必读文档

在进行任何非琐碎（非机械重复）操作前，AI 必须：

1. **读取核心文档**：
   - `.aodw-next/01-core/aodw-constitution.md`
   - `.aodw-next/06-project/ai-overview.md`
   - `.aodw-next/03-standards/ai-coding-rules.md`（本文件）
   - `.aodw-next/01-core/ai-knowledge-rules.md`

2. **按需加载开发规范**（根据任务类型）：
   - **通用编码规范**：必须读取 `.aodw-next/03-standards/ai-coding-rules-common.md`（文件大小、复杂度、拆分原则等）
   - **如果涉及前端开发**：必须读取对应的栈规范（React: `stacks/react-typescript/...`, Vue2: `stacks/vue2/...`）
   - **如果涉及后端开发**：必须读取对应的栈规范（Python: `stacks/python-fastapi/...`, Java: `stacks/java-springboot/...`）
   - **如果涉及 UI 设计**：必须读取 `.aodw-next/03-standards/ui-kit/ui-kit.md`

   **判断任务类型的依据**：
   - **代码路径**：
     - 包含 `frontend/`、`src/pages/`、`src/features/` 等 → 前端
     - 包含 `backend/`、`api/`、`services/` 等 → 后端
   - **文件类型**：
     - `.tsx`、`.ts`（在 frontend 目录下）→ 前端
     - `.py`、`.go`、`.java` 等 → 后端
   - **RT 文档**：
     - `intake.md` 或 `spec.md` 中明确说明的任务类型
   - **用户明确说明**：
     - 用户明确说"前端"、"后端"等关键词

3. **读取当前 RT 目录**（如存在）：
   - `RT/RT-XXX/**`

4. **读取相关模块 README**：
   - 根据代码路径与 `ai-overview.md` 中的映射，查找对应的模块文档。

如上信息缺失，AI 应主动提示用户并建议创建或补全。

---

## 1. 基本原则

1. **以终为始**  
   - 先明确目标与期望行为，再考虑具体改动。
2. **最小必要修改**  
   - 优先选择最小、可验证、可回滚的改动；
   - 避免大面积“顺手重构”。
3. **不破坏 Invariants**  
   - 在修改前查阅 `invariants.md`、`ai-overview.md` 中的不变条件；
   - 如确需修改，必须走 Spec-Full 流程并更新相关文档。
4. **文档先行，代码随后**  
   - 重要变更应在 spec / plan / impact / invariants 中有记录。

---

## 1.5 LLM 编码行为基线（防失误）

> 目标：减少 AI 过度实现、静默假设、无关重构与“改完才澄清”的问题。  
> 原则：在多数任务中优先稳健性，高于执行速度；对琐碎任务可适度简化。

### A. 先想后写（Think Before Coding）

在开始实现前，AI 必须显式给出：

1. **假设声明**：列出关键假设（输入、边界、依赖、预期行为）。
2. **不确定性声明**：如存在歧义，必须列出 2+ 种解释，不得静默选择其一。
3. **简化选项说明**：若存在更小改动方案，必须说明并优先推荐。
4. **阻断提问机制**：关键信息缺失时，必须暂停实现并提问，不得“先写后问”。

### B. 简单优先（Simplicity First）

AI 必须遵守最小实现原则：

- 不实现用户未请求的能力（禁止 scope creep）
- 不为一次性逻辑引入抽象层
- 不为“未来可能”增加配置项
- 不为不可能场景添加防御性错误处理

**自检问题（必须）**：  
“当前方案是否被资深工程师认为过度设计？”  
若答案是“可能是”，必须先简化再实现。

### C. 外科手术式修改（Surgical Changes）

AI 在修改现有代码时必须：

1. 仅修改与当前请求直接相关的代码行；
2. 不顺手重构、重排、格式化无关代码；
3. 保持原有代码风格（除非用户要求统一风格）；
4. 仅清理由本次改动引入的孤儿代码（unused import/var/function）。

如果发现预存死代码或可优化点：**只记录，不自动处理**。

### D. 目标驱动执行（Goal-Driven Execution）

AI 必须把需求改写为可验证目标，并形成“实现-验证”闭环：

- Bug 修复：先构造复现（测试或步骤），再修复并验证通过
- 行为增强：先定义成功判据，再实现并验证
- 重构任务：确保变更前后行为等价（测试或关键路径回归）

对于多步骤任务，必须先给出简要计划（步骤 + 对应验证方式）。

### E. 实现前最小输出模板（建议在 plan/回复中复用）

```markdown
## 实现前对齐
- 假设：
  - ...
- 歧义点：
  - 解释 A：...
  - 解释 B：...
  - 推荐：A（理由：...）
- 最小可行改动：
  - ...
- 成功标准（可验证）：
  - ...
```

---

## 2. 影响分析（Impact Analysis）

在提出任何解决方案之前，AI 必须生成一份影响分析，并写入当前 RT 的 `impact.md`（或更新之）。

建议结构：

```markdown
## 影响分析 (Impact Analysis)

### 1. 问题触发点
- 入口（界面 / 接口 / 调度任务）：
- 简要复现路径：

### 2. 直接相关模块
- 控制器 / 路由：
- Service：
- Repository / DAO：
- UI 组件：

### 3. 间接影响
- 依赖的共享组件：
- 事件 / 消息链：
- 可能受影响的上下游：

### 4. 风险点
- 潜在数据损坏风险：
- 潜在安全风险：
- 潜在性能风险：
```

---

## 3. 不可破坏原则（Invariants）

在动任何代码前，AI 必须：

1. 打开并检查：
   - `RT/RT-XXX/invariants.md`（如果存在）
   - `.aodw-next/06-project/ai-overview.md` 中的系统级 Invariants
2. 在 `invariants.md` 中列出本次改动必须保持的条件，例如：

```markdown
## 不可破坏行为 (Invariants)

- 保持 /api/v1/orders/{id} 的响应结构不变；
- 保证已存在的订单查询过滤逻辑不受影响；
- 保持用户权限检查机制不被绕过。
```

如发现当前行为已违反 invariants，应先修正文档或代码使其一致，再进行进一步改动。

---

## 4. 方案设计（Solution Design）

AI 提出变更方案时，应：

1. 至少给出 2–3 个不同方案（包括“维持现状但在文档中记录”的选项，如适用）；
2. 对每个方案简要说明：
   - 修改位置；
   - 优点；
   - 缺点；
   - 对风险点的影响；
3. 提供一个 **推荐方案**，并说明推荐理由；
4. 允许用户选择“推荐方案”或指定其他选项。

在 Spec-Full 流程中，方案设计应记录在 `plan.md`；  
在 Spec-Lite 流程中，记录在 `rt-lite.md` §2。

---

## 5. 修改策略（Safe Modification Strategy）

在修改代码时，AI 应遵守：

1. **局部化修改**  
   - 除非走 Spec-Full 且有充分设计，不进行大范围重构；
   - 尽量只修改与本 RT 相关的模块 / 文件。
2. **分步提交**  
   - 逻辑修改与格式化 / 重排分开提交；
   - 如一次 RT 需要多阶段修改，可分多次提交。
3. **保持兼容**  
   - 在不破坏 Invariants 的前提下，避免改变对外可见行为；
   - 如需要引入 breaking change，必须通过 Spec-Full 并在 `changelog.md` 中记录清晰。

---

## 6. 测试策略（Testing Strategy）

在任何非琐碎修改之后，AI 必须：

1. 在 `RT/RT-XXX/tests.md` 中补充或更新测试点，内容包括：
   - 需要新增的单元测试；
   - 需要回归的集成 / API 测试；
   - 特别需要关注的边界条件；
2. 如项目存在自动化测试框架：
   - 建议具体的测试文件与用例位置；
   - 如可能，直接生成或修改测试代码。

示例条目：

```markdown
- [ ] 为 OrderService.addItem 添加当库存不足时的异常分支测试（tests/orders/order_service.test.ts）
- [ ] 回归测试：用户从“我的订单”页面进入订单详情时的数据加载与权限检查
```


---

## 7. Git Discipline（完成与合并规则）

所有 Git 操作必须严格遵循 `.aodw-next/01-core/git-discipline.md` 中定义的规范，包括：

- **分支命名**：`feature/RT-XXX-short-name`
- **提交信息格式**：Conventional Commits + `Refs: RT-XXX`
- **标签规范**：`done-RT-XXX`
- **合并策略**：根据团队约定选择 merge / rebase
- **知识蒸馏**：合并前必须完成文档同步（详见 `git-discipline.md` Section 5）

AI 在完成 RT 时，应提示用户执行完整的 Git Discipline 流程，或使用团队内部的自动化脚本。



---

## 8. 代码复杂度与输出规范 (Complexity & Output Standards)

> **注意**：本节的详细规范已移至 `.aodw-next/03-standards/ai-coding-rules-common.md`。  
> 所有开发任务都必须读取该文件，了解文件大小限制、复杂度控制、拆分原则和输出策略。

**必须读取**：`.aodw-next/03-standards/ai-coding-rules-common.md`

该文件包含：
- 全局文件长度限制（软上限）
- 函数/方法/类限制
- 拆分原则 (Splitting Principle)
- 输出策略 (Output Strategy)
- 复杂度控制
- 代码质量检查

---

## 9. 开发规范索引 (Development Standards Index)

本文件采用模块化设计，根据不同任务类型按需加载相应的开发规范。

### 9.1 通用编码规范

**文件**：`.aodw-next/03-standards/ai-coding-rules-common.md`

**适用场景**：所有类型的代码开发

**内容**：
- 文件大小限制
- 函数/方法/类限制
- 拆分原则
- 输出策略
- 复杂度控制

**加载要求**：**必须读取**（所有开发任务）

---

### 9.2 前端开发规范

**文件**：`.aodw-next/03-standards/stacks/react-typescript/ai-coding-rules-frontend.md`

**适用场景**：
- 前端开发（React + TypeScript + Vite）
- UI 组件开发
- 前端工具配置

**内容**：
- 技术栈确认
- 工具配置检查（ESLint + Prettier）
- 目录结构规范
- 命名规范
- TypeScript 规范
- React 编码规范
- Tailwind & Radix 使用规范
- AI 实现流程约束
- 前端代码提交前检查清单

**加载要求**：**如果涉及前端开发，必须读取**

**判断依据**：
- 代码路径包含 `frontend/`、`src/pages/`、`src/features/` 等
- 文件类型为 `.tsx`、`.ts`（在 frontend 目录下）
- RT 文档中明确说明为前端任务
- 用户明确说明为前端开发

---

### 9.3 前端开发规范 (Vue 2)

**文件**：`.aodw-next/03-standards/stacks/vue2/ai-coding-rules-frontend.md`

**适用场景**：
- 前端开发（Vue 2.6 + Webpack 4）
- UI 组件开发
- 旧项目维护

**加载要求**：**如果涉及 Vue 2 开发，必须读取**

**判断依据**：
- `package.json` 中包含 `"vue": "^2.x"`
- 文件类型为 `.vue`
- 用户明确说明为 Vue 2 开发

---

### 9.4 后端开发规范 (Python FastAPI)

**文件**：`.aodw-next/03-standards/stacks/python-fastapi/ai-coding-rules-backend.md`

**适用场景**：
- 后端开发（FastAPI / Python、Node.js、Go 等）
- API 开发
- 数据库操作
- 后端工具配置

**内容**：
- 技术栈确认
- 工具配置检查（Ruff、Black 等）
- 目录结构规范
- 命名规范
- API 设计规范
- 数据库操作规范
- 安全规范
- 性能优化
- 测试规范
- 后端代码提交前检查清单

**加载要求**：**如果涉及后端开发，必须读取**

**判断依据**：
- 代码路径包含 `backend/`、`api/`、`services/` 等
- 文件类型为 `.py`、`.go`、`.java` 等
- RT 文档中明确说明为后端任务
- 用户明确说明为后端开发

---

### 9.5 后端开发规范 (Java SpringBoot)

**文件**：`.aodw-next/03-standards/stacks/java-springboot/ai-coding-rules-backend.md`

**适用场景**：
- 后端开发（Java 21 + Spring Boot 2.7）
- 企业级应用开发

**加载要求**：**如果涉及 Java 开发，必须读取**

**判断依据**：
- 代码路径包含 `src/main/java`
- 文件类型为 `.java`、`pom.xml`
- 用户明确说明为 Java 开发

---

### 9.6 UI 设计规范（将来）

**文件**：`.aodw-next/03-standards/ui-kit/ui-kit.md`

**适用场景**：
- UI 设计
- 设计系统规范
- 组件库使用规范

**加载要求**：**如果涉及 UI 设计，必须读取**（如果文件存在）

---

### 9.7 工具初始化规则

**文件**：`.aodw-next/05-tooling/ai-tools-init-rules.md`

**适用场景**：
- 用户说"初始化工具"、"设置开发工具"、"配置工具"等
- 编码前检测到工具未初始化

**内容**：
- 触发条件
- 执行流程（检测项目类型、检测工具状态、交互式引导、验证配置）
- 配置文件合并策略
- 安装命令参考
- 配置模板位置
- 状态文件格式
- 交互规范

**加载要求**：**如果用户表达工具初始化意图，或检测到工具未初始化，必须读取**

---

### 9.8 规范加载流程

AI 在执行开发任务时，必须按以下流程加载规范：

1. **第一步**：读取核心文档（见第 0 节）
2. **第二步**：判断任务类型（根据代码路径、文件类型、RT 文档、用户说明）
3. **第三步**：按需加载开发规范：
   - **必须**读取 `.aodw-next/03-standards/ai-coding-rules-common.md`（通用规范）
   - **如果涉及前端 (React)**：读取 `.aodw-next/03-standards/stacks/react-typescript/ai-coding-rules-frontend.md`
   - **如果涉及前端 (Vue 2)**：读取 `.aodw-next/03-standards/stacks/vue2/ai-coding-rules-frontend.md`
   - **如果涉及后端 (Python)**：读取 `.aodw-next/03-standards/stacks/python-fastapi/ai-coding-rules-backend.md`
   - **如果涉及后端 (Java)**：读取 `.aodw-next/03-standards/stacks/java-springboot/ai-coding-rules-backend.md`
   - **如果涉及 UI 设计**：读取 `.aodw-next/03-standards/ui-kit/ui-kit.md`
   - **如果用户表达工具初始化意图**：读取 `.aodw-next/05-tooling/ai-tools-init-rules.md`
4. **第四步**：根据规范执行开发任务
