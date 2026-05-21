# 模式选择指南

## 三层选择

### 第一层：Goal Mode vs Ralph Loop

| 维度 | Ralph Loop | Goal Mode |
|------|-----------|-----------|
| 上下文管理 | 每次迭代全新（天然隔离） | 单 session 累积（压缩风险） |
| 完成检测 | state.json 机械判断 | Haiku evaluator 语义判断 |
| 跨重启持久化 | 原生支持（state.json） | 需 `--resume`，不保证 |
| 额外 token 成本 | 无（仅 Worker） | 有（Worker + Evaluator 每个 turn） |
| 适合任务 | 多阶段、长流程、> 100K tokens | 单 session 可完成的中等任务 |
| 核心风险 | 过度烘焙、规格差 | 过早终止、token 爆炸 |

### 第二层：执行者模式 vs 自主者模式（Ralph Loop 内部）

| 维度 | 执行者模式（Executor） | 自主者模式（Autonomous） |
|------|----------------------|----------------------|
| 谁规划路径 | 人 | AI |
| 谁定义完成标准 | 人 | AI（人确认） |
| 过程记录 | 无（仅 checklist） | journal 详细记录 |
| 适合场景 | 目标+步骤都已知 | 目标已知，路径未知 |
| 人的参与度 | 高（写 checklist） | 低（只给目标） |
| 核心风险 | checklist 不完整 | AI 规划偏航 |

## 决策树

```
任务开始
  │
  ├─ 单 session 可完成（< 30 分钟）？
  │   └─ 是 → Goal Mode
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

选定 Ralph Loop 后：
  │
  ├─ 能预判所有完成条件？
  │   └─ 是 → 执行者模式
  │
  ├─ 用户说"AI 自己来"/"以终为始"？
  │   └─ 是 → 自主者模式
  │
  └─ 默认 → 执行者模式
```

## Goal Mode 最佳实践

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

对于复杂项目，可以混合使用：

1. **Ralph Loop** 完成多阶段主体工作
2. **Goal Mode** 处理中途发现的小修小补
3. **交互模式** 做架构决策和方案讨论

三者共享同一个 state.json（如果使用的话），保持状态一致。
