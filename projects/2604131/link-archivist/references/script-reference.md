# 脚本参考

## 脚本列表

| 脚本 | 用途 |
|------|------|
| `scripts/init_config.py` | 检测/创建配置文件 |
| `scripts/decide_mode.py` | 判断 short/full/ask |
| `scripts/toutiao_fetch.py` | 今日头条文章抓取 |
| `scripts/youtube_subtitle.py` | YouTube 字幕提取 |
| `scripts/douyin_process.py` | 抖音视频处理（API 或降级） |
| `scripts/video_archive.py` | 视频下载与归档 |
| `scripts/tavily_search.py` | Tavily Web Search |
| `scripts/archive_report.py` | 归档报告（含 KB 索引 + XGKB 同步） |
| `scripts/validate_report.py` | 报告完整性验证 |
| `scripts/kb_query.py` | 知识库查询 |
| `scripts/kb_rebuild.py` | 索引重建（全量/增量） |
| `scripts/kb_lint.py` | 索引质量巡检 |
| `scripts/kb_export_okf.py` | OKF-style 知识包导出 |

## 关键用法

```bash
# 判断模式
python3 scripts/decide_mode.py "<URL>" --content "<抓取到的内容>"

# 今日头条抓取
python3 scripts/toutiao_fetch.py "<头条URL>"
python3 scripts/toutiao_fetch.py "<头条URL>" --text-only  # 纯文本

# YouTube 字幕
python3 scripts/youtube_subtitle.py "<YouTube URL>"

# 视频归档下载
python3 scripts/video_archive.py --url "<url>" --platform youtube|douyin --mode full

# 视频归档 rename
python3 scripts/video_archive.py --rename --temp "<temp_path>" --archive-id "K-260620-001"

# 报告验证
python3 scripts/validate_report.py "<报告文件>" --mode full|short

# 归档（外部链接）
python3 scripts/archive_report.py \
  --file report.md --dir <archive_dir> \
  --title "标题" --source-url "https://..." \
  --summary "摘要" --entities '["实体"]' --tags '["标签"]' --confidence high

# 归档（手工录入）
python3 scripts/archive_report.py \
  --file doc.md --dir <archive_dir> \
  --title "标题" \
  --source-type manual --project-id <项目ID> --author <作者> \
  --summary "摘要" --confidence high

# KB 查询
python3 scripts/kb_query.py "关键词" --dir <archive_dir> --mode keyword
python3 scripts/kb_query.py "关键词" --dir <archive_dir> --prefix K  # 只搜外部资料
python3 scripts/kb_query.py "关键词" --dir <archive_dir> --prefix M  # 只搜项目文档

# KB 状态
python3 scripts/kb_query.py status --dir <archive_dir>

# KB 重建
python3 scripts/kb_rebuild.py --dir <archive_dir>              # 全量
python3 scripts/kb_rebuild.py --dir <archive_dir> --incremental  # 增量

# KB 巡检
python3 scripts/kb_lint.py --dir <archive_dir>

# OKF 导出
python3 scripts/kb_export_okf.py --dir <archive_dir>
python3 scripts/kb_export_okf.py --dir <archive_dir> --root --force
```

## 工具映射（非 OpenClaw 环境）

| SKILL 工具 | 其他环境对应 |
|------------|-------------|
| `web_fetch(url)` | `curl -sL {url}` |
| `web_search(query)` | `tavily_search.py` |
| `session_search(query)` | Agent 内置 |
| `exec(command)` | 终端执行 |
| `write(file, content)` | 文件写入 |
