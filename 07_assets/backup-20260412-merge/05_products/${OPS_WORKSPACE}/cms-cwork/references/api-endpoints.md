# CWork API Endpoints Reference

> Source: TypeScript `cwork-client.ts` (原始实现)
> 本文档详细记录 CWork 平台所有 API 接口，供 Agent 编排调用。

---

## Base URL

```
https://sg-al-cwork-web.mediportal.com.cn
```

## 认证

所有请求需携带 `appKey` 参数（通过 `CWORK_APP_KEY` 环境变量或客户端构造传入）。

---

## API 端点清单

### 1. 汇报管理 API

#### 1.1 搜索员工（按姓名）
```
POST /open-api/cwork-user/searchEmpByName
Body: { "searchKey": "姓名关键字" }
Response: { inside: { empList: [] }, outside: { empList: [] } }
```

#### 1.2 获取收件箱列表
```
POST /open-api/work-report/report/record/inbox
Body: {
  pageSize: int,
  pageIndex: int,
  reportRecordType?: int,      // 汇报类型：1=工作交流, 2=工作指引, 3=文件签批, 4=AI汇报, 5=工作汇报
  empIdList?: string[],
  beginTime?: int,             // 毫秒时间戳
  endTime?: int,               // 毫秒时间戳
  readStatus?: int,            // 0=未读, 1=已读
  orderColumn?: string,
  grade?: string,
  templateId?: int
}
```

#### 1.3 获取发件箱列表
```
POST /open-api/work-report/report/record/outbox
Body: { pageSize, pageIndex, reportRecordType?, empIdList?, beginTime?, endTime?, grade?, templateId? }
```

#### 1.4 获取汇报详情
```
GET /open-api/work-report/report/info?reportId={id}&appKey={key}
```

#### 1.5 获取未读汇报列表
```
POST /open-api/work-report/reportInfoOpenQuery/unreadList
Body: { pageIndex: int, pageSize: int }
```

#### 1.6 查询汇报是否已读
```
GET /open-api/work-report/reportInfoOpenQuery/isReportRead?reportId={id}&employeeId={empId}
```

#### 1.7 标记汇报已读
```
GET /open-api/work-report/open-platform/report/readReport?reportId={id}
```

---

### 2. 汇报操作 API

#### 2.1 提交汇报
```
POST /open-api/work-report/report/record/submit
Body: {
  appKey: string,
  main: string,                          // 汇报标题
  contentHtml: string,                   // HTML格式正文
  contentType: "html",                   // 默认 "html"
  typeId: int,                           // 汇报类型ID，默认 9999
  grade: "一般",                         // 密级
  privacyLevel: "非涉密",               // 隐私级别
  planId?: string,
  templateId?: int,
  acceptEmpIdList?: string[],           // 接收人 empId 列表
  copyEmpIdList?: string[],              // 抄送人 empId 列表
  reportLevelList?: [
    {
      level: int,                        // 节点级别 (1-74)
      type: string,                      // 节点类型
      nodeName: string,                  // 节点名称
      levelUserList: [{ empId: string }]
    }
  ],
  fileVOList?: [{ fileId?, name, type, fsize?, url? }]
}
```

#### 2.2 回复/点评汇报
```
POST /open-api/work-report/report/record/reply
Body: {
  appKey: string,
  reportRecordId: string,                // 汇报记录ID
  contentHtml: string,                   // 回复内容（HTML）
  addEmpIdList?: string[],               // @人员 empId 列表
  sendMsg?: boolean                      // 是否发送消息，默认 true
}
```

---

### 3. 草稿箱 API

#### 3.1 保存草稿
```
POST /open-api/work-report/draftBox/saveOrUpdate
Body: { appKey, main, contentHtml, contentType?, typeId?, grade?, privacyLevel?, planId?, templateId?, acceptEmpIdList?, copyEmpIdList?, reportLevelList?, fileVOList? }
```

#### 3.2 草稿列表
```
POST /open-api/work-report/draftBox/listByPage
Body: { pageIndex: int, pageSize: int }
```

#### 3.3 草稿详情
```
GET /open-api/work-report/draftBox/detail/{reportRecordId}
```

