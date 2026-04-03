---
name: cms-cwork
description: "工作协同 (CWork) Agent-First Skill — 8 个独立可执行的 Python 编排脚本，覆盖汇报发送/查询/审阅、任务创建/查询、催办闭环、待办管理、模板查询"
version: 3.0.0
---

# cms-cwork — Agent-First Architecture

## 概述

本 Skill 将 CWork（工作协同平台）的完整 API 能力封装为 **6 个意图级编排脚本**，每个脚本独立可执行，Agent 通过 `exec python3 scripts/<name>.py` 调用，JSON 输出到 stdout、错误到 stderr。

**设计原则**：
- **Agent-First**：脚本负责 API 编排，Agent 负责 LLM 推理和用户交互
- **幂等安全**：所有写操作支持 `--dry-run` / `--preview-only`
- **零 TypeScript 依赖**：纯 Python 3.10+，仅需标准库
- **TypeScript 参考**保留在 `references/` 目录

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `CWORK_APP_KEY` | ✅ | — | CWork API 认证密钥 |
| `CWORK_BASE_URL` | ❌ | `https://sg-al-cwork-web.mediportal.com.cn` | API 基础地址 |

## 8 个编排命令

### 1. 发送汇报 — `cwork-send-report.py`

**意图**：搜索接收人 → 校验 → 保存草稿 → 预览 → 发送 → 清理草稿

```bash
python3 scripts/cwork-send-report.py \
  --title "周报标题" \
  --content-html "<p>汇报内容</p>" \
  --receivers "张三,李四" \
  --grade "一般"
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` / `-t` | ✅ | 汇报标题 |
| `--content-html` / `-c` | ✅ | 正文 HTML |
| `--receivers` / `-r` | ❌ | 接收人姓名（逗号分隔，自动解析 empId） |
| `--cc` | ❌ | 抄送人姓名 |
| `--grade` | ❌ | 优先级：`一般`（默认）/ `紧急` |
| `--type-id` | ❌ | 汇报类型 ID（默认 9999） |
| `--file-paths` | ❌ | 本地附件路径（最多 10 个） |
| `--file-names` | ❌ | 附件显示名称 |
| `--plan-id` | ❌ | 关联的任务 ID |
| `--preview-only` | ❌ | 仅保存草稿+预览，不发送 |
| `--draft-id` | ❌ | 已有草稿 ID（更新模式） |

**流程步骤**：
1. **Resolve** — 按姓名搜索员工，精确匹配返回 empId
2. **Validate** — 未找到或多于一个匹配时报错终止
3. **Upload** — 上传本地文件（如有）
4. **Draft** — 调草稿 API 保存，返回 draftId
5. **Preview** — 输出结构化预览 JSON（含 confirmPrompt 供 Agent 展示）
6. **Submit** — 确认后发送汇报
7. **Cleanup** — 发送成功后删除草稿

---

### 2. 查询汇报 — `cwork-query-report.py`

**意图**：收件箱 / 发件箱 / 未读 / 汇报详情

```bash
# 收件箱（默认）
python3 scripts/cwork-query-report.py inbox --page-size 20

# 未读汇报
python3 scripts/cwork-query-report.py unread --page-size 20

# 发件箱
python3 scripts/cwork-query-report.py outbox

# 单条汇报详情（含回复链）
python3 scripts/cwork-query-report.py detail --report-id <id>
```

| 参数 | 说明 |
|------|------|
| `scope` | `inbox`（默认）/ `outbox` / `unread` / `detail` |
| `--page-size` | 分页大小（默认 20） |
| `--page-index` | 页码（默认 1） |
| `--report-id` | 汇报 ID（detail 必填） |
| `--grade` | 按优先级筛选 |
| `--begin-time` / `--end-time` | Unix ms 时间范围 |
| `--read-status` | 已读状态：0=未读 / 1=已读 |
| `--output-raw` | 输出原始 API 响应 |

**输出格式**（非 raw 模式）：
```json
{
  "success": true,
  "scope": "inbox",
  "total": 42,
  "items": [
    {"id": "...", "title": "...", "grade": "一般", "preview": "...", "time": "..."}
  ]
}
```

---

