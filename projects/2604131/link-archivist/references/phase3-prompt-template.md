# Phase 3 Prompt Template

本文档提供 Phase 3 调研时必须使用的 LLM prompt 模板，确保生成符合索引要求的 frontmatter。

## 核心要求

Phase 3 LLM **必须**输出符合以下格式的 YAML frontmatter，orchestrator 必须将提取的字段传递给 `archive_report.py`。

## Prompt 模板

```text
你是调研助手。基于以下内容生成结构化报告 + frontmatter 元数据。

**必须输出的 YAML 块**（在报告正文最前面，用 ```yaml ... ``` 包裹）：

```yaml
summary: <≤200 字中文摘要>
entities:
  - <关键实体1>
  - <关键实体2>
  # 最多 10 个
tags:
  - <标签1>
  - <标签2>
  # 最多 3 个，从 [AI, 架构, 安全, 运维, 产品, 运营, 前端, 后端, 数据库, 工具, 流程, 综合] 选
confidence: high | medium | low
relationships:
  - type: reference | topic
    target: <文档名/主题名>
    description: <关系说明>
```

报告正文 <报告内容>。
```

## 校验规则

`parse_frontmatter.py` 检测到以下任一情况视为 `frontmatter_invalid`：

- `summary` 缺失或 > 200 字
- `entities` 缺失（空数组允许）
- `tags` 缺失（空数组允许）
- `confidence` 不在 {high, medium, low}

## 用户反馈格式

索引失败时的用户反馈：

```
✅ 归档完成：{archive_path}
⚠️ 索引失败：frontmatter 字段缺失（summary/entities/tags/confidence）
   → 可手动补充后运行 `python3 scripts/kb_rebuild.py --dir {archive_dir} --incremental` 补建索引
   → 或运行 `python3 scripts/kb_rebuild.py --dir {archive_dir} --force-llm` 强制重编
```

## Orchestrator 实现

Orchestrator 必须按以下步骤执行：

1. 调用 Phase 3 LLM 生成报告
2. 从输出中提取 YAML frontmatter（在报告最前面的 ```yaml ... ``` 块）
3. 解析 `summary`、`entities`、`tags`、`confidence` 字段
4. 将这些字段传递给 `archive_report.py`：

```bash
python3 scripts/archive_report.py \
  --file <报告文件> \
  --dir <archive_dir> \
  --title "<标题>" \
  --summary "<summary>" \
  --entities '<["实体1", "实体2"]>' \
  --tags '<["AI", "架构"]>' \
  --confidence "high"
```

## 示例

### 输入内容
```
文档内容：关于 OpenClaw KB Graph 架构设计的技术讨论...
```

### LLM 应输出
````markdown
```yaml
summary: OpenClaw KB Graph 是一个五层架构的知识库索引系统，支持增量更新、语义查询和自动维护。
entities:
  - OpenClaw
  - KB Graph
  - 知识图谱
  - Louvain 算法
  - YAML frontmatter
tags:
  - AI
  - 架构
  - 工具
confidence: high
relationships:
  - type: reference
    target: link-archivist
    description: 本项目作为 Link Archivist 的内部模块
  - type: topic
    target: 知识库管理
    description: 属于知识库管理主题
```

# OpenClaw KB Graph 架构设计

## 概述

OpenClaw KB Graph 采用五层架构...
````

### Orchestrator 提取并调用
```bash
python3 scripts/archive_report.py \
  --file report.md \
  --dir ~/.openclaw/gateways/life/state/workspace-life/knowledge \
  --title "OpenClaw KB Graph 架构设计" \
  --summary "OpenClaw KB Graph 是一个五层架构的知识库索引系统，支持增量更新、语义查询和自动维护。" \
  --entities '["OpenClaw", "KB Graph", "知识图谱", "Louvain 算法", "YAML frontmatter"]' \
  --tags '["AI", "架构", "工具"]' \
  --confidence "high"
```

## OKF 字段映射

Link Archivist frontmatter 与 [OKF v0.1](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing) 字段天然兼容。Phase 3 LLM 不需要输出 OKF 字段；orchestrator 在归档时自动映射：

| Link Archivist 字段 | OKF 字段 | 说明 |
|---|---|---|
| 正文第一个 `#` 标题 | `title` | 自动提取 |
| `summary` | `description` | 语义等价 |
| `source` | `resource` | 语义等价 |
| `tags` | `tags` | 直接映射 |
| `created_at` | `timestamp` | 语义等价 |
| `source_type` | `type`（近似） | v2.1 可选扩展 |
| `archive` | — | Link Archivist 独有，OKF 未定义 |
| `entities` | — | Link Archivist 独有 |
| `relationships` | — | Link Archivist 独有（OKF 偏 Markdown link） |
| `confidence` | — | Link Archivist 独有 |

详细对齐策略见 `references/okf-alignment.md`。
