# CLAWFILE.md — Agent Factory 入口配置

## 工厂入口

本文件是 Agent Factory 的启动入口配置文件，供 OpenClaw 加载工厂主 Orchestrator。

### 配置

- **类型**: factory
- **版本**: v1.0
- **入口 SOUL**: `./SOUL.md`
- **角色定义**: `./AGENTS.md`
- **主工作区**: `./projects`

### 启动方式

OpenClaw 加载本目录作为 workspace 时，将以 `./SOUL.md` 定义的 Factory Orchestrator 作为主 Agent。

### 子 Agent 路径

| 角色 | SOUL 路径 |
|------|-----------|
| orchestrator | ./agents/orchestrator/SOUL.md |
| interview | ./agents/interview/SOUL.md |
| analyst | ./agents/analyst/SOUL.md |
| generator | ./agents/generator/SOUL.md |
| validator | ./agents/validator/SOUL.md |
| assembler | ./agents/assembler/SOUL.md |
| reviewer | ./agents/reviewer/SOUL.md |
| governance-officer | ./agents/governance-officer/SOUL.md |

### 模板路径

| 模板 | 路径 |
|------|------|
| Agent 定义 | ./TEMPLATES/agent-definition.md |
| Skill 设计 | ./TEMPLATES/skill-design.md |
| API 契约 | ./TEMPLATES/api-contract.md |
| 追溯矩阵 | ./TEMPLATES/agent-skill-api-matrix.csv |
| 验收清单 | ./TEMPLATES/acceptance-checklist.md |

### 技能路径

| 技能 | 路径 |
|------|------|
| tpr-framework | ./skills/tpr-framework/ |
| self-improving-proactive-agent | ./skills/self-improving-proactive-agent/ |

> 注意：技能安装在 `./skills/` 目录，工厂所有角色均可调用。

### 治理路径

| 台账 | 路径 |
|------|------|
| 入场台账 | ./governance/admission-log.md |
| Override 记录 | ./governance/override-log.md |
| 回滚记录 | ./governance/rollback-log.md |
| 版本历史 | ./governance/version-history/ |

---

*Agent Factory v1.0*
