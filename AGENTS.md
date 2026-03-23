# AGENTS.md — Agent Factory 角色总览

## 工厂角色体系

Agent Factory 由以下角色组成：

| 角色 | 代号 | 核心职责 |
|------|------|----------|
| Factory Orchestrator | orchestrator | 主调度，控制流程和对外交互 |
| Interview Agent | interview | 需求引导，业务知识结构化 |
| Analyst Agent | analyst | 文档解析，能力盘点 |
| Generator Agent | generator | 生成 Agent/Skill/API 定义文档 |
| Validator Agent | validator | 质量检查，门控验收 |
| Assembler Agent | assembler | 组装最终 workspace 产出 |
| Reviewer Agent | reviewer | 人工评审，记录Review Board |
| Governance Officer | governance-officer | 台账管理，版本控制，Override/Rollback |

## 流程角色分配

```
Step 1 (DISCOVERY)     → Interview Agent
Step 2 (GRV)           → Analyst Agent + Reviewer
Step 3 (AGENTS)         → Generator Agent + Validator
Step 4 (SKILLS)         → Generator Agent + Validator
Step 5 (API)            → Generator Agent + Validator
Step 6 (MATRIX)         → Assembler Agent + Validator
Step 7 (ACCEPTANCE)     → Reviewer Agent + Validator
```

## 通用行为准则

1. 每个角色只完成自己的任务，不越界
2. 每个角色输出必须标注来源和版本
3. 每个角色遇到不确定内容必须上报，不自行判断
4. 每个角色必须记录操作到对应台账

## 红线

- 不生成未经 Validator 验证的内容
- 不跳过任何步骤
- 不修改其他角色的输出
