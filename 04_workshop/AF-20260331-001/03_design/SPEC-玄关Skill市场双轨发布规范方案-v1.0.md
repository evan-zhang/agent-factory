# 玄关 Skill 市场双轨发布规范方案

**文档编号**：SPEC-XGJK-SKILL-DUAL-PUBLISH  
**版本**：v1.0  
**状态**：正式发布  
**日期**：2026-03-31  
**作者**：Agent Factory（张成鹏主导）  
**目标读者**：
- **Agent Factory 工程师**（第四部分）：负责实现 `publish_all.py` 双发布适配器
- **玄关 TE 平台团队**（第五部分）：负责内部 Skill 市场 API 升级
- **两方共读**：第一、二、三、六、七部分

---

## 第一部分：背景与目标

### 1.1 现状问题

Agent Factory 目前维护两条并行的 Skill 发布链路，每次发布一个 Skill 需要手动执行两套流程：

| 链路 | 平台 | 鉴权 | 打包格式 | 发布命令 |
|------|------|------|---------|---------|
| **ClawHub（国际）** | clawhub.com | `clawhub login` OAuth | 目录（含 SKILL.md） | `clawhub publish` |
| **玄关内部 TE 市场** | skills.mediportal.com.cn | `XG_USER_TOKEN` | ZIP 包（上传七牛） | `publish_skill.py` |

**核心痛点**：两套链路字段不兼容，维护成本翻倍，且容易出现两个平台版本不一致。

### 1.2 已发布 Skill 现状（基线）

| Skill | 当前版本 |
|-------|---------|
| `cas-chat-archive` | v1.2.0 |
| `bp-reporting-templates` | v0.4.3 |
| `cms-sop` | v1.0.0 |
| `cms-cwork` | v1.5.0 |
| `cms-meeting-materials` | v1.10.7 |
| `openclaw-model-rankings` | v1.0.1 |

以上 6 个 Skill 均通过 `publish_skill.py` 手动独立发布到内部市场。**迁移到双轨发布后，这 6 个 Skill 的 SKILL.md 无需任何改动。**

### 1.3 目标

> **让玄关内部 TE 市场严格遵循 ClawHub 国际规范，实现"ClawHub 可上架即玄关可上架"的一键无缝双发布。**

1. 发布者只需维护一套 `SKILL.md`，一条命令同时发布到两个平台
2. 内部 TE 市场字段体系向 ClawHub 规范对齐
3. 内部专有字段通过 `metadata.xgjk` namespace 隔离扩展

---

## 第二部分：现有规范差异分析

### 2.1 元数据字段差异

| 字段语义 | ClawHub（SKILL.md） | 玄关内部 API | 差异与处理方式 |
|---------|-------------------|------------|--------------|
| 唯一标识 | `name` | `code` | 字段名不同，语义相同；映射规则见第三部分 |
| 显示名称 | `name` | `name` | ✅ 相同，直接映射 |
| 版本号 | `version`（semver 字符串，如 `1.2.0`） | `version`（整型） | 格式不同；映射规则见第三部分 |
| 描述 | `description` | `description` | ✅ 相同，直接映射 |
| 标签 | `metadata.openclaw.tags[]`（数组） | `label`（单字符串） | 多标签→逗号拼接；见第三部分 |
| 依赖声明 | `metadata.openclaw.requires` | 无 | 阶段1忽略并输出 WARNING；阶段2 TE 支持 |
| 安装钩子 | `metadata.openclaw.install` | 无 | 阶段1忽略并输出 WARNING；阶段2 TE 支持 |
| 内部专有字段 | 无 | `isInternal`、`corpId` 等 | 通过 `metadata.xgjk` namespace 扩展（见第三部分） |
| Hook 声明 | `hooks/` 子目录 `HOOK.md` | 无 | 阶段2规划 |

### 2.2 打包与传输差异

