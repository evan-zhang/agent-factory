# 05_products — Skill 产品索引

> 本文件是工厂所有 Skill 产品的权威索引，持续更新。
> 每次新 Skill 发布、版本升级、状态变更后必须同步更新本文件。
>
> 最后更新：2026-04-01 | Zaowu

---

## 已发布产品（✅ RELEASED）

| 目录名 | 产品名称 | 版本 | ClawHub slug | 项目编号 | 发布日期 | 状态 |
|---|---|---|---|---|---|---|
| cms-cwork | CWork 工作协同 | v3.0.0 | `cms-cwork` | AF-20260323-001 | 2026-04-03 | ✅ Agent-First 重构 |
| cms-meeting-materials | CMS 会议素材镜像 | v1.10.10 | `cms-meeting-materials` | — | 2026-04-01 | ✅ 维护中 |
| cms-sop | 统一SOP执行框架 | v1.0.3 | `cms-sop` | AF-20260328-002 | 2026-03-29 | ✅ 观察期 |
| cas-chat-archive | CAS 聊天记录归档 | v1.2.3 | `cas-chat-archive` | AF-20260326-002 | 2026-03-31 | ✅ 观察期 |
| bp-reporting-templates | BP 报告模板 | v0.5.2 | `bp-reporting-templates` | AF-20260327-001 | 2026-04-01 | ✅ 发布 |
| create-xgjk-skill | 玄关 Skill 发布工具链 | v1.0.7 | `create-xgjk-skill` | — | 2026-04-01 | 🔄 移交玄关团队 |

| tpr-framework | TPR 三省制工作流框架 | v1.0.2 | `tpr-framework` | — | 2026-04-01 | ✅ 活跃 |
| xgjk-skill-auditor | 工厂 Skill 质检工具 | v1.0.1 | `xgjk-skill-auditor` | AF-20260331-002 | 2026-03-31 | ✅ 新发布 |
| xgjk-agent-core | 工厂 Agent 行为基础包（仅内部使用） | v1.0.1 | — | AF-20260401-001 | 2026-04-01 | 🔒 内部（2026-04-03 从 ClawHub 下架） |

---

## 在建产品（🔧 IN PROGRESS）

| 目录名 | 产品名称 | 当前版本 | 项目编号 | 阶段 | 说明 |
|---|---|---|---|---|---|
| cms-meeting-materials | AI慧记会议素材镜像 | v1.10.10 | AF-20260330-002 | Phase B 待开发 | W-03/W-04 技术债待修复后继续 |
| openclaw-model-rankings | OpenRouter 模型排行 | v1.0.2 | AF-20260330-003 | S4 执行中 | 第一阶段外部数据底座，未完成 |
| enterprise-memory | 企业级 Agent 记忆体系 | v0.1.0-beta | — | EXECUTE 压测中 | 代码已完成，2 周真实项目压测阶段；GitHub: evan-zhang/enterprise-agent-memory |

---

## 在建迭代版本（🔄 ITERATION）

| 目标产品 | 目标版本 | 项目编号 | 阶段 | 说明 |
|---|---|---|---|---|
| cas-chat-archive | v1.2.0 | AF-20260329-002 | EXECUTION | CAS 成长复盘体系 |

---

## 已废弃（❌ DEPRECATED）

| 目录名 | 产品名称 | 最终版本 | 废弃时间 | 原因 | 替代 |
|---|---|---|---|---|---|
| — | cms-soplite | v1.0.6 | 2026-03-29 | 被 cms-sop 合并取代 | `cms-sop`（Lite 模式）|

---

## L3 关联信息（Skill → Remote Repo 映射）

> 单一源码地原则：`05_products/{name}/` 是所有 Skill 的本地 SSOT。
> remote_repo 为可选备份/协作地，不接受直接 push（enterprise-memory 除外，独立维护）。
> 最后核查：2026-04-01 | Zaowu

