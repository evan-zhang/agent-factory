# TOOLS.md - Local Notes

## 发布规范

**发布 = push 到 GitHub master。**

- 何时发布：Evan 说「发布」时，才算正式版本
- 版本号：发布时更新 `projects/{id}/VERSION`
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

## 测试通知规范

每次 Skill 更新需要提交测试时，按以下模板在 Issue 或通知消息中填写：

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