| 项目 | ClawHub | 玄关内部 |
|------|---------|---------|
| 传输方式 | CLI 直接上传目录 | 打包 ZIP → 上传七牛 → API 注册 |
| 忽略规则 | `.clawhubignore` | 需对齐（规范见第三部分） |
| 入口文件 | `SKILL.md`（根目录必须存在） | `SKILL.md`（已对齐） |

### 2.3 鉴权差异

| 项目 | ClawHub | 玄关内部 |
|------|---------|---------|
| 认证方式 | OAuth（`clawhub login`） | AppKey 换 xgToken（`XG_USER_TOKEN`） |
| Token 生命周期 | 长效 refresh token | 会话级，需定期换取 |
| 权限粒度 | 个人 / 组织 | 企业（corpId） |

---

## 第三部分：统一规范定义

> 本部分是双方共同遵守的核心规范，所有实现必须以此为准。

### 3.1 SKILL.md 作为唯一权威元数据源

**规则**：
- 所有 Skill 的元数据以 `SKILL.md` frontmatter 为唯一来源
- 发布者不需要维护任何额外的内部元数据文件
- 内部平台必须能够直接解析 ClawHub 格式的 SKILL.md frontmatter

**SKILL.md 标准结构**：

```yaml
---
name: my-skill                          # 唯一标识（同时作为 ClawHub slug 和内部 code）
version: 1.2.0                          # semver 格式（必须）
description: "Skill 的一句话描述"         # 描述（必须）
metadata:
  openclaw:                             # ClawHub / OpenClaw 标准字段
    requires:
      bins: [python3]
    tags: ["工作协同", "自动化"]
  xgjk:                                 # 玄关内部扩展字段（ClawHub 发布时完全忽略）
    isInternal: false                   # 是否为内部专属 Skill，默认 false
    corpId: ""                          # 企业 ID，留空使用默认企业
    label: "工作协同"                    # 内部分类标签（优先级高于 tags 映射）
---
```

### 3.2 字段映射规范

发布工具读取 SKILL.md 后，按以下规则映射到内部 API：

| SKILL.md 字段 | 内部 API 字段 | 映射规则 |
|--------------|-------------|---------|
| `name` | `code` | 直接映射（唯一标识） |
| `name` | `name` | 直接映射（显示名） |
| `version` | `version` | 见 §3.3 版本映射规范 |
| `description` | `description` | 直接映射 |
| `metadata.openclaw.tags[]` | `label` | 数组→逗号拼接字符串；若 `metadata.xgjk.label` 存在则优先使用 xgjk.label |
| `metadata.xgjk.isInternal` | `isInternal` | 直接映射，默认 `false` |
| `metadata.xgjk.corpId` | `corpId` | 直接映射，默认 `""` |

### 3.3 版本号映射规范（阶段1）

**背景**：内部 API 当前 `version` 字段为整型，ClawHub 使用 semver 字符串，需无歧义转换。

**映射公式**：
```
内部 version 整型 = major × 10000 + minor × 100 + patch
```

**示例**：

| semver | 内部整型 | 验证无歧义 |
|--------|---------|---------|
| `1.2.0` | `10200` | |
| `1.20.0` | `11200` | ≠ 10200 ✅ |
| `2.0.1` | `20001` | |
| `0.4.3` | `403` | |

**约束**：
- `minor` 和 `patch` 各段不得超过 `99`
- 若超出，发布工具必须报错退出，不得强行映射
- 错误提示：`[ERROR] version X.Y.Z 中 minor/patch 超出内部市场支持上限(99)，请联系 TE 团队升级 API 至 semver 字符串模式`

**阶段2目标**：内部 API `version` 字段升级为直接支持 semver 字符串，届时整型映射废弃，上述约束解除。

### 3.4 .clawhubignore 统一忽略规则

**规则**：内部打包工具与 ClawHub 共用 `.clawhubignore`，确保两个平台打包产物的**文件路径集合相同**（不要求字节级一致）。

**"内容一致"定义**：排除 `.clawhubignore` 中列出的条目后，ClawHub 上传的文件列表与内部 ZIP 包内的文件列表完全相同。

