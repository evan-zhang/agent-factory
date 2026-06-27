# 模式选择指南

## 边界声明

Ralph Loop 和 OpenClaw Goal Mode 是**两个独立项目，互不依赖**。

- **Ralph Loop**（本项目）：基于 CLI 执行器（Claude Code / Codex）的持续编程循环，适合多阶段、长流程、需要机械验证的硬核编程任务。
- **OpenClaw Goal Mode**（OpenClaw 内置功能）：单 session 内的目标追踪，适合中等任务，不需要安装额外 CLI。

用户根据任务特征自行选择，不存在谁包装谁的关系。

## 第一层：用 Ralph Loop 还是 OpenClaw Goal Mode

| 维度 | Ralph Loop | OpenClaw Goal Mode |
|------|-----------|-----------|
| 上下文管理 | 每次迭代全新（天然隔离） | 单 session 累积（压缩风险） |
| 完成检测 | state.json + verify.sh 机械判断 | AI evaluator 语义判断 |
| 跨重启持久化 | 原生支持（state.json） | 需 `--resume`，不保证 |
| 自动回滚 | git reset + clean（失败迭代自动丢弃） | 无（坏改动留在 session 里） |
| 执行器依赖 | 需要本机装 Claude Code 或 Codex CLI | 不需要，用 OpenClaw 配置的模型 |
| 额外 token 成本 | 无（仅 Worker） | 有（Worker + Evaluator 每个 turn） |
| 适合任务 | 多阶段、长流程、> 100K tokens | 单 session 可完成的中等任务 |
| 核心风险 | 过度烘焙、规格差 | 过早终止、token 爆炸 |

## 决策树

```
任务开始
  │
  ├─ 单 session 可完成（< 30 分钟）？
  │   └─ 是 → OpenClaw Goal Mode
  │
  ├─ 没装 Claude Code / Codex CLI？
  │   └─ 是 → OpenClaw Goal Mode
  │
  ├─ 有明确的阶段划分（多 Phase）？
  │   └─ 是 → Ralph Loop
  │
  ├─ 预计上下文 > 100K tokens？
  │   └─ 是 → Ralph Loop
  │
  ├─ 需要跨重启持久化？
  │   └─ 是 → Ralph Loop
  │
  └─ 默认 → Ralph Loop（更安全）
```

## 第二层：Ralph Loop 内部 — 执行者模式 vs 自主者模式

| 维度 | 执行者模式（Executor） | 自主者模式（Autonomous） |
|------|----------------------|----------------------|
| 谁规划路径 | 人 | AI |
| 谁定义完成标准 | 人 | AI（人确认） |
| 过程记录 | 无（仅 checklist） | journal 详细记录 |
| 适合场景 | 目标+步骤都已知 | 目标已知，路径未知 |
| 人的参与度 | 高（写 checklist） | 低（只给目标） |
| 核心风险 | checklist 不完整 | AI 规划偏航 |

选定 Ralph Loop 后：
```
  │
  ├─ 能预判所有完成条件？
  │   └─ 是 → 执行者模式
  │
  ├─ 用户说"AI 自己来"/"以终为始"？
  │   └─ 是 → 自主者模式
  │
  └─ 默认 → 执行者模式
```

## OpenClaw Goal Mode 最佳实践（供参考）

> 以下内容仅帮助用户判断何时应该切换到 OpenClaw Goal Mode，不表示本项目集成了 Goal Mode。

Goal Mode 使用 `/goal` 命令，条件最多 4000 字符。

**好的条件**：
```
/goal 修复 src/components/*.tsx 中所有 TypeScript 编译错误。
完成条件：tsc --noEmit exit code 0 且无输出
```

**差的条件**：
```
/goal 修复 bug        ← 太模糊
/goal 让代码更好       ← 无法量化
```

**公式**：范围（什么文件） + 证据（什么证明完成） + 测试（怎么验证）

## 混合策略

对于复杂项目，两者可以独立使用但各走各的路：

1. **Ralph Loop** 完成多阶段主体工作（需要装 Claude Code / Codex）
2. **OpenClaw Goal Mode** 处理中途发现的小修小补（不需要额外安装）
3. **交互模式** 做架构决策和方案讨论

Ralph Loop 的状态在 state.json 里，Goal Mode 的状态在 OpenClaw session 里，互不同步。
