# AODW Workflow Guide (Level 2)

本文件为 AODW 的核心流程指令层，用于在触发任务时快速加载。

## 1. 核心流程（RT 生命周期）

created → intakeing → decided → in-progress → reviewing → done

关键动作：
- **Intake**：澄清范围、风险、模块影响，记录到 `intake.md`
- **Decision**：选择 Spec-Full / Spec-Lite，并记录到 `decision.md`
- **Plan**：先写 plan，获批后进入实现

## 2. Spec-Full vs Spec-Lite 决策

使用 Spec-Full：
- 跨模块影响
- 数据模型 / schema 变更
- 外部 API 合约变更
- 高风险或高复杂度变更

使用 Spec-Lite：
- 局部改动
- 单模块小修复
- 无外部 API 合约变化

## 3. Gate 检查点

- Gate 1：Intake 澄清完成
- Gate 2：分支确认（必须在 feature 分支）
- Gate 3：Plan 确认（未批准不得实现）
- Gate 4：提交前确认（展示 diff 与 status）
- Gate 5：完成确认（文档与测试齐备）

## 4. 加载策略（渐进式披露）

优先读取：
1. `.aodw-next/manifest.yaml`（规则索引）
2. 本文件（流程指令）
3. 必要规则文件（优先摘要 `*-summary.md`）

摘要策略：
- 先读 `*-summary.md`
- 需要细节再读完整文件

## 5. 关键文件入口

- 规则索引：`.aodw-next/manifest.yaml`
- RT 流程：`.aodw-next/02-workflow/rt-manager.md`
- Spec-Full：`.aodw-next/02-workflow/spec-full-profile.md`
- Spec-Lite：`.aodw-next/02-workflow/spec-lite-profile.md`
