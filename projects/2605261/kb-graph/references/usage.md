# KB Graph 使用指南

## 安装

```bash
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/2605261/kb-graph
```

## 配置

安装后运行 `python3 scripts/init_config.py`，在 `~/.openclaw/kb-graph-config.json` 中配置：

```json
{
  "watch_dirs": ["/path/to/your/markdown/directory"],
  "llm_provider": "minimax",
  "model": "MiniMax-M2.7-highspeed",
  "fallback_models": ["GLM-Z1-0528", "deepseek-ai/DeepSeek-V3-2503"]
}
```

可选配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| schema_file | .kb-schema.md | Schema 文件名 |
| index_file | .kb-index.md | 索引文件名 |
| cache_dir | .kb-workdir | 缓存目录 |
| auto_update | true | 文件变更时自动触发增量更新 |
| lint_schedule | daily | Lint 执行频率 |

无需配置即可用：`ingest.py --scan`、`validate_index.py`、`build_graph.py --dir`。

## 命令行接口

```bash
# 全量构建
python3 scripts/kb_graph.py build /path/to/dir

# 增量更新（单文件）
python3 scripts/kb_graph.py update-single /path/to/file.md --dir /path/to/dir

# 增量更新（目录）
python3 scripts/kb_graph.py update /path/to/dir

# 查询
python3 scripts/kb_graph.py query "关键词" --dir /path/to/dir

# 状态
python3 scripts/kb_graph.py status /path/to/dir

# Lint 质量检查
python3 scripts/kb_graph.py lint /path/to/dir
```

测试模式（跳过 LLM）：加 `--test-mode` 参数。

## 核心文件格式

- `.kb-schema.md`：全局格式规则（首次运行自动生成）
- `.kb-index.md`：目录索引（含 YAML frontmatter 摘要）
- `.kb-workdir/entries.json`：结构化条目数据
- `.kb-workdir/kb_cache.json`：SHA256 缓存

## 脚本说明

| 脚本 | 用途 | 需要 LLM |
|------|------|----------|
| init_config.py | 初始化配置文件 | 否 |
| ingest.py | 扫描文件、检测变更 | 否 |
| compile.py | LLM 语义编译 | 是 |
| build_graph.py | 构建图谱、Leiden 社区发现 | 否 |
| query.py | 关键词查询 | 否 |
| lint.py | 矛盾检测、孤儿文件检查 | 否 |
| validate_index.py | 验证索引格式 | 否 |
| kb_graph.py | CLI 统一入口 | 编译时需要 |

## 问题反馈

- Issue：https://github.com/evan-zhang/agent-factory/issues
- 标题格式：`[kb-graph] 问题描述`
- 建议包含：重现步骤、环境信息、日志输出