### 3. 创建任务 — `cwork-create-task.py`

**意图**：解析人员姓名 → 创建工作计划/任务

```bash
python3 scripts/cwork-create-task.py \
  --title "完成XXX功能" \
  --content "详细描述" \
  --assignee "张三" \
  --deadline 1743657600000 \
  --grade "一般"
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` / `-t` | ✅ | 任务标题 |
| `--content` / `-c` | ✅ | 任务描述（needful） |
| `--target` | ❌ | 预期目标（默认 = content） |
| `--assignee` | ❌ | 责任人姓名（自动解析 empId） |
| `--reporters` | ❌ | 汇报人姓名（默认 = assignee） |
| `--assist` | ❌ | 协办人姓名 |
| `--supervisors` | ❌ | 监督人姓名 |
| `--cc` | ❌ | 抄送人姓名 |
| `--observers` | ❌ | 观察员姓名 |
| `--deadline` / `-d` | ✅ | 截止时间（Unix ms 时间戳） |
| `--grade` | ❌ | `一般` / `紧急` |
| `--dry-run` | ❌ | 仅验证+解析，不创建 |

**流程步骤**：
1. 解析所有人员姓名 → empId
2. 校验必填项（title、content、deadline）
3. 汇总所有未匹配姓名 → 报错
4. `--dry-run` 时输出解析结果，不调用创建 API
5. 调用 `createPlan` API 创建任务

---

### 4. 审阅汇报 — `cwork-review-report.py`

**意图**：回复汇报 / 标记已读 / 获取回复链

```bash
# 标记已读
python3 scripts/cwork-review-report.py --action mark-read --report-id <id>

# 回复
python3 scripts/cwork-review-report.py --action reply \
  --report-id <id> --content-html "<p>回复内容</p>"

# 查看回复链
python3 scripts/cwork-review-report.py --action replies --report-id <id>
```

| 参数 | 说明 |
|------|------|
| `--action` / `-a` | `reply` / `mark-read` / `replies` |
| `--report-id` | 汇报记录 ID（必填） |
| `--content-html` | 回复内容（reply 必填） |
| `--add-emp-ids` | 回复中 @的人（逗号分隔 empId） |
| `--no-send-msg` | 禁止回复通知推送 |

---

### 5. 查询任务 — `cwork-query-tasks.py`

**意图**：我的任务 / 我创建的 / 团队任务 / 任务详情（含汇报链）

```bash
# 分配给我的任务
python3 scripts/cwork-query-tasks.py my --user-id <empId> --status 1

# 我创建的任务
python3 scripts/cwork-query-tasks.py created --user-id <empId>

# 团队/下属任务
python3 scripts/cwork-query-tasks.py team --subordinate-ids "id1,id2"

# 任务详情（含汇报历史链路）
python3 scripts/cwork-query-tasks.py detail --task-id <planId> --max-reports 10
```

| 参数 | 说明 |
|------|------|
| `scope` | `my` / `created` / `team` / `detail` |
| `--user-id` | 当前用户 empId（my/created 用） |
| `--subordinate-ids` | 下属 empId 列表（team 用） |
| `--task-id` | 任务/计划 ID（detail 必填） |
| `--status` | 任务状态：0=关闭 / 1=进行中 / 2=未启动 |
| `--report-status` | 汇报状态：0=关闭 / 1=待汇报 / 2=已汇报 / 3=逾期 |
| `--max-reports` | 详情模式下最多拉取汇报数（默认 20） |
| `--output-raw` | 输出原始 API 响应 |

---

### 6. 催办闭环 — `cwork-nudge-report.py`

**意图**：识别未闭环事项 → 生成催办文案 → 发送催办

```bash
# 第1步：识别未闭环任务
python3 scripts/cwork-nudge-report.py identify \
  --item-type task --days-threshold 7 --user-id <empId>

# 第2步：生成催办文案（规则模板，不依赖 LLM）
python3 scripts/cwork-nudge-report.py reminder \
  --item-id <id> --recipient "张三" \
  --days-unresolved 14 --original "完成XXX" --style polite

# 第3步：发送催办（通过回复触发通知）
python3 scripts/cwork-nudge-report.py nudge \
  --report-id <id> --content-html "<p>催办内容</p>"
```

