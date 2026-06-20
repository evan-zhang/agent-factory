---
name: link-archivist
version: "2.6.1"
skillcode: link-archivist
github: https://github.com/evan-zhang/agent-factory
description: 本地知识库管理 Skill。两类输入：外部链接抓取生成报告（K 编号）和手工录入项目文档（M 编号）。支持归档、索引、查询、导出。当用户发送链接/文件/文本、说"存文档"/"查知识库"/"导出知识包"时触发。
---

# Link Archivist

**本地知识库管理** — 采集、整理、归档、搜索。与云端知识库、玄关知识库、公司知识库区分。

安装与配置详见 `references/configuration.md`。

## 触发判断总图

```
收到消息
 ├─ URL/链接/文件/文本
 │   → 判断 URL 类型：
 │     ├─ 今日头条（m.toutiao.com）→ scripts/toutiao_fetch.py
 │     ├─ 抖音（v.douyin.com）→ scripts/douyin_process.py
 │     ├─ YouTube → references/youtube-workflow.md
 │     └─ 其他 URL → curl -sL https://r.jina.ai/{url}
 │   → decide_mode.py 判断模式（full/short/ask）
 │   → 调研生成报告
 │   → archive_report.py 归档（K 编号）
 │   → 详细流程见 references/workflow.md
 │
 ├─ "存文档"/"归档项目文档"/"手工录入"
 │   → 确认 project_id（推断或提问）
 │   → archive_report.py --source-type manual（M 编号）
 │
 ├─ "查知识库"/"搜归档"/"找之前的报告"
 │   → kb_query.py（可选 --prefix K/M 过滤来源）
 │
 ├─ "重建索引"/"全量更新"     → kb_rebuild.py
 ├─ "增量更新"/"刷新索引"     → kb_rebuild.py --incremental
 ├─ "索引质量"/"kb 巡检"      → kb_lint.py
 ├─ "导出知识包"/"OKF 导出"   → kb_export_okf.py
 │
 └─ 未初始化 → 引导配置 archive_dir
```

## 核心命令速查

**归档外部链接**（Phase 1-5 完整流程见 `references/workflow.md`）：
```bash
python3 scripts/archive_report.py \
  --file report.md --dir {archive_dir} \
  --title "标题" --source-url "https://原始链接" \
  --summary "摘要" --entities '["实体"]' --tags '["标签"]' \
  --confidence high
```

**手工录入文档**（M 编号）：
```bash
python3 scripts/archive_report.py \
  --file doc.md --dir {archive_dir} \
  --title "标题" \
  --source-type manual --project-id <项目ID> --author <作者> \
  --summary "摘要" --confidence high
```

**查询知识库**：
```bash
python3 scripts/kb_query.py "关键词" --dir {archive_dir}
python3 scripts/kb_query.py "关键词" --dir {archive_dir} --prefix K  # 只搜外部
python3 scripts/kb_query.py "关键词" --dir {archive_dir} --prefix M  # 只搜项目文档
```

> ⚠️ **归档纪律**：归档 **必须** 通过 `archive_report.py` 执行。禁止 Agent 自行拼接 frontmatter 或绕过脚本写文件。脚本会强制标准格式。

> ⚠️ **玄关同步纪律**：向 archive_dir 写文件的任何操作（含 write/edit/脚本），完成后必须调 xgkb-push 补推。详见 `references/configuration.md`。

## 边界

**负责**：外部资料采集归档、手工文档归档、知识库查询、索引管理、OKF 导出

**不负责**：渠道发送、文件解析（PDF/Word/PPT）、跨设备同步、wiki 主题页合成（memory-wiki 插件，可选）

## 参考文件

| 文件 | 内容 |
|------|------|
| `references/workflow.md` | **Phase 1-5 完整工作流** |
| `references/configuration.md` | **安装、配置、K/M 编号、XGKB 同步** |
| `references/execution-mode.md` | sub-agent 模式与直接执行 |
| `references/script-reference.md` | 全部脚本用法 |
| `references/survey-methodology.md` | 调研方法论 |
| `references/degradation-rules.md` | 降级策略 |
| `references/phase3-prompt-template.md` | Phase 3 LLM prompt 模板 |
| `references/kb-query-guide.md` | 知识库查询指南 |
| `references/youtube-workflow.md` | YouTube 处理流程 |
| `references/okf-alignment.md` | OKF 对齐说明 |
| `references/kb-index-architecture.md` | KB 索引架构 |
| `examples/` | 完整示例 |

## 问题反馈

https://github.com/evan-zhang/agent-factory/issues/new

标题格式：`[BUG] link-archivist: 简短描述`
