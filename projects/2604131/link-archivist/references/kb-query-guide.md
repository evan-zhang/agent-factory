# KB Query Guide

Link Archivist v2.0.0 内置知识库查询能力，支持关键词、语义和混合三种查询模式。

## 触发场景

当用户说以下任何一种话时触发：

- "查知识库" / "kb 查询" / "知识图谱"
- "搜索归档" / "找之前的报告" / "我之前研究过 X 吗？"
- "根据之前的笔记，..."

## 查询模式

### 1. Keyword 模式（默认）

无需外部 API，基于标题、摘要、实体、标签的全文搜索。

```bash
python3 scripts/kb_query.py "OpenClaw KB Graph" --dir <archive_dir>
```

**匹配规则：**
- title 匹配：+10 分
- summary 匹配：+5 分
- tags 匹配：+3 分
- entities 匹配：+3 分

### 2. Semantic 模式

需要 OPENAI_API_KEY，基于向量相似度的语义搜索。

```bash
python3 scripts/kb_query.py "我想找关于知识图谱的笔记" \
  --dir <archive_dir> \
  --mode semantic
```

**依赖：**
- OPENAI_API_KEY 环境变量
- `.kb-workdir/embeddings.json` 存在

### 3. Hybrid 模式

融合关键词和语义搜索，关键词 60% + 语义 40%。

```bash
python3 scripts/kb_query.py "知识图谱" \
  --dir <archive_dir> \
  --mode hybrid
```

## 返回格式

```json
{
  "ok": true,
  "query": "OpenClaw KB Graph",
  "method": "keyword",
  "total": 5,
  "results": [
    {
      "path": "2026/06/K-260619-001-openclaw-kb-graph.md",
      "title": "OpenClaw KB Graph 架构设计",
      "summary": "...",
      "entities": ["OpenClaw", "KB Graph", "..."],
      "tags": ["AI", "架构"]
    }
  ],
  "stats": [
    {
      "path": "2026/06/K-260619-001-openclaw-kb-graph.md",
      "score": 18,
      "keyword_score": 18,
      "semantic_score": 0,
      "matched_fields": ["title", "summary"]
    }
  ]
}
```

## 呈现方式

只展示前 5 条最相关的结果，避免信息过载。如果用户需要更多，再展示后续结果。

### 用户呈现模板

```
📚 找到 5 条相关归档

1. OpenClaw KB Graph 架构设计
   路径：2026/06/K-260619-001-openclaw-kb-graph.md
   摘要：OpenClaw KB Graph 是一个五层架构的知识库索引系统...
   实体：OpenClaw, KB Graph, 知识图谱
   标签：AI, 架构, 工具
   相关度：18 分

2. ...

[更多结果请说"继续"]
```

## Agent 调用方式

### Sub-Agent 模式

```python
# 在 orchestrator 中 spawn sub-agent 处理查询
sessions_spawn(
    task="请查询知识库：用户查询内容",
    cwd=skill_root,
    mode="run"
)
```

### 直接脚本调用

```python
import subprocess
import json

result = subprocess.run([
    "python3", "scripts/kb_query.py",
    query_str,
    "--dir", archive_dir,
    "--mode", "keyword"
], capture_output=True, text=True)

data = json.loads(result.stdout)
results = data.get("results", [])
```

## 配置检查

查询前检查索引状态：

```bash
python3 scripts/kb_query.py status --dir <archive_dir>
```

返回：
```json
{
  "ok": true,
  "status": "ready",
  "archive_dir": "/path/to/archive",
  "total_entries": 522,
  "workdir": "/path/to/archive/.kb-workdir"
}
```

## 常见问题

### Q: 查询无结果怎么办？

A: 可能原因：
1. 索引未构建：运行 `python3 scripts/kb_rebuild.py --dir <archive_dir>`
2. 查询词过泛：尝试更具体的关键词
3. 文档 frontmatter 缺失：运行 `python3 scripts/kb_lint.py --dir <archive_dir>` 检查

### Q: 语义搜索不可用？

A: 检查：
1. OPENAI_API_KEY 是否设置
2. embeddings.json 是否存在（需要首次运行时生成）

### Q: 如何提高查询准确度？

A:
1. 确保 Phase 3 LLM 生成的 entities 和 tags 准确
2. 使用 hybrid 模式融合关键词和语义
3. 运行 `python3 scripts/kb_lint.py --dir <archive_dir>` 检查索引进度
