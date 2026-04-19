# TOOLS.md - Local Notes

## Skill 版本与发布规范

### 版本号规则

- **测试包**：未正式发布前，版本号不变，用时间戳区分迭代
  - 命名：`v{版本号}-{YYYYMMDD}-{HHMM}.zip`
  - 示例：`v1.3.0-20260413-2144.zip`
  - 只在用户明确说「发布新版本」时才升版本号
- **正式发布**：由 Evan 手动决定版本号和发布时机

### 测试包构建

**项目目录结构**：
```
projects/{YYMMDDN}/
├── builds/          ← 测试包放这里
├── releases/        ← 正式发布包
└── {skill-name}/    ← skill 源码目录
    └── SKILL.md
```

**打包命令**（从 skill 源码目录执行，打到项目根的 builds/）：
```bash
cd {skill-name}
zip -r ../builds/v{版本号}-$(date +%Y%m%d-%H%M).zip . \
  -x '*.pyc' \
  -x '__pycache__/*' \
  -x '*.DS_Store' \
  -x 'backups/*' \
  -x 'builds/*'
```

### 发布流程（仅用户明确要求时执行）

1. **GitHub**：变更 commit 并 push
2. **ClawHub**：由 Evan 手动执行 `clawhub publish`
3. **发布说明**：写清楚更新内容、安装命令、反馈渠道

### Skill 发布前验证清单

发布前必须在干净目录执行 `clawhub install <skill>` 验证：

1. 安装后列出所有文件
2. 对比 SKILL.md 中提到的每个文件是否存在
3. 对比 references/ 目录文件是否完整
4. 检查是否有遗漏的占位符或空文件

---

### 外部平台文档（API 唯一来源）

| 平台 | GitHub 地址 | 覆盖业务模块 |
|------|-------------|-------------|
| 玄关开放平台 | https://github.com/xgjk/dev-guide/ | CWork(工作协同) / AI慧记 / BP / 所有 CMS 业务模块 |

使用方式：用 curl 直接获取官方文档。
