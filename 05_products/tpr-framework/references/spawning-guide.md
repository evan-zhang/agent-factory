# Sub-agent 派遣规范

## Battle Agent 模板

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

## 派遣前检查规则

**文件预创建**：派遣会写文件的 sub-agent 前，先用 `write` 工具创建带占位符的目标文件。原因：sub-agent 的 `edit` 工具要求文件已存在，预创建可避免写入失败。

**目录存在性**：派遣前验证目标目录存在，不存在则 `mkdir -p`。

**工具声明**：sub-agent 任务 prompt 中必须明确说明：
- 创建新文件 → 用 `write`
- 修改已有文件 → 用 `edit`（文件已预创建时注明路径）

## 错误恢复

sub-agent 报告"Edit failed"或文件写入错误 → 说明 `edit` 作用于不存在的文件，重新派遣并修正工具说明。

429 错误 → 立即用 Tier-2 模型重试，不要自己接手执行。每个 sub-agent 理想情况下应预定义 fallback 模型。

## 项目目录结构

```
projects/{PROJECT-ID}/
├── DISCOVERY.md
├── GRV.md
├── IMPLEMENTATION.md
├── battle/
│   ├── BATTLE-R1-MENXI.md
│   └── BATTLE-R1-SHANGSHU.md
└── output/
```

## Session 状态管理

每个阶段完成后：
1. 更新 `proactivity/session-state.md`（当前阶段 + 阻塞项）
2. 关键决策记录到 `self-improving/memory.md`
3. 出错时记录到 `self-improving/corrections.md`
