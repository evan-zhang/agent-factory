# 外部工具调用模板

## 审计/审查 → 禁止使用以下工具，一律 spawn `factory-reviewer`

理由：与生成者同环境同上下文，独立性不成立。

## OpenAI Codex（联网/研究/文件生成，非审计）

```bash
exec pty:true background:true command:"codex exec --dangerously-bypass-approvals-and-sandbox '任务'" timeout:600
```

- 必须用 `--dangerously-bypass-approvals-and-sandbox`（关闭沙箱，否则无法联网+写入）
- 不加 `--full-auto`（与 bypass 互斥）
- 需要 `pty:true` + `background:true`

完整指南：`references/CLAUDE-CODE-USAGE-GUIDE.md`

## Claude Code（代码生成/文件编辑/多步调试，非审计）

```bash
exec background:true command:"claude --print --permission-mode bypassPermissions '任务'" timeout:600
```

- 用 `--print --permission-mode bypassPermissions`
- 不用 `yieldMs`（内存泄漏 → SIGKILL）
- 长任务 `background:true`，不需要 PTY

spawn 模板见 `specs/agents/reviewer.md` + `specs/workflows/AF-REVIEW-SOP_独立评审标准流程.md` §6。
