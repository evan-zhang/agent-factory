# Link Archivist v1.3.0 完整工作流程

> 版本：v1.3.0
> 日期：2026-04-15
> 基于：Link Archivist Skill 文档

---

## 概述

Link Archivist 是一个用于对链接、文件或文本内容进行抓取、调研并生成报告的 Skill。

**输入类型**：YouTube 链接、通用 URL、文件、粘贴文本
**输出类型**：完整调研报告（full）或短摘要（short）
**核心能力**：抓取 → 判断模式 → 调研 → 生成报告 → 归档本地

---

## 阶段 0：初始化（首次使用）

Agent 启动后，先执行配置检测：

```bash
python3 scripts/init_config.py
```

返回结果：
- `{"ok": true, "configured": true}` → 配置就绪，进入阶段 1
- `{"ok": true, "configured": false, "hints": [...]}` → 引导用户配置

**配置文件**（按环境自动选择路径）：

| 环境 | 路径 |
|------|------|
| OpenClaw | `~/.openclaw/link-archivist-config.json` |
| Hermes | `~/.hermes/link-archivist-config.json` |
| 其他 | `~/.config/link-archivist-config.json` |

**配置字段**：

| 字段 | 必需 | 说明 |
|------|------|------|
| `archive_dir` | 是 | 知识库存储目录 |
| `xgjk_app_key` | 否 | AI 慧记转录密钥（用于 YouTube 视频转字幕）|
| `tavily_api_key` | 否 | Tavily 搜索密钥（提升报告质量）|

**配置文件示例**：
```json
{
  "archive_dir": "/path/to/knowledge-base",
  "xgjk_app_key": "your-key-here",
  "tavily_api_key": "your-tavily-key-here"
}
```

---

## 阶段 1：输入判断

```
用户消息
 ├─ 包含 URL/链接 → 阶段 2a（链接类型判断）
 ├─ 包含文件     → 阶段 2b（文件解析）
 ├─ 纯文本粘贴   → 直接跳阶段 3（决定模式）
 └─ 未初始化     → 引导配置
```

---

## 阶段 2a：链接抓取（按类型分支）

### 分支 A：YouTube 链接

> AI 读取：`references/youtube-workflow.md`

```
YouTube 链接
 │
 ├─ Step 1：获取基本信息
 │   → 首选：yt-dlp --print title --print duration --print uploader <URL>
 │   → 备用（JS Runtime 问题）：YouTube oEmbed API
 │       import requests
 │       r = requests.get('https://www.youtube.com/oembed',
 │                         params={'url': '<URL>', 'format': 'json'})
 │       → 获取标题 + 作者（无法获取时长）
 │
 ├─ Step 2：展示给用户，确认是否处理
 │   → "检测到视频：《标题》，时长 X 分钟，频道 XXX。是否处理？"
 │   → 用户选择否 → 结束
 │
 └─ Step 3：字幕提取
     │
     ├─ 方案 1：youtube_subtitle.py（优先）
     │   python3 scripts/youtube_subtitle.py "<URL>"
     │   → 成功 → 拿到字幕文本 → 跳 Step 5
     │   → 失败（no element found）→ 方案 2
     │
     ├─ 方案 2：yt-dlp 字幕降级
     │   yt-dlp --write-subs --sub-lang zh --skip-download "<URL>"
     │   → 成功 → Step 4
     │   → 失败 → Step 6（无字幕分支）
     │
     ├─ Step 4：解析 VTT 字幕
     │   跳过 WEBVTT 头部、元数据行、时间戳行
     │   只提取纯文本内容
     │   → 跳阶段 3
     │
     └─ Step 5：无字幕时的决策
         │ 时长 < 5 分钟 → 可直接总结
         │ 时长 5-15 分钟 → 询问用户是否转录
         └─ 时长 > 15 分钟 → 询问用户是否转录
             │
             ├─ 用户选择转录 → transcribe_audio.py（需 xgjk_app_key）
             └─ 用户选择不转录 → 只用标题+描述，跳阶段 3
```

### 分支 B：GitHub 链接

```
GitHub 链接
 │
 ├─ Step 1：r.jina.ai 抓取 README
 │   curl -sL https://r.jina.ai/{url}
 │   → 成功 → 跳阶段 3
 │   → 失败 ↓
 │
 └─ Step 2：GitHub API 备用
     # 读取 README（base64 编码）
     curl -sL https://api.github.com/repos/<owner>/<repo>/readme
     → 跳阶段 3
```

### 分支 C：通用网页

