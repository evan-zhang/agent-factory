# SKILL.md 标准模板 v1.0

> 每个 Skill 根目录必须有 `SKILL.md`。这是 Agent 加载 Skill 时读取的唯一入口文件。

---

## A. frontmatter（必须填写，Agent 平台依赖此识别）

```yaml
---
name: {skill-name}
description: "{1-3 句描述，3-5 个触发词，覆盖口语化表达}"
version: "1.0.0"
homepage: https://github.com/evan-zhang/agent-factory/tree/master/projects/{project-id}/{skill-name}/
issues: https://github.com/evan-zhang/agent-factory/issues/new?labels={skill-name}
---

> ⚠️ **由 Agent Factory 维护**
> 所属项目编号：`{project-id}`（如 2604191）
> 工厂主页：https://github.com/evan-zhang/agent-factory
> 提 Issue 前请阅读：https://github.com/evan-zhang/agent-factory/blob/master/CONTRIBUTING.md
```

---

## B. 正文结构（≤ 80 行）

### 触发判断
（描述什么情况下这个 Skill 应该被激活）

### 初始化（如需要配置）
（首次使用时的配置步骤）

### 核心流程
（1. … 2. … 3. …）

### 失败处理
（常见错误的处理方式）

### 示例
```
（1-2 个简洁示例）
```

---

## C. 填写说明

### frontmatter 必填字段

| 字段 | 说明 |
|---|---|
| `name` | 唯一标识，小写字母和连字符 |
| `description` | 3-5 个触发词，覆盖口语化表达，动词开头 |
| `version` | SemVer，如 1.0.0 |
| `homepage` | GitHub 上该 Skill 目录的链接 |
| `issues` | GitHub Issues 页面链接，带 skill-name 标签 |

### description 写法

❌ 避免：
```
"Use when the user wants to search for employees."
```

✅ 推荐：
```
"搜索员工。触发词：找人、查员工、搜一下谁、查查这个名字"
```

### 行数控制

- frontmatter description：~100 词以内
- SKILL.md 正文：≤ 80 行
- 细节推入 `references/` 目录

### references/ 规范

- ≤ 3 个文件
- 文件名：`maintenance.md`（维护信息）必须包含：
  - GitHub 仓库地址
  - 提 Issue 入口
  - 版本更新日志

---

## D. maintenance.md 模板

```markdown
# {skill-name} 维护信息

## 版本
当前版本：v1.0.0

## 仓库
https://github.com/evan-zhang/agent-factory/tree/master/projects/{project-id}/{skill-name}/

## 反馈问题
https://github.com/evan-zhang/agent-factory/issues/new?choose=1

提 Issue 时请：
1. 选择 "Bug Report" 或 "Feature Request"
2. 填写所属 Skill：{skill-name}
3. 填写项目编号：{project-id}

## 更新日志
- v1.0.0：（日期）初始版本
```
