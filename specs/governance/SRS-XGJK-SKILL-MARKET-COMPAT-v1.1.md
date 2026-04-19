# SRS — 玄关健康内部 Skill 市场与 ClawHub 国际规范对齐

**文档编号**：SRS-XGJK-SKILL-MARKET-COMPAT  
**版本**：v1.1  
**状态**：待 Evan 确认  
**日期**：2026-03-31  
**作者**：factory-orchestrator（与张成鹏确认）  
**目标读者**：玄关健康 TE 平台开发团队、Agent Factory 发布链路维护者  
**变更说明**：基于质检总监 v1.0 审核报告（F-01～F-10）修订

---

## 修订记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2026-03-31 | 初稿 |
| v1.1 | 2026-03-31 | 修复 F-01 版本映射歧义（P0）；补充依赖与风险章节（F-04）；消除 Out of Scope 与 FR-01 矛盾（F-07）；完善验收标准可测试性（F-02/03/05/06/08/09/10） |

---

## 一、背景与目标

### 1.1 现状

Agent Factory 目前存在两条并行的 Skill 发布链路：

| 链路 | 平台 | 规范来源 | 鉴权方式 | 打包格式 | 发布命令 |
|------|------|----------|----------|----------|----------|
| **ClawHub（国际）** | https://clawhub.com | ClawHub 开放规范 | `clawhub login`（OAuth） | 目录（含 SKILL.md） | `clawhub publish` |
| **玄关内部 TE 市场** | https://skills.mediportal.com.cn | 内部自研规范 | `XG_USER_TOKEN`（xgToken） | ZIP 包（上传七牛） | `publish_skill.py` |

两套链路在打包格式、鉴权方式、元数据字段、发布 CLI 上均不兼容，导致每次发布需要维护两套脚本，成本翻倍。

### 1.2 当前状态基线（F-10 新增）

已发布的 6 个 Skill 及当前发布方式：

| Skill | 版本 | 当前 ClawHub 发布方式 | 当前内部市场发布方式 |
|-------|------|----------------------|---------------------|
| `cas-chat-archive` | v1.2.0 | `clawhub publish` | `publish_skill.py` 手动 |
| `bp-reporting-templates` | v0.4.3 | `clawhub publish` | `publish_skill.py` 手动 |
| `cms-sop` | v1.0.0 | `clawhub publish` | `publish_skill.py` 手动 |
| `cms-cwork` | v1.5.0 | `clawhub publish` | `publish_skill.py` 手动 |
| `cms-meeting-materials` | v1.10.7 | `clawhub publish` | `publish_skill.py` 手动 |
| `openclaw-model-rankings` | v1.0.1 | `clawhub publish` | `publish_skill.py` 手动 |

迁移后：以上 6 个 Skill 统一改为 `publish_all.py` 双发布；`publish_skill.py` 作为内部发布底层实现保留，不废弃。

### 1.3 目标

**让玄关内部 TE 市场严格遵循 ClawHub 国际规范，实现"ClawHub 可上架即玄关可上架"的一键无缝迁移。**

具体目标：
1. 内部 TE 市场接受并正确解析 ClawHub 格式的 SKILL.md 作为权威元数据来源
2. 发布者只需维护一套 SKILL.md，一条命令即可同时发布到两个平台
3. 内部 TE 市场的字段体系向 ClawHub 规范对齐，内部扩展字段以 namespace 隔离

---

## 二、现有规范差异分析

### 2.1 Skill 元数据字段对比

| 字段语义 | ClawHub（SKILL.md frontmatter） | 玄关内部（register_skill API） | 差异 |
|----------|-------------------------------|-------------------------------|------|
| 唯一标识 | `name`（frontmatter） | `code`（API body） | 字段名不同，语义相同 |
| 显示名称 | `name`（frontmatter） | `name`（API body） | ✅ 相同 |
| 版本号 | `version`（frontmatter，semver 字符串） | `version`（API body，整型） | 格式不同，需映射规范（见 FR-02） |
| 描述 | `description`（frontmatter） | `description`（API body） | ✅ 相同 |
| 标签 | `metadata.openclaw.tags[]` | `label`（单字符串） | 结构不同：多标签 vs 单字符串 |
| 依赖声明 | `metadata.openclaw.requires` | 无 | 内部缺失，阶段1忽略并输出 WARNING |
| 安装钩子 | `metadata.openclaw.install` | 无 | 内部缺失，阶段1忽略并输出 WARNING（见 FR-01 补充） |
| 内部标记 | 无（通过 `metadata.xgjk` 扩展） | `isInternal`（布尔） | 内部独有，通过 FR-04 扩展机制解决 |
| Hook 声明 | hooks 子目录 `HOOK.md`（自动发现） | 无对应机制 | 内部缺失，阶段2规划 |

