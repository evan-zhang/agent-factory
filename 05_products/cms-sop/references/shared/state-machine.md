# 已加载 state-machine.md

## status 完整定义（13个状态）

| 状态 | 含义 |
|---|---|
| DISCUSSING | 讨论中，尚未确认 |
| READY | 已就绪，等待执行 |
| RUNNING | 执行中 |
| REVIEWING | 审查/复核中 |
| WAITING_USER | 等待用户输入/确认 |
| BLOCKED | 阻塞中 |
| PAUSED | 主动暂停 |
| ON_HOLD | 搁置中 |
| CANCELLED | 已取消 |
| DONE | 已完成 |
| ARCHIVED | 已归档 |
| HANDOVER_PENDING | 交接中 |
| UPGRADED | 已升级到 Full |

## stage 完整定义（6个阶段）

| 阶段 | 含义 |
|---|---|
| TARGET | 目标定义阶段 |
| PLAN | 计划制定阶段 |
| CHECKLIST | 确认单阶段 |
| EXECUTE | 执行实施阶段 |
| ARCHIVE | 归档阶段 |
| DONE | 完成 |

## mode 字段

| 值 | 含义 |
|---|---|
| lite | 轻量模式，预计≤20分钟，单系统，单次确认 |
| full | 完整模式，无限制，复杂任务，多轮确认 |

## 合法状态转换表

| 当前状态 | 可转换到 |
|---|---|
| DISCUSSING | READY, CANCELLED, UPGRADED |
| READY | RUNNING, CANCELLED, UPGRADED |
| RUNNING | REVIEWING, WAITING_USER, BLOCKED, PAUSED, DONE, ON_HOLD |
| REVIEWING | RUNNING, WAITING_USER, BLOCKED, PAUSED, DONE, ON_HOLD |
| WAITING_USER | RUNNING, READY, CANCELLED |
| BLOCKED | RUNNING, PAUSED, ON_HOLD, CANCELLED, UPGRADED |
| PAUSED | RUNNING, READY, ON_HOLD, CANCELLED |
| ON_HOLD | RUNNING, READY, CANCELLED, UPGRADED |
| CANCELLED | ARCHIVED |
| DONE | ARCHIVED |
| ARCHIVED | （终态） |
| HANDOVER_PENDING | READY, RUNNING, CANCELLED |
| UPGRADED | （终态） |