### 3.5 阶段1不支持字段的处理策略

以下字段在阶段1内部平台**不支持**，发布时**忽略但必须输出 WARNING**，不得静默：

| 字段 | WARNING 信息 |
|------|------------|
| `metadata.openclaw.requires` | `[WARN] requires 字段在内部市场暂不支持，已忽略。安装后依赖需手动处理，请联系 TE 团队升级支持。` |
| `metadata.openclaw.install` | `[WARN] install 字段在内部市场暂不支持，已忽略。安装钩子不会执行，请联系 TE 团队升级支持。` |
| `hooks/` 子目录 | `[WARN] hooks 子目录在内部市场暂不支持，已忽略。Hook 功能不可用，请联系 TE 团队升级支持。` |

---

## 第四部分：Agent Factory 侧实现规范

> **目标读者**：Agent Factory 工程师  
> **任务**：实现 `publish_all.py` 双发布适配器脚本（阶段1，不依赖 TE 团队，可立即启动）

### 4.1 publish_all.py 接口规范

**文件位置**：`05_products/create-xgjk-skill/scripts/skill-management/publish_all.py`

**命令行接口**：

```bash
# 一键双发（默认）
python3 publish_all.py <skill_dir>

# 仅发某一平台
python3 publish_all.py <skill_dir> --only clawhub
python3 publish_all.py <skill_dir> --only xgjk

# 预检模式（不实际发布，输出计划）
python3 publish_all.py <skill_dir> --dry-run

# 环境变量
XG_USER_TOKEN=xxx python3 publish_all.py <skill_dir>
```

**退出码规范**：

| 退出码 | 含义 |
|--------|------|
| `0` | 全部成功（或幂等：已是最新版本） |
| `1` | 部分成功（一个平台成功，一个失败） |
| `2` | 全部失败 |
| `3` | 预检失败（version 超限、SKILL.md 解析失败等），不执行任何发布 |

**重要**：任一平台失败时，**不回滚**已成功的平台（发布行为不可逆），记录不一致状态供人工处理。

### 4.2 adapter 接口规范（NFR-05 可扩展性）

工程师必须按以下接口实现两个 adapter，以支持未来接入第三方市场：

```python
class PublishAdapter:
    def get_current_version(self, skill_name: str) -> str | None:
        """查询该平台上 Skill 的当前版本，不存在返回 None"""
        ...

    def publish(self, skill_dir: str, meta: SkillMeta) -> PublishResult:
        """执行发布，返回结果"""
        ...

    def is_latest(self, skill_name: str, version: str) -> bool:
        """判断当前版本是否已是最新（幂等判断）"""
        ...

class SkillMeta:
    name: str          # Skill 唯一标识
    display_name: str  # 显示名（可与 name 不同，默认同 name）
    version: str       # semver 字符串（原始值）
    description: str
    label: str         # 映射后的标签字符串
    is_internal: bool  # 默认 False
    corp_id: str       # 默认 ""

class PublishResult:
    success: bool
    platform: str      # "clawhub" | "xgjk"
    skill_id: str      # 平台返回的 ID
    url: str           # 发布后的页面/下载链接
    error: str | None  # 失败时的错误信息
```

**两个必须实现的 adapter**：

- `ClawHubAdapter`：封装 `clawhub publish` CLI 调用
- `XgjkAdapter`：封装现有 `publish_skill.py`（保留不废弃），在其上加字段映射层

### 4.3 publish_all.py 核心逻辑伪代码

