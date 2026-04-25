---
name: multi-search
description: 多源搜索降级工具包。环境能力探测 + 搜索/抓取降级链 + 双运行时适配（OpenClaw/Hermes）+ 三轮递进检索策略。不包含业务逻辑，作为其他 Skill 的搜索基础设施层。
skillcode: multi-search
homepage: https://github.com/evan-zhang/agent-factory
source: projects/2604251/multi-search
version: "1.0.0"
---

# multi-search

## 核心定位

本 Skill 是**搜索/抓取基础设施层**，为其他 Skill 提供标准化的多源搜索和页面抓取能力。

不做任何业务决策，不包含具体检索词或渠道模板。只负责三件事：
1. 探测环境能力（搜索/抓取/JS渲染）
2. 声明搜索降级策略和抓取降级策略
3. 提供环境初始化脚本和配置指南

## 当前版本

**`1.0.0`**（见 `version.json`）

## 能力概览

| 能力 | 说明 |
|------|------|
| 环境探测 | 自动检测运行时（OpenClaw/Hermes）、搜索工具可用性、抓取工具JS渲染能力 |
| 搜索降级链 | MiniMax → Tavily → Exa → web_fetch → 停止 |
| 抓取降级链 | 内置工具 → Jina Reader → Crawl4AI → curl → 标注缺口 |
| 检索策略 | 三轮递进：精准查询（site:）→ 泛搜补充 → 兜底来源 |
| 双运行时 | OpenClaw（mcporter MCP）/ Hermes（config.yaml 原生 MCP）|

## 搜索降级链

```
MiniMax web_search（中文语义强，主力）
 ↓ 失败/无结果/超时
Tavily search（通用搜索，回退）
 ↓ 失败/无结果
Exa AI（includeDomains 定向搜索，精准补充）
 ↓ 失败/不可用
web_fetch / curl（基础抓取）
 ↓ 失败
停止执行，标注缺口
```

### 切换触发条件

- 搜索返回 0 条结果 → 切换下一个引擎
- 搜索超时（>30s）→ 切换下一个引擎
- 搜索引擎不可用（未配置/未安装）→ 跳过
- 切换后需在来源明细中记录实际使用的引擎

### Exa 特殊能力

Exa 支持 `includeDomains` 精准定向搜索：
- `includeDomains: ["gov.cn"]` — 只搜官方网站
- `includeDomains: ["lanzhou.gov.cn"]` — 只搜某城市官网
- 适用于需要提高官方来源占比的场景

## 抓取降级链

### 统一降级链（双运行时）

```
Level 1: 内置工具（最快，零依赖）
 ├─ OpenClaw: web_fetch（不支持 JS 渲染）
 └─ Hermes: browser_navigate + browser_snapshot（支持 JS 渲染）
 ↓ 空壳/JS渲染页面/正文<200字
Level 2: Jina Reader（零安装，远程渲染）
 ↓ 失败/超时/不可用
Level 3: Crawl4AI CLI（本地浏览器，完整 JS 渲染）
 ↓ 未安装/失败
Level 4: curl 兜底（纯静态）
 ↓ 失败
标注缺口
```

### 各级别说明

| 级别 | 工具 | JS 渲染 | 安装要求 | 适用场景 |
|------|------|---------|----------|----------|
| L1 | web_fetch / browser | 视运行时 | 无 | 静态页面、Hermes 的所有页面 |
| L2 | Jina Reader | ✅ 远程 | 无 | JS 动态页面、gov.cn |
| L3 | Crawl4AI CLI | ✅ 本地 | pip install | 复杂页面、需要完整渲染 |
| L4 | curl | ❌ | 无 | 最后兜底 |

### 抓取成功判断标准

- HTTP 200 + 正文纯文本 > 200 字 → 成功
- HTTP 200 + 正文 < 200 字 → 可能是 JS 渲染页面，尝试下一级
- 非 200 / 超时 / 空白 → 尝试下一级

