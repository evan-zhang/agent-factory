# MEMORY.md — Agent Factory 核心知识索引

## 架构认知

工厂 = 主 Life Agent 使用的 Factory domain package + `agent-factory-sop` Skill + 按需 spawn 的 `factory-reviewer`。L1 七步构建完整 Agent，L2 八阶段做单个 Skill。流程唯一真相源：`/Users/evan/.openclaw/skills/agent-factory-sop/SKILL.md`。

## Sub-Agent 模板

9 个模板在 `specs/agents/`：Interview/Analyst/Generator/Validator/Assembler/Reviewer/Governance Officer/Orchestrator/Worker。详见 `memory/sub-agent-reference.md`。

## 经验沉淀

Sub-agent 启动注入 EXPERIENCE.md 最近 5 条；完成后有条件写入（>10min / 阻塞 / 否定决策 / Evan 要求）。详见 `memory/experience-mechanism.md`。

## 关键规则

- 审计独占：`factory-reviewer` 唯一，禁用 Claude Code/Codex 跑审计
- life gateway 重启：`launchctl kickstart gui/501/ai.openclaw.gateway.life`
- 外部文档：xgjk/dev-guide 用 curl，不用 web_search
- 推送后自动发安装说明
- 模型由 Gateway / CC Switch 当前配置统一维护，不在 Factory domain 写死 provider/model

## 外部工具

Codex/Claude Code 调用模板见 `memory/external-tools.md`（仅非审计场景）。
