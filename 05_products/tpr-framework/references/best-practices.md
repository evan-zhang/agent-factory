# Orchestrator & Multi-Agent 最佳实践

> 来源：Claude Code Agent Teams + 工厂实践经验
> 建立时间：2026-04-05

---

## Orchestrator 职责边界

### 核心原则：框架 > 模型能力

Orchestrator 负责协调，不负责执行。

### 可以做的（Orchestrator）
- 分解任务、分配任务
- 维护任务状态和依赖关系
- 做决策和判断
- 读取文件获取上下文

### 不可以做的（Orchestrator）
- 不做执行工作（写代码、写文档）
- 不做深度审查（那是 Menxi 的工作）
- 不同时做两个以上角色的工作

### 允许的直接操作（低风险）
- 更新任务追踪文件
- 发送状态通知
- 读取/检查文件内容

---

## Read-Only First 原则

复杂任务分两个阶段：
1. **Read-only 阶段**：先派只读的 agent 收集上下文
2. **Write/Execute 阶段**：再派执行的 agent

这样可以避免上下文冲突。

---

## 上下文加载原则

### 不要这样做
```
task: You are X. Here is the full GRV: [粘贴 200 行文档...]
```

### 正确做法
1. 将上下文写入文件（如 `temp/context-001.md`）
2. 在 task 里只写文件路径和读取指令
3. 告诉 sub-agent 什么时候读、为什么读

```
task: You are X.
Read the GRV at {path}/temp/context-grv-001.md before starting.
Raise objections and write to {path}/temp/menxi-report-001.md.
```

---

## Multi-Agent 任务管理

### 必须定义的要素

| 要素 | 说明 |
|------|------|
| 任务状态 | pending / in_progress / completed / blocked |
| 依赖关系 | 哪些任务必须先完成 |
| 文件锁 | 同一文件只能有一个 agent 写 |
| 进度通知 | 用 announce，不用轮询 |

### 依赖管理规则
- A 依赖 B → B 必须完成才能启动 A
- 依赖未满足时，任务保持 pending
- 完成一个任务后，自动解锁依赖它的任务

### 并发限制
- 最多 4 个并发 sub-agent
- 超过时等待其中一个完成

---

## 自我改进机制

### 必须维护的文档

| 文档 | 更新频率 | 内容 |
|------|---------|------|
| task-tracker.md | 每次 spawn/完成 | 任务状态、依赖关系 |
| corrections.md | 每次犯错时 | 错误、修正、预防 |
| patterns.md | 每周复盘 | 成功模式、失败模式 |

### 触发自我反省的条件
- Orchestrator 自己干了 sub-agent 该干的事（越界）
- sub-agent 因为上下文问题需要重新执行
- 用户明确指出任务管理有问题
