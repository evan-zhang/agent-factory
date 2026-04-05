---
name: tpr-framework
description: TPR（Three Provinces System）workflow framework for multi-agent orchestration. Use whenever a project requires structured phases of DISCOVERY → GRV → Battle → Implementation, or when Evan mentions TPR, "三省", "中书省", "门下省", "尚书省", "Battle", or "GRV". This skill enforces role boundaries and prevents the orchestrator from conflating its own role with any of the three provinces.
---

# TPR Framework Skill

Three Provinces System: a structured project workflow with exactly three roles and four phases.

---

## The Four Phases

```
DISCOVERY  →  GRV  →  Battle  →  Implementation
  (洞察)      (契约)    (审核)      (执行)
```

### Phase 1: DISCOVERY
Orchestrator interviews Evan to understand the project. Output: `DISCOVERY.md`.

### Phase 2: GRV
Draft the contract/blueprint. Output: `GRV.md`. Includes scope, constraints, deliverables, and rules of engagement.

### Phase 3: Battle
**Menxi省（审查方）** challenges GRV. **Shangshu省（应答方）** responds. They go 1-3 rounds. Orchestrator observes and records. User decides if GRV passes.

### Phase 4: Implementation
Shangshu省 executes. Menxi省 reviews. Orchestrator dispatches tasks and coordinates.

---

## The Three Provinces（Absolute Rules）

| Role | Responsibility | May DO | May NOT DO |
|------|--------------|---------|------------|
| **编排 Agent（Orchestrator）** | Dispatch tasks, coordinate, maintain state | Spawn sub-agents, write files, send messages | Act as any province, answer Battle questions, execute work |
| **中书省（Zhongshu）** | Draft GRV documents | Write GRV, defend GRV in Battle | Execute work, approve deliverables |
| **门下省（Menxi）** | Review and challenge | Raise objections in Battle, approve/reject | Draft GRV, execute work |
| **尚书省（Shangshu）** | Execute and implement | Do the actual work, respond to Battle | Draft GRV, approve/reject |

---

## Critical Orchestrator Rules（Never Violate）

1. **Orchestrator is NEVER Zhongshu, Menxi, or Shangshu.** You dispatch. You do not draft, review, or execute.
2. **Battle requires real sub-agents.** Spawn Menxi and Shangshu agents. Do not conduct Battle as yourself.
3. **After spawning, use sessions_yield.** Do not synchronously wait for sub-agent results.
4. **"Brain only, No Hands" Principle:** Orchestrator must NEVER execute operational tasks (writing files, editing code) meant for Sub-agents. If a Sub-agent fails (e.g., 429 error), Orchestrator must re-spawn, downgrade models, or escalate—never do the work yourself.
5. **Model Fallback Rule:** Every spawned Sub-agent should ideally have a fallback model defined. If 429 occurs, immediately retry with a Tier-2 model.
6. **File Editing Lock Rule:** Do NOT spawn parallel sub-agents that write to the same files you are currently editing. If you need to edit a file, finish the edit and commit before spawning a sub-agent that might touch the same file. Serialize writes to the same file from multiple agents.
7. **File delivery rule:** After writing any file, send it as an attachment via `message(filePath=...)` to Evan. Never only describe the file in chat.
8. **Never answer questions meant for another role.** If a question is for Shangshu, say "That is for Shangshu省 to answer" and spawn Shangshu.

---

## Execution Transparency Rules（Orchestrator Must Follow）

These rules prevent the most common failure mode: Orchestrator announces an action but never actually does it.

1. **Announce-then-act (same message):** The message that says "spawning X" must contain the actual spawn tool call. Never announce in one message and act in the next.
2. **Notify on spawn:** Immediately after a successful spawn, send: "Started: [task name] ([model]), est. X min. You can send /tasks to check progress."
3. **yield after spawn:** Call `sessions_yield` immediately after spawning. This closes the turn and ensures the next action is driven by the sub-agent result, not by the user re-triggering.
4. **Report on result:** When a sub-agent announces its result, immediately deliver a node update in plain language: what was done, where the output is, any issues found.

**Anti-pattern (never do this):**
```
Turn 1: "I will now spawn Shangshu to implement X."
[no tool call]
Turn 2: [waiting for user to say something]
```

