---
name: douyin-video-analysis
version: "1.0.0"
description: 抖音视频分析 — 解析链接、下载视频、提取音频、转写语音、生成报告
trigger: 用户发送抖音链接（v.douyin.com 或 douyin.com）时触发，或手动调用
---

# 抖音视频分析 Skill

## 概述

分析抖音视频内容：从分享链接出发，自动完成 解析 → 下载视频 → 提取音频 → 语音转写 → 生成分析报告 的完整流程。

## 环境要求

| 组件 | 要求 | 检查方式 |
|------|------|---------|
| mcporter | 已安装，douyin 服务器已配置 | `mcporter config list` |
| Douyin MCP Server | `@yc-w-cn/douyin-mcp-server` 已全局安装 | `npm ls -g @yc-w-cn/douyin-mcp-server` |
| ffmpeg | 已安装（静态二进制即可） | `which ffmpeg` |
| Python 3 | requests 库可用 | `python3 -c "import requests"` |

## 工作流程

### Step 1: 解析抖音链接

使用 mcporter 调用 Douyin MCP Server：

```bash
mcporter call 'douyin.parse_douyin_video_info(share_link: "抖音分享链接")'
```

返回包含：标题、视频ID、无水印下载链接。

**备选方案**：如果 MCP 不可用，使用 Python requests 直接提取：
```bash
python3 scripts/douyin_process.py parse "https://v.douyin.com/XXXXX/"
```

### Step 2: 下载视频

```bash
curl -L -o /tmp/douyin_分析/video.mp4 \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)" \
  -H "Referer: https://www.douyin.com/" \
  "下载链接URL" \
  --max-time 300 --noproxy '*'
```

**重要**：必须加 `--noproxy '*'`，否则系统代理会导致下载失败。

### Step 3: 提取音频

```bash
ffmpeg -i /tmp/douyin_分析/video.mp4 -vn -acodec libmp3lame -ab 128k /tmp/douyin_分析/audio.mp3 -y
```

### Step 4: 语音转写

**优先级**（按可用性选择）：
1. **Whisper 本地**（如已安装）：`whisper audio.mp3 --model tiny --language Chinese`
2. **GLM-4V-Flash API**（免费，需有效 API key）
3. **跳过转写**，仅基于视频元数据生成摘要报告

### Step 5: 生成报告

综合视频标题、元数据、转写文本，生成 Markdown 分析报告。

## 调用方式

收到抖音链接后，按以下步骤执行：

1. 创建临时目录 `/tmp/douyin_分析/`
2. 用 mcporter 解析链接，获取视频标题和下载URL
3. 下载视频到临时目录
4. 用 ffmpeg 提取音频
5. 尝试语音转写（优先本地 Whisper，备选 API）
6. 生成 Markdown 报告，包含：标题、作者、时长、转写文本、内容摘要

## 输出

- 视频文件：`/tmp/douyin_分析/video.mp4`
- 音频文件：`/tmp/douyin_分析/audio.mp3`
- 转写文本：`/tmp/douyin_分析/transcript.txt`
- 分析报告：`/tmp/douyin_分析/report.md`

## 报告格式模板

```markdown
# 抖音视频分析报告

## 基本信息
- **标题**：{title}
- **视频ID**：{video_id}
- **来源链接**：{share_link}
- **分析时间**：{timestamp}

## 语音转写

{transcript}

## 内容摘要

{summary}

## 关键要点

{key_points}
```

## 已知问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| MCP 返回 400 错误 | 系统代理干扰 axios | MCP 已 patch（proxy:false），如重新安装需重新 patch |
| 下载链接过期 | CDN 链接约2小时有效 | 重新调用 parse 获取新链接 |
| yt-dlp 无法下载 | 需要新鲜 cookies | 不要用 yt-dlp，用 MCP + curl |
| 转写无模型 | Whisper 未安装 | 跳过转写，仅基于元数据生成报告 |

## MCP Server Patch 说明

系统代理（`HTTP_PROXY=http://127.0.0.1:10809`）会导致 MCP server 的 axios 请求失败。
已对 `/usr/lib/node_modules/@yc-w-cn/douyin-mcp-server/dist/index.js` 进行 patch：
- 3处 axios.get() 调用添加了 `proxy: false`
- 修复了 cleanUrl 中 `\u002F` 未解码的 bug

**如果 npm update 覆盖了 patch，需重新应用。**

## 与 Link Archivist 集成

当 Link Archivist 检测到抖音链接时（匹配 `v.douyin.com` 或 `douyin.com`），应先加载本 skill，走完整的视频分析流程，而非仅抓取 HTML 页面。
