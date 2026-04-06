# Corrections Log

> Orchestrator 犯的错误和修正记录。每条记录必须包含时间戳和具体情境。

---

## 最近修正（按时间倒序）

## [2026-04-06] 外部文档获取方式错误 - 使用 web_search 而不是 curl

**情境**：
用户要求检查 CWork Skill 的 API 规范是否与官方文档一致。我使用了 web_search 和 web_fetch 工具，但这些工具被阻止或无法获取完整内容。

**错误**：
1. 使用 web_search/web_fetch 而不是直接用 curl 获取官方文档
2. 依赖可能被阻止的工具，导致无法获取权威信息
3. 违反了"外部文档引用原则"中关于优先用 curl 的要求

**修正**：
1. 改用 curl 直接获取官方 GitHub 文档
2. 成功获取 `https://github.com/xgjk/dev-guide/raw/main/02.产品业务AI文档/工作协同/工作协同API说明.md`
3. 对比发现 SKILL.md 中"API 端点概览"表1完全错误

**发现的问题**：
- 搜索员工：SKILL.md 说 `/open-api/employee/simpleList`，官方是 `/cwork-user/searchEmpByName`
- 收件箱：SKILL.md 说 `/open-api/work-report/inbox/pageList`，官方是 `/work-report/report/record/inbox`
- 创建任务：SKILL.md 说 `/open-api/work-task/task/createTask`，官方是 `/work-report/open-platform/report/plan/create`
- 待办列表：SKILL.md 说 `/open-api/work-report/todo/v2/queryPageList`，官方是 `/work-report/reportInfoOpenQuery/todoList`

代码实现是正确的，与官方文档一致。SKILL.md 表1的端点是错误的。

**预防**：
1. 获取外部文档时，优先用 curl：`curl -sL "https://github.com/xgjk/dev-guide/raw/main/..."`
2. 禁止使用 web_search/web_fetch（可能被阻止）
3. 如果 web_search/web_fetch 失败，立即改用 curl
4. 更新 AGENTS.md 明确要求使用 curl

---

## [2026-04-06] API 调用错误 - 以本地文档质疑官方文档

**情境**：
在调用玄关开放平台 API 时，遇到接口调用错误，试图用本地 `references/api-endpoints.md` 中的定义质疑官方文档的正确性。

**错误**：
把本地 skill 文档当成 API 的权威来源，而不是官方 GitHub 文档（https://github.com/xgjk/dev-guide/）。导致基于错误的 API 定义进行调试，浪费时间且无法定位根本问题。

**修正**：
1. 立即访问官方 GitHub 文档，获取最新的 API 规范
2. 对比本地文档和官方文档的差异
3. 以官方文档为准，修正本地代码和文档

**预防**：
1. 每次调用 BP / CWork / 或任何内部系统 API 时，优先读官方 GitHub 文档
2. 本地 skill 文档仅供参考，必须注明「以官方文档为准」
3. 不允许以本地文档质疑官方文档的正确性
4. 定期同步官方文档到本地 references/ 目录

---

<!-- 新增格式：
## [YYYY-MM-DD HH:mm] [问题类型] [简短描述]

**情境**：在什么情况下发生
**错误**：具体做错了什么
**修正**：如何修复
**预防**：下次如何避免

-->