> 包含今日头条、博客、新闻等

```
通用 URL
 │
 ├─ Step 1：r.jina.ai 抓取
 │   curl -sL https://r.jina.ai/{url}
 │   → 成功 → 跳阶段 3
 │   → 失败（返回空内容）↓
 │
 ├─ Step 2：BeautifulSoup 降级
 │   # 适用：今日头条移动端（m.toutiao.com/is/xxx）
 │   import requests
 │   from bs4 import BeautifulSoup
 │   url = '<目标URL>'
 │   headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)...'}
 │   r = requests.get(url, headers=headers, timeout=10)
 │   soup = BeautifulSoup(r.text, 'html.parser')
 │   article = soup.find('article')
 │   → 成功 → 跳阶段 3
 │   → 失败 ↓
 │
 └─ Step 3：web_search 兜底
     搜索关键信息
     → 跳阶段 3
```

---

## 阶段 2b：文件输入

```
收到文件（PDF/Word/PPT/图片等）
 │
 └─ 调用外部解析工具提取文本
     → 成功 → 阶段 3
     → 失败 → 提示用户"无法解析此文件格式，请粘贴正文"
```

---

## 阶段 3：决定模式

> AI 读取：`references/decision-rules.md`

调用 `scripts/decide_mode.py`：

```bash
# 快速判断（URL）
python3 scripts/decide_mode.py "https://example.com"

# 深度判断（传入抓取内容）
python3 scripts/decide_mode.py "https://example.com" --content "<抓取到的内容>"
```

**两阶段判断机制：**

### 阶段 3-1：快速判断（无需抓取内容）

| 来源/关键词 | 结果 |
|------------|------|
| YouTube / GitHub 链接 | → full |
| 用户说"详细看看" | → full |
| 用户说"简单说" | → short |
| Full 关键词命中 | → full |
| Short 关键词命中 | → short |
| 都不满足 | → 阶段 3-2 |

**Full 关键词**：github, star, 开源, 框架, 论文, Agent, LLM, 大模型, 深度, 分析, 评测, architecture, benchmark...

**Short 关键词**：news, 新闻, 热点, 快讯, 公告, 更新, 观点...

### 阶段 3-2：内容判断（需要抓取后分析）

| 条件 | 结果 |
|------|------|
| full 关键词 ≥ 2 个 | → full |
| short 关键词 ≥ 1 个 | → short |
| full 关键词 ≥ 1 个 | → full |
| 都不满足 | → ask（问用户）|

### 三种模式

| 模式 | 触发条件 | 输出 |
|------|----------|------|
| `full` | YouTube/GitHub 或 full 关键词命中 | 完整调研报告 |
| `short` | Short 关键词命中 | 2-3 句话摘要 |
| `ask` | 不确定 | 问用户 |

---

## 阶段 4：执行调研（full 模式）

> AI 读取：`references/survey-methodology.md`

### 4.1 内容分析

分析已抓取的内容，判断类型：

| 内容类型 | 处理方式 |
|----------|----------|
| 开源项目介绍 | 重点分析架构、技术栈、团队背景 |
| 新闻/资讯 | 提取关键信息，不写长报告 |
| 教程/讲解 | 提取步骤，可操作执行 |
| 对比分析 | 重点做对比表格 |
| 观点/评论 | 记录观点，不做深度分析 |

### 4.2 信息补充与交叉验证

#### 4.2.1 开源项目：GitHub API 优先

```bash
# 搜索仓库（按 Star 数排序）
curl -sL "https://api.github.com/search/repositories?q=<项目名>&sort=stars"

# 读取 README
curl -sL "https://api.github.com/repos/<owner>/<repo>/readme"
```

获取：Star 数、描述、更新时间、README 全文。

#### 4.2.2 通用内容：Web Search 交叉验证

**搜索策略：**

| 内容类型 | 搜索词 |
|----------|--------|
| 开源项目 | `<项目名> GitHub <功能关键词> 2026` |
| 新闻事件 | `<项目名> 最新 2026` |
| 融资/公司 | `<公司名> 融资 投资 2026` |

**必须验证的数据：**
- Star 数 / 用户数 / 融资额
- 投资方、金额、轮次
- 创始人背景、公司历史

#### 4.2.3 Web Search 降级链

```
OpenClaw web_search（Perplexity，直接可用）
 → 失败 ↓
tavily_search.py（需配置 tavily_api_key）
 → 失败 ↓
session_search 搜历史会话
 → 失败 ↓
跳过搜索，报告中注明"未进行交叉验证"
```

