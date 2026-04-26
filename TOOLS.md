# TOOLS.md - Local Notes

## 发布规范

**发布 = push 到 GitHub master。**

- 何时发布：Evan 说「发布」时，才算正式版本
- 安装方式：只取单个 skill 目录，不 clone 全量仓库
- **推荐方式（git sparse-checkout）**：
  ```bash
  git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
  cd agent-factory
  git sparse-checkout set projects/{id}/{skill-name}
  ```
- **备选方式（svn export）**：
  ```bash
  svn checkout https://github.com/evan-zhang/agent-factory/trunk/projects/{id}/{skill-name}
  ```
- Skill 目录：`projects/{id}/{skill-name}/`
- 不打包、不占 GitHub 空间
- ClawHub 等第三方平台由 Evan 自行决定

## 版本号管理

版本号在以下三处同步更新（发版时必须全部修改）：

| 位置 | 文件路径 | 内容 |
|------|---------|------|
| 项目级 | `projects/{id}/VERSION` | `1.2.3`（纯文本） |
| Skill 级 | `projects/{id}/{skill}/SKILL.md` frontmatter | `version: "1.2.3"` |
| Skill 级 | `projects/{id}/{skill}/version.json` | `{"skillcode":"...","version":"1.2.3"}` |

版本号格式：SemVer（主版本.次版本.修订号），例如 `1.4.0`。

## 发版流程

### Step 1：确定版本号
- 从上一个版本递增（修订号 +1 适用于 bugfix，，次版本 +1 适用于新功能，主版本 +1 适用于破坏性变更）
- 版本号同时更新到以上三处

### Step 2：提交 Git
```bash
git add projects/{id}/{skill}/
git commit -m "release: {skill} v{x.y.z}"
git push origin master
```

### Step 3：发测试通知
按下方「测试通知模板」填写，发送到对应 Issue 或通知渠道。

### Step 4（如需发布到 ClawHub）
```bash
clawhub publish ./projects/{id}/{skill} \
  --slug {skill-slug} \
  --name "{Skill 名称}" \
  --version {x.y.z} \
  --changelog "本次更新：1. xxx 2. xxx"
```

> 注意：`clawhub install` 默认安装到 `{workdir}/skills/{slug}`，需手动同步到正确路径。

## 测试通知模板

每次 Skill 更新需要提交测试时，按以下模板填写：

```
🔬 {Skill 名称} v{x.y.z} 测试包

📦 安装命令：
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/{id}/{skill-name}

Skill 目录：agent-factory/projects/{id}/{skill-name}/

本次更新内容：
1. {更新点1}
2. {更新点2}
3. ...

重点测试方向：
- {测试点1}
- {测试点2}
```

## 外部平台文档（API 唯一来源）

| 平台 | GitHub 地址 | 覆盖业务模块 |
|------|-------------|-------------|
| 玄关开放平台 | https://github.com/xgjk/dev-guide/ | CWork(工作协同) / AI慧记 / BP / 所有 CMS 业务模块 |

使用方式：用 curl 直接获取官方文档。

## Skill 规范（工厂标准）

所有 Skill 的 SKILL.md 必须包含以下两个标准节：

### 「配置与授权」节

说明安装后如何配置，包含：
- 必填配置项和获取方式
- 可选配置项和获取方式
- 无需配置即可用的能力
- 配置文件位置

### 「问题反馈」节

说明遇到问题如何反馈，包含：
- Issue 地址
- 标题格式
- 建议包含的信息（重现步骤、环境信息、日志）
