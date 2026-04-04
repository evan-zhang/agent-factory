---
name: cms-cwork
description: "使用 CWork API 搜索员工（支持模糊查询）、发送/查询汇报、管理待办（决策/建议/反馈）、创建/查询任务。触发词：cwork/CWork/工作协同/发送汇报/发汇报/汇报/申请/周报/待办/任务/催办/搜索员工/查收件箱。输入：员工姓名/汇报内容/待办 ID，输出：员工列表/汇报 ID/待办列表/任务列表"
version: 3.2.1
---

# cms-cwork — Agent-First Architecture

## ⚠️ 强制规则（MUST READ）

**所有 CWork API 调用必须使用本 Skill 提供的 Python 脚本，禁止直接使用 curl/HTTP 调用。**

### 为什么必须使用脚本？

#### 1. URL 编码自动处理
**问题**：API 要求中文参数 URL 编码（UTF-8）

```bash
# ❌ 错误：中文未编码 → 400 Bad Request
curl "https://.../searchEmpByName?searchKey=张"

# ✅ 正确：脚本自动编码
python3 scripts/cwork_api.py search-emp --name "张"
```

#### 2. 参数验证完整
**问题**：API 有复杂的参数要求

```bash
# ❌ 手动调用：缺少参数 → 400/500 错误
curl -X POST "https://.../submit" -d '{"title":"周报"}'

# ✅ 脚本自动验证：提前报错
python3 scripts/cwork-send-report.py --title "周报"
# Error: --content-html is required
```

#### 3. 错误处理统一
**问题**：API 错误信息不明确

```bash
# ❌ 手动调用：看不出具体错误
curl "https://.../submit"
# {"resultCode":0,"resultMsg":null}

# ✅ 脚本提供清晰错误
python3 scripts/cwork-send-report.py --title "周报"
# {"success":false,"error":"缺少必填项 --content-html","suggestion":"请提供汇报正文"}
```

#### 4. 重试机制
**问题**：网络异常导致失败

```bash
# ❌ 手动调用：网络抖动直接失败
curl "https://.../api"  # timeout

# ✅ 脚本自动重试：提升成功率
python3 scripts/cwork_api.py ...  # 自动重试 3 次
```

### 违规示例（❌ 禁止）

```bash
# ❌ 禁止：未使用脚本，中文未编码
curl "https://.../searchEmpByName?searchKey=张"

# ❌ 禁止：未使用脚本，缺少参数验证
curl -X POST "https://.../submit" -d '{"title":"..."}'

# ❌ 禁止：未使用脚本，类型错误
curl -d '{"empId":"1514822118611259394"}' ...  # 应该是数字不是字符串
```

### 正确示例（✅ 必须）

```bash
# ✅ 正确：使用搜索脚本
python3 scripts/cwork-query-report.py --mode inbox --page-size 20

# ✅ 正确：使用发送脚本
python3 scripts/cwork-send-report.py \
  --title "周报" \
  --content-html "<p>内容</p>" \
  --receivers "张三"

# ✅ 正确：使用待办脚本
python3 scripts/cwork-todo.py list --page-size 20
```

### 例外情况

**仅当 Python 脚本不可用时**，才可使用 curl，但**必须**：
1. 参考 `cwork_client.py` 中的编码逻辑
2. 对中文参数进行 URL 编码（UTF-8）
3. 手动验证所有必填参数
4. 处理可能的错误响应

### 调试技巧

如果需要查看脚本的实际请求：

```bash
# 使用 --debug 参数（如果脚本支持）
python3 scripts/cwork_api.py search-emp --name "张" --debug

# 查看脚本源码中的编码逻辑
cat scripts/cwork_client.py | grep urlencode
```

---

## 概述

本 Skill 将 CWork（工作协同平台）的完整 API 能力封装为 **9 个意图级编排脚本**，每个脚本独立可执行，Agent 通过 `exec python3 scripts/<name>.py` 调用，JSON 输出到 stdout、错误到 stderr。

**设计原则**：
- **Agent-First**：脚本负责 API 编排，Agent 负责 LLM 推理和用户交互
- **幂等安全**：所有写操作支持 `--dry-run` / `--preview-only`
- **零 TypeScript 依赖**：纯 Python 3.10+，仅需标准库
- **强制封装**：所有 API 调用必须通过脚本，禁止直接 HTTP 调用
- **TypeScript 参考**保留在 `references/` 目录

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `CWORK_APP_KEY` | ✅ | — | CWork API 认证密钥 |
| `CWORK_BASE_URL` | ❌ | `https://sg-al-cwork-web.mediportal.com.cn` | API 基础地址 |

