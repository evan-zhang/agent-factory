---
name: bp-manager
description: BP管理助手 — 查看/管理自己与下级的BP（目标/关键成果/关键举措）、AI质量检查。触发词：bp/BP/BP管理/BP目标/BP成果/BP举措/衡量标准/对齐/关键任务/关键成果/上级BP/下级BP/承接/目标管理/OKR/KR/我的目标/我的成果/新增目标/新增成果/新增举措/查看BP/查看目标。
metadata:
  requires:
    env: [BP_APP_KEY]
  homepage: https://github.com/xgjk/dev-guide/tree/main/02.产品业务AI文档/BP
  version: v1.0.2
  status: DRAFT
tools_provided:
  - name: bp_client
    category: exec
    risk_level: medium
    permission: exec
    description: BP系统API客户端，封装所有BP相关接口调用
    status: active
  - name: commands
    category: exec
    risk_level: medium
    permission: exec
    description: BP管理命令集合（查看/新增/搜索BP任务）
    status: active
---

# BP Manager

> BP 管理助手 — 查看/管理自己与下级的BP，AI质量检查，延期提醒

---

## 角色定位

BP Manager 是面向管理者和员工的 BP 日常管理工具，核心能力包括：

1. **BP 查看**：查看自己或下级的 BP（目标/关键成果/关键举措）
2. **BP 管理**：新增关键成果/关键举措
3. **AI 检查**：基于康哲规则检查 BP 质量（结构/承接/衡量标准）
4. **延期提醒**：向指定员工发送延期提醒汇报
5. **汇报查看**：查看任务关联的汇报历史
6. **搜索功能**：按名称搜索任务或分组

---

## 核心场景

### 场景一：查看 BP

**用户意图**：快速了解 BP 全貌

**触发词**：
- "查看我的 BP"
- "查看下属的 BP"
- "查看产品中心的 BP"

**执行流程**：
1. 识别用户身份（通过员工ID）
2. 获取周期列表，选择当前周期
3. 获取分组树，定位到目标分组
4. 调用 `getGroupMarkdown` 获取完整 BP
5. 格式化输出给用户

**示例**：
```
用户：查看我的 BP
助手：正在获取您的 BP...
[输出 Markdown 格式的 BP 内容]
```

---

### 场景二：新增关键成果

**用户意图**：为某个目标添加新的关键成果

**触发词**：
- "为目标X新增关键成果"
- "添加一个关键成果"

**执行流程**：
1. 解析用户意图，识别目标ID
2. 收集必要信息：
   - 关键成果名称（必填）
   - 计划起止时间（可选）
   - 承接人（可选）
   - 衡量标准（可选）
3. 调用 `addKeyResult` 接口
4. 确认创建结果

**示例**：
```
用户：为目标 A4-1 新增一个关键成果：完成全栈交付项目模式探索的报告
助手：已成功创建关键成果【完成全栈交付项目模式探索的报告】
关键成果ID: 2014631829004376001
```

---

### 场景三：新增关键举措

**用户意图**：为某个关键成果添加关键举措

**触发词**：
- "为成果X新增关键举措"
- "添加一个关键举措"

**执行流程**：
1. 解析用户意图，识别关键成果ID
2. 收集必要信息：
   - 关键举措名称（必填）
   - 计划起止时间（可选）
   - 承接人（可选）
   - 衡量标准（可选）
3. 调用 `addAction` 接口
4. 确认创建结果

**示例**：
```
用户：为成果 1.1 新增关键举措：每周拜访5家客户
助手：已成功创建关键举措【每周拜访5家客户】
关键举措ID: 2014631829004376002
```

---

### 场景四： AI 检查 BP

**用户意图**：检查 BP 是否符合康哲规则

**触发词**：
- "检查我的 BP"
- "BP 质量检查"
- "帮我检查一下这个 BP"

**执行流程**：
1. 获取目标 BP 内容（Markdown 格式）
2. 基于康哲规则进行检查：
   - 结构完整性：是否按 G-R-A 三层拆解
   - 承接关系：下级目标是否承接上级关键举措
   - 衡量标准：是否符合 SMART 原则
   - 层级深度：是否符合所在层级要求
3. 输出检查结果和改进建议

**检查规则**（来自 BP系统业务说明.md）：
- **集团层级**：拆解到 2 层（目标 → 关键成果）
- **中心/部门/员工层级**：拆解到 3 层（目标 → 关键成果 → 关键举措）
- **衡量标准**：必须包含指标/阈值/口径/数据源/统计频率
- **承接规则**：下级目标承接上级关键成果/关键举措

