# YouTube 视频处理详细流程

> 当 YouTube 视频处理需要查看详细步骤时，AI 读取此文件。

## 前置步骤：获取基本信息

**首选**：`yt-dlp --print title --print duration --print uploader <URL>`

**已知问题**：沙盒环境可能有 JavaScript Runtime 警告（`WARNING: No supported JavaScript runtime`），但基本信息通常不受影响。

**备用**：YouTube oEmbed API（不需要 JS runtime）

```python
import requests
r = requests.get('https://www.youtube.com/oembed', params={'url': '<YouTube URL>', 'format': 'json'}, timeout=10)
if r.status_code == 200:
    data = r.json()
    print(f"Title: {data.get('title', '')}")
    print(f"Author: {data.get('author_name', '')}")
```

**oEmbed 限制**：只能获取标题和作者，无法获取时长、字幕或下载视频。

## 完整处理步骤

```
YouTube 链接收到后：
1. 【前置】获取基本信息
   yt-dlp --print title --print duration --print uploader <URL>
2. 【前置】展示给用户，确认是否处理
3. 用户确认后 → 字幕提取
4. 字幕失败 → 降级 yt-dlp
5. 解析 VTT
6. 有字幕 → 直接用
7. 无字幕 → 询问用户是否转录
8. 用户确认 → transcribe_audio.py
```

## 字幕提取优先级

| 优先级 | 工具/方案 | 说明 |
|--------|----------|------|
| 1st | `youtube_subtitle.py` | 手动字幕优先，速度快 |
| 2nd | `yt-dlp --write-subs --sub-lang zh --skip-download` | 自动字幕降级 |

## VTT 字幕解析规则

- 跳过 WEBVTT 头部
- 跳过元数据行
- 跳过时间戳行
- 只提取纯文本内容

## 无字幕时的决策

| 时长 | 决策 | 理由 |
|------|------|------|
| < 5 分钟 | 可直接总结 | 信息密度低 |
| 5-15 分钟 | 询问用户 | 标准长度，视内容价值决定 |
| > 15 分钟 | 询问用户 | 信息量大，值得完整处理 |

用户选择不转录 → 只抓标题+描述，继续后续流程。
用户选择转录 → `transcribe_audio.py` 调用 AI 慧记转录（需配置 xgjk_app_key）。
