---
name: kb-graph
version: "0.3.0"
skillcode: kb-graph
github: https://github.com/evan-zhang/agent-factory
description: 为指定目录下的 Markdown 文件构建知识库图谱，支持多目录监控、LLM 语义编译、Leiden 社区发现和双引擎查询。触发词：知识库、kb、图谱、索引、语义搜索
---

# KB Graph

为 Markdown 文件构建知识库图谱。增量索引、LLM 语义编译、社区发现、关键词查询、语义搜索、混合查询。

## 五层架构

```
采集层 → 文件发现、SHA256 变更检测
编译层 → LLM 语义编译（摘要/实体/标签/关系/置信度）
图谱层 → 节点/边构建（实体/标签/引用/主题）、Leiden 社区发现
查询层 → 关键词搜索 / 语义向量搜索 / 混合查询
维护层 → Lint 矛盾检测、孤儿文件检查
```

## 快速开始

```bash
# 全量构建
python3 scripts/kb_graph.py build /path/to/dir

# 关键词查询
python3 scripts/kb_graph.py query "关键词" --dir /path/to/dir --mode keyword

# 语义查询（需先构建向量索引）
python3 scripts/kb_graph.py build-embeddings /path/to/dir
python3 scripts/kb_graph.py query "查询内容" --dir /path/to/dir --mode semantic

# 混合查询
python3 scripts/kb_graph.py query "查询内容" --dir /path/to/dir --mode hybrid

# 状态
python3 scripts/kb_graph.py status /path/to/dir

# Lint
python3 scripts/kb_graph.py lint /path/to/dir
```

测试模式（跳过 LLM）：`python3 scripts/kb_graph.py build /path/to/dir --test-mode`

## 核心产出

- `.kb-index.md` — 目录索引（YAML frontmatter 格式）
- `.kb-workdir/entries.json` — 结构化条目（标题/摘要/实体/标签/关系/置信度/置信度分数）
- `.kb-workdir/embeddings.json` — 语义向量索引（用于语义搜索）
- `.kb-workdir/kb_cache.json` — SHA256 缓存（增量更新依据）

## 配置与授权

运行 `python3 scripts/init_config.py` 初始化。配置文件：`~/.openclaw/kb-graph-config.json`

必填：`watch_dirs`（要索引的 Markdown 目录列表）、`llm_provider` 和 `model`。

需要至少一个 LLM API Key 环境变量：`MINIMAX_API_KEY`、`ZHIPU_API_KEY` 或 `DEEPSEEK_API_KEY`。

语义搜索需要：`OPENAI_API_KEY` 环境变量。

无需配置即可用：`ingest.py --scan`（扫描）、`build_graph.py --dir`（图谱构建）、`validate_index.py`（索引验证）。

详细配置说明和完整命令参考见 `references/usage.md`。

## Agent 调用接口

标准 OpenClaw Skill，可通过以下方式调用：

```bash
# 直接调用
python3 scripts/kb_graph.py query "AI架构设计" --dir /path/to/dir --mode hybrid

# 代理调用（在其他 Agent 中）
import subprocess
result = subprocess.run(
    ["python3", "scripts/kb_graph.py", "query", "AI架构设计", "--dir", "/path/to/dir", "--mode", "hybrid"],
    capture_output=True, text=True
)
```

## 边界

- 不修改原始文件（只读索引）
- 零数据库（所有数据存 Markdown/JSON）
- 仅支持 .md 文件
- Schema 首次运行自动生成

## 问题反馈

- Issue：https://github.com/evan-zhang/agent-factory/issues
- 标题格式：`[kb-graph] 问题描述`
- 建议包含：重现步骤、环境信息、日志输出
