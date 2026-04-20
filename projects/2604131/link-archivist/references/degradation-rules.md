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
| 3rd | 搜索引擎绕行法（见下方） | 中国平台反爬屏蔽时 |
| 4th | `web_search` 搜索关键信息补充 | 以上全部失败时 |

### 搜索引擎绕行法（中国平台反爬专用）

**适用场景**：今日头条、知乎、微信公众号等有 JS 反爬机制，jina.ai 返回空、curl 拿到 JS 加密页面、浏览器未安装时。

**核心思路**：不从目标平台抓内容，而是通过搜索引擎找到**同一主题的原始来源**，直接从原始来源获取。

**步骤**：

1. **提取标题关键词**：从用户消息或短链接重定向后的 URL 提取标题关键信息
2. **DuckDuckGo 搜索**（优先于 Google，不易触发 CAPTCHA）：
   ```bash
   curl -sL "https://r.jina.ai/https://html.duckduckgo.com/html/?q=<关键词>" -H "Accept: text/markdown"
   ```
3. **定位原始来源**：从搜索结果中找到一手来源（GitHub Gist/Repo、个人博客、原始论文等）
4. **直接获取原始内容**：
   - GitHub Gist raw：`https://gist.githubusercontent.com/karpathy/<id>/raw/<filename>`
   - GitHub README：`curl -sL https://api.github.com/repos/<owner>/<repo>/readme`（API 方式）
   - 普通博客：`curl -sL https://r.jina.ai/<url>`
5. **交叉验证**：多个搜索结果互相印证，确保信息准确

**实测案例**（2026-04-14）：
- 今日头条链接 → jina.ai 空内容、curl 拿到 JS 加密页 → Playwright + wait_for_timeout 等待动态内容
- → DuckDuckGo 搜索标题关键词 → 找到 CSDN/知乎/GitHub 上的同题文章
- → 定位到 Karpathy 的 GitHub Gist 原文 → 直接 raw URL 抓取成功
- → 获得比头条文章更完整的一手信息

**BeautifulSoup 抓取模板**（对不严重反爬的网站仍可用）：

```python
import requests
from bs4 import BeautifulSoup

url = '<目标URL>'
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
}
r = requests.get(url, headers=headers, timeout=60)
soup = BeautifulSoup(r.text, 'html.parser')
article = soup.find('article')
if article:
    for tag in article(['script', 'style']):
        tag.decompose()
    text = article.get_text(' ', strip=True)
```

**Playwright 配置**（用于有 JS 反爬的目标网站）：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)  # 额外等待 5s，确保动态内容加载完毕
    content = page.content()
    browser.close()
```

> 超时统一设 60s，等待时间设 5s 以上（头条等重 JS 网站可设 10s）。

**注意**：今日头条移动端短链接（m.toutiao.com/is/xxx）有 _$jsvmprt JS 加密，BeautifulSoup 方案基本无效，请直接使用搜索引擎绕行法。

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
