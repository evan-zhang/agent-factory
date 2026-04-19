# TOOLS.md - Local Notes

### 发布规范（简化版）

**发布 = push 到 GitHub master。**

- 何时发布：Evan 说「发布」时，才算正式版本
- 版本号：发布时更新 `projects/{id}/VERSION`
- 发布方式：push master 到 GitHub，用户从 master 下载源码
- 不再打包 zip，不占 GitHub 空间
- ClawHub 等第三方平台由 Evan 自行决定是否发布

### 测试规范

- 不需要打包
- 不需要 GitHub Release
- 测试 agent 直接 clone master：`git clone --depth 1 https://github.com/evan-zhang/agent-factory.git`
- Skill 目录：`projects/{id}/{skill-name}/`

---

### 外部平台文档（API 唯一来源）

| 平台 | GitHub 地址 | 覆盖业务模块 |
|------|-------------|-------------|
| 玄关开放平台 | https://github.com/xgjk/dev-guide/ | CWork(工作协同) / AI慧记 / BP / 所有 CMS 业务模块 |

使用方式：用 curl 直接获取官方文档。
