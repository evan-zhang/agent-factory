# 工厂权重矩阵

## Skill 类型分类

先读 SKILL.md description 和目录结构，按主要用途分类：

| 类型 | 判断标准 |
|------|---------|
| **API 集成类** | 主要功能是调用外部 API（CWork/BP/CAS 等），有 scripts/ 或 shared/ |
| **工作流类** | 多步骤流程编排，有 checklist/decision/流程控制逻辑 |
| **纯文档类** | 只有 SKILL.md + references/，无脚本无 API 调用 |
| **混合类** | 同时具备以上两种以上特征，各占约 40%+ |

## 权重矩阵

| 维度 | API 集成类 | 工作流类 | 纯文档类 | 混合类 |
|------|-----------|---------|---------|--------|
| D1 结构质量 | 15% | 20% | 25% | 20% |
| D2 触发质量 | 15% | 25% | 25% | 20% |
| D3 内容质量 | 20% | 25% | 35% | 25% |
| D4 安全合规 | 35% | 15% | 5%  | 20% |
| D5 发布合规 | 15% | 15% | 10% | 15% |

> D4 对 API 集成类权重最高（35%），因为凭证处理是最大风险。
> D3 对纯文档类权重最高（35%），因为内容质量是唯一核心价值。

## 工厂已知 Skill 类型对照

| Skill | 类型 |
|-------|------|
| cms-cwork | API 集成类 |
| cms-sop | 工作流类 |
| bp-reporting-templates | API 集成类 |
| create-xgjk-skill | 工作流类 |
| xgjk-skill-auditor | 工作流类 |
| cas-chat-archive | API 集成类 |
| tpr-framework | 纯文档类 |
| self-improving-proactive-agent | 纯文档类 |

## 混合类处理

两种权重各取 50% 平均后四舍五入到整数，总和保持 100%。
