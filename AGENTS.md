# AGENTS.md — Agent Factory Domain

## 架构

- 当前入口：Life Gateway 的 `chat-main-agent`
- Factory 不再保留独立外部入口 Agent；旧 `factory-orchestrator` 已停用
- Factory 是主 Life workspace 下的 domain package，行为边界见 `SOUL.md`
- Sub-Agent 角色模板在 `specs/agents/`；真实独立评审 Agent 是 `factory-reviewer`
- 详见 `memory/sub-agent-reference.md`

## Spawn 规则

- task ≤500 字；详细上下文写临时文件，路径传递，必指定 `cwd`
- 首次失败 → 重试一次（精简 task）；二次失败 → 降级执行并告知用户
- spawn 前通知用户："正在启动：[任务名]，预计 X 分钟"
- 单次 spawn 任务 ≤2 分钟；复杂任务拆批，收到 announce 再继续
- 不在本 domain 硬编码 provider/model；使用 Gateway / CC Switch 当前模型配置
- 评审统一调用 `factory-reviewer`；高风险评审只在 task 中说明需要更强评审档

## 经验沉淀

- Sub-agent 启动时注入 `_runtime/experience/EXPERIENCE.md` 最近 5 条
- 完成后有条件写入（耗时>10min / 遇阻塞 / 否定式决策 / Evan 要求）
- 详见 `memory/experience-mechanism.md`

## 流程 → Sub-Agent 映射

**SOP 唯一真相源**：`/Users/evan/.openclaw/skills/agent-factory-sop/SKILL.md`（GitHub: <https://github.com/evan-zhang/agent-factory-sop>）
本地 `specs/workflows/` 只保留指针，不再存放或维护 SOP 副本。

**L1（构建完整 Agent）**：DISCOVERY→Interview | GRV→Analyst+Reviewer | AGENTS/SKILLS→Generator+Validator | API→Generator+Validator | MATRIX→Assembler+Validator | ACCEPTANCE→Reviewer+Validator

**L2（Skill 产品生命周期）**：S0-S2→Interview | S3→Analyst+Generator+Validator | S4→Orchestrator/coding-agent | S5→Validator+Reviewer | S6→Assembler | S7-S8→按需

## 操作红线

Sub-Agent 禁止：Gateway 管理、进程管理（kill/pkill）、env/shell profile 修改、网络配置修改。
允许：工作区文件读写、只读命令、python3 数据处理、只读 git、只读网络。

## Orchestrator 纪律

1. 修复后强制 verify：修复→验证→报告
2. 不主动重启 Gateway；只有用户明确要求或配置变更确需重启时，才使用 `launchctl kickstart gui/501/ai.openclaw.gateway.life`
3. 重启后校验：读 `_runtime/state/` state.json → memory_search 24h 闭环 → 三项式回答
4. 编辑某文件时禁止 spawn 会写同一文件的 sub-agent

## 上下文纪律

- 大型工具输出立即提炼，不留在上下文当摆设
- 内部操作过程叙述从简，不输出填充语
- 长会话主动建议 `/compact`

## 外部文档

玄关开放平台 API 文档唯一来源：`https://github.com/xgjk/dev-guide/`
用 curl 直接获取，不用 web_search/web_fetch。本地文档仅供参考。
