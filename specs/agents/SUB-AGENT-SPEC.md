# Sub-Agent 模板规范

> 适用范围：工厂所有 Sub-Agent 定义。其他场景使用 Sub-Agent 时可参考同样的结构。

---

## 规范结构

Sub-Agent 模板包含 **8 个板块**，分三层：身份层、行为层、协作层。

```
Sub-Agent 模板
├── 身份层（接口签名）
│   ├── ① 角色定义
│   ├── ② 接收输入
│   └── ③ 输出要求
├── 行为层（工作规范）
│   ├── ④ 行为契约 ← 核心
│   ├── ⑤ 降级规则
│   └── ⑥ 行为红线
└── 协作层（交接协议）
    ├── ⑦ 交接协议
    └── ⑧ 触发时机
```

---

## 一、身份层（你是谁）

### ① 角色定义

一句话说清这个 Sub-Agent 做什么。

- 不是"你是一个 XX 者"的空标签，而是明确职责边界
- 示例：Validator 是"质量门控者"，不是"帮你检查文档的助手"

### ② 接收输入

明确它需要什么才能工作。

- 哪些文档、哪些上下文、哪些前置产出
- 这决定了 Orchestrator spawn 时要传什么参数

### ③ 输出要求

明确它必须交回什么。

- 文件路径、文件名规范
- 必须包含的字段
- 格式要求

> ①②③ 合在一起就是"接口签名"——Orchestrator 按这个来决定 spawn 参数和验收产出。

---

## 二、行为层（你怎么做）

### ④ 行为契约（核心）

定义工作质量和方法。包含三个维度：

**工作方法** — 具体步骤和方法论
- 示例：Interview 的"先开放邀请再补结构"、Generator 的"边界先行分步生成"

**质量标准** — 可检查的质量要求
- 示例：Validator 的"触发词检查"、Generator 的"输出风险预测"

**强制规则** — 必须执行的约束
- 示例：Interview 的"排除边界强制"、Generator 的"description 质量自检"

### ⑤ 降级规则

输入不完整或遇到阻塞时怎么办。

- **什么情况降级**：文档缺失、信息不足、争议无法判定
- **降级动作**：标注缺口 / 标注阻塞 / 交回 Orchestrator
- **不允许的动作**：不猜测、不杜撰、不降标准

### ⑥ 行为红线

绝对不能做的事。

- 每个角色有独占红线（如 Validator"不修改任何内容"、Reviewer"不参与被评审文档的修改"）
- 全局红线在 AGENTS.md 定义（Sub-Agent 禁止 Gateway 管理、进程管理等）

---

## 三、协作层（你和 Orchestrator/其他角色怎么配合）

### ⑦ 交接协议

和上下游角色的接口约定。

- 产出的交付物规范（路径、命名、格式）
- 交接时必须标注的信息（如"待填写项汇总为清单"、"来源标注"）
- 核心原则：Sub-Agent 之间需要明确的接口契约，不依赖隐含上下文

### ⑧ 触发时机

写在模板开头的 `>` 引用行。

- Orchestrator 在哪个阶段、什么条件下 spawn 这个角色
- 这不是 Sub-Agent 自己执行的，是 Orchestrator 的调度依据

---

## 最关键的两个板块

- **④ 行为契约**：决定产出质量
- **⑦ 交接协议**：决定协作效率

这两个板块是 Sub-Agent 从"能跑"到"可靠"的分水岭。

---

## 当前模板清单

| 模板 | 文件 | 适用场景 |
|------|------|----------|
| Interview | `specs/agents/interview.md` | L2 S1-S2：需求引导、业务摘要结构化 |
| Analyst | `specs/agents/analyst.md` | L2 S3：文档解析、能力盘点、缺口分析 |
| Generator | `specs/agents/generator.md` | L2 S3-S4：生成规范文档、SKILL.md |
| Validator | `specs/agents/validator.md` | 每步完成后：质量门控 PASS/FAIL |
| Assembler | `specs/agents/assembler.md` | L2 S5-S6：组装 workspace、追溯矩阵 |
| Reviewer | `specs/agents/reviewer.md` | 独立外部评审（审计独占） |
| Governance Officer | `specs/agents/governance-officer.md` | 治理合规记录（纯记录角色，行为契约简单） |
