# 工厂任务索引清单（Factory Task Index）

> 目的：支持快速查看每个项目的**状态、介绍、安装方法**。
> 适用范围：`04_workshop/AF-*` 项目 + 已发布 Skill。

---

## 1) 已发布（可安装）

| 项目ID | Skill / 产品 | 当前版本 | 状态 | 一句话介绍 | 安装/更新命令 |
|---|---|---:|---|---|---|
| AF-20260330-002 | `cms-meeting-materials` | v1.10.7 | ✅ RELEASED | 会议素材镜像（meetingChatId/meetingNumber/auto），支持120s短任务调度与护栏。 | `clawhub install cms-meeting-materials`<br>`clawhub update cms-meeting-materials --force` |
| AF-20260330-003 | `openclaw-model-rankings` | v1.0.1 | ✅ RELEASED | OpenRouter 模型目录本地化，支持互动问答式筛选/排序/对比。 | `clawhub install openclaw-model-rankings`<br>`clawhub update openclaw-model-rankings --force` |
| AF-20260328-002 | `cms-sop` | v1.0.0 | ✅ RELEASED | 统一 SOP 执行框架（Lite+Full） | `clawhub install cms-sop`<br>`clawhub update cms-sop --force` |
| AF-20260329-001 | `cms-cwork` | v1.5.0 | ✅ RELEASED | 工作协同能力包（汇报/任务/决策/分析） | `clawhub install cms-cwork`<br>`clawhub update cms-cwork --force` |
| AF-20260326-002 | `cas-chat-archive` | v1.2.0 | ✅ RELEASED | 聊天归档 + 查询 + 复盘沉淀（append-only） | `clawhub install cas-chat-archive`<br>`clawhub update cas-chat-archive --force` |
| AF-20260327-001 | `bp-reporting-templates` | v0.4.3 | ✅ RELEASED | BP 报告模板复刻与自动填充 | `clawhub install bp-reporting-templates`<br>`clawhub update bp-reporting-templates --force` |

---

## 2) 在建/暂停（不可安装或不建议安装）

| 项目ID | 项目名称 | 状态 | 当前阶段 | 一句话介绍 | 安装方式 |
|---|---|---|---|---|---|
| AF-20260329-002 | CAS 成长复盘体系 | 🚧 RUNNING | DESIGN | 面向 CAS 的成长复盘体系设计与落地路线。 | 暂无（未发布） |
| AF-20260329-003 | BP价值拆解与归因评分系统 | 🚧 RUNNING | EXECUTION | BP 价值拆解与归因评分，已恢复推进（方案C权重改造）。 | 暂无（未发布） |
| AF-20260330-001 | bp-scorer | 🚧 IN_PROGRESS | EXECUTION | BP 评分能力实现项目（当前未收口发布）。 | 暂无（未发布） |

---

## 3) 快速导航（源码路径）

- `AF-20260330-002` → `04_workshop/AF-20260330-002/`
- `AF-20260330-003` → `04_workshop/AF-20260330-003/`
- `cms-sop` 源码 → `05_products/cms-sop/`
- `cms-cwork` 源码 → `05_products/cms-cwork/`
- `cas-chat-archive` 源码 → `04_workshop/AF-20260326-002/cas-chat-archive/`

---

## 4) 维护规则（索引更新）

1. 新项目立项后，先在本清单补一行（状态=RUNNING/IN_PROGRESS）。
2. 发布到 ClawHub 后，补齐版本号与安装命令。
3. 项目暂停/废弃时，状态改为 PAUSED/DEPRECATED，并保留历史记录。
4. 每次重大发布后，同步更新 `03_governance/factory-registry.md`。

---

*最后更新：2026-03-30*