## 9 个编排命令

### 0. 搜索员工 — `cwork-search-emp.py` ✨ 新增

**意图**：根据姓名/关键词搜索员工 ID 和详细信息

**使用场景**：
1. ✅ **发送汇报前确认接收人** - 确保姓名和 empId 准确
2. ✅ **处理待办时确认发件人** - 查看发件人部门/职位
3. ✅ **创建任务时确认责任人** - 避免姓名错误（重名/错别字）
4. ✅ **催办时确认责任人信息** - 获取完整的员工信息

```bash
# 基础搜索（模糊匹配）
python3 scripts/cwork-search-emp.py --name "张"

# 精确搜索
python3 scripts/cwork-search-emp.py --name "成伟"

# 详细模式（包含 personId、dingUserId 等）
python3 scripts/cwork-search-emp.py --name "刘丽华" --verbose

# 更多结果
python3 scripts/cwork-search-emp.py --name "刘" --max-results 10

# 原始 API 响应（调试用）
python3 scripts/cwork-search-emp.py --name "张" --output-raw
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--name` / `-n` | ✅ | 员工姓名或关键词（支持模糊匹配） |
| `--max-results` / `-m` | ❌ | 每个类别最多返回数量（默认 5） |
| `--verbose` / `-v` | ❌ | 包含额外信息（personId、dingUserId、corpId） |
| `--output-raw` | ❌ | 输出原始 API 响应（调试用） |

**输出格式**：
```json
{
  "success": true,
  "searchKey": "成伟",
  "inside": [
    {
      "empId": "1514822118611259394",
      "name": "成伟",
      "title": "首席架构师",
      "mainDept": "技术部",
      "status": "在职"
    }
  ],
  "outside": [
    {
      "empId": "1897870576398327809",
      "name": "成伟",
      "title": "",
      "mainDept": "其他",
      "status": "在职",
      "company": "德镁医药"
    }
  ],
  "totalInside": 1,
  "totalOutside": 1
}
```

**注意事项**：
- ✅ **URL 编码已自动处理**（支持中文参数）
- ✅ **模糊匹配**：搜索"刘"会返回所有姓刘的员工
- ✅ **内外部区分**：`inside`（玄关健康员工）+ `outside`（外部联系人/其他公司）
- ⚠️ **重名问题**：可能返回多个同名员工，需要根据部门/职位区分
- 💡 **推荐用法**：发送汇报前先搜索确认 empId

---

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

**意图**：收件箱 / 发件箱 / 未读 / 汇报详情 / 节点详情 / **历史上下文检索** ✨ 新增

```bash
# 收件箱（默认）
python3 scripts/cwork-query-report.py --mode inbox --page-size 20

# 未读汇报
python3 scripts/cwork-query-report.py --mode unread --page-size 20

# 发件箱
python3 scripts/cwork-query-report.py --mode outbox

# 单条汇报详情（含回复链）
python3 scripts/cwork-query-report.py --mode detail --report-id <id>

# 节点详情（含审批/建议/反馈状态与处理意见）✨ v3.1.0 新增
python3 scripts/cwork-query-report.py --mode node-detail --report-id <id>

# 历史上下文检索（审批决策支持）✨ v3.1.1 新增
# 查询发件人历史汇报
python3 scripts/cwork-query-report.py --mode sender-history \
  --sender-emp-id <empId> \
  --days 90

# 关键字搜索汇报（客户端过滤）
python3 scripts/cwork-query-report.py --mode keyword-search \
  --keyword "公章" \
  --days 90
```

| 参数 | 说明 |
|------|------|
| `--mode` | `inbox` / `outbox` / `unread` / `detail` / `node-detail` / `sender-history` / `keyword-search` / `pending` / `my-sent` |
| `--page-size` | 分页大小（默认 20） |
| `--page-index` | 页码（默认 1） |
| `--report-id` | 汇报 ID（detail / node-detail 必填） |
| `--sender-emp-id` | 发件人员工 ID（sender-history 必填） |
| `--keyword` | 搜索关键词（keyword-search 必填） |
| `--days` | 回溯天数（sender-history / keyword-search，默认 90） |
| `--report-type` | 汇报类型：1-工作交流 / 2-工作指引 / 3-文件签批 / 4-AI汇报 / 5-工作汇报 |
| `--status` | 已读状态：0=未读 / 1=已读 |
| `--start-date` / `--end-date` | 时间范围（YYYY-MM-DD） |