| 参数 | 说明 |
|------|------|
| `action` | `identify` / `reminder` / `nudge` |
| `--item-type` | `task` / `decision` / `feedback` |
| `--days-threshold` | 超期天数阈值（默认 7） |
| `--user-id` | 检查指定用户的任务 |
| `--item-id` | 事项 ID（reminder 用） |
| `--recipient` | 催办接收人姓名 |
| `--days-unresolved` | 未解决天数 |
| `--original` | 原始任务/决策描述 |
| `--style` | 催办风格：`polite` / `urgent` / `formal` |
| `--report-id` | 催办回复的汇报 ID（nudge 用） |
| `--content-html` | 催办内容 HTML（nudge 用） |

**识别逻辑**：
- 查询活跃任务（status ≠ 0）
- 计算 `now - lastReportTime` 的天数差
- 超过阈值 → 标记为未闭环，附带建议行动

**催办文案**（规则模板）：
- 三种风格：礼貌 / 紧急 / 正式
- 包含：标题、问候、事项描述、紧迫度、结束语
- Agent 可在此基础上调用 LLM 进一步优化

---

### 7. 待办管理 — `cwork-todo.py`

**意图**：查询待办列表 / 完成待办

```bash
# 查询待办列表
python3 scripts/cwork-todo.py list --page-size 20 --status pending

# 完成待办
python3 scripts/cwork-todo.py complete --todo-id <id> --content "已完成"
```

| 参数 | 说明 |
|------|------|
| `action` | `list` / `complete` |
| `--page-index` | 页码（默认 1） |
| `--page-size` | 每页数量（默认 20） |
| `--status` | 状态筛选 |
| `--todo-id` | 待办 ID（complete 必填） |
| `--content` | 完成说明（complete 必填） |
| `--operate` | 操作类型（默认 complete） |
| `--dry-run` | 仅预览（complete 可用） |

---

### 8. 模板管理 — `cwork-templates.py`

**意图**：查询汇报模板列表

```bash
# 查询模板列表
python3 scripts/cwork-templates.py list --limit 50

# 带时间范围
python3 scripts/cwork-templates.py list --begin-time 1710000000000 --end-time 1712000000000
```

| 参数 | 说明 |
|------|------|
| `action` | `list` |
| `--limit` | 返回数量限制（默认 50） |
| `--begin-time` | 开始时间戳（毫秒） |
| `--end-time` | 结束时间戳（毫秒） |
| `--output-raw` | 输出原始 API 响应 |

**输出字段**：
- `id` — 模板 ID
- `name` — 模板名称
- `type` — 类型 ID
- `typeName` — 类型名称
- `grade` — 优先级

---

## 共享 API 模块 — `cwork_api.py`

所有脚本共用 `scripts/cwork_api.py` 中的 `CWorkClient` 类。该模块封装了：

| API 端点 | 方法 |
|----------|------|
| `/open-api/cwork-user/searchEmpByName` | `search_emp_by_name()` |
| `/open-api/work-report/report/record/inbox` | `get_inbox_list()` |
| `/open-api/work-report/report/record/outbox` | `get_outbox_list()` |
| `/open-api/work-report/report/info` | `get_report_info()` |
| `/open-api/work-report/report/record/submit` | `submit_report()` |
| `/open-api/work-report/report/record/reply` | `reply_report()` |
| `/open-api/work-report/reportInfoOpenQuery/unreadList` | `get_unread_list()` |
| `/open-api/work-report/open-platform/report/readReport` | `mark_report_read()` |
| `/open-api/work-report/report/plan/searchPage` | `search_task_page()` |
| `/open-api/work-report/report/plan/getSimplePlanAndReportInfo` | `get_simple_plan_and_report_info()` |
| `/open-api/work-report/open-platform/report/plan/create` | `create_plan()` |
| `/open-api/work-report/draftBox/saveOrUpdate` | `save_draft()` |
| `/open-api/work-report/draftBox/listByPage` | `list_drafts()` |
| `/open-api/work-report/draftBox/detail/{id}` | `get_draft_detail()` |
| `/open-api/work-report/draftBox/delete/{id}` | `delete_draft()` |
| `/open-api/cwork-file/uploadWholeFile` | `upload_file()` |
| `/open-api/work-report/template/listTemplates` | `list_templates()` |
| `/open-api/work-report/reportInfoOpenQuery/todoList` | `get_todo_list()` |
| `/open-api/work-report/open-platform/todo/completeTodo` | `complete_todo()` |

