---
name: kb-graph
version: "0.3.2"
skillcode: kb-graph
github: https://github.com/evan-zhang/agent-factory
description: ⚠️ DEPRECATED - 请迁移到 Link Archivist v2.0.0。本 Skill 已于 2026-06-19 标记为废弃，将在 2026-12-19 删除。
---

# KB Graph ⚠️ DEPRECATED

> **重要提示**：本 Skill 已于 **2026-06-19** 标记为 **deprecated**（废弃）。
>
> 请迁移到 **Link Archivist v2.0.0**，它已内置知识库索引功能：
> ```bash
> cd ~/.openclaw/skills/link-archivist
> git pull
> python3 scripts/init_config.py
> ```
>
> 本 Skill 将在 **2026-12-19**（6 个月后）从 GitHub 删除。
>
> 迁移文档：[Link Archivist references/migration-from-kb-graph.md](../../2604131/link-archivist/references/migration-from-kb-graph.md)

## 兼容性说明

KB Graph v0.3.2 仅作为 deprecation release，**不删除任何代码**。

- ✅ 现有配置文件仍可用（`~/.openclaw/kb-graph-config.json`）
- ✅ 索引文件格式不变（`.kb-workdir/`）
- ✅ 命令接口保持兼容（虽然部分命令未实现）
- ❌ 不再添加新功能
- ❌ 不再修复 bug（除非严重安全问题）

## 迁移步骤

1. 安装 Link Archivist v2.0.0
2. 运行 `python3 scripts/init_config.py` 自动合并配置
3. 验证索引：`python3 scripts/kb_query.py status --dir <archive_dir>`
4. 卸载 KB Graph Skill（可选）

详细迁移指南见：[Link Archivist Migration Guide](../../2604131/link-archivist/references/migration-from-kb-graph.md)

## 原有功能（仅作参考）

### 触发场景（已废弃）

- ✅ 支持使用：请改用 Link Archivist 的触发场景
- ❌ 不再推荐：本 Skill 的触发场景

### 命令接口（部分未实现）

```bash
# 查询（支持）
python3 scripts/kb_graph.py query "关键词" --dir <归档目录> --mode keyword

# 状态（支持）
python3 scripts/kb_graph.py stats --dir <归档目录>

# 以下命令未实现，请迁移到 Link Archivist：
# python3 scripts/kb_graph.py build <归档目录>
# python3 scripts/kb_graph.py update-single <文件> --dir <归档目录>
# python3 scripts/kb_graph.py update <归档目录>
# python3 scripts/kb_graph.py lint <归档目录>
```

### 边界（原设计）

- ✅ 只读操作，不修改原始归档文件
- ✅ 查询依赖已构建的索引（.kb-workdir/entries.json）
- ✅ Link Archivist 归档新文件时会自动增量更新索引（v1.12.1+）

## 版本历史

- **v0.3.2** (2026-06-19): Deprecation release，引导用户迁移
- **v0.3.1** (2026-06-15): 独立版本，部分命令未实现
- **v0.3.0** (2026-06-10): 初始版本

## 问题反馈

迁移过程中遇到问题，请提交 Issue：

**地址**：https://github.com/evan-zhang/agent-factory/issues/new

**标题格式**：`[MIGRATION] link-archivist: 简短描述`

**建议包含**：
1. KB Graph 旧配置（去除敏感信息）
2. Link Archivist 新配置
3. 迁移过程中的错误信息
