# Hermes Agent Kanban 自动拆解任务升级：Triage + Orchestrator 自动分派

> 来源：今日头条 - 鹏叔大玩家
> 链接：https://m.toutiao.com/is/u3nqsrjPQGM/ | 原文：https://toutiao.com/group/7641159177989063168/
> 调研日期：2026-05-22

---

## 概述

Hermes Agent（Nous Research 开源项目）在 Kanban 看板功能上再次升级，新增 **Triage（分诊）自动拆解**和 **Agent Profile 画像描述**两大特性。用户只需在看板的 Triage 列丢一句话需求，Orchestrator 智能体即可自动拆解子任务、按角色能力分派、链接依赖关系并执行。此次升级由 Teknium（Hermes Agent 联合创始人兼首席工程师）于 2026 年 5 月 18 日在 X 平台公布。

## 核心功能

### 1. Triage 自动拆解（Auto-Decomposition）

**之前**：用户需手动创建多个看板卡片，逐一指派角色、设置依赖——谁先干、谁后干、谁等谁的结果，全部人工安排。

**现在**：用户在 Triage 列输入一句话（如"研究整个云迁移方案"），Orchestrator Agent 自动：

- **拆解**：大目标 → 多个子任务（成本研究、性能对比、方案合成、报告撰写）
- **指派**：根据每个子任务所需能力，匹配对应 Agent Profile
- **链接依赖**：并行任务（成本研究 || 性能对比）→ 合成任务等待 → 最终报告

**触发方式**：在看板卡片上点击 ⚗ Decompose 按钮，或通过 CLI `hermes kanban decompose` 命令。

### 2. Agent Profile 画像描述

新增对每个 Agent Profile（角色）的文字描述字段。例如：

- `researcher`："适合做文献调研、数据分析、竞品对比，擅长读取和总结大量文本"
- `code-worker`："适合做代码编写、调试、测试，擅长工程实现"

Orchestrator 读取描述后，能精准判断任务归属，不再仅靠 Profile 名称猜测。

### 3. 底层架构：持久化工作队列

Kanban 看板的核心是 SQLite 数据库（`~/.hermes/kanban.db`），每个任务一行记录，状态机驱动：`triage → todo → ready → running → blocked → done → archived`。

**与一次性委托（delegate_task）对比**：

- **主进程阻塞**：一次性委托会阻塞 → Kanban 不会（fire-and-forget）
- **故障恢复**：一次性委托无法恢复 → Kanban 支持 block → unblock → re-run
- **人类介入**：一次性委托不支持 → Kanban 随时 comment / unblock
- **审计记录**：一次性委托丢失 → Kanban 永久 SQLite 记录
- **跨角色接力**：一次性委托不支持 → Kanban 天然支持

## 技术栈

| 组件 | 技术 |
|------|------|
| Agent 框架 | Hermes Agent (Nous Research) |
| 存储层 | SQLite（看板持久化） |
| 调度器 | 内嵌 Dispatcher + 状态机 |
| 语言 | Python |
| 协议 | kanban_* 工具集（kanban_show, kanban_list, kanban_complete 等） |
| License | MIT |

## 关键数据

- GitHub Stars：**162,299**（截至 2026-05-22，GitHub API 实查）
- Forks：26,454
- Open Issues：13,024
- 首次发布：2025-07-22
- 官方文档：https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban
- 社区讨论：Reddit r/hermesagent 活跃讨论中

## 隐含项目发现

| 项目名 | Star 数 | 更新时间 | 与原内容关联 |
|--------|---------|---------|------------|
| NousResearch/hermes-agent | 162,299 | 2026-05-22 | ✅ 文章主题项目，数据一致 |

## Claim 验证