**示例**：
```
用户：检查我的 BP
助手：正在检查您的 BP...

检查结果：
✅ 结构完整性：通过（3层结构完整）
✅ 承接关系：通过（目标承接了上级关键举措）
⚠️ 衡量标准：关键成果 1.2 缺少数据源
✅ 层级深度：通过（符合部门层级要求）

建议：
- 为关键成果 1.2 补充数据源信息
```

---

### 场景五：下级 BP 建议

**用户意图**：为下级的 BP 提供创建关键举措的建议

**触发词**：
- "帮我看看下属的 BP"
- "给下级提点建议"
- "为下属的 BP 创建关键举措"

**执行流程**：
1. 获取下级 BP 内容
2. 分析 BP 内容，识别：
   - 哪些关键成果缺少关键举措
   - 哪些关键举措过于空泛，需要拆解
   - 哪些关键举措缺少承接人
3. 基于分析结果，生成关键举措建议
4. 输出建议列表

**示例**：
```
用户：帮我看看张三的 BP，给他提点建议
助手：正在分析张三的 BP...

建议为张三的 BP 新增以下关键举措：

**关键成果 1.1：客户拜访量达到50家**
- 建议新增举措：建立拜访记录系统，记录每次拜访的详细信息
- 建议新增举措：制定月度拜访计划，明确每周拜访目标

**关键成果 1.2：签约客户数达到20家**
- 建议新增举措：重点客户专项跟进，建立客户档案
- 建议新增举措：每周五回报跟进进度，及时调整策略

是否需要我帮您创建这些关键举措？
```

---

### 场景六：延期提醒

**用户意图**：向指定员工发送延期提醒

**触发词**：
- "发送延期提醒给张三"
- "提醒李四他的 BP 延期了"

**执行流程**：
1. 识别目标员工
2. 收集延期任务信息：
   - 任务名称
   - 计划结束日期
   - 当前状态
3. 生成提醒内容
4. 调用 `sendDelayReport` 接口
5. 确认发送结果

**示例**：
```
用户：发送延期提醒给张三，他的关键成果延期了
助手：请提供以下信息：
- 延期的任务名称
- 计划结束日期
- 您想提醒的内容

用户：关键成果【客户拜访量达到50家】，计划结束日期是2026-02-28
助手：已成功发送延期提醒给张三
提醒内容：您负责的关键成果【客户拜访量达到50家】已延期，计划结束日期为2026-02-28，请尽快跟进处理。
```

---

### 场景七：查看汇报历史

**用户意图**：查看某个任务关联的汇报历史

**触发词**：
- "查看目标 X 的汇报历史"
- "这个任务的汇报记录"

**执行流程**：
1. 识别目标任务
2. 调用 `pageAllReports` 接口
3. 格式化输出汇报列表

**示例**：
```
用户：查看目标 A4-1 的汇报历史
助手：正在获取汇报历史...

目标【A4-1】的汇报历史（共5条）：

1. 手动汇报 - 2026-03-10
   - 标题： Q1 进度汇报
   - 业务时间： 2026-03-08

2. AI汇报 - 2026-03-05
   - 标题： AI进度分析
   - 业务时间： 2026-03-01

...
```

---

### 场景八：搜索任务

**用户意图**：按名称搜索 BP 任务

**触发词**：
- "搜索关于客户拜访的任务"
- "找一下包含'全栈'的任务"

**执行流程**：
1. 识别搜索关键词
2. 确定搜索范围（分组ID）
3. 调用 `searchTaskByName` 接口
4. 输出搜索结果

**示例**：
```
用户：搜索关于客户拜访的任务
助手：正在搜索...

找到 2 个相关任务：

1. 【关键成果】客户拜访量达到50家
   - 分组： 技术部
   - 状态： 进行中
   - 承接人： 张三

2. 【关键举措】每周拜访5家客户
   - 分组： 技术部
   - 状态： 进行中
   - 承接人： 李四
```

---

## 环境变量

| 变量名 | 说明 | 获取方式 |
|--------|------|----------|
| BP_APP_KEY | BP 系统 API 密钥 | 从玄关开放平台获取 |

---

## API 接口清单