```python
def main(skill_dir, only=None, dry_run=False):
    # Step 1: 解析 SKILL.md
    meta = parse_skill_md(skill_dir)           # 解析 frontmatter，失败则 exit(3)
    validate_version(meta.version)             # 检查 minor/patch ≤ 99，失败则 exit(3)
    warn_unsupported_fields(skill_dir, meta)   # 输出 WARNING（requires/install/hooks）

    # Step 2: 预检（--dry-run）
    if dry_run:
        print_dry_run_plan(meta, skill_dir)    # 输出版本对比表 + 文件清单 diff
        exit(0)

    # Step 3: 执行发布
    adapters = get_adapters(only)              # 根据 --only 参数决定发布哪些平台
    results = []
    for adapter in adapters:
        if adapter.is_latest(meta.name, meta.version):
            print(f"[{adapter.platform}] 已是最新版本 {meta.version}，跳过")
            results.append(PublishResult(success=True, ...))
            continue
        result = adapter.publish(skill_dir, meta)
        results.append(result)

    # Step 4: 输出结果
    print_summary(results)                     # 输出双平台链接或错误信息
    exit(calc_exit_code(results))              # 0/1/2 根据结果决定
```

### 4.4 --dry-run 输出规范

```
=== Dry Run: my-skill ===

版本对比：
  平台          当前版本    待发布版本
  ClawHub       v1.2.0      v1.3.0
  玄关内部市场   v1.2.0      v1.3.0  ← 内部整型：10300

文件清单 Diff（ClawHub vs 内部 ZIP）：
  [相同] SKILL.md
  [相同] scripts/main.py
  [相同] requirements.txt
  差异：无

[WARN] requires 字段在内部市场暂不支持，已忽略。
```

### 4.5 安全要求（NFR-02）

- `XG_USER_TOKEN` **不得出现**在任何 stdout、stderr、日志文件、异常堆栈中
- HTTP 请求异常时**不得打印完整 URL**（含 token 的请求头必须脱敏，如 `access-token: ***`）
- Code review checklist 必须包含 token 泄露检查项

---

## 第五部分：TE 平台升级需求

> **目标读者**：玄关 TE 平台团队  
> **任务**：升级内部 Skill 市场 API，支持 ClawHub 规范字段（阶段2，需排期配合）

### 5.1 背景

当前内部 Skill 市场 API 与 ClawHub 规范存在以下不兼容，阻碍双轨发布的完整实现：

1. `version` 字段为整型，无法直接存储 semver 字符串
2. 缺少 `metadata` 扩展字段（无法存储 `xgjk` 扩展内容）
3. 缺少对 `requires`、`install`、`hooks` 的支持
4. 无法直接接收和解析 `SKILL.md` 原文

### 5.2 API 升级需求清单

**接口**：`im/skill/register` 和 `im/skill/update`

**字段变更（新增 / 修改）**：

```json
{
  "code": "my-skill",
  "name": "My Skill",
  "version": "1.2.0",           // 【修改】从整型升级为 semver 字符串（向后兼容整型输入）
  "description": "...",
  "label": "工作协同",
  "downloadUrl": "...",
  "isInternal": false,           // 已有，保留
  "corpId": "",                  // 【新增】企业 ID
  "requires": {                  // 【新增】依赖声明（来自 metadata.openclaw.requires）
    "bins": ["python3"],
    "python": ">=3.10"
  },
  "skillMdContent": "..."        // 【新增】原始 SKILL.md 内容（可选，供平台 UI 展示）
}
```

**优先级**：

| 字段 | 优先级 | 说明 |
|------|--------|------|
| `version` 支持 semver 字符串 | **P0** | 阶段1整型映射的根本问题，优先解决 |
| `corpId` 字段 | P1 | 支持多企业场景 |
| `requires` 字段 | P1 | 支持依赖声明展示 |
| `skillMdContent` 字段 | P2 | 供平台 UI 展示用，可后做 |

### 5.3 验收要求

- [ ] `version` 字段接受 semver 字符串（`"1.2.0"`），同时保持对整型的向后兼容
- [ ] 重复注册同版本 Skill 不报错，返回"已存在"标识
- [ ] API 返回的版本号与输入格式一致（输入 semver 返回 semver）

---

## 第六部分：三阶段落地路线图