### 2.2 打包格式差异

| 项目 | ClawHub | 玄关内部 |
|------|---------|----------|
| 入口文件 | `SKILL.md`（必须在根目录） | `SKILL.md`（已对齐，`pack_skill.py` 校验） |
| 传输方式 | CLI 直接上传目录 | 打包 ZIP → 上传七牛 → 注册 API 传 downloadUrl |
| 忽略规则 | `.clawhubignore` 控制 | 需对齐（见 FR-05） |
| 子目录约定 | `scripts/`、`hooks/`、`references/`、`data/` | 无约束 |

### 2.3 鉴权机制差异

| 项目 | ClawHub | 玄关内部 |
|------|---------|----------|
| 认证方式 | OAuth（`clawhub login`） | AppKey 换 xgToken，环境变量 `XG_USER_TOKEN` |
| Token 生命周期 | 长效 refresh token | 会话级，需定期换取 |
| 权限粒度 | 个人/组织维度 | 企业维度（corpId） |

---

## 三、需求规格

### 3.1 功能需求

#### FR-01 SKILL.md 作为唯一权威元数据源

- **描述**：内部 TE 平台在接收 Skill 时，必须能够解析 ClawHub 格式的 SKILL.md frontmatter，并将其映射到内部字段，而非要求发布者维护额外的内部元数据文件。

- **阶段1处理策略（F-07 补充）**：以下字段在阶段1内部发布时**忽略但必须输出 WARNING**：
  - `metadata.openclaw.requires`（依赖声明）
  - `metadata.openclaw.install`（安装钩子）
  - `hooks/` 子目录（Hook 声明）
  - WARNING 格式：`[WARN] 字段 X 在内部市场不支持，已忽略。安装后相关功能不可用，请联系 TE 团队升级支持。`

- **验收标准**：
  - [ ] 给定一个标准 ClawHub SKILL.md，内部平台能自动提取 `name`/`version`/`description` 等字段
  - [ ] 无需额外的内部 metadata 文件即可完成发布
  - [ ] 解析失败时退出码非 0，并输出明确错误信息（包含失败字段名和行号）
  - [ ] 包含 `metadata.openclaw.requires`/`install` 或 `hooks/` 的 Skill 发布时必须输出 WARNING，不得静默忽略

---

#### FR-02 字段映射规则（标准化）

内部平台必须按以下规则将 SKILL.md 字段映射到内部 API：

| SKILL.md 字段 | 内部 API 字段 | 映射规则 |
|--------------|--------------|---------|
| `name`（frontmatter） | `code` | 直接映射（作为唯一标识） |
| `name`（frontmatter） | `name` | 直接映射（显示名） |
| `version`（semver） | `version` | 见下方版本映射规范（F-01 修复） |
| `description` | `description` | 直接映射 |
| `metadata.openclaw.tags[]` | `label` | 多标签 → 逗号拼接字符串 |

**版本映射规范（F-01 P0 修复）**：

阶段1（内部 API 仍为整型时），使用以下无歧义映射公式：

```
内部 version 整型 = major × 10000 + minor × 100 + patch
```

示例：
- `1.2.0` → `10200`
- `1.20.0` → `11200`（无歧义）
- `2.0.1` → `20001`

约束：
- `minor` 和 `patch` 不得超过 99（即 semver 各段最大值为 99）；若超出，`publish_all.py` 必须报错退出，不得强行映射
- 当 minor ≥ 100 或 patch ≥ 100 时，错误信息：`[ERROR] version X.Y.Z 中 minor/patch 超出内部市场支持上限(99)，请升级内部 API 至 semver 字符串模式后再发布`