#### 3.4 删除草稿
```
POST /open-api/work-report/draftBox/delete/{draftId}
```

---

### 4. 任务管理 API

#### 4.1 查询任务列表
```
POST /open-api/work-report/report/plan/searchPage
Body: {
  pageSize: int,
  pageIndex: int,
  keyWord?: string,
  status?: int,                          // 任务状态：0=已关闭, 1=进行中, 2=未启动
  reportStatus?: int,                   // 汇报状态：1=已逾期, 2=未逾期
  empIdList?: string[],
  grades?: string[],
  labelList?: string[],
  isRead?: int
}
```

#### 4.2 获取任务详情（包含汇报链路）
```
GET /open-api/work-report/report/plan/getSimplePlanAndReportInfo?planId={id}&appKey={key}
```

#### 4.3 创建任务
```
POST /open-api/work-report/open-platform/report/plan/create
Body: {
  appKey: string,
  main: string,                          // 任务名称
  needful: string,                       // 任务描述/需求
  target: string,                        // 目标描述
  typeId: int,                           // 任务类型，默认 9999
  reportEmpIdList?: string[],            // 汇报对象 empId
  ownerEmpIdList?: string[],             // 负责人 empId
  assistEmpIdList?: string[],            // 协办人 empId
  supervisorEmpIdList?: string[],        // 监督人 empId
  copyEmpIdList?: string[],              // 抄送人 empId
  observerEmpIdList?: string[],          // 观察人 empId
  pushNow: 0|1,                          // 是否立即推送
  endTime: int                           // 截止时间（毫秒时间戳）
}
```

---

### 5. 待办/反馈 API

#### 5.1 查询我创建的任务反馈
```
POST /open-api/work-report/todoTask/listCreatedFeedbacks
Body: { pageNum: int, pageSize: int }
```

#### 5.2 查询待办列表
```
POST /open-api/work-report/reportInfoOpenQuery/todoList
Body: { pageIndex: int, pageSize: int, status?: string }
```

#### 5.3 完成待办
```
POST /open-api/work-report/open-platform/todo/completeTodo
Body: { appKey, todoId: string, content: string, operate?: string }
```

---

### 6. 文件上传 API

#### 6.1 上传文件
```
POST /open-api/cwork-file/uploadWholeFile
Content-Type: multipart/form-data
Form Field: file (binary)
Response: { fileId: string }
```

---

### 7. 模板 API

#### 7.1 查询模板列表
```
POST /open-api/work-report/template/listTemplates
Body: { appKey, beginTime?, endTime?, limit? }
```

---

## reportLevelList 节点类型定义

| level | type | 说明 |
|-------|------|------|
| 1 | read / 接收人 | 接收人（默认） |
| 2 | 决策人 | 决策人节点 |
| 3 | 抄送人 | 抄送人 |
| 4 | 知会人 | 知会人 |
| 5 | 知晓人 | 知晓人 |
| 6 | 观察人 | 观察人 |
| 7 | 汇报人 | 汇报人 |
| 8-9 | 会签 | 会签节点 |
| 10 | 审批人 | 审批人 |
| 11 | 跟踪人 | 跟踪人 |
| 12 | 催收汇报 | 催收汇报 |
| 13 | 传达人 | 传达人 |
| 14 | 知识库 | 知识库归档 |
| 15 | 外部系统 | 外部系统集成 |
| 16 | 归档 | 归档节点 |
| 17 | 共享 | 共享 |
| 18 | 查阅人 | 查阅人 |
| 19 | 分发人 | 分发人 |
| 20 | 协办人 | 协办人 |
| 21-74 | (其他类型) | 见完整定义 |

---

## 汇报类型 (reportRecordType / typeId)

| 值 | 类型名称 |
|----|----------|
| 1 | 工作交流 |
| 2 | 工作指引 |
| 3 | 文件签批 |
| 4 | AI汇报 |
| 5 | 工作汇报 |

---

## 通用响应格式

```json
{
  "resultCode": 1,
  "resultMsg": "success",
  "data": { ... }
}
```

- `resultCode === 1` 表示成功
- 其他值表示失败
