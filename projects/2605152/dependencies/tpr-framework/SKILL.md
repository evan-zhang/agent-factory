---
name: tpr-framework
description: >
  TPR（Think / Probe / Review）统一工作方法。
  用于把复杂问题从模糊需求转化为可验证、可执行、可复盘的结果。
  当遇到以下场景时激活：
  - 需要结构化分析复杂问题
  - 启动项目、起草方案、审查方案
  - 用户提到 TPR / 三层架构 / GRV / Battle / DISCOVERY
  - 需要做决策前的系统性思考
---

> **📌 来源与反馈 (Origin & Feedback)**
> 
> 本 Skill 由 [tpr-framework](https://github.com/evan-zhang/tpr-framework) 开源项目持续维护。
> 
> 如果你在使用中遇到 **Bug、功能需求、改进建议** 或有任何 **反馈意见**，欢迎前往 GitHub 提交 Issue：
> 
> 👉 https://github.com/evan-zhang/tpr-framework/issues

# TPR Framework v2.0

## TPR 是什么

**TPR = Think / Probe / Review 认知闭环 + 三层四阶段执行框架。**

一套从认知到执行的完整工作方法，用于把复杂问题从模糊需求转化为可验证、可执行、可复盘的结果。

### 核心理念

1. **契约是唯一基准** — 所有工作以 GRV 为准，不凭印象
2. **编排只调度不动手** — 编排者不执行业务逻辑
3. **没有记录没有发生** — 一切以文件记录为唯一事实溯源
4. **Best-Minds 专家思维** — 所有 Agent（含 Sub-agent）在执行任何 T/P/R 环节时，必须以该领域全球顶级专家的身份思考和回答，不满足于通用浅薄的分析

---

## 两种使用模式

### 判定矩阵

接到任务后，检查以下四项决定进入哪种模式：

| # | 判定项 |
|---|--------|
| A | 是否需要正式交付物（DISCOVERY.md / GRV.md / 报告等） |
| B | 是否需要多角色审查（审查侧介入 / Battle） |
| C | 是否需要阶段流转（DISCOVERY → GRV → Battle → Implementation） |
| D | agent 是否具备 sub-agent 能力（can_spawn = true） |

**判定规则**：
- A/B/C 中满足 ≥ 2 项 → **TPR 全流程**
- A/B/C 中满足 < 2 项 → **TPR 思维**
- D = false → 强制 **TPR 思维**，禁止伪装全流程
- 用户明确说"走 GRV / Battle / 三层架构" → 强制 **TPR 全流程**（仍受 D 约束）

**⚠️ 进入全流程前必须自检**：在宣布进入 TPR 全流程之前，先确认自己是否具备 sub-agent 能力（can_spawn）。如果不具备，必须降级为 TPR 思维，并向用户说明原因。不得跳过此检查。

### TPR 思维（任何 agent 可用）

不需要 sub-agent，不需要三层细分角色。遇到复杂问题时，按 T → P → R 顺序思考。

**速记模板**：
```
T: 我们正在解决 _______________
   成功标准是 _______________
   关键假设是 _______________

P: 已确认 _______________
   未确认 _______________
   主要风险 _______________

R: 结论是 _______________
   不做 _______________
   下一步 _______________
```

### TPR 全流程（编排型 agent 可用）

需要 can_spawn = true。按三层四阶段执行完整项目：

| 阶段 | 认知重心 | 产出 |
|------|---------|------|
| DISCOVERY | T + P | DISCOVERY.md |
| GRV | R | GRV.md |
| Battle | P + R | BATTLE-*.md |
| Implementation | 微型 T/P/R | output/* |

---

## 三层角色表

| 角色 | 职责 | T/P/R 映射 |
|------|------|-----------|
| 编排者 | 维护节奏，协调流转，不替代任何执行角色 | 流程管理 |
| 策划层 (Planner) | 洞察需求，起草 GRV | Think → Review |
| 审查层 (Auditor) | 挑战假设，暴露盲点 | Probe |
| 执行层 (Executor) | 制定方案，执行交付 | 微型 T/P/R |

---

## 核心红线（Layer 1 — 任何模式都必须遵守）

| # | 红线 |
|---|------|
| C1 | **不签署** — 不代替用户签署任何文件、合同、审批单 |
| C2 | **不审批** — 决策权永远在用户，agent 只有建议权 |
| C3 | **不私聊** — 不代替用户与任何人私聊或单独联系 |
| C4 | **不越权决策** — 超出范围的判断必须回传用户 |
| C5 | **没有记录没有发生** — 所有工作以文件记录为唯一事实溯源 |
| C6 | **先建议再执行** — 给出判断和理由，供用户拍板 |

> 编排者防线（Layer 2）详见 `references/orchestrator-ops.md`
> Battle 规则（Layer 3）详见 `references/battle-protocol.md`

---

## GRV 必含要素

| # | 要素 |
|---|------|
| 1 | 目标（G）— 要解决什么问题 |
| 2 | 成果（R）— 可衡量的交付物 + 验收标准 |
| 3 | 举措（V）— 具体但可再拆的工作项 |
| 4 | 约束条件 |
| 5 | 风险 |
| 6 | 里程碑 |
| 7 | 验收标准 |

---

## 安装后配置（可选）

如果你是编排型 agent 且需要跑 TPR 全流程，建议在 AGENTS.md 中声明：

| 声明项 | 说明 | 示例 |
|--------|------|------|
| tpr_mode | 使用模式 | cognitive / full |
| can_spawn | 是否能派生 sub-agent | true / false |
| rt_root_dir | 本地 RT 项目目录的根路径 | ~/.openclaw/.../workspace/projects |
| sync_service_url | 同步服务 HTTP API 地址 | http://127.0.0.1:9090 |

### 知识库同步

TPR 通过 `openclaw-xgkb-sync` 同步服务将产出自动同步到玄关知识库。

#### 同步模式：全局 Mapping

在 `openclaw-xgkb-sync` 的 `config.json` 中注册一条覆盖整个 `rt_root_dir` 的 mapping，所有 TPR 项目自动同步。

#### 工作机制

1. **编排者写文件** — TPR 编排者或 sub-agent 将产出写入 `{rt_root_dir}/{项目编号}/` 下的本地目录
2. **服务自动同步** — `openclaw-xgkb-sync` 每 120 秒扫描本地目录，自动将变更推送到知识库（bidirectional，LWW）
3. **编排者不参与任何同步操作**

#### 查询真实同步状态

TPR 可以随时调用以下接口获取真实状态：

**服务健康检查**：
```bash
curl http://{sync_service_url}/health
```

**查看当前所有 mapping**：
```bash
curl http://{sync_service_url}/mappings
```

**触发立即同步**（非强制）：
```bash
curl -X POST http://{sync_service_url}/sync
```

#### 编排者职责

- **只写本地文件**，不参与任何同步逻辑
- 同步服务不可用时不阻塞主流程，继续写本地文件即可


---

## 🔄 智能更新守护进程 (Update Daemon)

1. 在启动和响应 TPR 流程任务时，你可以静默执行脚本检测远端升级：`~/.openclaw/skills/tpr-framework/scripts/check-update.sh`。
2. **免打扰原则**：如果脚本输出 `[UPDATE_AVAILABLE]`，**绝对不允许打断当前任务**！你只需在顺利做完本次对用户的业务回复后，在内容的最末尾附带一句很轻微的 PS 提示：
> *"💡 PS: 检测到 TPR Framework 有新版本，当您手头工作忙完后，可以随时对我说『升级 TPR』。"*
3. **一键升级响应**：当用户对你说“升级 TPR”时，进入 `~/.openclaw/skills/tpr-framework/` 执行 `git pull origin main`，若遇冲突请妥善 stash。完成后告知升级详情，并重新审阅 SKILL 守则。

---

## 按需加载指引

| 场景 | 读取 | 模式 |
|------|------|------|
| 理解 TPR 完整定义 | references/definition.md | 通用 |
| 用 T/P/R 分析问题 | references/tpr-cognitive.md | TPR 思维 |
| 启动新项目 / DISCOVERY | references/tpr-execution.md § DISCOVERY | 全流程 |
| 起草 GRV | references/grv-standard.md | 全流程 |
| 执行 Battle | references/battle-protocol.md | 全流程 |
| 评估项目分级 | references/project-grading.md | 全流程 |
| 初始化项目目录 | references/templates/ | 全流程 |
| 编排操作 / 派遣 sub-agent | references/orchestrator-ops.md | 全流程 |
| 设计多 Agent 架构 | references/multi-agent-pattern.md | 全流程 |
| 产出交付规范 | references/output-delivery.md | 全流程 |
| Implementation 阶段 | references/tpr-execution.md § Implementation | 全流程 |