**阶段2（推荐，需 TE 配合）**：内部 API `version` 字段升级为直接支持 semver 字符串，整型映射作废，阶段1的约束随之解除。

---

#### FR-03 一键双发布命令

提供 `publish_all.py` 统一发布工具，支持单命令同时发布到 ClawHub 和内部市场。

```bash
# 一键双发（目标态）
python3 publish_all.py ./my-skill

# 仅发某一平台
python3 publish_all.py ./my-skill --only clawhub
python3 publish_all.py ./my-skill --only xgjk

# 预检模式（不实际发布）
python3 publish_all.py ./my-skill --dry-run
```

**错误处理规范（F-05 补充）**：

| 场景 | 退出码 | 行为 |
|------|--------|------|
| 双发布全部成功 | 0 | 输出双平台链接 |
| ClawHub 成功，内部失败 | 1 | 输出 ClawHub 链接 + 内部错误信息；**不回滚 ClawHub**（发布行为不可逆，记录不一致状态供人工处理） |
| ClawHub 失败，内部成功 | 1 | 输出内部链接 + ClawHub 错误信息 |
| 双发布全部失败 | 2 | 输出双端错误信息 |
| 预检失败（如 version 映射超限） | 3 | 输出具体错误，不执行任何发布 |

重试策略：网络错误自动重试 2 次，间隔 3 秒，超出后报错；不支持断点续发（v1 不做）。

**验收标准**：
- [ ] 一条命令成功发布到两个平台，退出码为 0
- [ ] 任一平台失败时退出码非 0，输出明确错误，不影响另一平台已成功的发布结果
- [ ] 发布结果输出两个平台的 Skill ID / 下载地址 / 页面链接
- [ ] `--dry-run` 模式输出待发布信息和双平台文件清单 diff，不实际执行任何写操作

---

#### FR-04 内部市场扩展字段支持（namespace 隔离）

ClawHub 规范中未覆盖的内部专有字段，通过 SKILL.md 的 `metadata.xgjk` namespace 扩展：

```yaml
---
name: my-skill
version: 1.2.0
description: "我的 Skill"
metadata:
  openclaw:
    requires:
      bins: [python3]
  xgjk:                    # 玄关内部扩展字段（ClawHub 发布时忽略）
    isInternal: true       # 是否为内部 Skill
    corpId: "default"      # 企业 ID（留空则使用默认企业）
    label: "工作协同"       # 内部分类标签（覆盖 tags 映射结果）
---
```

**验收标准**：
- [ ] `metadata.xgjk` 字段被内部平台正确读取并映射到对应 API 字段
- [ ] ClawHub 发布时 `metadata.xgjk` 被完整忽略，不出现在发布包中
- [ ] 不包含 `metadata.xgjk` 的 Skill 发布到内部市场时，`isInternal` 默认为 `false`，`corpId` 使用默认值
- [ ] 不破坏现有 6 个 Skill 的 SKILL.md 对 ClawHub 的兼容性

---

#### FR-05 `.clawhubignore` 统一忽略规则

内部打包工具与 ClawHub 共用 `.clawhubignore` 规则，确保两个平台打包产物的**文件路径集合相同**（不要求字节级一致）。

**"内容一致"定义**：排除 `.clawhubignore` 中列出的文件后，ClawHub 上传的文件列表与内部 ZIP 包内的文件列表完全相同。

**验收标准**：
- [ ] `.clawhubignore` 中列出的文件不出现在内部打包 ZIP 中
- [ ] `publish_all.py --dry-run` 输出两个平台的文件清单 diff，结果为空（无差异）
- [ ] 当存在差异时，`--dry-run` 明确列出差异文件并标注来源（ClawHub 独有 / 内部独有）

---

#### FR-06 版本一致性校验

发布时检查同一 Skill 在两个平台的当前版本号：

**验收标准**：
- [ ] 若两个平台当前版本不一致，`publish_all.py` 输出 WARNING（不阻断发布）
- [ ] `--dry-run` 模式下输出双平台当前版本与待发布版本的三列对比表（平台 / 当前版本 / 待发布版本）
- [ ] 若待发布版本低于任一平台当前版本（降版本发布），必须报错退出（防止误操作）

---

### 3.2 非功能需求

