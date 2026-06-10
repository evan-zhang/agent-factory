# Git Discipline for AODW

本文件定义 AODW 工作流中必须遵守的 Git 操作规范。
这些规则旨在确保代码历史清晰、可回溯，并便于自动化工具检查。

> **核心原则**：AI 可以执行所有 Git 操作，但涉及不可逆操作前必须向用户明确确认，获得同意后立即执行。

---

## 0. AI 操作边界

### 核心原则：确认门控执行（Confirm-Gated Execution）

AI 可以执行所有 Git 操作，包括提交、合并、推送、打标签、创建和清理 worktree 等。

**凡涉及不可逆操作，AI 必须在执行前向用户做明确确认，获得用户同意后立即执行。**

> 背景：用户主要通过语音与 AI 交互，AI 是唯一的操作执行手。"提供脚本让用户手动执行"的模式不再适用。

---

### 需要确认门控的操作

| 操作 | 确认内容要点 |
|------|------------|
| `git commit` | 提交哪些文件、commit message 是什么、关联哪个 RT |
| `git merge --no-ff` | 从哪个分支合并到哪里、是否存在冲突风险 |
| `git push` | 推送到哪个远程、推送内容（分支 + tag） |
| `git tag` | 打什么 tag、打在哪个 commit 上 |
| `git worktree add` | 创建哪个 worktree、挂载哪个分支、对应哪个 RT |
| `git worktree remove` | 删除哪个 worktree、确认该 RT 已完成合并 |
| `git branch -d` | 删除哪个本地分支 |

### 确认格式规范

确认话术必须满足：
- **简短**：不超过 3 句话
- **明确**：说清楚做什么、影响是什么、是否可撤销
- **二选一**：以"要我现在执行吗？"结尾，用户回答"可以"即执行

**示例：**

```
合并前：
"RT-XXX 的代码已全部提交，我准备将 feature/RT-XXX-short-name 合并到 master，
使用 --no-ff 保留分支历史，随后打 done-RT-XXX 标签并推送。合并后无法撤销。要我现在执行吗？"

Worktree 清理：
"RT-XXX 已合并完成，我准备删除本地 worktree 目录 VoiceX-RT-XXX/ 和
feature/RT-XXX-short-name 分支。要我现在执行吗？"

代码提交：
"我准备提交以下文件到 feature/RT-XXX：[文件列表]，
commit message 为 'feat(stt): xxx — Refs: RT-XXX'。要我现在执行吗？"
```

### 无需确认、AI 可直接执行的操作

- 读取文件、查看 git log / status / diff
- 创建 RT 目录和文档
- 创建 feature 分支（`git checkout -b`）
- 切换到已存在的分支（`git checkout`）

---

## 1. 分支命名 (Branch Naming)

所有开发工作必须在 Feature 分支上进行，禁止直接在主分支（master/main）提交。

### 1.1 命名格式
```text
feature/RT-{seq}-{short-name}
```

- **RT-{seq}**: 关联的 RT ID，必须与 `RT/` 目录下的 ID 一致（如 `RT-001`）。
- **{short-name}**: 简短描述，使用小写英文和连字符（kebab-case），建议 2-4 个单词。

### 1.2 示例
- ✅ `feature/RT-001-login-fix`
- ✅ `feature/RT-023-export-csv`
- ❌ `feature/login-fix` (缺少 RT ID)
- ❌ `RT-001/login` (格式错误)

---

## 2. Worktree 管理 (Worktree Management)

### 2.0 核心约定

**一个 RT = 一个 Worktree = 一个 Feature 分支**，三者 RT 序号严格对齐。

| 角色 | 路径 | 分支 |
|------|------|------|
| 主仓库 | `~/VoiceX-0409/VoiceX/` | `master`（只读参考，禁止在此改代码）|
| RT 工作区 | `~/VoiceX-0409/VoiceX-RT-{seq}/` | `feature/RT-{seq}-{name}` |

### 2.1 创建 Worktree（Decision 阶段）

feature 分支创建完成后，AI 向用户确认 worktree 创建，用户同意后执行：

```bash
git worktree add ../VoiceX-RT-XXX feature/RT-XXX-short-name
git worktree list  # 验证
```

**并行 RT 冲突检查（必须执行）**：创建新 worktree 前，AI 读取 `RT/index.yaml`，检查所有 `in-progress` 状态的 RT 是否与新 RT 涉及同一模块。如有重叠，向用户明确告知冲突范围和合并风险，由用户决策是否继续。

### 2.2 工具隔离原则

每个 AI 工具实例（Cursor / Codex 等）只能读写自己绑定的 worktree 目录，禁止跨目录操作。多个实例可并行工作于各自的 worktree，互不干扰。

### 2.3 Merge 顺序

多个 RT 同时完成时，合并顺序、冲突解决全部由用户决定，AI 不推断合并优先级。

### 2.4 状态检查命令

```bash
git worktree list              # 查看所有 worktree
git worktree prune --dry-run   # 检查可清理的 worktree
```

---

## 3. 提交信息 (Commit Message)

提交信息必须遵循 Conventional Commits 规范，并包含 RT 引用。

### 3.1 格式模板
```text
<type>(<scope>): <subject>

[optional body]

Refs: <RT-ID>
```

### 3.2 字段说明
- **type**:
  - `feat`: 新功能
  - `fix`: 修复 bug
  - `docs`: 文档变更
  - `style`: 代码格式（不影响逻辑）
  - `refactor`: 重构（既不是新增功能也不是修改 bug）
  - `perf`: 性能优化
  - `test`: 增加测试
  - `chore`: 构建过程或辅助工具的变动
