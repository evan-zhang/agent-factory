# AGENTS.md — Agent Factory Sub-Agent 模板库

## 架构说明

Agent Factory 采用**超级 Orchestrator 模式**：
- **唯一长期 Agent**：Factory Orchestrator（由根目录 `SOUL.md` 定义行为）
- **6 个 Sub-Agent 模板**：存放在 `agents/` 目录下，Orchestrator 按需 spawn，任务完成后销毁

每个 sub-agent 模板是一个**任务指令文件**，Orchestrator 在 spawn 时将其作为 `task` 参数传入。

## Sub-Agent 模板清单

| 模板 | 目录 | 适用场景 | 对应四总师 |
|------|------|----------|-----------|
| **Interview** | `agents/interview/SOUL.md` | L2 S1-S2：需求引导、业务摘要结构化 | 工厂调度员 |
| **Analyst** | `agents/analyst/SOUL.md` | L2 S3 或 L1 Step 2：文档解析、能力盘点、缺口分析 | 设计总工 |
| **Generator** | `agents/generator/SOUL.md` | L2 S3 或 L1 Step 3-5：生成 Agent/Skill/API 规范文档 | 设计总工 |
| **Validator** | `agents/validator/SOUL.md` | 每步完成后：质量门控检查，PASS/FAIL 判定 | 质检总监 |
| **Assembler** | `agents/assembler/SOUL.md` | L2 S5-S6 或 L1 Step 6：组装最终 workspace、生成追溯矩阵 | 交付总管 |
| **Reviewer** | `agents/reviewer/SOUL.md` | 需要独立外部评审时：方案评审、技术评审 | 质检总监 |

## Spawn 用法

```python
# 示例：在 S3 设计阶段 spawn Analyst
sessions_spawn(
    task=open("agents/analyst/SOUL.md").read() + "\n\n---\n\n当前项目资料：...",
    label="analyst-s3",
    mode="run"
)
```

Orchestrator 将模板内容 + 项目上下文拼接为完整的 `task` 参数。

## 流程阶段 → Sub-Agent 映射

### L1 七步流程（构建完整 Agent）

```
DISCOVERY       → Interview（需求引导）
GRV             → Analyst + Reviewer（分析 + 评审）
AGENTS/SKILLS   → Generator + Validator（生成 + 检查）
API             → Generator + Validator（生成 + 检查）
MATRIX          → Assembler + Validator（组装 + 检查）
ACCEPTANCE      → Reviewer + Validator（评审 + 验收）
```

### L2 八阶段（Skill 产品生命周期）

```
S1 背景了解     → Interview
S2 需求确认     → Interview
S3 方案设计     → Analyst + Generator + Validator
S4 开发         → （Orchestrator 直接执行或 spawn coding-agent）
S5 测试         → Validator + Reviewer
S6 发布         → Assembler
S7 版本管理     → Orchestrator 直接执行
S8 持续维护     → 按需 spawn 对应角色
```

## 通用行为准则

1. 每个 sub-agent 只完成自己的任务，不越界
2. 输出必须标注来源和版本
3. 遇到不确定内容必须上报，不自行判断
4. 操作必须记录到对应台账

## 文件编辑锁规则（Critical）

**禁止并发写入同一文件。**
- Orchestrator 在编辑某个文件时，禁止同时 spawn 会写同一文件的 sub-agent
- sub-agent 执行期间，Orchestrator 不得修改该 sub-agent 正在写入的文件
- 违反此规则导致文件损坏或冲突，由 Orchestrator 负全责

## 可用 Skill（全局安装）

工厂 Agent 可调用以下全局 Skill（安装路径：`./skills/` 或 `05_products/`）：

| Skill | ClawHub slug | 用途 |
|---|---|---|
| tpr-framework | `tpr-framework` | TPR 三省制工作流框架 |
| coding-agent | — | 代码任务委托（本地） |

> 注意：工厂不引用、不依赖任何第三方 Skill，所有基础能力必须自研可控。
> 新增技能时，同步更新本文件和 `05_products/index.md`。
