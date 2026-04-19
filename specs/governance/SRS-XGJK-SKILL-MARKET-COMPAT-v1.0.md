# SRS — 玄关健康内部 Skill 市场与 ClawHub 国际规范对齐

**文档编号**：SRS-XGJK-SKILL-MARKET-COMPAT  
**版本**：v1.0  
**状态**：草稿  
**日期**：2026-03-31  
**作者**：factory-orchestrator（与张成鹏确认）  
**目标读者**：玄关健康 TE 平台开发团队、Agent Factory 发布链路维护者

---

## 一、背景与目标

### 1.1 现状

Agent Factory 目前存在两条并行的 Skill 发布链路：

| 链路 | 平台 | 规范来源 | 鉴权方式 | 打包格式 | 发布命令 |
|------|------|----------|----------|----------|----------|
| **ClawHub（国际）** | https://clawhub.com | ClawHub 开放规范 | `clawhub login`（OAuth） | 目录（含 SKILL.md） | `clawhub publish` |
| **玄关内部 TE 市场** | https://skills.mediportal.com.cn | 内部自研规范 | `XG_USER_TOKEN`（xgToken） | ZIP 包（上传七牛） | `publish_skill.py` |

两套链路在打包格式、鉴权方式、元数据字段、发布 CLI 上均不兼容，导致每次发布需要维护两套脚本，成本翻倍。

### 1.2 目标

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
| 版本号 | `version`（frontmatter） | `version`（API body，整型） | 格式不同：ClawHub 为 semver 字符串（`1.2.0`），内部为整型（`2`） |
| 描述 | `description`（frontmatter） | `description`（API body） | ✅ 相同 |
| 标签 | `metadata.openclaw.tags` 等 | `label`（单字符串） | 结构不同：ClawHub 多标签，内部单字符串 |
| 依赖声明 | `metadata.openclaw.requires` | 无 | 内部缺失 |
| 安装钩子 | `metadata.openclaw.install` | 无 | 内部缺失 |
| 内部标记 | 无 | `isInternal`（布尔） | 内部独有，需扩展机制 |
| Hook 声明 | hooks 子目录 `HOOK.md`（自动发现） | 无对应机制 | 内部缺失 |

### 2.2 打包格式差异

| 项目 | ClawHub | 玄关内部 |
|------|---------|----------|
| 入口文件 | `SKILL.md`（必须在根目录） | `SKILL.md`（已对齐，`pack_skill.py` 校验） |
| 传输方式 | CLI 直接上传目录 | 打包 ZIP → 上传七牛 → 注册 API 传 downloadUrl |
| 隐藏文件 | `.clawhubignore` 控制忽略 | `.clawhubignore` 已兼容（`pack_skill.py` 跳过 `.` 开头） |
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
- **验收标准**：
  - [ ] 给定一个标准 ClawHub SKILL.md，内部平台能自动提取 `name`/`version`/`description` 等字段
  - [ ] 无需额外的内部 metadata 文件即可完成发布
  - [ ] 解析失败时给出明确错误提示

#### FR-02 字段映射规则（标准化）

内部平台必须按以下规则将 SKILL.md 字段映射到内部 API：

| SKILL.md 字段 | 内部 API 字段 | 映射规则 |
|--------------|--------------|---------|
| `name`（frontmatter） | `code` | 直接映射（作为唯一标识） |
| `name`（frontmatter） | `name` | 直接映射（显示名） |
| `version` | `version` | semver → 整型映射（`1.2.0` → 取 minor+patch 组合，如 `120`；或维护 semver 字符串字段） |
| `description` | `description` | 直接映射 |
| `metadata.openclaw.tags[]` | `label` | 多标签 → 逗号拼接字符串 |

> 推荐：内部 API `version` 字段扩展为支持 semver 字符串（`"1.2.0"`），放弃整型，以消除映射歧义。

#### FR-03 一键双发布命令

提供统一发布工具，支持单命令同时发布到 ClawHub 和内部市场：

```bash
# 只发 ClawHub
clawhub publish ./my-skill --slug my-skill --version 1.2.0

# 只发内部市场
python3 publish_skill.py ./my-skill --code my-skill --name "My Skill"

# 一键双发（目标态）
python3 publish_all.py ./my-skill
# 或：
clawhub publish ./my-skill --also-publish-to xgjk
```

- **验收标准**：
  - [ ] 一条命令成功发布到两个平台
  - [ ] 任一平台失败时给出明确提示，不影响另一平台的发布结果
  - [ ] 发布结果输出两个平台的 Skill ID / 下载地址

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
  xgjk:                    # 玄关内部扩展字段
    isInternal: true       # 是否为内部 Skill
    corpId: "default"      # 企业 ID
    label: "工作协同"       # 内部分类标签（覆盖 tags 映射）