- **scope**: (可选) 影响范围，如 `auth`, `api`, `ui`。
- **subject**: 简短描述，使用祈使句，不加句号。
- **Refs**: (必须) 关联的 RT ID，用于链接 Git 历史与需求文档。

### 3.3 示例
```text
fix(auth): handle token expiration gracefully

Update the interceptor to refresh token on 401 error.

Refs: RT-001
```

---

## 4. 标签 (Tagging)

当一个 RT 完成并合并到主分支后，必须打标签以标记里程碑。

### 4.1 命名格式
```text
done-<RT-ID>
```

### 4.2 示例
- ✅ `done-RT-001`
- ✅ `done-RT-042`

---

## 5. 合并策略 (Merge Strategy)

- **禁止 Fast-forward**: 合并 Feature 分支时应使用 `--no-ff`，以保留分支历史。
- **Squash**: 对于琐碎的提交（如 "fix typo", "update"），建议在合并前进行 Squash，但保留关键的逻辑提交。

---

## 6. 合并前检查清单 (Pre-Merge Checklist)

在合并 feature 分支到主分支前，必须完成以下检查：

### 6.1 功能检查
- [ ] 功能测试通过
- [ ] 单元测试通过
- [ ] 集成测试通过（如适用）

### 6.2 编码规范检查（必须）

> **注意**：编码规范检查是合并的硬性要求，未通过编码规范检查的代码不能合并。

- [ ] **前端编码规范**（如涉及）：
  - [ ] ESLint 检查全部通过
  - [ ] Prettier 格式化已运行
  - [ ] 目录结构和分层符合规范（参考 `.aodw-next/03-standards/stacks/react-typescript/ai-coding-rules-frontend.md`）
  - [ ] 文件大小和复杂度符合规范（页面 ≤ 300 行，组件 ≤ 200 行，函数 ≤ 60 行，复杂度 ≤ 10）
- [ ] **后端编码规范**（如涉及）：
  - [ ] Ruff 检查全部通过
  - [ ] Black 格式化已运行
  - [ ] 分层架构符合规范（api → services → repositories，参考 `.aodw-next/03-standards/stacks/python-fastapi/ai-coding-rules-backend.md`）
  - [ ] 文件大小和复杂度符合规范（模块 ≤ 300 行，函数 ≤ 60 行）
- [ ] **通用编码规范**：
  - [ ] 文件大小符合规范（参考 `.aodw-next/03-standards/ai-coding-rules-common.md`）
  - [ ] 函数/方法长度符合规范
  - [ ] 复杂度符合规范

### 6.3 文档检查
- [ ] 相关文档已更新（spec / plan / changelog）
- [ ] 模块 README 已更新（如涉及）

### 6.4 CI 检查
- [ ] CI 检查全部通过
- [ ] 代码覆盖率符合要求（如适用）

---

## 7. 自动化检查 (Automation)

AI 或 CI 工具应检查：

### Step 0: Knowledge Distillation (知识蒸馏) - **必须优先执行**
在合并代码前，必须检查：
1.  **模块文档更新**：本次改动是否修改了系统行为？如果是，对应的 `docs/modules/*.md` 是否已更新？
2.  **索引一致性**：`modules-index.yaml` 是否准确反映了当前的模块结构？

### Step 1: Git 规范检查
1.  当前分支名是否符合 `feature/RT-*` 格式。
2.  提交信息是否包含 `Refs: RT-*`。
3.  RT 完成时是否已创建对应的 `done-*` 标签。

### Step 2: 编码规范检查
1.  前端代码（如涉及）：ESLint 和 Prettier 检查是否通过
2.  后端代码（如涉及）：Ruff 和 Black 检查是否通过
3.  文件大小和复杂度是否符合规范

---

## 8. RT 完成流程 (Completion Workflow)

当 RT 的所有工作完成后，AI 按以下步骤逐一向用户确认并执行。

### Step 1：知识蒸馏（自动执行，无需确认）
1. 读取 `modules-index.yaml`，找到受影响的模块
2. 更新对应的模块文档（`docs/modules/*.md`）
3. 向用户报告更新结果

### Step 2：确认合并

AI 向用户确认：
> "RT-XXX 的知识蒸馏已完成。我准备将 feature/RT-XXX-short-name 合并到 master，使用 --no-ff 保留分支历史，随后打 done-RT-XXX 标签并推送到远程。合并后无法撤销。要我现在执行吗？"

用户确认后，AI 依次执行：
```bash
git checkout master
git pull origin master
git merge --no-ff feature/RT-XXX-short-name
git tag done-RT-XXX
git push origin master
git push origin done-RT-XXX
```

### Step 3：确认清理

AI 向用户确认：
> "RT-XXX 已成功合并并推送。我准备删除本地 worktree 目录 VoiceX-RT-XXX/ 和 feature/RT-XXX-short-name 分支，并更新 RT/index.yaml 状态为 done。要我现在执行吗？"

用户确认后，AI 依次执行：
```bash
git worktree remove ../VoiceX-RT-XXX
git branch -d feature/RT-XXX-short-name
# 更新 RT/index.yaml：RT-XXX status → done
```

### Step 4：播报完成

> "RT-XXX 全部完成。master 已更新，标签 done-RT-XXX 已推送，worktree 已清理。"
