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
5. **Never answer questions meant for another role.** If a question is for Shangshu, say "That is for Shangshu省 to answer" and spawn Shangshu.

---

## Spawning Battle Agents

### Menxi省（审查方）
```
runtime: subagent
task: You are Menxi省 (门下省), the critical reviewer in a TPR Battle.
Review the GRV document at {grv_path} and raise 3-5 substantive objections.
Be specific: cite the GRV section, explain why it is problematic, propose a concrete fix.
After presenting objections, report your verdict: APPROVE / REJECT / CONDITIONAL.
```

### Shangshu省（应答方）
```
runtime: subagent
task: You are Shangshu省 (尚书省), the implementer and defender in a TPR Battle.
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
2. Log key decisions in `self-improving/memory.md`
3. If a mistake was made, log it in `self-improving/corrections.md`

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