```
阶段1（立即可启动，Agent Factory 自行完成）
─────────────────────────────────────────
目标：实现 publish_all.py，完成双发布自动化
工作：
  ① 实现 ClawHubAdapter（封装 clawhub publish CLI）
  ② 实现 XgjkAdapter（封装 publish_skill.py + 字段映射）
  ③ 实现 publish_all.py 主流程（含 --dry-run、退出码、WARNING）
  ④ 对 6 个现有 Skill 执行 --dry-run 回归验证
依赖：无外部依赖
约束：版本号各段 ≤ 99（整型映射上限）

阶段2（需 TE 平台团队配合排期）
─────────────────────────────────────────
目标：内部 API 升级，消除整型映射约束，支持完整规范
工作（TE 团队）：
  ① version 字段升级为 semver 字符串
  ② 新增 corpId、requires、skillMdContent 字段
  ③ install/hooks 支持（可选，视优先级）
工作（Agent Factory）：
  ① publish_all.py 升级：移除整型映射，直接传 semver
  ② 验证 6 个 Skill 在升级后的 API 下正常发布

阶段3（长期目标，不在本方案范围内）
─────────────────────────────────────────
目标：ClawHub CLI 原生支持多目标发布
方式：向 ClawHub 官方提议 --also-publish-to 插件扩展
```

---

## 第七部分：验收检查清单

> 工程师实现完成后，按以下清单逐项验收。

### 7.1 功能验收

- [ ] **G1** 双发布速度：包 ≤ 10MB、带宽 ≥ 10Mbps 环境下，处理耗时（排除网络传输）≤ 30 秒
- [ ] **G2** 双平台可搜索：发布后 ≤ 5 分钟，通过 Skill name 精确搜索在两个平台均可返回结果
- [ ] **G3** 幂等性：重复运行 `publish_all.py`（相同版本）退出码为 0，输出"已是最新版本，跳过发布"
- [ ] **G4** 向后兼容回归：对现有 6 个 Skill 执行 `--dry-run`，全部输出 OK，无 ERROR（WARNING 允许）
- [ ] **G5** xgjk 字段隔离：含 `metadata.xgjk` 的 Skill 发布到 ClawHub 后，ClawHub API 响应中不含 xgjk 字段
- [ ] **G6** 版本映射无歧义：`1.2.0`、`1.20.0`、`2.0.1` 三个版本映射整型值两两不同
- [ ] **G7** WARNING 输出：含 `metadata.openclaw.install` 或 `requires` 的 Skill 发布内部市场时，stdout 出现 `[WARN]`

### 7.2 安全验收

- [ ] **S1** 执行发布后，grep stdout/stderr 不含 `XG_USER_TOKEN` 的值
- [ ] **S2** 故意传入错误 token 触发 HTTP 错误，确认错误信息中无完整 URL 含 token 内容

### 7.3 可扩展性验收

- [ ] **E1** 新增一个 mock adapter（模拟第三方平台），不修改 `publish_all.py` 主流程即可接入

---

## 附录：依赖与风险

### 外部依赖

| 依赖方 | 依赖内容 | 影响阶段 | 当前状态 |
|--------|---------|---------|---------|
| 玄关 TE 平台团队 | API 升级（semver、metadata、SKILL.md 解析） | 阶段2 | **待 TE 团队确认排期** |
| ClawHub 官方 | `--also-publish-to` 插件 | 阶段3 | 长期规划 |

### 风险识别

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 阶段2 TE 延迟，整型映射长期使用 | 中 | 中 | 约定版本号各段 ≤ 99；超出时先协调 TE 升级 |
| ClawHub CLI 版本变更导致 adapter 失效 | 低 | 高 | adapter 封装隔离，锁定 clawhub 版本 |
| 七牛上传超时 | 中 | 低 | 自动重试 2 次，60 秒超时；ClawHub 不受影响 |
| 内部同名 Skill 冲突（他人发布的同名 Skill） | 低 | 高 | 发布前查询版本；内部市场单企业场景无多租户冲突风险，可直接走更新流程 |

---

*本方案由 Agent Factory 起草，版本 v1.0，2026-03-31。*  
*阶段1实现由 Agent Factory 工程师负责；阶段2请 TE 平台团队评估排期。*
