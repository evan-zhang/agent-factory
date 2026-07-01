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
| 1st | `python3 scripts/firecrawl_fetch.py <url>` | **默认方案**（大多数网站，输出最干净） |
| 2nd | `python3 scripts/toutiao_fetch.py <url>` | **头条文章专用**（见下方说明） |
| 3rd | `crwl "<url>" -o markdown`（Crawl4AI） | Firecrawl 配额耗尽 / 月底兜底 |
| 4th | `curl -sL https://r.jina.ai/<url>` | 离线/网络封禁 Jina 环境 |
| 5th | BeautifulSoup + requests 直接抓取 | 通用方案返回空内容或不完整时 |
| 6th | 搜索引擎绕行法（见下方） | 中国平台反爬屏蔽时 |
| 7th | `web_search` 搜索关键信息补充 | 以上全部失败时 |

### Firecrawl 默认抓取（2026-07 升级）

**适用 URL**：所有通用 URL（非头条、非抖音、非 YouTube）

**原理**：Firecrawl v2 API 提供 LLM 友好的精炼 Markdown 输出，自动过滤导航/侧栏/广告，附带 metadata（title/og:description/og:image）。

**使用方法**：
```bash
# 推荐：从配置文件读取 firecrawl_api_key
python3 scripts/firecrawl_fetch.py "<url>"

# 完整 JSON 输出（含 metadata）
python3 scripts/firecrawl_fetch.py "<url>" --json

# 截断过长内容（默认无限制）
python3 scripts/firecrawl_fetch.py "<url>" --max-chars 50000
```

**输出**：
- 标出模式：返回 `Title: 标题` + 精炼 Markdown 正文
- JSON 模式：返回 `{ok, markdown, title, metadata, error}`
- 返回 `{ok: false, error: ...}` 时表示抓取失败，进入降级链下一级

**降级阈值判断**：
- `ok: false` → 进入 3rd（Crawl4AI）
- `ok: true` 但 `markdown < 500 字` → 进入 3rd（Crawl4AI）二次验证
- `ok: true` 且 `markdown ≥ 500 字` → 成功继续

**配额注意**：免费版 1000 页/月，Hobby plan $16/月 5000 页。每月 25-28 号检查用量，避免月底爆配额导致归档失败。

**降级触发频率监控**：建议每月统计 Firecrawl 失败/降级占比；若 Firecrawl 失败率 > 30%，考虑直接关闭降级到 Jina Reader。

### 今日头条专用抓取（2026-05 新增）

**适用 URL**：所有 `m.toutiao.com` 和 `www.toutiao.com` 文章链接

**原理**：头条移动端 SSR 页面在 HTML 的 `<script id="RENDER_DATA">` 中直接嵌入了完整的 `articleInfo` JSON（含标题、正文、作者、发布时间），无需执行 JS。

**使用方法**：
```bash
python3 scripts/toutiao_fetch.py "<头条文章URL>" --text-only  # 纯文本摘要（用于 short 模式）
python3 scripts/toutiao_fetch.py "<头条文章URL>"               # 完整 JSON（用于 full 模式）
```

**输出字段**：
- `title`：文章标题
- `content`：HTML 格式正文
- `content_text`：纯文本正文
- `detail_source`：作者/媒体名称
- `publish_time`：发布时间戳
- `is_original`：是否原创
- `keywords`：关键词

**实测效果**（2026-05-07）：
- 移动端文章页（`m.toutiao.com/i{article_id}/`）：✅ 直接提取成功，完整 6000+ 字文章
- jina.ai 抓取：❌ 451 拦截（DDoS 保护误杀）
- 直接 curl HTML + _$jsvmprt JS 解密：❌ 复杂（不建议）
- 搜索引擎绕行法：⚠️ 可行但信息可能有损失

**注意**：头条短链接（`m.toutiao.com/is/xxx`）会先 302 重定向到带 ID 的 URL，脚本会自动 follow 重定向。

### 搜索引擎绕行法（中国平台反爬专用）

**适用场景**：知乎、微信公众号等有 JS 反爬机制，jina.ai 返回空、curl 拿到 JS 加密页面时。

> ⚠️ 今日头条已优先使用上方 toutiao_fetch.py，搜索引擎绕行法仅作为头条的保底方案。

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

**实测案例**（2026-05-07）：
- 今日头条链接 → jina.ai 451拦截 → 直接使用 toutiao_fetch.py 从 SSR RENDER_DATA 提取
- → 提取 6000+ 字完整文章内容 ✅

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

> 头条移动端页面无需 Playwright，直接用 toutiao_fetch.py 即可。Playwright 方案仅适用于其他严重 JS 反爬的平台。

> **注意**：头条短链接（m.toutiao.com/is/xxx）会自动重定向到含 ID 的 URL，toutiao_fetch.py 会自动 follow，无需手动处理。

## 决策树

```
收到链接 → 是头条文章（m.toutiao.com 或 www.toutiao.com）？
 ├─ YES → python3 toutiao_fetch.py（头条专用提取）
 │         ├─ 成功 → 继续
 │         └─ 失败 → 降级到 Firecrawl
 └─ NO → python3 firecrawl_fetch.py（默认 Firecrawl）
         ├─ 成功且正文≥500字 → 继续
         ├─ 成功但正文<500字 → 升级到 Crawl4AI（crwl）验证
         │                       ├─ 成功 → 继续
         │                       └─ 失败 → BeautifulSoup 直接抓取
         │                                    ├─ 成功 → 继续
         │                                    └─ 失败 → 搜索引擎绕行法
         └─ 失败/配额耗尽 → crwl（Crawl4AI）
                          ├─ 成功 → 继续
                          └─ 失败 → curl r.jina.ai
                                  ├─ 成功 → 继续
                                  └─ 失败 → 搜索引擎绕行法
                                          └─ 失败 → web_search 补充

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
