---
name: kb-graph
version: "0.3.1"
skillcode: kb-graph
github: https://github.com/evan-zhang/agent-factory
description: 查询知识库图谱、搜索本地索引文件、查找归档报告中的相关内容。触发词：查知识库、搜索引、知识图谱、kb查询、找归档报告、知识库搜索
---

# KB Graph

知识库图谱查询 Skill。在本地 Markdown 归档目录中搜索相关内容，返回匹配文件的标题、摘要、实体和标签。

## 何时触发

当用户的请求涉及以下场景时触发：
- 查询/搜索知识库或归档内容
- 查找之前归档的报告或调研
- 询问某个主题在知识库中的相关信息
- 需要基于已有知识库内容回答问题

## 执行步骤

1. 读取配置获取归档目录：`cat ~/.openclaw/kb-graph-config.json`，取 `watch_dirs[0]`
2. 执行查询：
```
python3 ~/.openclaw/skills/kb-graph/scripts/kb_graph.py query "用户查询内容" --dir <归档目录> --mode keyword
```
3. 解析 JSON 结果，提取 `results` 数组中的条目
4. 将结果以可读格式呈现给用户

## 查询模式

默认使用 keyword 模式。仅在用户明确要求语义搜索时使用 hybrid 模式（需要 OPENAI_API_KEY）。

## 结果格式

将查询结果整理为：
- 文件标题和路径
- 相关度分数
- 摘要（如有）
- 关键实体和标签

只展示前 5 条最相关的结果，避免信息过载。如果用户需要更多，再展示后续结果。

## 全量重建

仅在用户明确要求"重建索引"或"全量更新"时执行：
```
python3 ~/.openclaw/skills/kb-graph/scripts/kb_graph.py build <归档目录>
```
此操作耗时较长（351个文件约20分钟），执行前必须告知用户预计时间。

## 边界

- 只读操作，不修改原始归档文件
- 查询依赖已构建的索引（.kb-workdir/entries.json）
- Link Archivist 归档新文件时会自动增量更新索引，通常无需手动重建