| 接口 | 方法 | 用途 |
|-----|------|------|
| `GET /bp/period/list` | 获取周期列表 | 选择工作周期 |
| `GET /bp/group/list` | 获取分组树 | 导航到目标分组 |
| `POST /bp/group/getPersonalGroupIds` | 批量获取个人分组ID | 快速定位员工 |
| `GET /bp/task/v2/getSimpleTree` | 获取BP任务树 | 了解完整结构 |
| `GET /bp/goal/list` | 获取目标列表 | 查看目标概览 |
| `GET /bp/goal/{goalId}/detail` | 获取目标详情 | 查看单个目标完整信息 |
| `GET /bp/keyResult/list` | 获取关键成果列表 | |
| `GET /bp/keyResult/{keyResultId}/detail` | 获取关键成果详情 | |
| `GET /bp/action/list` | 获取关键举措列表 | |
| `GET /bp/action/{actionId}/detail` | 获取关键举措详情 | |
| `GET /bp/group/markdown` | 获取分组BP Markdown | AI 分析友好 |
| `GET /bp/task/children` | 获取任务子树骨架 | |
| `POST /bp/task/v2/addKeyResult` | 新增关键成果 | |
| `POST /bp/task/v2/addAction` | 新增关键举措 | |
| `POST /bp/task/relation/pageAllReports` | 查询任务关联汇报 | |
| `POST /bp/delayReport/send` | 发送延期提醒汇报 | |
| `GET /bp/delayReport/list` | 查询延期汇报历史 | |
| `GET /bp/task/v2/searchByName` | 按名称搜索任务 | |
| `GET /bp/group/searchByName` | 按名称搜索分组 | |

---

## 数据模型

### Period（周期）
```typescript
interface Period {
  id: string;        // 周期 ID
  name: string;      // 周期名称
  status: number;    // 1=启用，0=未启用
}
```

### Group（分组）
```typescript
interface Group {
  id: string;           // 分组 ID
  name: string;         // 分组名称
  type: 'org' | 'personal';  // 组织/个人
  levelNumber: string;  // 层级编码
  employeeId?: string;  // 个人分组时的员工ID
  parentId?: string;    // 父分组 ID
  childCount?: number;  // 下级分组数量
  children?: Group[];   // 子分组
}
```

### Goal（目标）
```typescript
interface Goal {
  id: string;              // 目标 ID
  name: string;            // 目标名称
  fullLevelNumber: string; // 目标编码
  statusDesc: string;      // 状态描述
  reportCycle: string;     // 汇报周期
  planDateRange: string;   // 计划时间范围
  taskUsers: TaskUser[];   // 参与人
  krCount?: number;        // 关键成果数量
  actionCount?: number;    // 关键举措数量
  keyResults?: KeyResult[];// 关键成果列表
}
```

### KeyResult（关键成果）
```typescript
interface KeyResult {
  id: string;              // 关键成果 ID
  name: string;            // 关键成果名称
  fullLevelNumber: string; // 编码
  statusDesc: string;      // 状态描述
  measureStandard: string; // 衡量标准
  reportCycle: string;     // 汇报周期
  planDateRange: string;   // 计划时间范围
  taskUsers: TaskUser[];   // 参与人
  actionCount?: number;    // 关键举措数量
  actions?: Action[];      // 关键举措列表
}
```

### Action（关键举措）
```typescript
interface Action {
  id: string;              // 关键举措 ID
  name: string;            // 关键举措名称
  fullLevelNumber: string; // 编码
  statusDesc: string;      // 状态描述
  reportCycle: string;     // 汇报周期
  planDateRange: string;   // 计划时间范围
  taskUsers: TaskUser[];   // 参与人
}
```

### TaskUser（任务参与人）
```typescript
interface TaskUser {
  taskId: string;   // 任务 ID
  role: string;     // 角色：承接人/协办人/抄送人/监督人/观察人
  empList: Employee[]; // 员工列表
}
```

### Employee（员工）
```typescript
interface Employee {
  id: string;   // 员工 ID
  name: string; // 员工姓名
}
```

---

## 错误处理

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 1 | 请求成功 | 正常处理 |
| 0 | 通用失败 | 提示用户稍后重试 |
| 610002 | appKey 无效 | 检查 BP_APP_KEY 环境变量 |
| 610015 | 无访问权限 | 提示用户无权限访问该资源 |

---

## 使用注意事项

1. **API 限制**：当前系统不支持编辑和删除操作，只能通过 Web UI 进行
2. **权限控制**：部分接口有数据权限校验，无权限时返回空列表
3. **周期管理**：建议每次操作前先确认当前周期
4. **性能考虑**：`getGroupMarkdown` 返回完整 BP，Token 消耗较大，适合 AI 分析场景

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0.0 | 2026-04-04 | 初版，包含 BP 查看/管理/检查/提醒功能 |
