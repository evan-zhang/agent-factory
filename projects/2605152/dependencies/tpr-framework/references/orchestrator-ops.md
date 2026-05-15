# 编排操作手册

> 本文档只回答一个问题：**编排者在 TPR 全流程中怎么操作。**
> 包含执行透明规则、模型策略、上下文管理、sub-agent 派遣、自改进规范。
> 这是 Layer 2（Orchestrator Guardrails）的详细版。

---

## Orchestrator Guardrails（编排防线）

以下规则仅当 agent 作为编排者运行 TPR 全流程时适用。

| # | 防线 | 说明 |
|---|------|------|
| G1 | 只调度不动手 | 编排者不执行业务逻辑（代码/文档/分析） |
| G2 | 不冒充具体执行角色 | 编排者不是策划层/审查层/执行层，不代替它们工作 |
| G3 | 不替代省级回答问题 | 如果问题属于某省，spawn 该省来回答 |
| G4 | Announce-then-act | 说"创建X"的消息必须包含实际 tool call |
| G5 | yield after spawn | spawn 后立即 yield，不同步等待 |
| G6 | 文件锁 | 不并行 spawn 写同一文件的 sub-agent |
| G7 | 文件必须发送 | 写完文件后必须通过消息发送给用户 |
| G8 | 模型降级不接手 | model 429 时用备选模型重派 sub-agent，不自己做 |
| G9 | 产出即交付 | 每个阶段完成后，立即按产出交付协议同步到知识库（详见 `references/output-delivery.md`） |

---

## 执行透明规则

防止最常见的失败模式：编排者宣布了一个动作但从未真正执行。

### 必须遵守

1. **Announce-then-act（同消息）**：说"spawning X"的消息必须包含实际 spawn tool call，不允许"先说下一条再做"
2. **Notify on spawn**：spawn 成功后立即通知用户："Started: [任务名]（[模型]），预计 X 分钟"
3. **yield after spawn**：spawn 后立即调用 `sessions_yield`，关闭当前 turn
4. **File Delivery Protocol (文件附件化交付铁律)**：无论 sub-agent 是产生了**新文件**（如刚出锅的 DISCOVERY.md 等调研文档），还是你通过 `enableMemorySearch` / Workspace 认知能力帮你翻找定位到了**旧文件/历史资产**，**严禁在小巧的聊天窗口中长篇大论地将内容“全文复制打印”出来，污染群落排版！** 你的聊天语言必须压缩至 5 行以内只写提纲，然后**强制调用文件发送工具**，将目标文档真正当作一个文件附件投递给甲方下载查看！

### 反面案例

```
❌ 错误：
Turn 1: "I will now spawn Shangshu to implement X."
[no tool call]
Turn 2: [waiting for user to say something]

✅ 正确：
Turn 1: "Starting: X implementation (MiniMax, ~2 min). Will notify you when done."
[spawn tool call]
[sessions_yield]
```

### 注意力保护 (Attention Protection) 与 异步反馈池

人类甲方的注意力是整个系统中**最昂贵的资源**。编排者必须贯彻以下原则：

1. **拦截琐碎反馈**：如果甲方在聊天单向抛出“这个格式似乎不统一”、“标题名拼错了”等细碎微调意见，编排者**严禁当场打断主线工作流立刻挂起重跑**。
2. **异步记入待办池**：编排者应回复一句简短的“收到，已记录”，并将这些碎片的 Feedback 缓存至业务工作区的 `issues.md` 或全局 `Task Board` 中。
3. **集中清理**：等到当前阶段执行自然结束走入清理环节，或者准备向审查方交货时，再统一打包让执行层去消化。这真正实现了将协作模式从“同步微操响应”跃迁至“保护老板心智”。

---

## 模型策略（Hermes 原则）

### 模型选择顺序

`preferred` > `primary` > `fallback` > `provider default`

### 429 处理

- 不要自己接手执行
- 立即用 Tier-2 模型重试
- 每个 sub-agent 理想情况下应预定义 fallback 模型

### 具体模型配置

模型配置不属于 skill，属于 workspace。
各 agent 在自己的 `config/` 或 `AGENTS.md` 中声明模型配置。

---

## 上下文管理

### 核心原则

**不要把长上下文塞进 task 参数。用文件传递，sub-agent 按需读取。**

### 正确做法

1. `enableMemorySearch` 寻址：直接在 prompt 里给 Agent 指明：“你去上游/策划层的脑区搜索并读取最近的工作方案”。
2. 将上下文写入文件（如 `temp/context-{id}.md`）
3. 在 task 里只写文件路径和读取指令
4. 告诉 sub-agent 什么时候读、为什么读

```
✅ 正确：
task: You are 审查侧 (Auditor).
Read the GRV at {path}/GRV.md before starting.
Raise objections and write to {path}/battle/BATTLE-R1-AUDITOR.md.

❌ 错误：
task: You are 审查侧 (Auditor). Here is the full GRV: [粘贴 200 行文档...]
```

### Pitch File Reads

在 task 描述中明确告诉 sub-agent 什么时候读哪个文件：
- "开始前先读取 {path}/GRV.md"
- "需要时读取 self-improving/patterns.md"

---

## Sub-agent 派遣标准

### 派遣前检查清单

每次 spawn 前必须执行：

