# Archive Template — 本地归档

## 配置
归档主目录由用户首次使用时配置，存储位置由环境自动决定：
- OpenClaw：`~/.openclaw/link-archivist-config.json`
- Hermes：`~/.hermes/link-archivist-config.json`
- 其他：`~/.config/link-archivist-config.json`

## 目录结构

```
{archive_dir}/
├── 2026-04-13/
│   ├── K-260413-001-{标题简称}.md
│   └── K-260413-002-{标题简称}.md
├── 2026-04-14/
│   └── ...
└── .index.json          ← 索引文件（由 LLM Wiki 项目管理）
```

## 编号规则

- **格式**：`K-YYMMDD-NNN`，如 `K-260413-001`
- **YYMMDD**：建档日期（2位年+2位月+2位日）
- **NNN**：当日序号（001-999），每日从 001 开始
- **生成方式**：扫描当日目录下已有编号，取最大 +1

## YAML 元信息头

```yaml
---
archive: K-260413-001
source: https://example.com
source_type: 今日头条
created_at: 2026-04-13T10:00:00+08:00
tags: [AI, 开源, Agent]
---
```

## 归档流程

1. 生成报告内容
2. 确定编号（扫描当日目录）
3. 写入 `{archive_dir}/{YYYY-MM-DD}/K-{YYMMDD}-{NNN}-{标题简称}.md`
4. 索引更新由 LLM Wiki 项目（AF-20260413-003）负责

## 关联项目
- 知识管理：AF-20260413-003（LLM Wiki）
- 云端同步：AF-20260413-002（知识库同步服务）