| # | 作者原话 | 声称数据 | 实际核查 | 结论 |
|---|---------|---------|---------|------|
| 1 | "Teknium 是 Hermes Agent 联合创始人兼首席工程师" | Teknium 身份 | Teknium 确实是 Nous Research 联合创始人，Hermes Agent 核心开发者 | ✅ 已验证 |
| 2 | "一句话拆成 N 个任务，AI 自动分派" | Triage 自动拆解功能 | 官方文档确认 Kanban Decompose 功能存在，支持 Triage 列自动拆解 | ✅ 已验证 |
| 3 | "智能体画像描述"新增功能 | Agent Profile 描述字段 | 官方 Kanban 文档确认 Worker Lanes 和 Profile Description 功能 | ✅ 已验证 |
| 4 | "每个任务都是 SQLite 数据库里的一行记录" | SQLite 存储 | 官方文档确认 `~/.hermes/kanban.db` 为存储后端 | ✅ 已验证 |
| 5 | "子智能体断了能恢复" | 故障恢复能力 | Kanban vs delegate_task 对比表确认 block/unblock/re-run 机制 | ✅ 已验证 |
| 6 | 隐含暗示：这是"大升级" | 版本级别判断 | 基于已有 v0.13.0 (2026-05-07)，此升级可能对应 v0.14 或 patch release，属于 Kanban 功能迭代 | ⚠️ 属于功能迭代，非架构级升级 |

注：文章内容与官方文档高度一致，无夸大或不实信息。唯一需要注意的是，文章将此次功能更新描述为"大升级"，实际上更接近 Kanban 功能的持续迭代增强。

## 对比分析

**与上次调研（K-260508-008, Hermes v0.13.0 Tenacity Release）对比**：

- v0.13.0（2026-05-07）：Stars 138,536 → 本次 162,299，**15 天增长 23,763 Stars**，增速极快
- v0.13.0 首次引入完整 Kanban 看板 → 本次升级是 Kanban 的功能增强（自动拆解 + 画像描述）
- Worker Lanes 和 Profile Description 是在 v0.13.0 Kanban 基础上的自然演进

**与其他多 Agent 框架对比**：

- Hermes Kanban 更侧重**本地部署 + SQLite 持久化**场景
- OpenClaw 的 Code Agent 平台更侧重**云端多 Agent 编排 + 实时审批**
- 两者在多 Agent 协作理念上有交集，但部署场景差异明显

## 应用场景

- **研究调研管线**：并行研究 → 分析 → 写作，人类在关键节点介入审查
- **工程流水线**：需求拆解 → 并行开发（worktree）→ 代码审查 → PR
- **定时运维**：每日自动报告生成，多角色接力
- **数字孪生**：持久命名的助手（inbox-triage、ops-review），随时间积累记忆
- **批量运营**：一个管理者同时管理 N 个账号/服务

## 局限性

- 文章作者"鹏叔大玩家"非原创内容，是对 Teknium 公告的二次解读，信息深度有限
- 文章以比喻为主（"大排档点菜"等），对技术细节描述较少
- Kanban 目前基于本地 SQLite，尚无分布式存储方案的官方文档
- 自动拆解依赖 Orchestrator 的模型能力，复杂需求可能拆解不准确
- Profile 描述的有效性取决于用户配置质量

## 个人洞察

结合我们已有的两次 Hermes 调研（K-260508-008 v0.13.0、K-260516-030 Kanban 实战教程），可以看到 Hermes Agent 在 Kanban 方向上的持续加码：从 v0.13.0 的完整看板落地，到现在的 Triage 自动拆解 + Profile 画像描述，Kanban 正在从"需要手动配置的任务板"进化为"近乎自治的项目管理系统"。

值得关注的趋势：
1. **Hermes Star 增速惊人**：15 天 +23K，说明社区对多 Agent 协作的需求非常强烈
2. **Triage 自动拆解**与 OpenClaw 的 Code Agent 工作流在理念上趋同——都是"人只说一句话，系统自动编排"
3. Hermes 的 SQLite 持久化方案在单机场景够用，但面对跨团队/跨地域协作可能需要向分布式演进

对想尝试的用户建议：直接阅读官方 Kanban 文档和 Kanban Tutorial，比头条文章更准确完整。

---

*调研时间：2026-05-22*
*档案编号：K-260522-055（待归档确认）*
