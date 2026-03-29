# 工厂总台账 (Factory Product Registry)

本文档记录 Agent Factory 生产的所有 Skill 产品及其生命周期状态。

---

## 1. 活跃产品线 (Active Products)

| 产品编号 | 产品名称 | 最新版本 | ClawHub slug | 当前阶段 | 负责调度员 | 最近更新 | 状态 |
|---|---|---|---|---|---|---|---|
| **AF-20260328-002** | cms-sop 统一SOP执行框架（Lite+Full）| v1.0.0 | `cms-sop` | S8（观察期）| Zaowu | 2026-03-29 | ✅ RELEASED |
| **AF-20260327-001** | bp-reporting-templates 复刻项目 | v0.4.3 | `bp-reporting-templates` | S6（RELEASED） | Zaowu | 2026-03-28 | ✅ RELEASED |
| **AF-20260326-002** | CAS 聊天记录全量存档系统 | v1.1.1 | `cas-chat-archive` | S8（观察期） | Zaowu | 2026-03-28 | ✅ RELEASED |

| **AF-20260323-001** | CWork 工作协同 | v1.4.0 | `cms-cwork` | S8（维护中） | Zaowu | 2026-03-29 | ✅ RELEASED |

---

## 2. 废弃产品记录 (Deprecated)

| 产品编号 | 产品名称 | 最终版本 | 废弃时间 | 原因 | 替代产品 |
|---|---|---|---|---|---|
| AF-20260328-001 | cms-soplite（轻量SOP）| v1.0.6 | 2026-03-29 | 被 cms-sop 合并取代 | `cms-sop`（Lite模式）|
| AF-20260326-001 | BP 数据采集系统 | — | 2026-03-29 | S1 停滞，需求未明确，主动终止 | 无 |

> 注：AF-20260328-001 项目档案已从工厂物理删除；ClawHub slug `cms-soplite` 已软删除。

---

## 3. 历史交付记录 (Archive)

| 项目编号 | 项目名称 | 完成日期 | 交付版本 | 成果说明 |
|---|---|---|---|---|
| AF-20260323-001 | CWork 核心能力开发 | 2026-03-24 | v1.0.0 | 实现 41 个 Skill，涵盖任务/汇报/决策/闭环/分析/LLM 等能力。 |

---

## 4. 产品全景视图 (Portfolio)

### AF-20260328-002: cms-sop 统一SOP执行框架
- 定位：统一 Lite/Full 双模式 SOP 执行框架，按任务复杂度自动路由。
- ClawHub slug：`cms-sop`，当前版本 `v1.0.0`
- 发布标识：`k974cgg7vskk33vfsqsj109s2d83t9d0`
- 三层防护：SKILL.md显式约束 + 脚本业务逻辑门控 + guide-token可审计链路
- 源码路径：`05_products/cms-sop/`

### AF-20260327-001: bp-reporting-templates 复刻项目
- 定位：将原"模板型 skill"复刻为可执行代码化 Skill。
- 当前阶段：S6 RELEASED。
- 发布标识：`k978cqsswkvg08bt1sgej0fsbd83sd19`

### AF-20260326-002: CAS 聊天记录全量存档系统
- 定位：聊天全量归档 + 可运营查询 + 手动复盘沉淀（append-only）。
- 当前阶段：S8 发布后观察期。
- 发布渠道：ClawHub + 公司内部 Skill 市场（双通道，均已成功）。
- 发布范围：`life/ops/company`；`code` 本期 deferred（用户确认）。
- 发布标识：`k97cdeq84b0kmvpw67fhtwvrms83r0c0`

### AF-20260323-001: CWork 工作协同
- 定位：企业级任务与汇报协同引擎，68个原子能力（v1.4.0新增联系人分组管理4个）。
- ClawHub slug：`cms-cwork`，当前版本 `v1.4.0`
- 源码路径：`05_products/cms-cwork/`（软链接到 workspace-life/skills/cms-cwork）

---

## 5. ClawHub 已发布 Skill 全景（2026-03-29 核实）

| Skill | slug | 版本 | 发布时间 | 状态 |
|---|---|---|---|---|
| 统一SOP执行框架 | `cms-sop` | v1.0.0 | 2026-03-29 | ✅ 活跃 |
| CWork 工作协同 | `cms-cwork` | v1.4.0 | 2026-03-29 | ✅ 活跃 |
| 聊天归档 | `cas-chat-archive` | v1.1.1 | 2026-03-28 | ✅ 活跃 |
| BP 报告模板 | `bp-reporting-templates` | v0.4.3 | 2026-03-28 | ✅ 活跃 |
| 企业发布工具链 | `create-xgjk-skill` | v1.0.7 | 2026-03-22 | ✅ 活跃 |
| 自改进主动 Agent | `self-improving-proactive-agent` | v1.0.0 | 2026-03-12 | ✅ 活跃 |
| CMS SOP Lite | `cms-soplite` | v1.0.6 | 2026-03-28 | ❌ 已废弃删除（被cms-sop取代）|

*最后更新：2026-03-29 | Zaowu*