| 目录名 | local_path | remote_repo | clawhub_slug | 源码地 |
|---|---|---|---|---|
| cms-cwork | `05_products/cms-cwork/` | — | `cms-cwork` | 本地 |
| cms-meeting-materials | `05_products/cms-meeting-materials/` | — | `cms-meeting-materials` | 本地 |
| cms-sop | `05_products/cms-sop/` | — | `cms-sop` | 本地 |
| cas-chat-archive | `05_products/cas-chat-archive/` | — | `cas-chat-archive` | 本地 |
| bp-reporting-templates | `05_products/bp-reporting-templates/` | — | `bp-reporting-templates` | 本地 |
| tpr-framework | `05_products/tpr-framework/` | — | `tpr-framework` | 本地 |
| xgjk-skill-auditor | `05_products/xgjk-skill-auditor/` | — | `xgjk-skill-auditor` | 本地 |
| xgjk-agent-core | `05_products/xgjk-agent-core/` | — | `xgjk-agent-core` | 本地 |
| openclaw-model-rankings | `05_products/openclaw-model-rankings/` | — | `openclaw-model-rankings` | 本地 |
| enterprise-memory | `05_products/enterprise-memory/` | `evan-zhang/enterprise-agent-memory` | — | **GitHub（独立维护）** |
| create-xgjk-skill | `05_products/create-xgjk-skill/` | — | `create-xgjk-skill` | 本地（已移交） |

---

## 产品详情

### cms-cwork — CWork 工作协同
- 定位：企业级任务与汇报协同引擎，6个Python编排脚本覆盖汇报/任务/审阅/催办/创建五大能力域
- 对应平台模块：工作协同（`https://github.com/xgjk/dev-guide`）
- 当前版本：v3.0.0，Agent-First 架构重构（AF-20260323-001）

### cms-sop — 统一SOP执行框架
- 定位：Lite/Full 双模式 SOP 执行框架，按任务复杂度自动路由
- 无平台接口依赖

### cas-chat-archive — CAS 聊天记录归档
- 定位：聊天全量归档 + 可运营查询 + 手动复盘沉淀（append-only）
- 发布渠道：ClawHub + 公司内部 Skill 市场（双通道）
- v1.2.0 迭代中（AF-20260329-002，成长复盘体系）

### bp-reporting-templates — BP 报告模板
- 定位：从 BP 数据生成月报/季报/半年报/年报填写模板，含严格审查规则
- 对应平台模块：BP 系统

### create-xgjk-skill — 玄关 Skill 发布工具链 【已移交】
- 定位：三位一体 Skill 全生命周期工具（发现/创建/发布）
- 对应平台：玄关开放平台 Skill 市场（`https://skills.mediportal.com.cn`）
- 移交原因：工具依赖玄关内部 API，由玄关团队长期维护更合理；ClawHub slug 被占用无法发布
- 源码保留路径：`05_products/create-xgjk-skill/`（不删除，供参考）

### tpr-framework — TPR 三省制工作流框架
- 定位：多 Agent 编排工作流框架，强制 DISCOVERY → GRV → Battle → Implementation 阶段边界

### cms-meeting-materials — AI慧记会议素材镜像（在建）
- 定位：拉取并持续同步会议转写文本到本机，为总结/问答/纪要 Skill 提供标准化原始素材
- 对应平台模块：AI慧记
- 当前状态：Phase B 技术债（W-03 摘要计时器逻辑缺陷、W-04 断连恢复未触发全量校验）待修复

### openclaw-model-rankings — OpenRouter 模型排行（在建）
- 定位：本地化 OpenRouter 模型目录，支持模型选型/价格对比/能力筛选问答
- 当前状态：S4 执行中，第一阶段外部客观数据底座未完成

### enterprise-memory — 企业级 Agent 记忆体系（在建）
- 定位：类人多层记忆系统，支持多任务交替推进时的上下文保持，核心解决 Agent 跨任务记忆丢失问题
- GitHub repo：`evan-zhang/enterprise-agent-memory`（private，独立维护）
- 架构：项目层 + 会话层 + 全局索引层，三个核心脚本（update_index.py / switch_project.py / compress.py）
- 当前状态：EXECUTE 阶段，代码完成，2026-03-31 进入 2 周真实项目压测
- 管理方式：代码在独立 repo，工厂仅做状态跟踪，不干预内部实现