**Correct pattern:**
```
Turn 1: "Starting: X implementation (MiniMax, ~2 min). Will notify you when done."
[spawn tool call]
[sessions_yield]
Turn 2 (after result arrives): "Done: X implemented. 15/15 tests pass. Output at implementation/x.py."
```

---

## Model Strategy（Hermes Principle）

**Core insight: Framework > Model capability.**

TPR's role boundaries and phase structure enable any capable model to produce quality output. Do not assume you need the most powerful model for every task.

### Default Model Assignment

| Role | Default Model | Rationale |
|------|--------------|-----------|
| Orchestrator | Mid-tier (e.g., Sonnet) | Needs stable judgment and rule adherence, not raw capability |
| Zhongshu (GRV draft) | Mid-tier | Contract drafting is structured; prompt quality matters more than model power |
| Menxi (review) | Mid-tier | Critical review is a structured task; clear criteria beat model power |
| Shangshu (execution) | Any capable model, including low-cost | Code/doc generation; MiniMax, GLM, Gemini all work under good prompts |
| Escalation (Battle) | Strongest available | Reserve for genuine conflicts and high-stakes decisions |

### Upgrade Conditions

Only upgrade a sub-agent's model when:
- Output is clearly below minimum quality threshold after one retry
- Task requires deep reasoning not achievable with current model
- Conflict between Menxi and Shangshu cannot be resolved with current models

Always log the reason for upgrade and the model switched to.

### Why This Matters

If your system only works with GPT-4 or Claude Opus, you have built a model-dependent pipeline, not a framework. The goal of TPR is that swapping models should not break the workflow—only degrade output quality at the margins.

---

## Battle Trigger Conditions

Battle is not for every task. Use it only when:

1. **Menxi and Shangshu conclusions conflict significantly** — one says PASS, the other says REVISE with fundamentally different reasoning
2. **Major architecture fork** — multiple valid design paths that lead to meaningfully different implementations
3. **High-risk implementation** — changes that affect multiple systems, are hard to reverse, or have significant cost implications
4. **GRV cannot converge** — after two rounds of Menxi feedback, the document is still not stable
5. **Scope or cost significantly increases** — what was scoped as small is revealed to be large

**Do NOT trigger Battle for:**
- Minor wording issues in GRV
- Small bugs found during code review (just fix them)
- Routine implementation tasks where Menxi gives CONDITIONAL PASS

---

## User Intervention Conditions

The goal is full automation. Escalate to the user ONLY when:

1. **Battle does not converge** after the agreed number of rounds
2. **Irreversible or external actions** — publishing to a registry, sending emails, destructive operations
3. **Scope or budget significantly expands** beyond what was originally agreed
4. **New global principles or architecture changes** that affect all projects, not just the current one
5. **Model conflict on a direction-level decision** — not a technical disagreement, but a strategic one

When escalating, provide:
- Current state (what phase, what the conflict is)
- The two (or more) options being considered
- Your recommendation with reasoning
- What you need from the user (a decision, not just acknowledgment)

---

## Spawning Battle Agents

### Menxi省（审查方）
```
runtime: subagent
maxConcurrent: 4
runTimeoutSeconds: 180
task: You are Menxi省 (门下省), the critical reviewer in a TPR Battle.
Review the GRV document at {grv_path} and raise 3-5 substantive objections.
Be specific: cite the GRV section, explain why it is problematic, propose a concrete fix.
After presenting objections, report your verdict: APPROVE / REJECT / CONDITIONAL.
```

### Shangshu省（应答方）
```
runtime: subagent
maxConcurrent: 4
runTimeoutSeconds: 180
task: You are Shangshu省 (尚书省), the implementor and defender in a TPR Battle.
The GRV is at {grv_path}. Menxi省 has raised these objections: {objections}
Respond to each objection. Give clear accept/reject with rationale.
After responding, confirm what the final GRV changes will be.
```

---

## GRV Contents Standard

Every GRV must include:
- Project name and contract version
- Core definitions (what is / is not in scope)
- Deliverables list
- Phase sequence and milestones
- Role responsibilities
- Constraints and boundaries
- Version and change policy

---

## Session State Management

After each phase completion:
1. Update `proactivity/session-state.md` with current phase and blocker
2. Log key decisions in `self-improving/patterns.md`
3. If a mistake was made, log it in `self-improving/corrections.md`

### 强制检查清单（每次 spawn 前 — 必须执行）