| 编号 | 类型 | 描述 |
|------|------|------|
| NFR-01 | 兼容性 | 现有已发布 6 个 Skill（见 1.2 清单）无需修改 SKILL.md，通过 `--dry-run` 回归验证（见 G4） |
| NFR-02 | 安全性 | `XG_USER_TOKEN` 不得出现在**任何**标准输出、标准错误、日志文件、异常堆栈中；HTTP 请求异常时不得打印完整 URL（含 token 的请求头需脱敏）；code review checklist 必须包含此项 |
| NFR-03 | 幂等性 | 重复发布同版本 Skill 不报错，输出"已是最新版本，跳过发布"并以退出码 0 退出 |
| NFR-04 | 可观测性 | 发布结果必须输出两个平台的页面链接，供人工核验 |
| NFR-05 | 可扩展性 | 发布器采用 adapter 模式，新增第三方市场只需实现对应 adapter，不修改 `publish_all.py` 核心逻辑 |

---

## 四、技术方案建议

### 4.1 推荐实现路径（三阶段）

```
阶段1（立即可做，不依赖 TE 团队）
    publish_all.py
    ├── 解析 SKILL.md frontmatter
    ├── 版本号：semver → major×10000+minor×100+patch 整型（超限报错）
    ├── 调用 clawhub publish（ClawHub adapter）
    ├── 调用 publish_skill.py（内部 adapter）+ 字段映射
    ├── 错误处理：独立执行，退出码规范（见 FR-03）
    └── metadata.xgjk 字段解析 + install/requires 字段 WARNING

阶段2（需 TE 配合，预计排期待确认）
    内部 TE 市场 API 升级
    ├── version 字段支持 semver 字符串（阶段1整型映射作废）
    ├── 新增 metadata 字段（存储 xgjk 扩展内容）
    ├── 接收并解析 SKILL.md 原文（可选，供平台 UI 展示）
    └── requires/install/hooks 字段支持（依赖声明、安装钩子、Hook 声明）

阶段3（长期目标，不依赖本项目）
    clawhub publish --also-publish-to xgjk
    └── ClawHub CLI 官方插件扩展
```

### 4.2 阶段1 适配器架构

```python
# publish_all.py — 双发布适配器
#
# 接口约定（adapter 模式，NFR-05）：
#   class PublishAdapter:
#       def check_version(skill_name) -> str     # 返回平台当前版本
#       def publish(skill_dir, meta) -> Result    # 发布，返回 {id, url, status}
#       def is_latest(skill_name, version) -> bool
#
# ClawHubAdapter  → 封装 clawhub publish CLI
# XgjkAdapter     → 封装 publish_skill.py + 字段映射
# 新平台           → 实现同一接口，publish_all.py 无需修改
```

### 4.3 内部 API 字段扩展建议（阶段2，给 TE 平台开发团队）

`im/skill/register` 和 `im/skill/update` 接口新增字段：

```json
{
  "code": "my-skill",
  "name": "My Skill",
  "version": "1.2.0",         // 升级为 semver 字符串（替代整型）
  "description": "...",
  "label": "工作协同",
  "downloadUrl": "...",
  "isInternal": true,
  "corpId": "default",
  "skillMdContent": "..."     // 可选：原始 SKILL.md 内容，供平台 UI 展示
}
```

---

## 五、不在范围内（Out of Scope）

| 项目 | 原因 |
|------|------|
| 内部 TE 市场 UI 改版 | 纯后端 API 对齐即可满足发布需求 |
| ClawHub 官方 CLI 修改 | 阶段1通过封装脚本解决，不需要修改上游 |
| **install 侧对齐（安装行为）** | **仅排除安装行为对齐**；install/requires 字段的发布侧解析已纳入 FR-01（输出 WARNING）。安装时的依赖自动安装能力为阶段2规划项 |
| 审批流程对齐 | 两个平台的审核机制不同，暂不对齐 |
| 自动同步（无需人工触发） | 阶段3再考虑，现阶段需人工触发 |
| 断点续发（partial publish 重试） | v1 不做，失败后重新运行即可 |

---

## 六、依赖与风险（F-04 新增）

### 6.1 外部依赖

