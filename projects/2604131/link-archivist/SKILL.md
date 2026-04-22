---
name: link-archivist
version: "1.4.0"
skillcode: link-archivist
github: https://github.com/evan-zhang/agent-factory
description: 当用户发送一个链接（YouTube/通用 URL）、文件或粘贴文本，需要抓取内容并生成调研报告时触发。
---

# Link Archivist

## 触发判断

```
收到消息
 ├─ URL/链接         → 抓取内容 → 决定模式
 ├─ 文件             → 调用外部解析工具提取文本 → 决定模式
 ├─ 粘贴文本         → 直接判断模式
 └─ 未初始化         → 引导配置 archive_dir
```

## 初始化配置

运行 `scripts/init_config.py` 检查配置状态。

配置文件（按环境自动选择路径）：
- OpenClaw：`~/.openclaw/link-archivist-config.json`
- Hermes：`~/.hermes/link-archivist-config.json`
- 其他：`~/.config/link-archivist-config.json`

**配置文件示例**：
```json
{
  "archive_dir": "/path/to/knowledge-base",
  "obsidian_dir": "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/github分享/AI调研",
  "xgjk_app_key": "your-app-key-here",
  "tavily_api_key": "your-tavily-api-key"
}
```

- `archive_dir`：本地归档主目录（必填）
- `obsidian_dir`：Obsidian 同步目录（可选，留空则跳过同步）
- Obsidian 同步格式：`{obsidian_dir}/YYYY-MM-DD/{标题简称}-YYYY-MM-DD.md`

配置 tavily_api_key 可显著提升报告质量（Web Search 交叉验证）。获取：https://tavily.com

## 工作流

1. **检测配置** → `scripts/init_config.py`
2. **抓取内容** → r.jina.ai（通用）/ yt-dlp（YouTube）/ 外部文件解析
   - **抖音视频**（v.douyin.com / douyin.com）：调用 `scripts/douyin_process.py`，流程：mcporter 解析链接 → curl 下载视频 → ffmpeg 提取音频 → 报告生成，然后基于输出继续调研流程
   - **YouTube 视频**：详见 `references/youtube-workflow.md`（AI 自动在需要时读取）
3. **决定模式** → `scripts/decide_mode.py`（来源优先 + 关键词判断）
   - **full**：GitHub/YouTube，或关键词命中（开源/框架/论文等）→ 完整调研报告
   - **short**：新闻资讯类 → 2-3 句话摘要
   - **ask**：不确定 → 问用户
4. **执行调研**（full 模式含 web_search 交叉验证）→ 详见 `references/survey-methodology.md`
5. **生成洞察**
   1. 使用 `session_search` 搜相关历史会话记录
   2. 使用 `read_index` 搜本地知识库文件
   3. 结合两者动态生成个性化洞察
6. **归档本地 + Obsidian 同步**
   - 本地归档 → `{archive_dir}/{YYYY-MM-DD}/K-{YYMMDD}-{NNN}-{标题简称}.md`
   - Obsidian 同步（需配置 `obsidian_dir`）→ `{obsidian_dir}/{YYYY-MM-DD}/{标题简称}-YYYY-MM-DD.md`
   - 同步由 `archive_report.py` 自动完成，无需额外操作

## 降级策略

详见 `references/degradation-rules.md`（YouTube 字幕 / Web Search / 音频转录三种场景）

## 脚本

| 脚本 | 用途 |
|------|------|
| `scripts/init_config.py` | 检测/创建配置文件 |
| `scripts/decide_mode.py` | 判断 short/full/ask |
| `scripts/youtube_subtitle.py` | YouTube 字幕提取 |
| `scripts/tavily_search.py` | Tavily Web Search |
| `scripts/douyin_process.py` | 抖音视频：mcporter 解析 → curl 下载 → ffmpeg 提取音频 → 报告生成 |
| `scripts/archive_report.py` | 归档报告到本地目录 |

**关键用法**：
```bash
# 判断模式
python3 scripts/decide_mode.py "<URL>" --content "<抓取到的内容>"

# YouTube 字幕提取
python3 scripts/youtube_subtitle.py "<YouTube URL>"
# {"ok": true, "text": "字幕全文", "source": "manual"}

# Tavily 搜索
python3 scripts/tavily_search.py "<关键词>" [max_results]
```

## 参考

| 文件 | 内容 |
|------|------|
| `references/report-template.md` | 报告模板（full + short） |
| `references/archive-template.md` | 归档目录结构、编号规则 |
| `references/decision-rules.md` | 模式判断规则说明 |
| `references/youtube-workflow.md` | YouTube 详细处理流程 |
| `references/survey-methodology.md` | 调研方法论（执行调研完整说明）|
| `references/degradation-rules.md` | 完整降级策略 |
| `references/SOP-诸葛工作流.md` | 详细 SOP |
| `examples/` | 4 个完整示例 |

## 工具映射（非 OpenClaw 环境）

| SKILL 工具 | 其他环境对应 | 说明 |
|------------|-------------|------|
| `web_fetch(url)` | `curl -sL {url}` | 网页抓取 |
| `web_search(query)` | OpenClaw 内置 web_search，或 tavily_search.py | 网络搜索 |
| `session_search(query)` | Agent 内置 session_search | 搜历史会话和记忆 |
| `read_index(target)` | `search_files(target="files")` | 搜本地知识库文件 |
| `exec(command)` | 终端执行 | 执行命令 |
| `write(file, content)` | 文件写入 | 写文件 |
| `message(channel, text)` | 无需对应 | Skill 不负责发送 |

## 边界

**本 Skill 负责**：抓取 → 判断 → 调研 → 生成报告 → 归档本地 → 同步 Obsidian

**不负责**：渠道发送（Agent 自行决定）、文件解析（PDF/Word/PPT/图片）、知识索引管理（AF-20260413-003）