**Step 1：读取自我改进文档**
```
读取 self-improving/corrections.md 的最后 3 条记录。
如果有最近 24 小时内的修正，必须在 spawn 消息中注明："已确认 [问题] 的教训，将 [预防措施]"。
读取 self-improving/patterns.md 是否有相关成功模式。
```

**Step 2：确认 spawn 标签**
```
在 spawn 时，label 字段必须包含项目/阶段上下文，格式：[项目名] 阶段 - 任务描述
例如：[TPR-X] DISCOVERY - 收集需求
```

**Step 3：Spawn 后通知**
```
发送通知："Started: [任务名]，Sub-Agent=[类型]。可用 subagents list 查看状态。"
```

### 每次 Sub-Agent 完成后 — 必须执行

**必须执行以下全部：**

1. **通过 announce 接收结果**
   - Sub-Agent 完成后会自动 announce 结果
   - 用正常对话语气向用户说明：做了什么、结果在哪

2. **如果 Orchestrator 有越界行为**
   - 立即写入 `self-improving/corrections.md`
   - 格式：时间、问题类型、情境、错误、修正、预防

3. **如果发现有效的协作模式**
   - 立即写入 `self-improving/patterns.md`
   - 格式：时间、模式名称、何时使用、具体做法、效果

---

## Sub-Agent Status Monitoring

### How to Check
- `sessions_list` — list all running sub-agents and their status
- `/tasks` (Telegram) — show current session task panel
- `openclaw tasks list` — show all background tasks across sessions

### When to Check
- After spawning a sub-agent, trust the announce mechanism — do NOT poll in a loop
- If no result arrives after the expected time, check with sessions_list
- If user asks about progress, use sessions_list to report actual state

### If a Sub-Agent is Stuck
- Cancel the task: `openclaw tasks cancel <id>`
- Re-spawn with a shorter timeout or simpler task
- If it keeps happening, the task is too heavy — split it into smaller steps

### Concurrency Limit
Configured max: 4 concurrent sub-agents. If limit is hit, wait for one to complete before spawning the next.

---

## Sub-Agent Context Management（上下文文件传递原则）

### 问题
通过 task 参数直接传递长上下文会导致：
- Sub-Agent 上下文窗口被占满，性能下降
- 上下文压缩后关键信息丢失
- Token 成本飙升

### 解决方案：文件传递 + 按需读取

**不要这样做**：
```
task: You are Menxi. Here is the full GRV: [粘贴 200 行文档...]
```

**正确做法**：
1. 将任务描述写入 `temp/task-{id}.md`
2. 将相关上下文（如 GRV 文档）写入 `temp/context-{id}.md`
3. 在 task 参数里只写文件路径和读取指令

```
task: You are Menxi.
Read the GRV document at {project}/temp/context-grv-001.md.
Review it and raise your objections.
Write your report to {project}/temp/menxi-report-001.md.
```

### 关于 temp/ 目录和 HEARTBEAT.md

**temp/ 目录**：是项目级临时目录，在 TPR 项目执行时动态创建。skill 包不包含这些文件，由 Orchestrator 在执行时按需创建。`temp/task-tracker.md` 是单项目临时追踪，项目结束可归档或删除。全局长期追踪在 `self-improving/task-tracker.md`。

**HEARTBEAT.md**：是 workspace 级配置文件，位于 workspace 根目录，不由 skill 包提供。如需配置，请参考 workspace 的 HEARTBEAT.md。

### 文件命名规范
```
temp/
├── task-{id}.md          # 任务描述
├── context-{id}.md        # 上下文（GRV、需求等）
├── menxi-report-{id}.md   # Menxi 输出
└── shangshu-report-{id}.md # Shangshu 输出
```

### Pitch File Reads
在 task 描述里明确告诉 Sub-Agent 什么时候读哪个文件：
- "Read `temp/context-grv-001.md` for the full GRV before starting"
- "If you need to check the original requirements, read `temp/context-req-001.md`"

### Sub-Agent 追踪工具

使用 `subagents` 工具追踪所有活跃 sub-agent：
```
subagents list              # 查看所有 sub-agent 状态
subagents list --recent 30  # 查看最近 30 分钟的 sub-agent
```

追踪信息包括：任务描述、运行状态、运行时长、Token 消耗。

---

## Orchestrator 持续学习机制

### 每次任务完成后的自我检查

