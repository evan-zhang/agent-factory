---
archive: K-260513-001
source: agent-factory
created_at: 2026-05-13T11:50:00+08:00
tags: [prd, instinct-learner, v1]
revision: "基于 OpenClaw v2026.5 Hooks 实际能力修订"
---

# PRD：Instinct 持续学习 OpenClaw Skill（修订版）

> 本文档基于原始 PRD（2026-05-08）修订。
> 修订原因：原始 PRD 假设的 Hook 事件（`afterResponse`、`beforePromptBuild`）在 OpenClaw 中不存在，需要映射到实际支持的事件。
> 修订依据：OpenClaw 官方文档 `docs/automation/hooks.md` + 源码验证。

## 项目名称

`instinct-learner` — OpenClaw 的会话经验自动提取与复用 Skill

## 背景

Everything Claude Code (ECC, 175K Stars) 有一个 Instinct 持续学习系统：Agent 在每次会话中自动提取行为模式，形成带置信度评分的"本能"，可跨会话复用、演化成 Skill、导入导出。

OpenClaw 目前有 Memory 系统（MEMORY.md + memory/*.md），但是**手动维护**的。缺少自动化的"从会话中学习"机制。

本 Skill 的目标：**用 OpenClaw 的 Internal Hooks + Python 脚本实现类似 ECC Instinct 的自动化持续学习**。

---

## 核心概念

### Instinct（本能）

一个 Instinct 是一条从会话经验中提取的结构化学习记录：

```yaml
---
id: instinct-20260508-001
created: 2026-05-08T13:00:00+08:00
confidence: 0.85
times_used: 5
times_validated: 4
last_used: 2026-05-08T20:00:00+08:00
tags: [memory-search, embedding, ollama]
status: active
---

## 触发条件
当 memory_search 失败（embedding 服务不可用）时

## 行动建议
回退到 grep + 文件时间排序作为本地搜索降级方案，
不要直接告诉用户"记忆不可用"

## 证据
- 2026-05-08: memory_search 挂了，用 grep 找到了相关文件，用户满意
- 2026-05-07: 类似情况，也用了 grep 降级
```

### Instinct 生命周期

```
Agent 启动 → bootstrap 注入 Top-K instincts → Agent 回复时标记使用的 instinct →
用户下一条消息到达 → Hook 判断用户反馈 → 更新置信度 → 每N条消息触发提取 →
写入新 instinct → 网关启动时清理过期记录
```

---

## OpenClaw Internal Hooks 事件映射（修订核心）

> ⚠️ 原始 PRD 使用了 `afterResponse` / `beforePromptBuild` / `heartbeat`，
> 这些在 OpenClaw 中**不存在**。以下为实际可用事件的映射关系。

| PRD 原始设计 | OpenClaw 实际事件 | 说明 |
|---|---|---|
| `beforePromptBuild`（F2 加载） | `agent:bootstrap` | Agent 启动时通过 bootstrap 注入 MEMORY.md |
| `afterResponse`（F3 验证） | `message:sent` + `message:received` 配合 | sent 时记录使用的 instinct ID，received 时根据用户反馈更新置信度 |
| `afterResponse`（F1 提取） | `message:received` | 每收到 N 条用户消息触发一次提取 |
| `heartbeat`（F4 清理） | `gateway:startup` | 网关启动时按时间间隔触发清理 |

### 实际可用事件列表（来自 OpenClaw docs/automation/hooks.md）

| 事件 | 触发时机 |
|---|---|
| `command:new` | `/new` 命令 |
| `command:reset` | `/reset` 命令 |
| `command:stop` | `/stop` 命令 |
| `command` | 任意命令 |
| `session:compact:before` | 压缩前 |
| `session:compact:after` | 压缩后 |
| `session:patch` | session 属性修改 |
| `agent:bootstrap` | Agent 启动，注入 bootstrap 文件 |
| `gateway:startup` | 网关启动 |
| `gateway:shutdown` | 网关关闭 |
| `gateway:pre-restart` | 网关重启前 |
| `message:received` | 收到用户消息 |
| `message:transcribed` | 语音转写完成 |
| `message:preprocessed` | 消息预处理完成 |
| `message:sent` | 发送 Agent 回复 |

---

## 功能需求

### F1：自动提取

**触发时机**：`message:received`（收到用户消息时，每 N 条触发一次）

**实现方式**：Python 脚本 `scripts/extract_instinct.py`

**输入**：Hook handler 从 session 日志（`<workspace>/.openclaw/instinct-learner/session.jsonl`）中取最近 30 条消息，通过 stdin 传入 JSON

**逻辑**：
1. 分析最近对话中是否有"值得记住"的模式
2. "值得记住"的判断标准：
   - 用户纠正了 Agent 的错误 → 记录"不要做 X"
   - Agent 尝试了某个方法失败后换了一个成功的方法 → 记录"方法 A 失败时用方法 B"
   - Agent 自己发现了某个有用的模式 → 记录"在 Y 场景下用 Z"
   - 用户给出了明确的偏好/规则 → 记录偏好
3. 如果有新的学习点，生成一个 Instinct 文件写入 `<workspace>/instincts/YYYY-MM-DD-{NNN}.md`

**输出**：Instinct 文件（YAML frontmatter + Markdown body）

**约束**：
- 每次提取最多生成 1 个 instinct（避免膨胀）
- MVP 阶段使用**关键词+模式匹配**，不依赖额外 LLM 调用（省 token 省钱）
- 配置项 `extraction_mode` 预留 `"llm"` 值供未来扩展
- 如果没有值得提取的内容，不生成任何文件
- 提取频率：每 N 条用户消息触发一次，N 默认为 1（可配置 `extractEveryNMessages`）

### F2：会话加载（注入到上下文）

**触发时机**：`agent:bootstrap`（Agent 启动时）

**实现方式**：Python 脚本 `scripts/load_instincts.py`

**注入机制**：
1. Hook handler 在 `agent:bootstrap` 事件中调用 `load_instincts.py`
2. 脚本输出格式化的 Markdown
3. Handler 将其写入临时 MEMORY.md 文件，注入到 `event.context.bootstrapFiles` 数组中
4. OpenClaw 将该文件作为 MEMORY.md 注入到 Agent 上下文

**注入内容包括**：
- 使用约定说明（告知 Agent 如何标记使用了哪条 instinct）
- Top-K 条 active instinct 的摘要

**注入格式**：
```markdown
# Active Instincts (auto-injected)

## 使用约定（用于自动验证）

- 如果你在本轮回复中**实际参考/应用**了某条 instinct，请在回复末尾追加一个 HTML 注释标记：
  - 形如：`<!-- instinct:<instinct_id> -->`
  - 可多条（每条一行）。

## 🧠 Active Instincts (相关度最高的 5 条)

1. **[memory-search 降级]** 当 memory_search 失败时，用 grep + 文件时间排序降级（置信度 0.85，使用 5 次）
2. ...
```

**约束**：
- Top-K 默认 5，不超过 10（控制 token 消耗）
- 只加载 active 状态的 instinct
- 如果没有匹配的 instinct，不注入任何内容（不要浪费 token）
- bootstrap 时 query 为空（无法预知用户消息），按置信度 + 使用次数排序

### F3：验证与置信度更新

**触发时机**：`message:sent`（记录使用的 instinct）+ `message:received`（根据用户反馈更新）

**实现方式**：Hook handler + Python 脚本 `scripts/validate_instinct.py`

**两阶段机制**：

**阶段 A：`message:sent` 时**
1. 解析 Agent 回复内容，查找 `<!-- instinct:<id> -->` 标记
2. 将匹配到的 instinct ID 存入 state 文件（`.openclaw/instinct-learner/state.json`）的 `pendingValidateIds` 字段

**阶段 B：`message:received` 时（下一条用户消息）**
1. 读取 state 中的 `pendingValidateIds`
2. 分析用户消息是否包含纠正信号（关键词匹配：你说错/不对/应该/正确/别这样/不要这样/不是）
3. 如果有纠正信号 → `outcome = "corrected"`
4. 如果没有纠正信号 → `outcome = "success"`
5. 调用 `validate_instinct.py` 更新对应 instinct：
   - `times_used += 1`
   - `last_used = now()`
   - success → `times_validated += 1`，`confidence = min(1.0, confidence + 0.05)`
   - corrected → `confidence = max(0.0, confidence - 0.1)`
6. 写回 instinct 文件的 YAML frontmatter
7. 清空 `pendingValidateIds`

### F4：清理过期 Instinct

**触发时机**：`gateway:startup`（网关启动时，按时间间隔执行）

**实现方式**：Python 脚本 `scripts/prune_instincts.py`

**规则**：
- 30 天未使用 → `status: dormant`
- 60 天未使用 → `status: expired`
- confidence < 0.3 且 times_used > 5 → `status: expired`（反复验证失败的）
- expired 文件移动到 `<workspace>/instincts/archived/`
- active 数量超过 `max_active_instincts`（默认 50）时，将最低置信度的降为 dormant

**执行频率**：通过 state 文件记录 `lastPruneAtMs`，与 `pruneIntervalHours`（默认 24 小时）比较，避免每次启动都执行。

### F5：状态查看（CLI）

**命令**：`python3 scripts/instinct_status.py --data-dir <workspace>/instincts`

**输出**：
```
Instinct 状态概览
=================
总计: 12 条 active, 3 条 dormant, 5 条 archived

Top 5 高置信度:
1. [memory-search 降级] 置信度 0.95 (使用 12 次)
2. ...

最近 5 条:
1. [instinct-xxx] 2026-05-13 置信度 0.60
```

### F6：安装脚本

**命令**：`python3 scripts/install_hook.py --workspace <workspace路径> --enable-config --restart-gateway`

**功能**：
1. 将 `references/workspace-hook/instinct-learner/` 拷贝到 `<workspace>/hooks/instinct-learner/`
2. 初始化 `<workspace>/instincts/` 数据目录（instincts/*.md + instincts/archived/ + instincts/index.json）
3. 合并写入 OpenClaw 配置启用 hook
4. 若有变更则重启网关

---

## 目录结构

```
skills/instinct-learner/
├── SKILL.md                    # Skill 定义
├── scripts/
│   ├── instinct_lib.py         # 公共库（frontmatter 解析、排序、去重等）
│   ├── extract_instinct.py     # F1: 自动提取
│   ├── load_instincts.py       # F2: 加载注入
│   ├── validate_instinct.py    # F3: 验证更新
│   ├── prune_instincts.py      # F4: 清理过期
│   ├── install_hook.py         # F6: 安装脚本
│   └── instinct_status.py      # F5: 状态查看
├── config.json                 # 默认配置
├── references/
│   ├── PRD-Instinct-Learner-Skill-2026-05-08.md  # 原始 PRD
│   ├── INSTALL.md              # 安装说明
│   └── workspace-hook/
│       └── instinct-learner/
│           ├── HOOK.md         # Hook 元数据
│           └── handler.js      # Hook handler（TS/JS）
└── instincts/                  # 开发时样例数据（安装后使用 <workspace>/instincts/）
    ├── archived/
    ├── index.json
    └── 2026-05-08-001.md       # 样例 instinct
```

**运行时数据目录**（不包含在 Skill 分发包中，安装时创建）：

```
<workspace>/
├── instincts/                  # instinct 数据
│   ├── YYYY-MM-DD-NNN.md       # instinct 文件
│   ├── archived/               # 过期 instinct
│   └── index.json              # 索引（by_fingerprint, by_id）
└── hooks/
    └── instinct-learner/       # workspace hook
        ├── HOOK.md
        └── handler.js
```

---

## Hook Handler 架构

### handler.js（TypeScript/JavaScript）

监听 4 种事件：

1. **`agent:bootstrap`** → 调用 `load_instincts.py` → 生成临时 MEMORY.md → 注入到 `bootstrapFiles`
2. **`message:sent`** → 解析回复中的 `<!-- instinct:<id> -->` 标记 → 存入 state
3. **`message:received`** → 
   - 先执行 F3 验证（如有 pendingValidateIds）
   - 递增 inboundCount，每 N 条触发 F1 提取
   - 将消息追加到 session 日志
4. **`gateway:startup`** → 按时间间隔触发 F4 清理

### handler.js 中的 HOOK_KEY

当前 handler.js 中 `HOOK_KEY` 变量的值为 `"***"`（占位符）。正式版本需要改为 `"instinct-learner"`。

### session 日志

路径：`<workspace>/.openclaw/instinct-learner/session.jsonl`

格式：每行一个 JSON 对象：
```json
{"sessionKey":"xxx","ts":1715577600000,"role":"user","content":"..."}
```

用于 F1 提取时提供近期对话上下文。保留最近 30 条。

### state 文件

路径：`<workspace>/.openclaw/instinct-learner/state.json`

```json
{
  "inboundCount": 0,
  "pendingValidateIds": [],
  "lastPruneAtMs": 0
}
```

---

## OpenClaw 配置

```json
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "instinct-learner": {
          "enabled": true,
          "k": 5,
          "extractEveryNMessages": 1,
          "pruneIntervalHours": 24
        }
      }
    }
  }
}
```

**配置项说明**：

| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `enabled` | boolean | true | 是否启用此 hook |
| `k` | number | 5 | bootstrap 时注入的 Top-K instinct 数量 |
| `extractEveryNMessages` | number | 1 | 每收到 N 条用户消息触发一次提取 |
| `pruneIntervalHours` | number | 24 | 清理间隔（小时） |

**config.json（Skill 内部配置）**：

```json
{
  "max_instincts_load": 5,
  "max_inject_tokens": 500,
  "confidence_threshold": 0.3,
  "dormant_days": 30,
  "expired_days": 60,
  "max_active_instincts": 50,
  "extraction_mode": "keyword"
}
```

| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `max_instincts_load` | number | 5 | 每次 bootstrap 注入的最大 instinct 数 |
| `max_inject_tokens` | number | 500 | 注入内容最大 token 数 |
| `confidence_threshold` | number | 0.3 | 低于此值标记为 expired |
| `dormant_days` | number | 30 | 未使用天数变为 dormant |
| `expired_days` | number | 60 | 未使用天数变为 expired |
| `max_active_instincts` | number | 50 | 最大 active instinct 数 |
| `extraction_mode` | string | "keyword" | 提取方式：keyword（MVP）或 llm（未来） |

---

## 约束与边界

1. **不依赖额外 LLM 调用**——MVP 提取逻辑用关键词匹配，不调用 API（省 token 省钱）
2. **Token 预算**：每次注入不超过 500 tokens（约 5 个 instinct 的摘要）
3. **幂等性**：同一模式不重复创建 instinct（按内容 hash 去重）
4. **不与现有 Memory 冲突**——instinct 是 Memory 的补充，不是替代
5. **不与 HEARTBEAT.md 冲突**——heartbeat 是手动操作，instinct 是自动操作
6. **运行时数据与 Skill 代码分离**——instinct 数据存在 `<workspace>/instincts/`，不存 skill 目录内

---

## 与原始 PRD 的差异汇总

| 项目 | 原始 PRD | 修订版 | 修订原因 |
|---|---|---|---|
| F1 提取触发 | `afterResponse` / `heartbeat` | `message:received`（每N条） | `afterResponse` 不存在 |
| F2 加载触发 | `beforePromptBuild` | `agent:bootstrap` | `beforePromptBuild` 不存在 |
| F3 验证触发 | `afterResponse` | `message:sent` + `message:received` 两阶段 | `afterResponse` 不存在 |
| F4 清理触发 | `heartbeat` | `gateway:startup`（按时间间隔） | `heartbeat` 不是 hook 事件 |
| 数据存储 | 未明确区分 | Skill 代码 vs `<workspace>/instincts/` 分离 | 明确运行时数据位置 |
| Hook Handler | 未涉及 | handler.js 架构 + session 日志 + state 文件 | 补充实现细节 |
| HOOK_KEY | 未提及 | 需从 `"***"` 改为 `"instinct-learner"` | handler.js 硬编码问题 |
| 安装脚本 | 未涉及 | F6 install_hook.py | 明确安装流程 |

---

## 验收标准

1. ✅ 安装后，Agent 每次会话启动时自动加载相关 instinct（通过 bootstrap 注入）
2. ✅ 会话中发现新模式时自动创建 instinct 文件（`message:received` 触发提取）
3. ✅ Instinct 被参考后自动更新置信度（`message:sent` 记录 → `message:received` 验证）
4. ✅ 过期 instinct 自动清理（`gateway:startup` 触发）
5. ✅ `instinct_status.py` 可正常查看状态
6. ✅ 不增加每次会话超过 500 tokens 的额外消耗
7. ✅ 不依赖额外 API 调用
8. ✅ 与现有 Memory 系统共存不冲突
9. ✅ HOOK_KEY 值正确（`"instinct-learner"`）
10. ✅ `install_hook.py` 可一键完成 hook 安装 + 配置 + 网关重启
