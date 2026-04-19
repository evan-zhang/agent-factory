# 降级策略完整规则

> 当工具不可用或出错时，AI 按此文件降级处理。

## YouTube 字幕提取降级

| 优先级 | 方案 | 触发条件 |
|--------|------|----------|
| 1st | `youtube_subtitle.py` | 首选方案 |
| 2nd | `yt-dlp --write-subs --sub-lang zh --skip-download` | youtube_subtitle.py 失败时 |
| 3rd | 抓标题+描述，跳过转录 | yt-dlp 也失败时 |
| 4th | 询问用户是否下载视频转录 | 用户主动要求 |

## Web Search 降级

| 优先级 | 方案 | 触发条件 |
|--------|------|----------|
| 1st | OpenClaw `web_search` | Perplexity API，直接可用 |
| 2nd | `python3 scripts/tavily_search.py` | 配置了 tavily_api_key |
| 3rd | `session_search` 搜历史会话 | Tavily 也不可用 |
| 4th | 跳过搜索，报告中注明"未进行交叉验证" | 全部不可用时 |

## 音频转录降级

| 优先级 | 方案 | 触发条件 |
|--------|------|----------|
| 1st | `transcribe_audio.py` | 配置了 xgjk_app_key |
| 2nd | 跳过转录，只用标题+描述 | 未配置 key |

## 网页抓取降级

| 优先级 | 方案 | 触发条件 |
|--------|------|----------|
| 1st | `curl -sL https://r.jina.ai/{url}` | 通用方案，多数网站有效 |
| 2nd | BeautifulSoup + requests 直接抓取 | jina.ai 返回空内容或不完整时 |
| 3rd | `web_search` 搜索关键信息 | 抓取全部失败时 |

**BeautifulSoup 抓取模板**（适用于今日头条等有反爬的网站）：

```python
import requests
from bs4 import BeautifulSoup

url = '<目标URL>'
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
}
r = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')
article = soup.find('article')
if article:
    for tag in article(['script', 'style']):
        tag.decompose()
    text = article.get_text(' ', strip=True)
```

**注意**：今日头条移动端短链接（m.toutiao.com/is/xxx）需要用移动端 User-Agent。

## 决策树

```
字幕提取失败？
 ├─ YES → yt-dlp 降级
 │         ├─ 成功 → 继续
 │         └─ 失败 → 抓标题描述 或 询问用户
 └─ NO → 继续

Web Search 失败？
 ├─ YES → tavily_search.py
 │         ├─ 成功 → 继续
 │         └─ 失败 → session_search
 │                   ├─ 成功 → 继续
 │                   └─ 失败 → 跳过，报告中注明
 └─ NO → 继续
```