---
```

- **验收标准**：
  - [ ] `metadata.xgjk` 字段被内部平台正确读取
  - [ ] ClawHub 发布时忽略 `metadata.xgjk`（不上传到 ClawHub）
  - [ ] 不破坏现有 SKILL.md 对 ClawHub 的兼容性

#### FR-05 .clawhubignore 统一忽略规则

内部打包工具与 ClawHub 共用 `.clawhubignore` 规则：

- `pack_skill.py` 已实现跳过 `.` 开头文件/目录（与 ClawHub 对齐）
- 需新增：读取 `.clawhubignore` 文件并按规则排除文件
- **验收标准**：
  - [ ] `.clawhubignore` 中列出的文件不出现在打包 ZIP 中
  - [ ] ClawHub 与内部 ZIP 包内容一致（除平台元数据外）

#### FR-06 版本一致性校验

发布时校验两个平台上的版本号一致：

- **验收标准**：
  - [ ] 若同一 Skill 在两个平台版本不一致，发布工具输出警告
  - [ ] `--dry-run` 模式下输出双平台当前版本与待发布版本对比

### 3.2 非功能需求

| 编号 | 类型 | 描述 |
|------|------|------|
| NFR-01 | 兼容性 | 现有已发布 Skill（6个）不需要重新打包，向前兼容 |
| NFR-02 | 安全性 | 内部鉴权 token 不得出现在发布命令输出或日志中 |
| NFR-03 | 幂等性 | 重复发布同版本 Skill 不报错，给出"已是最新版本"提示 |
| NFR-04 | 可观测性 | 发布结果输出两个平台的链接，供人工核验 |
| NFR-05 | 可扩展性 | 架构支持未来接入第三方市场（如企业微信应用市场），不需要改核心逻辑 |

---

## 四、技术方案建议

### 4.1 推荐实现路径（三阶段）

```
阶段1（适配层）：publish_all.py 封装双发布
    ├── 读取 SKILL.md frontmatter
    ├── 调用 clawhub publish（ClawHub）
    └── 调用 publish_skill.py（内部）+ 字段映射

阶段2（字段对齐）：内部 TE 市场 API 升级
    ├── version 字段支持 semver 字符串
    ├── 新增 metadata 字段（存储 xgjk 扩展）
    └── 接收 SKILL.md 作为 multipart 直接解析

阶段3（完全统一）：clawhub publish --also-publish-to xgjk
    └── ClawHub CLI 官方插件扩展（长期目标）
```

### 4.2 阶段1 立即可交付的适配脚本设计

```python
# publish_all.py — 双发布适配器（阶段1实现）
# 输入：Skill 目录
# 流程：
#   1. 读取 SKILL.md frontmatter（name/version/description/metadata.xgjk）
#   2. 并发（或串行）调用：
#      A. clawhub publish <dir> --slug <name> --version <version>
#      B. python3 publish_skill.py <dir> --code <name> --name <显示名> [--internal]
#   3. 汇总两个平台的结果，输出双链接
# 环境变量：XG_USER_TOKEN（内部）+ clawhub 已登录（国际）
```

### 4.3 内部 API 字段扩展建议（给 TE 平台开发团队）

在 `im/skill/register` 和 `im/skill/update` 接口中新增：

```json
{
  "code": "my-skill",
  "name": "My Skill",
  "version": "1.2.0",        // 新增：支持 semver 字符串
  "description": "...",
  "label": "工作协同",
  "downloadUrl": "...",
  "isInternal": true,
  "skillMdContent": "..."    // 新增：原始 SKILL.md 内容（可选，供平台直接解析）
}
```

---

## 五、不在范围内（Out of Scope）

| 项目 | 原因 |
|------|------|
| 内部 TE 市场 UI 改版 | 纯后端 API 对齐即可满足发布需求 |
| ClawHub 官方 CLI 修改 | 阶段1通过封装脚本解决，不需要修改上游 |
| Skill 安装（install）侧对齐 | 本期仅对齐发布（publish）侧 |
| 审批流程对齐 | 两个平台的审核机制不同，暂不对齐 |
| 自动同步（发布一次自动推到另一平台）| 阶段3再考虑，现阶段需人工触发 |

---

## 六、验收门控

| 门控项 | 标准 |
|--------|------|
| G1 | 给定一个符合 ClawHub 规范的 Skill 目录，`publish_all.py` 能在 5 分钟内完成双发布 |
| G2 | 发布后在 ClawHub 和 `skills.mediportal.com.cn` 均可搜索到该 Skill |
| G3 | 重复运行 `publish_all.py` 不报错，输出"已是最新版本"（幂等） |
| G4 | 已发布的 6 个 Skill（cas-chat-archive 等）无需改动 SKILL.md，兼容现有格式 |
| G5 | `metadata.xgjk` 字段在 ClawHub 发布时被忽略，不污染国际市场 |

---

## 七、相关文档

| 文档 | 路径 |
|------|------|
| 玄关内部发布脚本 | `05_products/create-xgjk-skill/scripts/skill-management/publish_skill.py` |
| 玄关内部 API 规范 | `05_products/create-xgjk-skill/openapi/skill-management/publish-skill.md` |
| ClawHub CLI Skill | `/opt/homebrew/lib/node_modules/openclaw/skills/clawhub/SKILL.md` |
| 工厂任务索引 | `03_governance/factory-task-index.md` |
| 工厂总台账 | `03_governance/factory-registry.md` |

---

*SRS 草稿，待 Evan 审阅确认后可立项执行。*  
*下一步：确认此 SRS → 立项 AF-2026XXXX-00X → 设计总工（Generator）出详细设计方案。*
