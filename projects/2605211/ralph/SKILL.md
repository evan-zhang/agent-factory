---
name: ralph
description: |
  Ralph Loop — AI 自主循环执行协议。三种模式：
  · 引导执行模式（Guided）：用户只说目标，AI 生成 PROMPT + checklist + verify.sh，用户确认后执行
  · 执行者模式（Executor）：人定义 checklist，AI 按清单执行并验证
  · 自主者模式（Autonomous）：人只给目标，AI 自主规划、执行、验证、记录全过程
  核心机制：每次迭代全新上下文 + state.json 跨迭代状态持久化 + 机械验证。
metadata:
  version: "3.1.0"
  author: "Based on Geoffrey Huntley's Ralph Loop pattern"
  reference: "https://ghuntley.com/loop/"
---

# Ralph Loop — AI 自主循环执行协议

## 安装

### 前置要求

- **bash**（macOS / Linux 自带）
- **AI 执行器**（任选其一）：
  - [Claude Code](https://docs.anthropic.com/en/docs/claude-code)（`claude` 命令）
  - [OpenAI Codex](https://github.com/openclaw/codex)（`codex` 命令）
- **git**

### 安装步骤

```bash
# 1. 克隆仓库（如果还没有）
git clone https://github.com/evan-zhang/agent-factory.git
cd agent-factory

# 2. Ralph Loop 已包含在仓库中，位于：
#    projects/2605211/ralph/
#    含：SKILL.md（本文件）、scripts/、references/

# 3. 验证安装
bash projects/2605211/ralph/scripts/ralph-loop.sh --help
bash projects/2605211/ralph/scripts/init-state.sh --help
```

### 集成到你的项目

```bash
# 复制到你的项目目录（可选，修改编号为你的项目编号）
cp -r projects/2605211/ralph projects/<your-project-id>/ralph
```

### 不想克隆整个仓库？

可以只下载需要的文件：

```bash
# 创建目录
mkdir -p ralph/scripts ralph/references

# 下载核心文件
curl -o ralph/SKILL.md https://raw.githubusercontent.com/evan-zhang/agent-factory/master/projects/2605211/ralph/SKILL.md
curl -o ralph/scripts/ralph-loop.sh https://raw.githubusercontent.com/evan-zhang/agent-factory/master/projects/2605211/ralph/scripts/ralph-loop.sh
curl -o ralph/scripts/init-state.sh https://raw.githubusercontent.com/evan-zhang/agent-factory/master/projects/2605211/ralph/scripts/init-state.sh
curl -o ralph/version.json https://raw.githubusercontent.com/evan-zhang/agent-factory/master/projects/2605211/ralph/version.json
chmod +x ralph/scripts/*.sh

# 下载参考模板（按需）
curl -o ralph/references/prompt-template-executor.md https://raw.githubusercontent.com/evan-zhang/agent-factory/master/projects/2605211/ralph/references/prompt-template-executor.md
curl -o ralph/references/prompt-template-autonomous.md https://raw.githubusercontent.com/evan-zhang/agent-factory/master/projects/2605211/ralph/references/prompt-template-autonomous.md
```

---

## 核心原理

```
while !done; do executor <prompt>; done
```

每次迭代是**全新进程**，无对话历史。状态仅通过 `state.json` 持久化。

五个设计原则：
1. 每次迭代全新上下文 — 避免"上下文腐烂"
2. 一次一个任务 — 每次迭代聚焦 1-2 个未完成条件
3. 文件系统即记忆层 — state.json 是唯一的跨迭代记忆
4. 规格驱动 — 定义"做什么"和"什么叫完成"
5. 机械验证（Backpressure）— 每次改动后必须运行验证

## 两种运行模式

### 引导执行模式（Guided）

用户只给目标，AI 分析项目上下文，自动生成 PROMPT.md + checklist + verify.sh，展示给用户确认后按执行者模式执行。

适合：**不想自己写 checklist 和 verify.sh，希望一句话启动的场景。**

流程：
1. 用户提供目标（一句话）
2. AI 分析项目结构，生成 PROMPT.md（范围+证据+测试）、checklist（具体可验证条件）、verify.sh（自动化验证脚本）
3. **展示方案给用户确认**（展示 PROMPT.md、checklist、verify.sh）
4. 用户确认后，按执行者模式运行，verify.sh 做自动门控

特点：用户只需给目标，后续所有专业工作由 AI 完成。兼顾低门槛和高严谨性。

### 执行者模式（Executor）

人定义目标 + 完成条件 checklist，AI 按清单逐条执行并验证。

适合：目标清晰、步骤已知、人可以预判完成标准的任务。

流程：
1. 人提供目标和 checklist
2. AI 逐条执行，通过后标记 true
3. 全部 true → 完成

### 自主者模式（Autonomous）

人只给目标，AI 自己规划路径、自己执行、自己验证、自己记录过程。

适合：目标清晰但路径未知、需要 AI 自主探索和决策的任务。

流程：
1. 人提供目标（一句话即可）
2. AI 自己拆解路径、定义验证标准、写入 state.json
3. **安全网：AI 完成初始规划后暂停，等待人审阅 route 和 checklist**
4. 人确认后，AI 开始自主执行
5. 每次迭代：从 route 取下一步 → 执行 → 验证（附可复验证据）→ 记录 journal
6. AI 认为完成时，汇总结果供人确认

### 模式选择

用户启动时选择。也可以由 AI 根据任务特征建议：

```
能预判所有完成条件？
  ├─ 是 → 执行者模式
  └─ 否 → 自主者模式

用户说"我自己定 checklist" → 执行者
用户说"AI 自己来" / "以终为始" → 自主者
用户只想说一句话 → 引导执行模式（默认推荐）
```

## 触发场景

- "用 Ralph Loop / 自主循环 完成 XXX"
- "无人值守跑这个任务"
- "/ralph ..."
- "启动循环" / "自主完成"
- 任何多阶段、预计耗时 > 10 分钟的任务

## 使用方式

### 方式一：交互式引导（推荐）

直接告诉 AI 你要做什么，AI 会：

1. 根据任务特征建议模式（或由你指定）
2. 帮你定义完成条件（执行者模式）或确认目标（自主者模式）
3. 生成 `state.json` 和 `PROMPT.md`
4. 启动循环

### 方式二：半自动模式

```bash
# 1. 选择模式并准备描述
cp "${RALPH_SKILL_DIR}/references/prompt-template-executor.md" /tmp/my-task.md
# 或
cp "${RALPH_SKILL_DIR}/references/prompt-template-autonomous.md" /tmp/my-task.md
# 编辑 /tmp/my-task.md ...

# 2. 初始化状态
bash "${RALPH_SKILL_DIR}/scripts/init-state.sh" /tmp/my-state.json \
  --task "任务描述" \
  --goal "完成条件" \
  --mode executor \
  --checklist "条件A" "条件B" "条件C"
# 或自主者模式：
bash "${RALPH_SKILL_DIR}/scripts/init-state.sh" /tmp/my-state.json \
  --task "任务描述" \
  --goal "完成条件" \
  --mode autonomous

# 3. 启动循环
bash "${RALPH_SKILL_DIR}/scripts/ralph-loop.sh" \
  --prompt /tmp/my-task.md \
  --state /tmp/my-state.json \
  --max-iterations 15
```

### 方式三：Goal Mode（单 session 轻量任务）

适用于上下文 < 100K tokens 的中等任务：

```
/goal <完成条件，含范围+证据+测试>
```

### 模式选择决策树

```
任务开始
  ├─ 有明确的阶段划分（多 Phase）？ → Ralph Loop
  ├─ 预计上下文 > 100K tokens？     → Ralph Loop
  ├─ 需要跨重启持久化？              → Ralph Loop
  ├─ 单 session 可完成？             → Goal Mode
  └─ 默认                           → Ralph Loop（更安全）
```

## 完成条件规范

**三要素公式**（来自 Linas Substack）：

| 要素 | 说明 | 示例 |
|------|------|------|
| 范围 | 涉及哪些文件/区域 | `src/components/*.tsx` |
| 证据 | 什么证明完成 | `tsc --noEmit` 无输出 |
| 测试 | 怎么验证 | `pytest tests/` exit 0 |

**执行者模式**：人用三要素公式写 checklist。

**自主者模式**：AI 自己定义三要素，写入 state.json 供人审阅。

**反例**（不合格）：
- ~~"修复 bug"~~ — 太模糊
- ~~"优化性能"~~ — 无法量化
- ~~"完成功能"~~ — 无验证标准

## state.json 规范

### 引导执行模式

与执行者模式结构相同，mode 为 "guided"，phase 为 "initialized"。AI 生成方案后 phase 变为 "awaiting_approval"，用户确认后变为 "working"，完成后变为 "done"。

### 执行者模式

```json
{
  "task": "一句话任务描述",
  "goal": "完成条件原文",
  "mode": "executor",
  "phase": "initialized | working | done",
  "iteration": 0,
  "checklist": {
    "条件描述1": false,
    "条件描述2": false
  },
  "blockers": [],
  "decisions": [],
  "startedAt": "",
  "completedAt": "",
  "meta": {}
}
```

### 自主者模式

```json
{
  "task": "一句话任务描述",
  "goal": "最终要达成的结果",
  "mode": "autonomous",
  "phase": "initialized | planning | awaiting_approval | working | done",
  "iteration": 0,
  "checklist": {},
  "route": [],
  "journal": [],
  "blockers": [],
  "decisions": [],
  "startedAt": "",
  "completedAt": "",
  "meta": {}
}
```

### 字段说明

**通用字段**：
- `task` — 一句话任务描述
- `goal` — 完成条件
- `mode` — `executor` 或 `autonomous`
- `phase` — 当前阶段
- `iteration` — 迭代计数
- `checklist` — 完成条件映射（执行者模式人预设，自主者模式 AI 自建）
- `blockers` — 遇到的阻塞
- `decisions` — 做过的决策及理由
- `meta` — 项目特定元数据

**自主者模式额外字段**：
- `route` — AI 自己规划的执行路径（步骤数组）
- `journal` — 每次迭代的过程记录

### Journal 条目格式（自主者模式）

```json
{
  "iteration": 3,
  "timestamp": "2026-05-21T12:30:00Z",
  "action": "做了什么（一句话）",
  "reason": "为什么这么做",
  "evidence": "可复验的证据（命令输出、文件 diff、URL 等）",
  "result": "success | partial | fail",
  "learned": "学到了什么（成功或失败的经验）",
  "nextFocus": "下一次迭代聚焦什么"
}
```

注意：journal 会随迭代增长。建议每次迭代时保留最近 5 条完整记录，更早的条目压缩为一句话摘要，避免 prompt 过长。

关键规则：
- 执行者模式：Agent 每次迭代**先读取** checklist，只做未完成的部分；条件通过后标记为 `true`，**绝不回退**
- 自主者模式：Agent 自己判断当前最该做什么，完成后自己验证，每次迭代写入 journal
- 全部 checklist 为 `true` 后 phase 设为 `"done"`
- 遇到技术选择记录到 `decisions`（含理由）
- 自主者模式的 journal 用于复盘和避免重复走错路

## 质量控制

### 每次迭代的 Quality Gate

**执行者模式**：
```
[ ] 产出可验证
[ ] 相关检查通过
[ ] 改动范围 ≤ 本次迭代目标（无发散）
[ ] state.json 已如实更新
```

**自主者模式**：
```
[ ] 本次迭代聚焦一个目标
[ ] 产出有可验证的证据
[ ] journal 已如实记录
[ ] state.json 已如实更新
[ ] 无重复走错路（检查 journal 历史）
```

### 反模式检测

| 信号 | 含义 | 处理 |
|------|------|------|
| 同一文件/目标修改 > 3 次 | 方案有问题 | 回退，换实现方式 |
| 验证反复在同一处失败 | 理解有误 | 重新阅读相关资料 |
| checklist 无进展 > 2 次迭代 | 拆分不合理 | 重新拆分子任务 |
| 新增 blocker | 遇到未预期依赖 | 尝试绕过或解决 |
| 出现无关功能 | 过度烘焙 | 收紧 prompt，减少迭代次数 |

## 配置参考

| 参数 | 默认值 | 说明 |
|------|--------|------|
| MAX_ITERATIONS | 20 | 安全上限，防止过度烘焙 |
| COOLDOWN_SECONDS | 3 | 迭代间冷却，避免 API 限流 |
| ITERATION_TIMEOUT | 600000ms | 单次迭代超时（10 分钟） |

## 执行器配置

Ralph Loop 不绑定特定 AI 工具。通过 `--executor` 参数指定：

| 执行器 | 参数值 | 说明 |
|--------|--------|------|
| Claude Code | `claude`（默认） | `claude --print` |
| Codex | `codex` | `codex exec` |
| 自定义 | 任意可执行命令 | 必须接受 stdin 或文件参数作为 prompt |

## 项目适配

Ralph Loop 本身与项目无关。项目特定的内容通过以下方式注入：

1. **CLAUDE.md** — 定义项目的验证命令、目录结构、编码规范
2. **PROMPT.md** — 每个任务的具体描述（项目特定）
3. **state.json meta** — 项目特定的元数据（如库名、阶段号）

不需要修改 Skill 本身来适配不同项目。

## References 索引

| 文件 | 何时加载 |
|------|---------|
| `references/prompt-template-executor.md` | 执行者模式：准备任务描述时 |
| `references/prompt-template-autonomous.md` | 自主者模式：准备任务描述时 |
| `references/state-example-executor.json` | 执行者模式：初始化状态文件时 |
| `references/state-example-autonomous.json` | 自主者模式：初始化状态文件时 |
| `references/anti-patterns.md` | 任务陷入僵局时 |
| `references/goal-vs-ralph.md` | 选择执行模式时 |
