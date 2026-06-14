# Review Brief — bp-object-audit-generate v0.1.1

## 评审对象

工厂项目 `2606131/bp-object-audit-generate/` 整个 skill，含以下文件：

### skill 内容（7 个，来自源 zip v0.1.1 原始版）
- `bp-object-audit-generate/SKILL.md`（含工厂落地注释）
- `bp-object-audit-generate/agents/agent.yaml`
- `bp-object-audit-generate/references/core_rules.md`
- `bp-object-audit-generate/references/interactive_state_machine.md`
- `bp-object-audit-generate/references/object_templates.md`
- `bp-object-audit-generate/references/output_package.md`（含工厂落地注释）
- `bp-object-audit-generate/references/source_manifest.md`（含工厂落地注释 + Evan 本地源表）

### 项目级元数据（3 个）
- `bp-object-audit-generate/version.json`（v0.1.1）
- `projects/2606131/VERSION`（v0.1.1）
- 项目目录下的标准 skill 目录结构

## 项目背景

- 项目编号：2606131（2026-06-13 开工）
- Skill 类型：BP（业务计划）对象审计 + 互动确认 + 生成 + 归档
- 原版来源：康哲集团 joy 同事本地工作区，硬编码 `/Users/joy/...` 路径
- Evan 落地：改写为 `/Users/evan/...` 路径，引入 PROJECT_ROOT 机制，版本 v0.1.1
- 落地改动：SKILL.md / source_manifest.md / output_package.md 顶部加了 Evan 落地配置块

## 评审维度（工厂标准 5 维）

1. **Skill 完整性**：SKILL.md + references + agents 是否齐全并相互一致
2. **路径改写正确性**：所有硬编码路径是否已正确改写为 PROJECT_ROOT 相对路径或 Evan 绝对路径
3. **落地注释质量**：工厂加的落地配置块是否清晰、不影响原始 skill 行为
4. **与工厂标准的兼容性**：是否符合 Agent Factory 的 skill 规范（VERSION、version.json、SKILL.md 必要章节等）
5. **可执行性**：v0.1.1 状态能否真正被 OpenClaw 加载并工作（flow 跑通）

## 已知的局限（请评审时考虑）

- 工厂端只跑了 2 次空审计 smoke test，**未在真实 BP 业务对象上验证**
- 原 skill 的默认源材料（康哲集团 15 份具体业务 BP）**缺失待补**，本 skill 的语义/流程/模板层不依赖这些，但实际 BP 审计任务需要时必须由用户补
- BP 报告母版 5 份模板尚未纳入 source manifest（待 Evan 确认）
- BP 系统 API 说明.md 尚未决定是否从 source manifest 移出（待 Evan 确认）

## 评审产出要求

按 `specs/agents/reviewer.md` 规范：
- 总体评级：PASS / CONDITIONAL_PASS / FAIL
- 3-5 个关键问题（每个含严重度和修复建议）
- 维度评分表（1-5 分 × 5 维度）
- 一条最重要的建议

**外部视角**，不要被「已经做完了」的心理影响，独立判断。