**输出格式**（sender-history）：
```json
{
  "success": true,
  "data": {
    "senderEmpId": "1514822194347806721",
    "totalReports": 15,
    "recentReports": [
      {
        "id": "2039993163862765570",
        "main": "互联网公司公章借出申请",
        "createTime": "2026-04-03 17:11:48",
        "reportRecordType": 5
      }
    ]
  }
}
```

**输出格式**（keyword-search）：
```json
{
  "success": true,
  "data": {
    "keyword": "公章",
    "total": 5,
    "reports": [
      {
        "id": "2039993163862765570",
        "main": "互联网公司公章借出申请",
        "content": "用于办理工商变更...",
        "createTime": "2026-04-03 17:11:48",
        "sendEmpName": "刘丽华"
      }
    ]
  }
}
```

**输出格式**（node-detail）：
```json
{
  "success": true,
  "data": {
    "id": 汇报ID,
    "main": "汇报标题",
    "content": "汇报正文",
    "writeEmpName": "汇报人",
    "createTime": "发起时间",
    "nodeList": [
      {
        "nodeName": "建议人",
        "type": "建议",
        "status": "已完成",
        "level": 1,
        "userList": [
          {
            "empId": 员工ID,
            "name": "张三",
            "status": "已处理",
            "operate": "建议",
            "content": "建议增加异常处理",
            "finishTime": "2026-04-03 11:00:00"
          }
        ]
      }
    ]
  }
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

**意图**：查询待办列表 / 完成待办（支持决策/建议/反馈三种类型）

**支持的三种待办类型**：
| 类型 | 英文标识 | 必填参数 | 说明 |
|------|---------|---------|------|
| **决策** | `decide` | `--operate agree/disagree` | 决策人必须明确同意或不同意 |
| **建议** | `suggest` | `--content` | 建议人提供意见或建议 |
| **反馈** | `feedback` | `--content` | 反馈人回复评论或补充信息 |

```bash
# 查询待办列表
python3 scripts/cwork-todo.py list --page-size 20 --status pending

# 完成决策待办（必须指定 operate）
python3 scripts/cwork-todo.py complete \
  --todo-id <id> \
  --content "同意该方案，建议增加异常处理" \
  --operate agree

# 完成建议待办
python3 scripts/cwork-todo.py complete \
  --todo-id <id> \
  --content "从技术角度看，建议采用微服务架构"

# 完成反馈待办
python3 scripts/cwork-todo.py complete \
  --todo-id <id> \
  --content "已补充相关数据，详见附件"

# 查看汇报详情（含节点与处理意见）
python3 scripts/cwork-query-report.py node-detail --report-id <id>
```

| 参数 | 说明 |
|------|------|
| `action` | `list` / `complete` |
| `--page-index` | 页码（默认 1） |
| `--page-size` | 每页数量（默认 20） |
| `--status` | 状态筛选 |
| `--todo-id` | 待办 ID（complete 必填） |
| `--content` | 完成说明（建议/反馈必填，决策可选） |
| `--operate` | 决策操作：`agree`（同意）/ `disagree`（不同意）。**仅决策类型必填** |
| `--dry-run` | 仅预览（complete 可用） |

**输出格式**（complete）：
```json
{
  "success": true,
  "todoId": "12345",
  "todoType": "decide",
  "operate": "agree",
  "content": "同意该方案",
  "message": "决策已完成"
}
```

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
| `/open-api/work-report/report/getReportNodeDetail` | `get_report_node_detail()` |
| — | `get_sender_history()` ✨ v3.1.1 新增 |
| — | `search_reports_by_keyword()` ✨ v3.1.1 新增 |

## 目录结构

```
cms-cwork/
├── SKILL.md                          ← 本文件（意图级接口文档）
├── scripts/
│   ├── cwork_api.py                  ← 共享 API 客户端模块
│   ├── cwork_client.py               ← 低层 HTTP 客户端
│   ├── cwork-search-emp.py           ← 0. 搜索员工 ✨ v3.2.0 新增
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

| v1（TypeScript 64 个 Skill） | v3（Python 9 个脚本） |
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
