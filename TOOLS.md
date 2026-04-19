# TOOLS.md - Local Notes

## Skill 版本与发布规范

### 版本号规则

- **测试包**：未正式发布前，版本号不变，用时间戳区分迭代
  - 命名：`v{版本号}-{YYYYMMDD}-{HHMM}.zip`
  - 示例：`v1.3.0-20260413-2144.zip`
  - 只在用户明确说「发布新版本」时才升版本号
- **正式发布**：由 Evan 手动决定版本号和发布时机

### 发布流程（用户说「发布新版本」时执行）

1. 更新 `projects/{id}/VERSION` 文件
2. 从 skill 源码目录打包到 releases/：
```bash
cd projects/{id}/{skill-name}
zip -r ../releases/v{版本号}-$(date +%Y%m%d-%H%M).zip . \
  -x '*.pyc' -x '__pycache__/*' -x '*.DS_Store' -x 'builds/*' -x 'releases/*'
```
3. git commit + push

### 测试包构建

```bash
cd projects/{id}/{skill-name}
zip -r ../builds/v{版本号}-$(date +%Y%m%d-%H%M).zip . \
  -x '*.pyc' -x '__pycache__/*' -x '*.DS_Store' -x 'builds/*' -x 'releases/*'
```

---

### 外部平台文档（API 唯一来源）

| 平台 | GitHub 地址 | 覆盖业务模块 |
|------|-------------|-------------|
| 玄关开放平台 | https://github.com/xgjk/dev-guide/ | CWork(工作协同) / AI慧记 / BP / 所有 CMS 业务模块 |

使用方式：用 curl 直接获取官方文档。
