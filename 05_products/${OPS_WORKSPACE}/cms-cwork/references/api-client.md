# CWork API Client Reference (Python)

> Source: `scripts/cwork_api.py` (Python port of `cwork-client.ts`)
> 本文件是 `cwork_client.py` 的 API 封装说明文档。

---

## 环境变量

| 变量名 | 默认值 | 必填 |
|--------|--------|------|
| `CWORK_BASE_URL` | `https://sg-al-cwork-web.mediportal.com.cn` | 否 |
| `CWORK_APP_KEY` | — | **是** |

---

## CWorkClient 类方法

### 初始化

```python
from cwork_client import CWorkClient, make_client

# 方式1：直接传入 app_key
client = CWorkClient(app_key="your-app-key")

# 方式2：从环境变量读取
client = make_client()  # 需设置 CWORK_APP_KEY
```

---

### 员工查询

#### `search_emp_by_name(search_key: str) -> dict`
按姓名搜索员工，返回 `{inside: {empList: []}, outside: {empList: []}}`

---

### 汇报查询

#### `get_inbox_list(page_size, page_index=1, **kwargs) -> dict`
获取收件箱列表。

**参数：**
- `page_size`: int — 每页大小
- `page_index`: int — 页码（默认1）
- `report_record_type`: int — 汇报类型（1-5）
- `emp_id_list`: list[str] — 指定员工ID列表
- `begin_time`: int — 开始时间（毫秒）
- `end_time`: int — 结束时间（毫秒）
- `read_status`: int — 已读状态（0=未读, 1=已读）
- `grade`: str — 密级
- `template_id`: int — 模板ID

#### `get_outbox_list(page_size, page_index=1, **kwargs) -> dict`
获取发件箱列表。参数同 `get_inbox_list`（不含 read_status）。

#### `get_report_info(report_id: str) -> dict`
获取汇报详情。

#### `get_unread_list(page_index, page_size) -> dict`
获取未读汇报列表。

#### `is_report_read(report_id, employee_id) -> bool`
查询汇报是否已读。

#### `mark_report_read(report_id) -> None`
标记汇报已读。

---

### 汇报操作

#### `submit_report(main, content_html, **kwargs) -> dict`
提交汇报。返回 `{id: string}`

**参数：**
- `main`: str — 汇报标题
- `content_html`: str — HTML格式正文
- `content_type`: str — 内容类型，默认 "html"
- `type_id`: int — 汇报类型，默认 9999
- `grade`: str — 密级，默认 "一般"
- `privacy_level`: str — 隐私级别，默认 "非涉密"
- `plan_id`: str — 关联计划ID
- `template_id`: int — 模板ID
- `accept_emp_id_list`: list[str] — 接收人
- `copy_emp_id_list`: list[str] — 抄送人
- `report_level_list`: list[dict] — 汇报节点配置
- `file_vo_list`: list[dict] — 附件列表

#### `reply_report(report_record_id, content_html, **kwargs) -> int`
回复汇报，返回回复ID。

**参数：**
- `report_record_id`: str — 汇报记录ID
- `content_html`: str — 回复内容
- `add_emp_id_list`: list[str] — @人员
- `send_msg`: bool — 是否发送消息

---

### 草稿箱

#### `save_draft(main, content_html, **kwargs) -> dict`
保存草稿，返回 `{id: string}`

#### `list_drafts(page_index, page_size) -> dict`
分页查询草稿列表。

#### `get_draft_detail(report_record_id) -> dict`
获取草稿详情。

#### `delete_draft(draft_id) -> bool`
删除草稿。

---

### 任务管理

#### `search_task_page(page_size, page_index=1, **kwargs) -> dict`
分页查询任务列表。

**参数：**
- `page_size`: int
- `page_index`: int
- `key_word`: str — 关键词搜索
- `status`: int — 任务状态（0=已关闭, 1=进行中, 2=未启动）
- `report_status`: int — 汇报状态（1=已逾期, 2=未逾期）
- `emp_id_list`: list[str]
- `grades`: list[str]
- `label_list`: list[str]
- `is_read`: int

#### `get_simple_plan_and_report_info(plan_id) -> dict`
获取任务详情（含汇报链路）。

#### `create_plan(main, needful, target, end_time, **kwargs) -> str`
创建任务，返回 planId 字符串。

**参数：**
- `main`: str — 任务名称
- `needful`: str — 任务描述
- `target`: str — 目标描述
- `end_time`: int — 截止时间（毫秒时间戳）
- `type_id`: int — 任务类型，默认 9999
- `report_emp_id_list`: list[str] — 汇报对象
- `owner_emp_id_list`: list[str] — 负责人
- `assist_emp_id_list`: list[str] — 协办人
- `supervisor_emp_id_list`: list[str] — 监督人
- `copy_emp_id_list`: list[str] — 抄送人
- `observer_emp_id_list`: list[str] — 观察人
- `push_now`: bool — 是否立即推送，默认 True

---

### 待办/反馈

#### `list_created_feedbacks(page_num, page_size) -> dict`
查询我创建的反馈列表。

#### `get_todo_list(page_index, page_size, **kwargs) -> dict`
查询待办列表。

#### `complete_todo(todo_id, content, **kwargs) -> bool`
完成待办。

---

### 文件上传

#### `upload_file(file_path: str) -> dict`
上传文件，返回 `{fileId: string}`

---

### 模板

#### `list_templates(begin_time=None, end_time=None, limit=None) -> dict`
查询汇报模板列表。

---

## 异常处理

```python
from cwork_client import CWorkClient, CWorkError

try:
    client = CWorkClient(app_key="your-key")
    result = client.search_emp_by_name("张三")
except CWorkError as e:
    print(f"API Error: {e}")
```

---

## 使用示例

```python
import json
from cwork_client import make_client

client = make_client()

# 搜索员工
emps = client.search_emp_by_name("张三")
print(json.dumps(emps, indent=2, ensure_ascii=False))

# 查询收件箱
inbox = client.get_inbox_list(page_size=20, page_index=1)
print(json.dumps(inbox, indent=2, ensure_ascii=False))

# 创建任务
plan_id = client.create_plan(
    main="完成季度报告",
    needful="整理Q1数据，撰写分析报告",
    target="Q1收入增长15%",
    end_time=1744300800000,  # 2026-04-10 00:00:00
    owner_emp_id_list=["emp001"],
    push_now=True
)
print(f"任务ID: {plan_id}")

# 提交汇报
result = client.submit_report(
    main="日报-4月3日",
    content_html="<p>今日完成：...</p>",
    type_id=5,  # 工作汇报
    accept_emp_id_list=["emp001"]
)
print(f"汇报ID: {result.get('id')}")
```
