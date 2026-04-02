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

## 文件编辑锁规则（Critical）

**禁止并发写入同一文件。**
- 主 Orchestrator 在编辑某个文件时，禁止同时 spawn 会写同一文件的 sub-agent
- sub-agent 执行期间，主 Orchestrator 不得修改该 sub-agent 正在写入的文件
- 违反此规则导致文件损坏或冲突，由 Orchestrator 负全责

## 红线

- 不生成未经 Validator 验证的内容
- 不跳过任何步骤
- 不修改其他角色的输出

## 四总师 ↔ 技术角色映射表

**四总师**是 AF-SOP-01（L2 八阶段）中使用的业务视角角色名。
**技术角色**是 SOUL.md（L1 七步）中实际的 Agent 代号。
两者是**同一组角色的不同命名视角**，映射关系如下：

| 四总师（业务视角） | 技术角色代号 | 对应 L2 阶段 | 核心职责 |
|---|---|---|---|
| 工厂调度员 | `orchestrator` | 全程 | 流程控制、用户交互、任务分发 |
| 设计总工 | `analyst` + `generator` | S1-S3（背景/需求/设计） | 文档解析、方案设计、能力盘点 |
| 交付总管 | `assembler` | S4-S6（开发/测试/发布） | 编码执行、组装输出、发布分发 |
| 质检总监 | `validator` + `reviewer` | S5-S7（测试/版本管理） | 质量检查、红蓝对抗、验收门控 |

**判断标准**：
- 在文档/规则中看到"设计总工"→ 指的是 `analyst` 和 `generator` 的职责
- 在文档/规则中看到"质检总监"→ 指的是 `validator` 和 `reviewer` 的职责
- 在 SOUL.md/代码中看到 `orchestrator` → 就是"工厂调度员"

## 可用 Skill（全局安装）

工厂 Agent 可调用以下全局 Skill（安装路径：`./skills/` 或 `05_products/`）：

| Skill | ClawHub slug | 用途 |
|---|---|---|
| tpr-framework | `tpr-framework` | TPR 三省制工作流框架 |
| coding-agent | — | 代码任务委托（本地） |

> 注意：工厂不引用、不依赖任何第三方 Skill，所有基础能力必须自研可控。
> 新增技能时，同步更新本文件和 `05_products/index.md`。