## 目录结构

```
cms-cwork/
├── SKILL.md                          ← 本文件（意图级接口文档）
├── scripts/
│   ├── cwork_api.py                  ← 共享 API 客户端模块
│   ├── cwork_client.py               ← 低层 HTTP 客户端
│   ├── cwork-send-report.py          ← 1. 发送汇报
│   ├── cwork-query-report.py         ← 2. 查询汇报
│   ├── cwork-create-task.py          ← 3. 创建任务
│   ├── cwork-review-report.py        ← 4. 审阅汇报
│   ├── cwork-query-tasks.py          ← 5. 查询任务
│   ├── cwork-nudge-report.py         ← 6. 催办闭环
│   ├── cwork-todo.py                 ← 7. 待办管理
│   └── cwork-templates.py            ← 8. 模板管理
└── references/                       ← TypeScript 源码参考（保留）
    ├── api-client.md
    ├── api-endpoints.md
    └── api-reference.md
```

## Agent 调用模式

### 模式 A：简单查询（单次 exec）

```
用户：「帮我看看今天有没有未读汇报」
Agent → exec: python3 scripts/cwork-query-report.py unread --page-size 10
Agent ← JSON → 摘要呈现给用户
```

### 模式 B：多步编排（Agent 协调多次 exec）

```
用户：「给张三发一份周报，内容是XXX」
Agent → exec: python3 scripts/cwork-send-report.py --preview-only \
          --title "周报" --content-html "..." --receivers "张三"
Agent ← JSON（含 confirmPrompt）
Agent → 展示预览给用户
用户：「确认」
Agent → exec: python3 scripts/cwork-send-report.py \
          --title "周报" --content-html "..." --receivers "张三"
Agent ← JSON（含 reportId）
Agent → 告知发送成功
```

### 模式 C：催办闭环（3步分离）

```
Agent → exec: python3 scripts/cwork-nudge-report.py identify --days-threshold 7
Agent ← JSON（未闭环列表）
Agent → （LLM 推理）筛选需要催办的事项
Agent → exec: python3 scripts/cwork-nudge-report.py reminder \
          --item-id <id> --recipient "张三" --days-unresolved 14 --style polite
Agent ← JSON（催办文案）
Agent → （可选 LLM 优化文案）
Agent → exec: python3 scripts/cwork-nudge-report.py nudge \
          --report-id <id> --content-html "..."
```

## 错误处理

所有脚本遵循统一错误约定：
- **成功**：JSON 到 stdout，含 `"success": true`
- **失败**：JSON 到 stderr，含 `"success": false` 和 `"error"` 字段，exit code ≠ 0
- **Agent 应同时检查 stdout 和 stderr**

## 从 v1 迁移

| v1（TypeScript 64 个 Skill） | v3（Python 8 个脚本） |
|---|---|
| `emp-search` + `report-validate-receivers` + `report-submit` + `draft.ts` | `cwork-send-report.py` |
| `inbox-query` + `outbox-query` + `unread-report-list` + `report-get-by-id` | `cwork-query-report.py` |
| `task-structure` + `task-create` + `emp-search` | `cwork-create-task.py` |
| `report-reply` + `report-read-mark` + `report-is-read` | `cwork-review-report.py` |
| `task-my-assigned` + `task-my-created` + `task-manager-dashboard` + `task-chain-get` | `cwork-query-tasks.py` |
| `identify-unclosed-items` + `reminder-tip` + `report-remind` | `cwork-nudge-report.py` |
| `todo-list` + `todo-complete` | `cwork-todo.py` |
| `template-list` | `cwork-templates.py` |
| LLM 依赖 Skill（`draft-gen`、`outline-gen`、`ai-*` 等） | 由 Agent 的 LLM 能力直接处理 |
