# AF-SOP-01_Agent工厂 2.0 核心工作流规范 (Standard Operating Procedure)

- 版本：v4.6
- 状态：DRAFT (等待 Evan 审阅)
- 适用范围：**Agent Factory 作为 Skill 产品工厂的整体运营规范**
- 核心定位：**工业化生产线模式 (含四重发布分发体系)**

---

## 0. 工厂定位：Agent Factory 是什么？

**Agent Factory 不是一个项目，而是一个 Skill 产品工厂。**

---

## 1. Skill 产品生命周期八阶段 (Universal Lifecycle)

| 阶段 | 核心任务 | 责任主体 | 关键产出 |
|---|---|---|---|
| **S1: 背景了解 (Context)** | 理解业务系统、API 文档、用户痛点 | 工厂调度员 | `CONTEXT-01` |
| **S2: 需求确认 (Requirements)** | 访谈用户，固化需求边界与验收标准 | 工厂调度员 | `REQ-01` |
| **S3: 方案设计 (Design)** | 制定技术方案、数据流、接口规范 | 设计总工 | `DESIGN-01` |
| **S4: 开发 (Development)** | 编写代码、脚本、配置文件 | 交付总管 | `CODE-01` |
| **S5: 测试 (Testing)** | 功能测试、边界测试、真实数据验证 | 质检总监 | `TEST-01` |
| **S6: 发布 (Release)** | 执行物理、云端、企业、样件四重分发 | 交付总管 | `RELEASE-01` |
| **S7: 版本管理 (Versioning)** | 维护版本号、变更日志、兼容性矩阵 | 工厂调度员 | `CHANGELOG.md` |
| **S8: 持续修复 (Maintenance)** | Bug 修复、功能增强、用户反馈响应 | 工厂调度员 | `HOTFIX-XX` |

---

## 2. S6 发布阶段：四重分发体系 (Quad-channel Distribution)

发布不再是简单的“上传文件”，而是针对不同应用场景的资产化动作：

### 2.1 物理发布 (Local On-boarding)
- **动作**：**交付总管** 将 `04_workshop` 中的开发成果物理迁移至 `05_products/` 目录。
- **价值**：确保 Skill 在工厂本地环境中处于“就绪”状态。

### 2.2 云端发布 (ClawHub Registry)
- **动作**：执行 `clawhub publish {skill-name}`。
- **价值**：将标准化 Skill 包注册到公共云端仓库，实现跨环境“一键分发”。

### 2.3 企业发布 (Internal Skill Market)
- **动作**：通过企业发布工具链执行内部发布，默认使用 `create-xgjk-skill/scripts/skill-management/publish_skill.py` 一站式流程（打包→上传→注册/更新）。
- **价值**：满足企业内部合规与私有化部署需求，确保核心业务技能在组织内部安全流转。
- **标准输出**：必须保留 `Skill ID / code / downloadUrl / isInternal` 作为发布证据并写入项目台账。
- **发布后引导**：内部发布成功后，必须主动引导 Evan 到企业 Skill 市场主页核验：`https://skills.mediportal.com.cn/`。

### 2.4 业务交付 (Artifact Delivery)
- **动作**：将测试阶段产生的全量“工业级业务样件”打包，推送至 Evan 的交互窗口。
- **价值**：完成从“代码资产”到“管理成果”的最后一公里交付。

---

## 3. 工厂核心角色定义 (The Roles)

| 工业化角色名 (对外) | 核心职责 | 对应三省角色 |
|---|---|---|
| **设计总工 (Chief Designer)** | 出图纸、定标准、方案架构设计 | 中书省 (Zhongshu) |
| **交付总管 (Delivery Manager)** | 生产执行、代码编写、四重分发 | 尚书省 (Shangshu) |
| **质检总监 (Quality Director)** | 找茬压测、红蓝对抗、质量把控 | 门下省 (Menxi) |
| **工厂调度员 (Orchestrator)** | 产品经理、调度决策、用户窗口 | - |

---

## 4. Skill 设计档案与讨论沉淀（新增强制项）

为确保每个 Skill 都有可追溯设计思路、可持续优化路径，所有 Skill 项目必须在 Skill 目录下维护 `design/` 档案集。

### 4.1 每个 Skill 必备设计档案

每个 Skill 目录（如 `xxx-skill/`）必须包含：

- `design/DESIGN.md`
  - 产品目标、边界、不做什么
  - 核心流程与关键设计决策
  - 用户体验与失败兜底策略（如 fail-soft）
- `design/DISCUSSION-LOG.md`
  - 每次与用户讨论后的要点记录
  - 本次结论、变更点、待办项
- `design/LEARNING-LOOP.md`
  - 日/周/月复盘框架
  - 每次复盘必须产出“改进建议”
- `design/SHARE-LOG.jsonl`
  - 经验分享去重台账（是否已分享、何时、在哪个群）

### 4.2 讨论后维护规则（强制）

每次用户与 AI 对某个 Skill 发生“设计/体验/流程”讨论，必须执行：

1. 更新 `DISCUSSION-LOG.md`
2. 若有设计变更，同步更新 `DESIGN.md`
3. 若涉及能力提升建议，同步更新 `LEARNING-LOOP.md`
4. 若发生对外分享，记录 `SHARE-LOG.jsonl`

未完成以上动作，不得标记该轮讨论“已闭环”。

### 4.3 提醒机制

工厂调度员需通过定时提醒或会话收口提醒，推动用户执行“讨论后归档”。
默认采用“手动触发复盘 + 去重分享”策略（稳妥优先，不强制全自动群播）。

---

## 5. 复盘与分享机制（手动触发优先）

### 5.1 手动复盘触发

用户通过自然语言触发即可，例如：

- “生成今日复盘”
- “分享未分享的日经验”
- “分享未分享的周经验”
- “强制分享 2026-03-26 日经验”

### 5.2 去重分享规则

- 默认：已分享内容不重复分享
- 强制：仅在用户明确“强制分享”时允许重发
- 每次分享前必须查询 `SHARE-LOG.jsonl`

### 5.3 复盘最重要输出（必须包含）

- 问题修复沉淀（Problem → Rule）
- 预期偏差校正（Mismatch → Preference）
- 用户工作模式更新（Pattern → Twin）

---

## 6. 修订记录
| 版本 | 日期 | 变更摘要 | 变更人 |
|---|---|---|---|
| v4.2 | 2026-03-26 | 角色重塑：全量采用“设计总工/交付总管/质检总监”工业化称谓 | Zaowu |
| v4.3 | 2026-03-26 | **发布体系升级**：引入“企业内部 Skill 市场”分发路径，形成四重发布模式 | Zaowu |
| v4.4 | 2026-03-27 | **新增 Skill 设计档案强制规范**：要求每个 Skill 维护 design 档案集；引入讨论后更新规则与“手动复盘+去重分享”机制 | Zaowu |
| v4.5 | 2026-03-27 | **企业发布动作标准化**：S6企业发布默认走 xgjk-skill 一站式发布工具链，并强制留存 Skill ID/下载地址证据 | Zaowu |
| v4.6 | 2026-03-27 | **内部发布验收补充**：内部发布成功后，必须引导 Evan 访问 `https://skills.mediportal.com.cn/` 做页面核验 | Zaowu |