### Jina Reader 用法（L2）

```bash
curl -s "https://r.jina.ai/{URL}" -H "Accept: text/markdown"
```

### Crawl4AI 用法（L3）

```bash
# 安装
pip install -U crawl4ai && crawl4ai-setup

# 抓取
crwl "{URL}" -o markdown
```

## 检索策略：三轮递进

### 第一轮：精准查询

```
site:{目标域名} {关键词1} {关键词2} {年份}
```

- 使用 site: 限定到具体官方域名
- 每个指标至少 2 条不同查询
- 适合：已知目标网站，需要精准定位

### 第二轮：泛搜补充

```
{城市/主体} {关键词} {年份}
{城市/主体} {别名/简称} {关键词}
{省份/上级} {部门名} {关键词}
```

- 无 site: 限定，扩大搜索范围
- 加入城市别名、省份简称、部门别名等变体
- 适合：第一轮查不到或结果不完整

### 第三轮：兜底来源

```
site:{辅助来源域名} {关键词}
{城市}本地宝 {关键词}
```

- 辅助来源（本地宝等）作为最后兜底
- 必须在来源明细中标注来源类型（官方/辅助）
- 适合：官方来源确实不存在

### 降级规则

- 第一轮查不到 → 自动进第二轮
- 第二轮查不到 → 自动进第三轮
- 每轮每个指标至少 2 条查询，一条查不到不直接放弃
- 切换搜索引擎时从第一轮重新开始

## 环境初始化

使用 `scripts/setup-env.sh` 完成环境初始化：

```bash
# 基础初始化（交互式）
bash scripts/setup-env.sh

# 带 API Key 初始化（非交互式）
bash scripts/setup-env.sh --key sk-cp-j-xxx

# 指定 API Host
bash scripts/setup-env.sh --key sk-cp-j-xxx --host https://api.minimax.chat

# 环境变量方式
MINIMAX_API_KEY=sk-cp-j-xxx bash scripts/setup-env.sh
```

脚本会自动：
1. 检测运行时（OpenClaw / Hermes）
2. 检查/安装 uv（uvx）
3. 配置 MiniMax MCP（写入对应位置）
4. 验证搜索可用性
5. 探测 4 级抓取能力（内置 → Jina Reader → Crawl4AI → curl）
6. 输出完整工具清单

## 统一规范

- 真源：本 Skill 的 `references/*.md` 和 `scripts/`
- 配置指南：`docs/search-setup-guide.md`
- 日志：由调用方管理，本 Skill 不产生日志

## 在本流水线中的使用方式

本 Skill 不单独执行，作为基础设施被其他 Skill 引用：

1. 调用方在 SKILL.md 中声明：`依赖 multi-search Skill 的搜索/抓取能力`
2. 调用方在 references 中引用本 Skill 的降级策略
3. 执行前先运行 `scripts/setup-env.sh` 完成环境初始化
4. 调用方使用本 Skill 声明的搜索降级链和抓取降级链

## 路由与加载规则

| 用户意图 | 模块 | 说明 |
|----------|------|------|
| 初始化搜索环境 | setup | `./scripts/setup-env.sh` |
| 查看配置指南 | docs | `./docs/search-setup-guide.md` |
| 理解降级策略 | references | `./references/search-fallback.md` + `./references/fetch-fallback.md` |

## 宪章

- **不**包含任何业务逻辑（检索词、渠道模板、指标映射）
- **不**自行安装 Playwright/Jina Reader 等重量级抓取工具（等运行时内置）
- **不**做政策裁决或内容判断
- **不**修改调用方的 state.json 或输出文件
- 来源类型和可信度由调用方判断，本 Skill 只提供工具

## 目录结构

```text
multi-search/
├── SKILL.md
├── version.json
├── docs/
│   └── search-setup-guide.md
├── references/
│   ├── search-fallback.md
│   ├── fetch-fallback.md
│   └── search-strategy.md
└── scripts/
    └── setup-env.sh
```
