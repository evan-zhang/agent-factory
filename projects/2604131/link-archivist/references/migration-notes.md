# Migration Notes

## v10 → v11 迁移清单

### 1. 配置文件变更
- **v10**：无配置文件
- **v11**：新增 `init_config.py`，配置路径根据环境自动选择

### 2. 脚本变更
- **删除**：`update_learning_index.py`（索引交给 LLM Wiki）
- **新增**：`init_config.py`（多环境配置检测）
- **增强**：`archive_report.py`（自动编号、建目录、写 YAML 头）

### 3. 路径清理
检查所有文件中的平台特定路径：
- `~/.openclaw/` → 改为环境自适应
- `/Users/evan/` → 改为 `/path/to/`
- `~/Library/Mobile Documents/...` → 删除 Obsidian 特定引用

### 4. 工具映射
SOP 中的 OpenClaw 特定工具需要映射：
- `web_fetch()` → `curl -sL {url}`
- `exec()` → 终端执行
- `message()` → 无需对应（Skill 不负责发送）

### 5. 示例更新
- **v10**：3 个简陋示例
- **v11**：4 个完整示例（新增 YouTube 转录、文件输入）

### 6. 职责边界
v11 明确了 Skill **不负责**：
- 发送到哪个渠道
- 文件解析（PDF/Word/PPT）
- 知识索引管理
- 云端同步

### 验证清单
- [ ] 配置文件路径已改为环境自适应
- [ ] SKILL.md 初始化章节完整
- [ ] archive_report.py 支持自动编号
- [ ] 工具映射表已添加
- [ ] 所有 macOS 特定路径已清理
