# Git Discipline 摘要

## 0. 确认门控

AI 可执行所有 Git 操作，但不可逆操作（commit / merge / push / tag / worktree add-remove / branch delete）执行前**必须向用户确认**。

无需确认：读取文件、git log/status/diff、创建/切换分支。

## 1. 分支命名

格式：`feature/RT-{seq}-{short-name}`（kebab-case，2-4 词）
示例：`feature/RT-001-login-fix`

## 2. Worktree

一个 RT = 一个 Worktree = 一个 Feature 分支。
- 创建：Decision 阶段 `git worktree add ../Project-RT-XXX feature/RT-XXX-name`
- 清理：RT 完成合并后删除

## 3. 提交信息

格式：`<type>(<scope>): <subject>` + `Refs: RT-XXX`
示例：`fix(auth): handle token expiration — Refs: RT-001`

## 4. 标签

完成后打标签：`done-RT-XXX`

## 5. 合并

- 禁止 fast-forward，使用 `--no-ff`
- 合并前必须通过 lint + test + 编码规范检查

## 6. 完成流程

知识蒸馏 → 确认合并 → 确认清理 → 播报完成