| 依赖方 | 依赖内容 | 影响阶段 | 当前状态 |
|--------|---------|---------|---------|
| 玄关 TE 平台团队 | 内部 API 升级（version semver 化、metadata 字段、SKILL.md 解析） | 阶段2 | **待确认排期**；建议将 TE 负责人列为本 SRS 评审人 |
| ClawHub 官方 | `--also-publish-to` 插件扩展 | 阶段3 | 长期规划，不在当前项目范围 |

### 6.2 风险识别

| 风险编号 | 风险描述 | 概率 | 影响 | 缓解措施 |
|---------|---------|------|------|---------|
| R-01 | 阶段2 TE 团队排期延迟，阶段1整型映射长期使用 | 中 | 中（minor/patch≥100 时阶段1无法发布） | 约定版本号规范：各段不超过 99；超出时先协调 TE 升级 API |
| R-02 | ClawHub API 变更导致 `clawhub publish` CLI 行为变化 | 低 | 高（双发布中断） | ClawHub adapter 封装隔离，版本锁定 |
| R-03 | 七牛上传超时（Skill 包过大或网络抖动） | 中 | 低（内部发布失败，ClawHub 不受影响） | 自动重试 2 次；超时阈值 60 秒 |
| R-04 | 两个平台同名 Skill code 冲突（内部已有同名但非本工厂发布的 Skill） | 低 | 高（覆盖他人 Skill） | 发布前 `check_version` 校验；不存在则走注册，存在则走更新 |

### 6.3 阶段2 block 时的降级策略

若 TE 团队无法在预期时间内完成 API 升级，阶段1方案可长期运行，约束如下：
- 所有 Skill 版本号各段必须 ≤ 99（现有 6 个 Skill 均满足）
- `publish_all.py` 在整型映射时输出提示：`[INFO] 内部平台使用整型版本 X，对应 semver Y.Z.W`
- 该约束记录在 `publish_all.py` README 和本文档中，直至阶段2完成

---

## 七、验收门控

| 编号 | 门控项 | 验收标准 | 说明 |
|------|--------|---------|------|
| G1 | 双发布速度 | 在包大小 ≤ 10MB、网络带宽 ≥ 10Mbps 的标准环境下，`publish_all.py` 处理耗时（排除实际网络传输）≤ 30 秒 | F-08 |
| G2 | 双平台可搜索 | 发布完成后 **≤ 5 分钟**内，通过 Skill name 精确搜索在两个平台均可返回该 Skill 条目 | F-02 |
| G3 | 幂等性 | 重复运行 `publish_all.py`（相同版本）退出码为 0，输出"已是最新版本，跳过发布" | — |
| G4 | 向后兼容回归 | 对现有 6 个 Skill 执行 `publish_all.py --dry-run`，全部输出 OK，无 ERROR（WARNING 允许存在） | F-03/NFR-01 |
| G5 | xgjk 字段隔离 | 包含 `metadata.xgjk` 的 Skill 发布到 ClawHub 后，ClawHub 页面和 API 响应中不含 `xgjk` 任何字段 | — |
| G6 | 版本映射无歧义 | 对 `1.2.0`、`1.20.0`、`2.0.1` 三个版本运行映射，输出整型值两两不同 | F-01 |
| G7 | WARNING 输出 | 含 `metadata.openclaw.install` 或 `requires` 的 Skill 发布内部市场时，stdout 中出现 `[WARN]` 信息 | F-07 |

---

## 八、相关文档

| 文档 | 路径 |
|------|------|
| 玄关内部发布脚本 | `projects/2604014/create-xgjk-skill/scripts/skill-management/publish_skill.py` |
| 玄关内部 API 规范 | `projects/2604014/create-xgjk-skill/openapi/skill-management/publish-skill.md` |
| ClawHub CLI Skill | `/opt/homebrew/lib/node_modules/openclaw/skills/clawhub/SKILL.md` |
| 工厂任务索引 | `_runtime/governance/factory-task-index.md` |
| v1.0 审核报告 | `projects/2603311/05_closure/REVIEW-REPORT-v1.0.md` |

---

*SRS v1.1，已纳入 v1.0 审核报告全部 10 条意见（P0×1、P1×6、P2×3）。*  
*待 Evan 确认后进入 S3 设计阶段。*
