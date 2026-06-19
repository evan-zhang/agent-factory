# Migration from KB Graph

本文档指导从 KB Graph v0.3.1 迁移到 Link Archivist v2.0.0。

## 迁移概览

- **破坏性变更**：是（触发场景变化、配置文件结构变化）
- **数据兼容性**：完全兼容（索引文件格式不变）
- **迁移时间**：<5 分钟
- **回滚路径**：保留 6 个月（2026-12-19 前）

## 迁移步骤

### 1. 安装 Link Archivist v2.0.0

```bash
cd ~/.openclaw/skills/link-archivist
git pull
# 或重新安装
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/2604131/link-archivist
cp -r projects/2604131/link-archivist ~/.openclaw/skills/
```

### 2. 配置合并（自动）

运行 `scripts/init_config.py` 自动检测并合并 KB Graph 配置：

```bash
cd ~/.openclaw/skills/link-archivist
python3 scripts/init_config.py
```

**自动行为：**
- 检测 `~/.openclaw/kb-graph-config.json`
- 如果 `watch_dirs[0]` == `archive_dir`：
  - 合并配置到 `link-archivist-config.json`
  - 将旧配置备份为 `kb-graph-config.json.bak`（不删除）
- 如果 `watch_dirs[0]` != `archive_dir`：
  - 不合并，提示用户手动决定

### 3. 验证索引数据

索引文件格式不变，验证数据完整性：

```bash
python3 scripts/kb_query.py status --dir <archive_dir>
```

应该返回：
```json
{
  "ok": true,
  "status": "ready",
  "total_entries": 462,
  ...
}
```

### 4. 增量更新（可选）

如果归档目录有新增文件，运行增量更新：

```bash
python3 scripts/kb_rebuild.py --dir <archive_dir> --incremental
```

## 新触发场景

### 之前（KB Graph）

```bash
# KB Graph 查询
python3 ~/.openclaw/skills/kb-graph/scripts/kb_graph.py query "关键词" \
  --dir <archive_dir> --mode keyword

# KB Graph 构建不存在（命令未实现）
```

### 现在（Link Archivist）

```bash
# 查询知识库
python3 ~/.openclaw/skills/link-archivist/scripts/kb_query.py "关键词" \
  --dir <archive_dir> --mode keyword

# 重建索引
python3 ~/.openclaw/skills/link-archivist/scripts/kb_rebuild.py \
  --dir <archive_dir>

# 增量更新
python3 ~/.openclaw/skills/link-archivist/scripts/kb_rebuild.py \
  --dir <archive_dir> --incremental

# 索引巡检
python3 ~/.openclaw/skills/link-archivist/scripts/kb_lint.py \
  --dir <archive_dir>
```

## 配置变更

### 旧配置（KB Graph）

`~/.openclaw/kb-graph-config.json`：
```json
{
  "watch_dirs": ["/path/to/knowledge"],
  "query_mode": "keyword",
  "auto_update": true,
  "embeddings_enabled": false
}
```

### 新配置（Link Archivist）

`~/.openclaw/link-archivist-config.json`：
```json
{
  "archive_dir": "/path/to/knowledge",
  "xgjk_app_key": "...",
  "tavily_api_key": "...",
  "video_archive_dir": "/path/to/videos",
  "kb_index": {
    "enabled": true,
    "query_mode": "keyword",
    "auto_update": true,
    "embeddings_enabled": false
  }
}
```

## 数据兼容性

### 索引文件（不变）

- `.kb-workdir/entries.json` - 格式不变，新字段可选
- `.kb-workdir/entities-registry.json` - 格式不变
- `.kb-workdir/graph-data.json` - 格式不变
- `.kb-workdir/kb_cache.json` - 格式不变

### Entry 数据结构（向后兼容）

**旧 entry（v0.3.1）：**
```json
{
  "path": "2026/06/K-260619-001.md",
  "title": "...",
  "summary": "...",
  "entities": [...],
  "tags": [...],
  "sha256": "..."
}
```

**新 entry（v2.0.0）：**
```json
{
  "path": "2026/06/K-260619-001.md",
  "title": "...",
  "summary": "...",
  "entities": [...],
  "tags": [...],
  "confidence": "high",
  "source_sha256": "...",
  "compiled_at": "2026-06-19T17:30:00",
  "compile_method": "frontmatter",
  "provider": "phase3_llm"
}
```

**兼容性：**
- 旧 entry 缺失新字段时，`update_single` 自动填充默认值
- `compile_method` 缺失时默认为 `"legacy"`

## 回滚路径

### 回滚到 KB Graph v0.3.1

```bash
cd ~/.openclaw/skills/link-archivist
git checkout v1.12.1

# 恢复旧配置（如果需要）
cp ~/.openclaw/kb-graph-config.json.bak ~/.openclaw/kb-graph-config.json

# 重启 gateway
openclaw gateway restart
```

### 回滚不影响数据

- 所有索引文件在 `.kb-workdir/` 中保留
- 回滚后 v0.3.1 仍可读取索引
- 新增的 entry 兼容旧格式

## 常见问题

### Q: 旧 KB Graph 配置会被删除吗？

A: 不会。如果目录一致，会备份为 `.bak`；如果目录不一致，不修改旧配置。

### Q: 我需要重新构建索引吗？

A: 不需要。索引文件格式兼容，除非你想为历史归档补充 frontmatter 字段。

### Q: 如何验证迁移成功？

A: 运行以下命令：
```bash
python3 scripts/kb_query.py status --dir <archive_dir>
python3 scripts/kb_lint.py --dir <archive_dir>
```

### Q: 迁移后 KB Graph Skill 还能用吗？

A: KB Graph v0.3.2 仍可独立运行，但已标记 deprecated，建议迁移到 Link Archivist。

### Q: 我可以同时安装两个 Skill 吗？

A: 技术上可以，但推荐只使用 Link Archivist，避免配置冲突。

## 贡献者

- Orchestrator: 实现合并逻辑
- Factory Reviewer: 审核迁移方案

## 版本历史

- v2.0.0 (2026-06-19): KB Graph 合并，内置知识库查询
- v1.12.1 (2026-06-18): 支持自动触发 KB Graph 索引（但命令不存在）
- v0.3.1 (2026-06-15): KB Graph 独立版本
