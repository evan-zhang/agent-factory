---
name: link-archivist
description: Link Archivist v10. 收到链接后先判断 short/full/ask，再抓取、调研、归档、发送。支持本地归档（Obsidian+Git）和玄关知识库入库。
---

# Link Archivist v10

## 规则
- 先判断内容类型
- short 直接简答
- full 做完整调研
- ask 先问 Evan
- 不把执行细节塞进正文，执行交给 scripts/

## 工作流
1. 收到链接
2. 抓基础信息
3. 决定模式（`scripts/decide_mode.py`）
4. 执行 short/full/ask
5. 归档和更新索引
6. 可选：入库到玄关知识库（`scripts/xgjk/`）

## 归档通道

### 本地归档（默认）
- Obsidian + Git
- 详见 `references/SOP-诸葛工作流.md`

### 玄关知识库入库（可选）
- 上传到玄关个人知识库
- API 详见 `references/xgjk-knowledge-api.md`
- 编号规则详见 `references/xgjk-archive-template.md`
- 脚本：`scripts/xgjk/upload.sh`、`scripts/xgjk/search.sh`
- Key 管理：首次绑定时存入 `~/.openclaw/knowledge-hub-key`

## 入口脚本
- `scripts/decide_mode.py`
- `scripts/archive_report.py`
- `scripts/update_learning_index.py`

## 资源
- `references/report-template.md`
- `references/decision-rules.md`
- `references/migration-notes.md`
- `references/xgjk-knowledge-api.md`
- `references/xgjk-archive-template.md`
- `examples/`

## 备份
- v9 在 `backups/link-archivist-v9-2026-04-12/`
