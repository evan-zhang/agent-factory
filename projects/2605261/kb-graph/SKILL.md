---
name: kb-graph
version: "0.1.0"
skillcode: kb-graph
github: https://github.com/evan-zhang/agent-factory
description: 为指定目录下的 Markdown 文件构建知识库图谱，支持多目录监控、LLM 语义编译、Leiden 社区发现和双引擎查询。
---

# KB Graph

为 Markdown 文件构建知识库图谱。增量索引、LLM 语义编译、社区发现、关键词查询。

## 五层架构

```
采集层 → 文件发现、SHA256 变更检测
编译层 → LLM 语义编译（摘要/实体/标签）
图谱层 → 节点/边构建、Leiden 社区发现
查询层 → 关键词搜索（title/summary/tags/entities）
维护层 → Lint 矛盾检测、孤儿文件检查
```

## 快速开始

```bash
# 全量构建
python3 scripts/kb_graph.py build /path/to/dir

# 查询
python3 scripts/kb_graph.py query "关键词" --dir /path/to/dir

# 状态
python3 scripts/kb_graph.py status /path/to/dir

# Lint
python3 scripts/kb_graph.py lint /path/to/dir
```

测试模式（跳过 LLM）：`python3 scripts/kb_graph.py build /path/to/dir --test-mode`

## 核心产出

- `.kb-index.md` — 目录索引（YAML frontmatter 格式）
- `.kb-workdir/entries.json` — 结构化条目（标题/摘要/实体/标签/置信度）
- `.kb-workdir/kb_cache.json` — SHA256 缓存（增量更新依据）

## 配置与授权

运行 `python3 scripts/init_config.py` 初始化。配置文件：`~/.openclaw/kb-graph-config.json`

必填：`watch_dirs`（要索引的 Markdown 目录列表）、`llm_provider` 和 `model`。

需要至少一个 LLM API Key 环境变量：`MINIMAX_API_KEY`、`ZHIPU_API_KEY` 或 `DEEPSEEK_API_KEY`。

无需配置即可用：`ingest.py --scan`（扫描）、`build_graph.py --dir`（图谱构建）、`validate_index.py`（索引验证）。

详细配置说明和完整命令参考见 `references/usage.md`。

## 边界

- 不修改原始文件（只读索引）
- 零数据库（所有数据存 Markdown/JSON）
- 仅支持 .md 文件
- Schema 首次运行自动生成

## 问题反馈

- Issue：https://github.com/evan-zhang/agent-factory/issues
- 标题格式：`[kb-graph] 问题描述`
- 建议包含：重现步骤、环境信息、日志输出