### 4.3 生成报告

按 `references/report-template.md` 格式输出，包含：
- 概述、核心功能/架构
- 技术栈、关键数据
- 对比分析、应用场景
- 局限性、个人洞察

---

## 阶段 5：生成洞察

> full 模式专属，short 模式跳过

```
Step 1：session_search 搜相关历史会话
Step 2：read_index 搜本地知识库文件
Step 3：结合两者动态生成个性化洞察
        写入报告的"个人洞察"栏目
```

---

## 阶段 6：归档本地

调用 `scripts/archive_report.py`：

```bash
# 位置参数
python3 scripts/archive_report.py <content_file> <archive_dir> [title]

# 命名参数（等效）
python3 scripts/archive_report.py --file <content_file> --title "标题"
```

**归档结果示例：**

```
{archive_dir}/
└── 2026-04-15/
    └── K-260415-001-项目名称.md
```

**编号规则**：`K-YYMMDD-NNN`
- YYMMDD：建档日期
- NNN：当日序号（每日从 001 开始，自动取最大 +1）

---

## 阶段 7：结束

报告已归档，流程结束。

Agent 可选择将摘要发送到目标渠道（发送不属于 Skill 职责，由 Agent 自行决定）。

---

## 降级策略速查

### YouTube 字幕提取

| 优先级 | 方案 | 触发条件 |
|--------|------|----------|
| 1st | `youtube_subtitle.py` | 首选方案 |
| 2nd | `yt-dlp --write-subs --sub-lang zh --skip-download` | youtube_subtitle.py 失败 |
| 3rd | 抓标题+描述，跳过转录 | yt-dlp 也失败 |
| 4th | 询问用户是否下载视频转录 | 用户主动要求 |

### Web Search

| 优先级 | 方案 | 触发条件 |
|--------|------|----------|
| 1st | OpenClaw `web_search` | Perplexity API，直接可用 |
| 2nd | `python3 scripts/tavily_search.py` | 配置了 tavily_api_key |
| 3rd | `session_search` 搜历史会话 | Tavily 不可用 |
| 4th | 跳过，报告中注明"未进行交叉验证" | 全部不可用 |

### 音频转录

| 优先级 | 方案 | 触发条件 |
|--------|------|----------|
| 1st | `transcribe_audio.py` | 配置了 xgjk_app_key |
| 2nd | 跳过转录，只用标题+描述 | 未配置 key |

### 网页抓取

| 优先级 | 方案 | 触发条件 |
|--------|------|----------|
| 1st | `curl -sL https://r.jina.ai/{url}` | 通用方案 |
| 2nd | BeautifulSoup + requests 直接抓取 | jina.ai 返回空 |
| 3rd | `web_search` 搜索关键信息 | 全部失败 |

---

## 决策树

```
输入是 URL？
 ├─ YES
 │   ├─ YouTube？
 │   │   └─ YES → 获取基本信息 → 询问用户 → 字幕提取 → 有/无字幕分支
 │   ├─ GitHub？
 │   │   └─ YES → r.jina.ai → GitHub API 备用 → 阶段 3
 │   └─ 其他？
 │       └─ YES → r.jina.ai → BeautifulSoup → web_search → 阶段 3
 └─ NO
     ├─ 文件？ → 外部解析 → 阶段 3
     ├─ 文本？ → 直接阶段 3
     └─ 未初始化？ → 引导配置

模式判断（阶段 3）
 ├─ full → 执行调研 → 生成洞察 → 归档
 ├─ short → 短摘要 → 归档
 └─ ask → 询问用户
```

---

## 文件索引

| 文件 | 内容 |
|------|------|
| SKILL.md | 主文档（110 行，核心流程骨架） |
| references/youtube-workflow.md | YouTube 详细处理流程 |
| references/survey-methodology.md | 调研方法论（full 模式执行细节）|
| references/degradation-rules.md | 完整降级策略 |
| references/decision-rules.md | 模式判断规则 |
| references/report-template.md | 报告模板（full + short）|
| references/archive-template.md | 归档目录结构和编号规则 |
| references/faq.md | 常见问题与处理 |
| scripts/init_config.py | 配置检测 |
| scripts/decide_mode.py | 模式判断 |
| scripts/youtube_subtitle.py | YouTube 字幕提取 |
| scripts/tavily_search.py | Tavily 搜索 |
| scripts/archive_report.py | 归档脚本 |

---

*文档版本：v1.3.0 | 最后更新：2026-04-15*
