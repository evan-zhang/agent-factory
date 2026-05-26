---
name: kb-graph
version: "0.1.0"
skillcode: kb-graph
github: https://github.com/evan-zhang/agent-factory
description: 为指定目录下的 Markdown 文件构建知识库图谱，支持多目录监控、LLM 语义编译、Leiden 社区发现和双引擎查询。
---

# KB Graph

KB Graph 是独立 OpenClaw Skill，为指定目录下的 Markdown 文件构建知识库图谱。

核心能力：
- 增量索引：文件变更自动检测，零数据库，所有数据存在 Markdown 文件里
- LLM 语义编译：自动生成摘要、提取实体和标签、推断文件间关系
- Leiden 社区发现：自动发现知识库内的主题社区结构
- 双引擎查询：图谱引擎 + Wiki 引擎融合定位相关文件

## 安装

```bash
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/2605261/kb-graph
```

## 配置与授权

### 必填配置项

在 `~/.openclaw/kb-graph-config.json` 中配置：

```json
{
  "watch_dirs": [
    "/path/to/your/markdown/directory"
  ],
  "llm_provider": "minimax",
  "model": "MiniMax-M2.7-highspeed",
  "fallback_models": [
    "GLM-Z1-0528",
    "deepseek-ai/DeepSeek-V3-2503"
  ]
}
```

### 可选配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| schema_file | .kb-schema.md | Schema 文件名 |
| index_file | .kb-index.md | 索引文件名 |
| cache_dir | .kb-workdir | 缓存目录 |
| auto_update | true | 文件变更时自动触发增量更新 |
| lint_schedule | daily | Lint 执行频率 |

### 无需配置即可用的能力

- `python3 scripts/ingest.py --scan <dir>` 扫描目录（无需 LLM）
- `python3 scripts/validate_index.py <path>` 验证索引格式（无需 LLM）
- `python3 scripts/build_graph.py --index <path>` 从已有索引构建图谱（无需 LLM）

## 工作流

### 五层架构

```
采集层（Ingestion）    → 文件发现、变更检测（SHA256 缓存）
编译层（Compilation）  → Markdown 解析、LLM 语义编译
图谱层（Graph）        → 节点/边构建、Leiden 社区发现
查询层（Query）        → 双引擎查询（图谱 + Wiki）
维护层（Maintenance）  → Lint、矛盾检测、自动修复
```

### 典型使用流程

1. **初始化配置**：`python3 scripts/init_config.py`
2. **全量构建**：`python3 scripts/kb_graph.py --build /path/to/dir`
3. **增量更新**：文件变更后自动触发，或手动 `python3 scripts/kb_graph.py --update-single <file>`
4. **查询**：`python3 scripts/query.py --query "问题" --index /path/to/.kb-index.md`
5. **Lint 巡检**：`python3 scripts/lint.py --index /path/to/.kb-index.md`

### 核心文件格式

- `.kb-schema.md`：全局格式规则（首次运行自动生成）
- `.kb-index.md`：目录索引（含 YAML frontmatter 摘要 + 图谱 JSON）
- `.kb-workdir/kb_cache.json`：SHA256 缓存

## 脚本

| 脚本 | 用途 | 是否需要 LLM |
|------|------|-------------|
| init_config.py | 初始化配置文件 | 否 |
| ingest.py | 扫描文件、检测变更 | 否 |
| compile.py | LLM 语义编译 | 是 |
| build_graph.py | 构建图谱、Leiden 社区发现 | 否 |
| query.py | 双引擎查询 | 否 |
| lint.py | 矛盾检测、孤儿文件检查 | 否 |
| validate_index.py | 验证索引格式 | 否 |

### 命令行接口

```bash
# 全量构建
python3 scripts/kb_graph.py --build /path/to/dir

# 增量更新（单文件）
python3 scripts/kb_graph.py --update-single /path/to/file.md

# 查询
python3 scripts/query.py --query "Evan 关于 AI Agent 知道些什么" --index /path/to/.kb-index.md

# Lint 质量检查
python3 scripts/lint.py --index /path/to/.kb-index.md

# 验证索引格式
python3 scripts/validate_index.py /path/to/.kb-index.md
```

## 边界

- **不修改原始报告**：归档的文件是只读历史记录
- **零数据库**：所有数据存在 Markdown 文件里
- **不跨语言**：仅支持 Markdown 文件（.md）
- **Schema 自举**：首次运行自动生成，无需人工配置

## 问题反馈

- Issue 地址：https://github.com/evan-zhang/agent-factory/issues
- 标题格式：`[kb-graph] 问题描述`
- 建议包含：重现步骤、环境信息、日志输出