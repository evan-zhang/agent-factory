# P0 候选深度调研报告

> 调研日期：2026-06-06
> 目标：评估三个候选方案的工程成熟度、MCP 工具集、免费可用性、与 multi-search 兼容性

---

## 1. zero-api-key-web-search（原 free-web-search-ultimate）

| 项目 | 内容 |
|------|------|
| **仓库** | [wd041216-bit/zero-api-key-web-search](https://github.com/wd041216-bit/zero-api-key-web-search) |
| **安装** | `pip install zero-api-key-web-search` |
| **MCP 启动** | `zero-mcp`（独立命令） |
| **运行时** | Python（非 uvx，但可装到环境后调用） |
| **Stars** | 较新但文档完善，含 OpenClaw skill |

### 引擎

| 路径 | 引擎 | 费用 | 配置 |
|------|------|------|------|
| Free | DuckDuckGo | 免费，零配置 | 默认即可 |
| Free + 验证 | SearXNG（自托管） | 免费 + 自建服务 | `./scripts/start-searxng.sh` |
| Production | Bright Data SERP（7引擎） | 5000次免费额度后付费 | `zero-setup` 向导 |
| Production+ | Bright Data + Web Unlocker | 同上 + 附加费 | 同上 |

可选的 Bright Data 引擎：`google`, `bing`, `duckduckgo`, `yandex`, `baidu`, `yahoo`, `naver`

### MCP 工具（8个）

| 工具 | 功能 |
|------|------|
| `list_providers` | 显示 provider 状态、profiles、goggles、配置提示 |
| `search_web` | 实时搜索，支持引擎选择 + 地区定位 |
| `llm_context` | 紧凑的带引用 Markdown 上下文（LLM 优化） |
| `browse_page` | 提取页面内容，自动解锁被屏蔽页面 |
| `verify_claim` | 评估声明是否被支持/争议/证据不足 |
| `evidence_report` | 完整证据报告 + 来源摘要 + 下一步建议 |
| `clear_cache` | 清除响应缓存 |
| `setup_providers` | 检查 provider 状态、测试 API Key |

### 亮点

- **证据验证引擎**：内置 claim verification，支持来源分类（支持/冲突/中立）
- **Goggles 预设**：`docs-first`（文档优先）、`research`（学术优先）、`news-balanced`
- **多平台 skill**：Claude Code、Gemini、Cursor、Copilot、Codex、OpenClaw 等
- **OpenClaw 适配**：项目内自带 `zero_api_key_web_search/skills/SKILL.md`
- **CLI 工具**：`zero-search`, `zero-context`, `zero-browse`, `zero-verify`, `zero-report`, `zero-setup`
- **Provider Profiles**：`free` → `free-verified` → `production` → `production-unlock` → `max-evidence`

### 问题

- **pip 安装**，不是 uvx，需要先 pip install 再调用 `zero-mcp`
- 免费的 DuckDuckGo 引擎可能被限速（需 `zero-setup` 向导配置 Bright Data 才稳定）
- **依赖较重**（包较大，有验证引擎+爬取+unlocker）
- **免费模式只 DuckDuckGo**，其他免费引擎需要自建 SearXNG

---

## 2. heventure-search-mcp

| 项目 | 内容 |
|------|------|
| **仓库** | [HughesCuit/heventure-search-mcp](https://github.com/HughesCuit/heventure-search-mcp) |
| **安装** | `pip install heventure-search-mcp` 或 `uvx heventure-search-mcp` |
| **MCP 启动** | `uvx heventure-search-mcp`（原生 uvx 支持） |
| **运行时** | Python 3.10+，asyncio |
| **Stars** | 社区较新，文档简洁 |

### 引擎

| 引擎 | 费用 | 是否需要配置 |
|------|------|-------------|
| DuckDuckGo | 免费 | 零配置 |
| Bing | 免费 | 零配置 |
| Google | 免费 | 零配置 |
| SerpAPI（可选） | 100次/月免费 | `export SERPAPI_KEY=xxx` |
| Tavily（可选） | 1000次/月免费 | `export TAVILY_API_KEY=xxx` |

### MCP 工具（2个）

| 工具 | 参数 | 说明 |
|------|------|------|
| `web_search` | `query`, `max_results`(1-20), `search_engine`(duckduckgo/bing/google/both) | 多引擎搜索 |
| `get_page_content` | `url` | 提取页面可读文本 |

### 内置工程特性

- **LRU 缓存**：100 条条目，300s TTL
- **自动限速**：内置 rate limiting
- **多语言支持**：`README_CN.md` 有中文文档
- **Docker 支持**：`docker run -p 8080:8080 heventure-search-mcp`

### 评价

- 最大的亮点是**三个免费引擎（DuckDuckGo + Bing + Google）零配置可用**，且天然支持 `uvx`
- 但只有 2 个 MCP 工具，功能相对单薄
- 免费的 Google 搜索非官方 API，稳定性可能不如 Brave 官方

---

## 3. brave-search-mcp-server

| 项目 | 内容 |
|------|------|
| **仓库** | [brave/brave-search-mcp-server](https://github.com/brave/brave-search-mcp-server) |
| **安装** | `npx -y @brave/brave-search-mcp-server`（NPX）或 Docker |
| **MCP 启动** | `npx -y @brave/brave-search-mcp-server` |
| **运行时** | Node.js / TypeScript |
| **维护方** | Brave 官方 |
| **许可证** | MIT |

### 费用

| 方案 | 免费额度 | 费用 |
|------|---------|------|
| Free Plan | 2000 次/月 | 免费 |
| Pro Plan | 按量 | 付费 |

Key 获取：https://brave.com/search/api/

### MCP 工具（8个）

| 工具 | 功能 |
|------|------|
| `brave_web_search` | 网页搜索，支持 country/语言/时间/结果过滤/拼写检查/safesearch/goggles |
| `brave_local_search` | 本地商家/地点搜索（Pro 完整，Free 降级为 web） |
| `brave_video_search` | 视频搜索，含元数据 + 缩略图 |
| `brave_image_search` | 图片搜索（v2 不再返回 base64，仅 URL） |
| `brave_news_search` | 新闻搜索，默认过去24小时，支持 breaking news |
| `brave_summarizer` | AI 总结：先用 web_search 的 summary 参数，再用返回的 key 生成总结 |
| `brave_place_search` | 地点搜索（经纬度/地名 + 半径） |
| `brave_llm_context` | LLM 优化内容：token 控制、snippet 数量、URL 数量、缓存策略，适合 RAG |

### 亮点

- **官方维护**：Brave 公司官方 MCP Server，v1→v2 有明确的 Migration 文档
- **工具最丰富**：8 个工具，覆盖搜索/本地/图片/视频/新闻/AI总结/LLM上下文
- **LLM Context 工具**：内置 token 预算控制、snippet 数量限制、source metadata 增强
- **AI Summarizer**：搜索结果可一键 AI 总结（类似 Perplexity 的效果）
- **Free Plan 2000次/月**：个人使用绰绰有余
- **Docker 部署支持**

### 问题

- **需要 API Key**（免费注册即可，2000次/月）
- **无中文优化**：默认 search_lang=en，兼容性不如 MiniMax
- **NPX 安装**：依赖 Node.js 环境（本地已有）

---

## 三个方案对比

| 维度 | zero-api-key-web-search | heventure-search-mcp | brave-search-mcp |
|------|:----------------------:|:-------------------:|:----------------:|
| 安装复杂度 | 中（pip + 包大） | **低**（uvx 一行） | **低**（npx 一行） |
| 免费引擎数 | 1/1（DDG/SearXNG） | **3**（DDG+Bing+Google） | 1（Brave 需 key） |
| 零配置免费 | ✅ DDG | ✅ DDG+Bing+Google | ❌ 需要 API Key |
| AI 增强 | ✅ 验证+报告 | ❌ | ✅ Summarizer+LLM |
| MCP 工具数 | 8 | **2** | **8** |
| 中文支持 | 有 Baidu（付费） | 中（Bing 中文还行） | 弱（默认英文） |
| 多平台 skill | ✅ 最多 | ❌ | ❌ |
| 官方维护 | ❌ 个人 | ❌ 个人 | ✅ Brave 官方 |
| 自托管选项 | ✅ SearXNG | ❌ | ❌ |
| 挂载复杂度 | 高（需 pip+CLI） | **低**（uvx） | **低**（npx） |
| 整体成熟度 | 功能最强但重 | 轻量但功能少 | **均衡 + 官方** |

---

## 初步结论

### 如果做主力搜索回退（替换 MiniMax）
**brave-search-mcp** 最佳。官方维护、免费 2000 次/月、工具集完整、有 AI Summarizer + LLM Context。挂载到 mcporter 即可。

### 如果要零成本多引擎
**heventure-search-mcp** 最佳。`uvx` 一行安装，三个免费引擎（DDG+Bing+Google）零配置可用。虽然只有 2 个工具，但作为降级链中的一环足够。

### 如果要做证据验证 + 深度分析
**zero-api-key-web-search** 最强，但安装和维护成本也最高。适合作为独立分析工具而非搜索降级链的一环。
