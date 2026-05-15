# 抓取降级链

## 设计原则

1. **零安装优先**：不需要额外安装的工具排前面
2. **双运行时兼容**：OpenClaw 和 Hermes 各自有独立的首选工具，但降级链共享中间层
3. **重量递增**：轻量工具先试，重量级工具放后面
4. **成本递增**：免费工具先试，付费工具放后面

## 降级链总览

```
Level 1: 内置工具（最快，零依赖）
 ├─ OpenClaw: web_fetch
 └─ Hermes: browser_navigate + browser_snapshot
 ↓ 空壳/JS渲染页面/正文<200字
Level 2: Jina Reader（零安装，远程渲染）
 ↓ 失败/超时/不可用
Level 3: Crawl4AI CLI（本地浏览器，完整 JS 渲染）
 ↓ 未安装/失败
Level 4: curl 兜底（纯静态）
 ↓ 失败
标注缺口
```

**不纳入的方案及原因**：
- ~~Playwright 原生~~：Crawl4AI 已内置 Playwright，且提供 CLI + Markdown 输出，比裸 Playwright 更适合 Agent 调用
- ~~Firecrawl API~~：Crawl4AI 开源版已覆盖其核心能力（JS 渲染 + Markdown 输出），且无需付费 API Key
- ~~远程 Claude Code~~：依赖特定基础设施（SSH + 远程机器），不具备通用性。如果将来有需要可以作为特定项目的扩展，不放进基础层

## 按运行时的降级链

### OpenClaw 环境

```
web_fetch（内置工具，静态抓取）
 ↓ 空壳/JS渲染页面/正文<200字
Jina Reader（远程渲染，零安装）
 ↓ 失败/超时
Crawl4AI CLI（本地浏览器，完整 JS 渲染）
 ↓ 未安装/失败
curl（纯静态兜底）
 ↓ 失败
标注「JS渲染失败」→ 记录在缺口表
```

**已知限制**：OpenClaw 的 web_fetch 不支持 JS 渲染。遇到动态页面（gov.cn 等）会拿到空壳。等 OpenClaw 内置浏览器后补齐。

### Hermes 环境

```
browser_navigate + browser_snapshot（内置浏览器，支持 JS 渲染）
 ↓ 失败
Jina Reader（远程渲染，轻量补充）
 ↓ 失败
Crawl4AI CLI（本地浏览器）
 ↓ 未安装/失败
curl（静态兜底）
 ↓ 失败
标注「页面无法抓取」→ 记录在缺口表
```

**Hermes 优势**：内置 browser 工具支持 JS 渲染，Level 1 命中率更高。Jina Reader 和 Crawl4AI 作为补充。

## 各级别详细说明

### Level 1: 内置工具

| 运行时 | 工具 | JS 渲染 | 速度 |
|--------|------|---------|------|
| OpenClaw | web_fetch | ❌ | 快（<2s）|
| Hermes | browser_navigate + browser_snapshot | ✅ | 中（2-5s）|

判断：HTTP 200 + 正文纯文本 > 200 字 → 成功，否则进入 Level 2。

### Level 2: Jina Reader

零安装、零成本、远程 JS 渲染。

```bash
# 基础抓取
curl -s "https://r.jina.ai/{URL}" -H "Accept: text/markdown"

# 判断成功：HTTP 200 + 正文 > 200 字
```

优势：`curl` 即可调用，无需安装任何依赖。
限制：需要网络可达 `r.jina.ai`，某些环境可能需要代理。

### Level 3: Crawl4AI CLI

开源（64k+ stars），内置 Playwright + 自动 JS 渲染 + LLM 友好 Markdown 输出。

```bash
# 安装
pip install -U crawl4ai
crawl4ai-setup  # 首次安装浏览器

# CLI 抓取
crwl "{URL}" -o markdown

# 判断成功：输出正文 > 200 字
```

优势：
- 完整 JS 渲染（内置 Playwright，不需要单独装）
- 输出干净的 Markdown，无需额外清理
- CLI 调用，适合 Agent 通过 exec 调用
- 反爬虫检测 + Shadow DOM 支持（v0.8.5+）
- 完全离线可用，不依赖外部服务

限制：需要安装（~200MB Chromium），首次 `crawl4ai-setup` 较慢。

### Level 4: curl 兜底

```bash
curl -sL --max-time 15 "{URL}"
```

纯静态抓取，最后防线。

## 抓取成功判断标准

| 判断 | 条件 | 动作 |
|------|------|------|
| 成功 | HTTP 200 + 正文纯文本 > 200 字 | 采集内容 |
| 可能是 JS 渲染页面 | HTTP 200 + 正文 < 200 字 | 尝试下一级 |
| 失败 | 非 200 / 超时 / 空白 / 403 | 尝试下一级 |
| 全部失败 | 所有级别都失败 | 标注缺口原因 |

## 来源记录要求

每条抓取结果必须记录：
- 实际使用的抓取工具（web_fetch / jina / crawl4ai / curl / browser）
- 抓取结果状态（完整/部分/JS渲染失败）
- 页面标题
- 完整 URL
- URL 可访问性验证结果
- 发布日期或更新时间（如有）
- 抓取时间

## 哪些内容不能当来源

- 搜索引擎摘要（未经打开页面）
- 未实际打开的 URL
- 404 / 错误页 / 空白页 / 登录拦截页
- JS 渲染失败拿到的空壳

## 可选扩展：远程 Claude Code（非标准层）

利用已有远程 Claude Code 环境（SSH 可达的 Mac Studio），通过 Claude Code 的 MCP browser/web-reader 工具实现 JS 渲染 + AI 内容理解。

**为什么不放进标准降级链**：依赖特定基础设施（SSH + 远程机器 + Claude Code），不具备通用性。

**什么时候用**：
- 标准降级链全部失败时，作为最后手段
- 页面需要 AI 理解内容（不只是抓文本，还需要提取结构化信息）
- 已有 SSH 可达的 Claude Code 环境

**用法**：
```bash
# 通过 SSH 调用远程 Claude Code
ssh user@remote-host "claude --print --dangerously-skip-permissions \
  --max-turns 2 \
  '请使用你的 web reader 工具抓取以下页面的完整内容：{URL}'"
```

**配置要求**：
- SSH 可达的远程机器
- 远程机器已安装 Claude Code CLI + MCP 工具链
- `sshpass` 或 SSH Key 认证

**能力探测**：
```bash
if ssh -o ConnectTimeout=5 user@host "which claude" 2>/dev/null; then
    ok "可选扩展：远程 Claude Code 可用"
fi
```

**优缺点**：
- ✅ 完整 JS 渲染 + AI 理解，能处理任何页面
- ✅ 已有基础设施，零额外成本
- ❌ 延迟较高（5-15s）
- ❌ 依赖远程服务可用性
- ❌ 并发受限

## 缺口标注格式

当抓取失败时，在缺口表中记录：

```
缺口原因：JS渲染失败 / 页面无法打开 / 内容不明确 / 其他
已尝试工具：web_fetch → jina → crawl4ai → curl
已尝试 URL：https://xxx.gov.cn/...
失败原因：HTTP 200 但正文 < 50 字，疑似 JS 渲染页面
```