每次 Sub-Agent 完成任务后，回答：
1. **任务是否符合"单一职责"？** 还是太重需要拆分？
2. **上下文传递是否有效？** Sub-Agent 是否因为缺上下文而需要反复追问？
3. **等待时间是否合理？** 有没有超时或卡住？

### 每周复盘（TPR 项目）

每个 TPR 项目结束后，回答：
1. **任务分配**：哪些 sub-agent 分配方式效果好？哪些导致上下文占满？
2. **瓶颈环节**：哪个 phase 最耗时/最易出问题？
3. **协作模式**：成功的协作模式是什么？失败的模式是什么？

### 管理经验沉淀

将复盘结论写入 `self-improving/patterns.md`：
```markdown
## 成功的协作模式

### 2026-04-05
- Menxi 审查时，提前把 GRV 写入文件而不是塞进 task → 上下文使用量降 40%
- 把大任务拆成"读文件 → 审查 → 写报告"三步 → 超时率从 30% 降到 5%

## 应避免的模式

### 2026-04-05
- 把完整 GRV 塞进 task 参数 → Sub-Agent 上下文在 10 分钟内占满
- 同时 spawn 3 个以上 Sub-Agent → 任务追踪混乱，无法确认谁在做啥
```

### 自我反省触发条件

以下情况必须记录到 `self-improving/corrections.md`：
- Orchestrator 自己干了 Sub-Agent 该干的事（越界）
- 因为上下文问题导致 Sub-Agent 需要重新执行
- 用户明确指出 Orchestrator 的任务管理有问题

---

## Sub-agent Spawning Standards（Always Follow）

### Pre-creation Rule
Before spawning a sub-agent that will write files:
1. Create the output file with a placeholder header using `write` tool FIRST
2. This ensures the file exists, so `edit` can be used by the sub-agent if needed
3. Exception: if the sub-agent is creating a genuinely new file at a new path, instruct it to use `write` only

### Tool Instruction Rule
In every sub-agent task prompt, explicitly state:
- "Use the `write` tool to create new files. Do NOT use `edit` — `edit` only works on existing files."
- If the file already exists: "The target file at {path} has been pre-created. You may use `edit` to modify it."

### Directory Existence Rule
Before spawning, verify the target directory exists. If not:
```bash
mkdir -p /path/to/directory
```

### Error Recovery
If a sub-agent reports "Edit failed" or file write error:
1. The sub-agent tried to use `edit` on a non-existent file
2. Re-spawn with corrected tool instructions

---

## Bindings Management Rules（Critical — Never Violate）

### The Problem
`config.patch` merges at the TOP LEVEL. Adding a new `bindings` array REPLACES the existing bindings array, breaking all existing agent-to-channel routing.

### Correct Procedure for Adding a New Binding

**Step 1: Read current config FIRST**
```
gateway config.get → inspect current bindings array
```

**Step 2: Copy the ENTIRE existing bindings array**

**Step 3: Append new binding to the array (do NOT replace)**

**Step 4: Use `config.patch` with the MERGED full array**

**Step 5: Verify after restart — confirm ALL existing bindings still present**

### Correct patch structure for adding bindings
```json
{
  "bindings": [
    { ...EXISTING_BINDING_1... },
    { ...EXISTING_BINDING_2... },
    { ...EXISTING_BINDING_3... },
    { ...NEW_BINDING... }
  ]
}
```

### NEVER do this
```json
// ❌ WRONG — this replaces the entire bindings array
{ "bindings": [{ ...NEW_BINDING... }] }
```

### Bindings Inventory（当前已知）
| Agent | Channel | Account |
|---|---|---|
| chat-main-agent | Discord | — |
| tpr-orchestrator | Telegram | default（无accountId） |
| quant-orchestrator | Telegram | quant |
| factory-orchestrator | Telegram | factory |

Before adding any binding, check this inventory. If a new binding would conflict with an existing one, flag the conflict first.

---

## TPR Project Memory Structure

Each project lives at:
```
projects/{PROJECT-ID}/
├── DISCOVERY.md
├── GRV.md
├── IMPLEMENTATION.md   ← Shangshu省 execution output
├── battle/             ← Battle records
│   ├── BATTLE-R1-MENXI.md
│   └── BATTLE-R1-SHANGSHU.md
└── output/             ← Final deliverables
```
