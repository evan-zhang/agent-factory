# 05_products — Skill 产品索引

> 本文件是工厂所有 Skill 产品的权威索引，持续更新。
> 每次新 Skill 发布、版本升级、状态变更后必须同步更新本文件。
>
> 最后更新：2026-04-05 | Zaowu

---

## 已发布产品（✅ RELEASED）

| 目录名 | 产品名称 | 版本 | ClawHub slug | 项目编号 | 发布日期 | 状态 |
|---|---|---|---|---|---|---|
| cms-cwork | CWork 工作协同 | v3.2.2 | `cms-cwork` | AF-20260323-001 | 2026-04-03 | ✅ Agent-First 重构 |
| bp-reporting-templates | BP 报告模板 | v1.0.2 | `bp-reporting-templates` | AF-20260327-001 | 2026-04-01 | ✅ 发布 |
| bp-prototype | BP 原型模板制造 | v0.5.2 | `bp-prototype` | — | 2026-04-04 | ✅ 新发布 |
| tpr-framework | TPR 三省制工作流框架 | v1.0.2 | `tpr-framework` | — | 2026-04-01 | ✅ 活跃 |
| xgjk-skill-auditor | 工厂 Skill 质检工具 | v1.0.1 | `xgjk-skill-auditor` | AF-20260331-002 | 2026-03-31 | ✅ 活跃 |
| create-xgjk-skill | 玄关 Skill 发布工具链 | v1.1.0 | `xgjk-skill-factory` | — | 2026-04-01 | 🔄 移交玄关团队 |

---

## 在建产品（🔧 IN PROGRESS）

| 目录名 | 产品名称 | 当前版本 | 项目编号 | 阶段 | 说明 |
|---|---|---|---|---|---|
| bp-auditor | BP 两级联动审计 | v1.0.0 | — | 🔧 待发布 | 两级联动 BP 审计工具 |
| bp-manager | BP 管理工具 | — | — | S3 设计中 | 查询/管理 BP 目标/成果/举措 |
| cms-meeting-monitor | AI慧记会议监控 | v1.0.2 | — | S5 测试中 | 从 AI慧记 拉取会议内容 |
| openclaw-model-rankings | OpenRouter 模型排行 | v1.0.3 | `openclaw-model-rankings` | S4 执行中 | 第一阶段外部数据底座 |
| skill-tool-registry | Skill 工具注册管理 | — | — | S3 设计中 | 统一管理 Gateway 层工具注册 |

---

## 已废弃（❌ DEPRECATED）

| 目录名 | 产品名称 | 最终版本 | 废弃时间 | 原因 |
|---|---|---|---|---|
| self-improving-proactive-agent | 主动增强 Agent | v1.0.0 | 2026-04-05 | 第三方 Skill，非工厂自研，已删除 |
| cms-soplite | SOP Lite | v1.0.6 | 2026-03-29 | 被 cms-sop 合并取代 |

---

## L3 关联信息（Skill → Remote Repo 映射）

> 单一源码地原则：`05_products/{name}/` 是所有 Skill 的本地 SSOT。
> remote_repo 为可选备份/协作地，不接受直接 push。
> 最后核查：2026-04-05 | Zaowu

| 目录名 | local_path | clawhub_slug | 状态 |
|---|---|---|---|
| cms-cwork | `05_products/cms-cwork/` | `cms-cwork` | ✅ 已发布 |
| bp-reporting-templates | `05_products/bp-reporting-templates/` | `bp-reporting-templates` | ✅ 已发布 |
| bp-prototype | `05_products/bp-prototype/` | `bp-prototype` | ✅ 已发布 |
| tpr-framework | `05_products/tpr-framework/` | `tpr-framework` | ✅ 已发布 |
| xgjk-skill-auditor | `05_products/xgjk-skill-auditor/` | `xgjk-skill-auditor` | ✅ 已发布 |
| create-xgjk-skill | `05_products/create-xgjk-skill/` | `xgjk-skill-factory` | 🔄 已移交 |
| cms-meeting-monitor | `05_products/cms-meeting-monitor/` | — | 🔧 在建 |
| openclaw-model-rankings | `05_products/openclaw-model-rankings/` | `openclaw-model-rankings` | 🔧 在建 |
| bp-auditor | `05_products/bp-auditor/` | — | 🔧 在建 |
| bp-manager | `05_products/bp-manager/` | — | 🔧 在建 |
| skill-tool-registry | `05_products/skill-tool-registry/` | — | 🔧 在建 |

---

## 产品详情

### cms-cwork — CWork 工作协同
- 定位：企业级任务与汇报协同引擎，6个Python编排脚本覆盖汇报/任务/审阅/催办/创建五大能力域
- 对应平台模块：工作协同（`https://github.com/xgjk/dev-guide`）
- 当前版本：v3.2.2

### bp-reporting-templates — BP 报告模板
- 定位：从 BP 数据生成月报/季报/半年报/年报填写模板，含严格审查规则
- 对应平台模块：BP 系统
- 当前版本：v1.0.2

### bp-prototype — BP 原型模板制造
- 定位：从 BP 规范和系统接口自动推理生成四套空白母版模板（年报/半年报/季报/月报）
- 对应平台模块：BP 系统
- 当前版本：v0.5.2

### tpr-framework — TPR 三省制工作流框架
- 定位：多 Agent 编排工作流框架，强制 DISCOVERY → GRV → Battle → Implementation 阶段边界
- 当前版本：v1.0.2

### xgjk-skill-auditor — 工厂 Skill 质检工具
- 定位：5 维度评分，给出 PASS/REVISE 判定 + 具体改进方向
- 当前版本：v1.0.1

### create-xgjk-skill — 玄关 Skill 发布工具链 【已移交】
- 定位：三位一体 Skill 全生命周期工具（发现/创建/发布）
- 对应平台：玄关开放平台 Skill 市场（`https://skills.mediportal.com.cn`）
- 移交原因：工具依赖玄关内部 API，由玄关团队长期维护更合理
- ClawHub slug 已改为 `xgjk-skill-factory`

### bp-auditor — BP 两级联动审计（在建）
- 定位：基于两级联动审计框架的 BP 审计 Skill，对 BP 进行递归审计
- 核心能力：Goal + KR + 举措拆解审计 + 下级 BP 承接审计
- 当前状态：v1.0.0，待发布

### bp-manager — BP 管理工具（在建）
- 定位：查询/管理 BP 目标/成果/举措
- 当前状态：S3 设计中

### cms-meeting-monitor — AI慧记会议监控（在建）
- 定位：从 AI慧记 拉取会议内容，支持字幕模式和静默模式
- 当前状态：v1.0.2，S5 测试中

### openclaw-model-rankings — OpenRouter 模型排行（在建）
- 定位：本地化 OpenRouter 模型目录，支持模型选型/价格对比/能力筛选问答
- 当前状态：v1.0.3，S4 执行中

### skill-tool-registry — Skill 工具注册管理（在建）
- 定位：统一管理 Gateway 层工具注册，支持 tools_provided 声明
- 当前状态：S3 设计中

---

*最后更新：2026-04-05 | 工厂 Skill 索引*
