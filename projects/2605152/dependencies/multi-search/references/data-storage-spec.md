# 数据落盘规范

## 设计原则

multi-search 是基础设施层，**不持有业务数据**，只定义存储规范。
所有搜索/抓取数据落盘到**调用方项目目录**。

## 存储位置

```
{调用方项目根目录}/
└── _data/
    └── multi-search/
        └── {session-id}/                # 每次采集会话
            ├── session.json             # 会话元数据
            ├── search/                  # 搜索结果
            │   ├── S-{seq}-{engine}.json
            │   └── ...
            └── fetch/                   # 抓取结果
                ├── F-{seq}-{domain}.md
                ├── F-{seq}-{domain}.meta.json
                └── ...
```

### session-id 生成规则

格式：`{YYYYMMDD}-{HHmmss}-{4位随机字符}`

示例：`20260425-214500-a3f2`

### 路径参数

| 参数 | 来源 | 示例 |
|------|------|------|
| 调用方项目根目录 | 调用方传入，或从 cwd 推断 | `projects/2604011/` |
| session-id | 首次搜索时自动生成 | `20260425-214500-a3f2` |

## session.json — 会话元数据

```json
{
  "sessionId": "20260425-214500-a3f2",
  "runtime": "openclaw",
  "createdAt": "2026-04-25T21:45:00+08:00",
  "closedAt": null,
  "stats": {
    "searchCount": 12,
    "fetchCount": 8,
    "fetchSuccess": 6,
    "fetchPartial": 1,
    "fetchFailed": 1
  },
  "engines": ["minimax", "jina", "crawl4ai"],
  "config": {
    "searchFallback": ["minimax", "tavily", "exa"],
    "fetchFallback": ["web_fetch", "jina", "crawl4ai", "curl"]
  }
}
```

## 搜索结果 — search/ 目录

### 文件命名

`S-{seq}-{engine}.json`

- seq：3 位顺序号，从 001 开始
- engine：实际使用的搜索引擎（minimax / tavily / exa / web_fetch）

示例：`S-001-minimax.json`、`S-002-tavily.json`

### 文件内容

```json
{
  "refId": "S-20260425-214500-a3f2-001",
  "timestamp": "2026-04-25T21:45:01+08:00",
  "engine": "minimax",
  "fallbackLevel": 0,
  "previousEngine": null,
  "query": {
    "text": "site:gov.cn 深圳 2026 落户政策",
    "round": 1,
    "strategy": "精准查询",
    "includeDomains": null
  },
  "results": [
    {
      "index": 1,
      "title": "深圳市户籍迁入若干规定",
      "url": "https://www.sz.gov.cn/...",
      "snippet": "...",
      "date": "2026-03-15",
      "fetchStatus": "pending"
    }
  ],
  "meta": {
    "totalResults": 5,
    "responseTime": 1200,
    "engineRawResponse": null
  }
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| refId | ✅ | 唯一引用ID，举证时用 |
| engine | ✅ | 实际使用的引擎 |
| fallbackLevel | ✅ | 降级层级（0=主力，1=第一次降级...） |
| previousEngine | 降级时有值 | 上一个失败的引擎 |
| query.text | ✅ | 原始查询词 |
| query.round | ✅ | 第几轮（1=精准，2=泛搜，3=兜底） |
| query.strategy | ✅ | 检索策略名 |
| results[].fetchStatus | ✅ | pending / fetched / failed / skipped |

## 抓取结果 — fetch/ 目录

### 文件命名

`F-{seq}-{domain}.md`（正文）
`F-{seq}-{domain}.meta.json`（元数据）

- seq：3 位顺序号，从 001 开始（独立于搜索序号）
- domain：URL 主域名，去掉特殊字符

示例：`F-001-sz.gov.cn.md`、`F-001-sz.gov.cn.meta.json`

### 正文文件（.md）

```markdown
# {页面标题}

> 来源：{完整URL}
> 抓取时间：{ISO时间}
> 抓取工具：{工具名}
> 引用ID：F-{session}-{seq}

---

{页面正文内容，Markdown 格式}
```

### 元数据文件（.meta.json）

```json
{
  "fetchId": "F-20260425-214500-a3f2-001",
  "sourceRefId": "S-20260425-214500-a3f2-001",
  "sourceIndex": 1,
  "timestamp": "2026-04-25T21:45:05+08:00",
  "url": "https://www.sz.gov.cn/...",
  "domain": "sz.gov.cn",
  "tool": "jina",
  "fallbackLevel": 1,
  "status": "success",
  "contentLength": 3520,
  "responseTime": 3200,
  "pageTitle": "深圳市户籍迁入若干规定",
  "publishedDate": "2026-03-15",
  "previousTool": "web_fetch",
  "previousFailReason": "正文 < 200 字，疑似 JS 渲染页面"
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| fetchId | ✅ | 唯一引用ID，举证时用 |
| sourceRefId | ✅ | 关联的搜索结果 refId |
| sourceIndex | ✅ | 关联搜索结果中的第几条 |
| tool | ✅ | 实际使用的抓取工具 |
| status | ✅ | success / partial / failed |
| contentLength | ✅ | 正文纯文本字数 |
| previousTool | 降级时有值 | 上一个失败的工具 |
| previousFailReason | 降级时有值 | 上一步失败原因 |

### status 含义

| status | 条件 |
|--------|------|
| success | 正文 > 200 字，内容完整 |
| partial | 正文 50-200 字，内容不完整 |
| failed | 正文 < 50 字或抓取异常 |

失败时 .md 文件仍然生成，正文写失败原因和已尝试的降级链。

## 证据链追溯

举证时的完整链路：

```
举证项（调用方矩阵）
  → fetchId: F-{session}-001
    → fetch/001-sz.gov.cn.md（页面正文）
    → fetch/001-sz.gov.cn.meta.json（抓取证词：何时、用什么工具、什么状态）
  → sourceRefId: S-{session}-001
    → search/001-minimax.json（搜索证词：搜了什么词、哪个引擎、第几轮）
```

每一条证据都能回答：
1. 搜了什么？→ query.text
2. 在哪搜的？→ engine
3. 搜到了什么？→ results
4. 打开了哪个页面？→ url
5. 什么时候抓的？→ timestamp
6. 用什么工具抓的？→ tool
7. 抓到了什么？→ .md 正文
8. 抓取质量如何？→ status + contentLength

## 调用方使用方式

multi-search skill 不直接写文件，由调用方 Agent 按此规范落盘：

1. 搜索前：创建 `_data/multi-search/{session-id}/` 目录和 `session.json`
2. 每次搜索后：写入 `search/S-{seq}-{engine}.json`
3. 每次抓取后：写入 `fetch/F-{seq}-{domain}.md` + `.meta.json`
4. 更新 `search/` 中对应结果的 `fetchStatus`
5. 会话结束时：更新 `session.json` 的 `stats` 和 `closedAt`

## .gitignore

`_data/` 目录应加入调用方项目的 `.gitignore`，搜索数据不上传 GitHub。