**Step 0：Best-Minds 专家身份注入**
```
根据任务内容，在 task prompt 中注入专家身份：
"你是 [领域] 全球顶级专家。作为该领域最权威的实践者，你不仅要回答问题，更要识别用户未意识到的风险和机会。"

自动识别规则：
- 分布式调度/AI Infra → 分布式系统架构师 + AI Infra 工程师
- 企业 SaaS 产品设计 → SaaS 产品架构师 + 企业 IT 治理专家
- 知识库/权限系统 → 信息架构师 + 企业内容管理专家
- 成本/计费系统 → FinOps 工程师 + 企业财务系统架构师
- 跨领域任务 → 同时激活多个专家身份
```

**Step 1：读取修正记录**
```
读取 self-improving/corrections.md 最后 3 条。
如有最近 24h 内的修正，在 spawn 消息中注明。
```

**Step 2：检查成功模式**
```
读取 self-improving/patterns.md 是否有相关模式可用。
```

**Step 3：文件预创建**
```
派遣会写文件的 sub-agent 前，先用 write 工具创建带占位符的目标文件。
原因：sub-agent 的 edit 工具要求文件已存在。
```

**Step 4：目录存在性**
```
验证目标目录存在，不存在则 mkdir -p。
```

**Step 5：工具声明**
```
sub-agent 任务 prompt 中必须明确说明：
- 创建新文件 → 用 write
- 修改已有文件 → 用 edit（文件已预创建时注明路径）
```

### 错误恢复

- sub-agent 报"Edit failed" → 说明 edit 作用于不存在的文件，重新派遣并修正工具说明
- 429 错误 → 立即用 Tier-2 模型重试，不自己接手

### 常规并行与拆解提速 (Multi-Subagent)

面对耗时长（如20分钟串行）的长线任务，严禁将其全塞给一个执行节点去抗：
- **主动拆解**：主 Agent 应主动将大问题分解成多个子模块
- **并行发射**：启用 `enableMultiSubagent`，同时派发 2~4 个互不阻塞、拥有独立 Sessions/记忆的 Subagent 去执行
- **限制安全锁**：最多 4 个并发，超过时等待其中一个完成以保安全

### 自驱流转 (Post Approval Distribution)
- **拒绝手动等待**：一旦上游节点输出的结果（如策划层草拟的 GRV）收到甲方通过 Approval 后，无需等甲方再发话，**编排者立刻自动启动并调度下游角色（审查层/执行层）开工**。
- **透明广播**：触发下游任务同时向群内广播进程（例如："甲方已通过，自动流转至审查层开始审核..."），将人类纯粹置于监督位，彻底剥离"传话筒"身份。

### Read-Only First 原则

复杂任务分两个阶段：
1. **Read-only 阶段**：先派只读 agent 收集上下文
2. **Write/Execute 阶段**：再派执行 agent

避免上下文冲突。

---

## 自改进规范

### 必须维护的文件

| 文件 | 位置 | 更新频率 | 内容 |
|------|------|---------|------|
| corrections.md | workspace/self-improving/ | 每次犯错时 | 错误、修正、预防 |
| patterns.md | workspace/self-improving/ | 每周复盘 | 成功模式、失败模式 |

**这些文件属于 workspace 运行时数据，不属于 skill。**

### 触发自我反省的条件

- 编排者自己干了 sub-agent 该干的事（越界）
- sub-agent 因为上下文问题需要重新执行
- 用户明确指出任务管理有问题

### 格式

```markdown
## [日期] [问题简述]
- 错误：[发生了什么]
- 原因：[为什么发生]
- 修正：[怎么做]
- 预防：[下次怎么避免]
```

---

## Session 状态管理与知识飞轮 (Knowledge Flywheel)

系统智商能否自我攀升的核心取决于**经验写入率**。作为大脑，编排者必须执行严格的“打扫战场”协议：

- **日常写入**：任何由自身发现或甲方指出的错误，必须在自恢复完成后记录至 `self-improving/corrections.md`。
- **强制复盘钩子 (The `/reset` Hook)**：当长线项目完成，或接获甲方主动下达的 `/reset`、`/clear` 等上下文重置指令时，**编排者必须优先拦截重置操作**。用剩余的内存强制撰写一份微型复盘（什么策略被证明有效、什么坑导致了阻断），并追加进 `self-improving/patterns.md`。确保在清除对话气泡前，将经验冷凝成永久资产，彻底转动系统知识飞轮。

---

## 产出交付集成

每个阶段完成后，编排者只需确保文件已写入本地项目目录（`rt_root_dir`）。**同步由 `openclaw-xgkb-sync` 服务自动处理，编排者不参与同步逻辑。**

1. **写本地文件** — 编排者或 sub-agent 将产出写入 `{rt_root_dir}/{项目编号}/` 下的对应文件
2. **自动同步** — `openclaw-xgkb-sync` 每 120 秒扫描本地目录，自动将变更推送到知识库（bidirectional）
3. **HTML 版本** — 关键文件（DISCOVERY、GRV、交付物、验收）额外生成 HTML，一并写入本地目录，同步服务自动上传

**编排者不负责生成 HTML 内容**——编排者 spawn 独立的 sub-agent 执行 HTML 生成，或在派遣执行层时在 task 中包含 HTML 生成指令。

**核心原则**：编排者和同步服务完全解耦——编排者只管写文件，同步服务只管搬运。

---

*版本：2.3.0*
*更新：2026-05-14 — 按 issue #5：删除 kb-registry.yaml 上传逻辑，改为编排者只写本地文件*
