---
name: cwork-tasks
description: 任务能力域，提供任务创建、查询、管理、卡点识别、结构调整、反馈管理等 Skill
---

## Skills

| Skill | 说明 | LLM 依赖 |
|-------|------|----------|
| task-create | 创建工作任务（支持完整参与者角色） | ❌ |
| task-list-query | 分页查询工作任务列表，支持状态/关键词/人员筛选 | ❌ |
| task-my-assigned | 查询分配给我的任务（我是责任人） | ❌ |
| task-my-created | 查询我创建的任务，支持按分配对象筛选 | ❌ |
| task-manager-dashboard | 管理者视角：查看下属任务执行情况汇总 | ❌ |
| task-chain-get | 拼接任务→汇报的完整链路 | ❌ |
| task-blocker-identify | 识别逾期/卡点/进度滞后的任务 | ❌ |
| todo-extract | 从内容中抽取待办事项 | ✅ |
| my-feedback-list | 查询我创建的反馈类型待办列表 | ❌ |
| task-structure | 将待办整理为结构化任务草稿 | ❌ |
| task-blocker-tip | 为卡点任务提供解决建议 | ✅ |
| task-adjustment-suggest | 基于进展情况提出任务调整建议 | ✅ |

## 触发条件

- 需要创建、跟踪、管理工作任务
- 需要识别和解决任务卡点
- 需要从汇报或讨论中提取待办并结构化
- 需要查看下属任务执行情况

## 使用方式

```typescript
import { taskCreate } from './task-create.js';
import { taskListQuery } from '../shared/task-list-query.js';
import { taskMyAssigned } from './task-my-assigned.js';
import { taskMyCreated } from './task-my-created.js';
import { taskManagerDashboard } from './task-manager-dashboard.js';
import { taskChainGet } from '../shared/task-chain-get.js';
import { taskBlockerIdentify } from './task-blocker-identify.js';
import { myFeedbackList } from './my-feedback-list.js';
import { todoComplete } from '../decisions/todo-complete.js';

// =============================================================================
// 场景一：任务查询
// =============================================================================

// 查看所有任务（分页，支持状态/关键词筛选）
const all = await taskListQuery({ pageSize: 30, pageIndex: 1, status: 1, keyWord: '登录' });

// 查询分配给我的任务（我是责任人）
const myAssigned = await taskMyAssigned({ userId: '1512393035869810690', status: 1 });
console.log(`分配给我 ${myAssigned.data.total} 个任务`);

// 查询我创建的任务（可按分配对象筛选下属）
const myCreated = await taskMyCreated({
  pageSize: 30,
  pageIndex: 1,
  status: 1,
  assigneeIds: ['empId_下属1', 'empId_下属2'],  // 不填则查全部
});

// =============================================================================
// 场景二：任务详情
// =============================================================================

// 查看任务详情（含关联汇报链路）
const chain = await taskChainGet({ taskId: '123456789' });
console.log(`任务: ${chain.data.plan.main}`);
console.log(`状态: ${chain.data.plan.status}`);
for (const r of chain.data.reports) {
  console.log(`  - 汇报: ${r.main} (${r.createTime})`);
}

// =============================================================================
// 场景三：任务创建
// =============================================================================
const created = await taskCreate({
  title: '完成登录功能',
  content: '实现用户登录模块',
  target: '登录功能上线',
  deadline: Date.now() + 7 * 24 * 60 * 60 * 1000,
  reportEmpIdList: ['empId_汇报人'],
  assignee: 'empId_责任人',
  assistEmpIdList: ['empId_协办人'],
  supervisorEmpIdList: ['empId_监督人'],
  copyEmpIdList: ['empId_抄送人'],
  observerEmpIdList: ['empId_观察员'],
  pushNow: true,
});
console.log(`任务创建成功，taskId: ${created.data.taskId}`);

// =============================================================================
// 场景四：管理者仪表盘
// =============================================================================
const dashboard = await taskManagerDashboard({
  subordinateIds: ['empId_下属1', 'empId_下属2'],
  taskStatus: 1,    // 进行中
  reportStatus: 3,  // 逾期优先
});
console.log(`总计 ${dashboard.data.summary.total} 个任务`);
console.log(`逾期: ${dashboard.data.summary.overdue}`);
console.log(`待汇报: ${dashboard.data.summary.pending}`);

// 按人看详情
for (const person of dashboard.data.byPerson) {
  console.log(`\n${person.empId}:`);
  console.log(`  进行中: ${person.inProgress}, 逾期: ${person.overdue}`);
}

// =============================================================================
// 场景五：识别卡点任务
// =============================================================================
const blockers = await taskBlockerIdentify({ pageSize: 50, status: 1 });
console.log(`发现 ${blockers.data.list.length} 个卡点任务`);
for (const b of blockers.data.list) {
  console.log(`  - ${b.main} (${b.reportStatus === 3 ? '已逾期' : '进度滞后'})`);
}

// =============================================================================
// 场景六：查询我创建的反馈待办
// =============================================================================
const feedback = await myFeedbackList({ pageSize: 20, pageIndex: 1 });
console.log(`我发起的反馈: ${feedback.data.total} 条`);
for (const f of feedback.data.list) {
  console.log(`  - [${f.status === 0 ? '未处理' : '已处理'}] ${f.content}`);
}
```

## 任务状态说明

| status | 说明 |
|---------|------|
| `0` | 已关闭 |
| `1` | 进行中 |
| `2` | 未启动 |

## 汇报状态（reportStatus）

| 值 | 说明 |
|----|------|
| 0 | 已关闭 |
| 1 | 待汇报 |
| 2 | 已汇报 |
| 3 | 逾期 |

## 注意事项

- 标记 ✅ 的 Skill 需要传入 `llmClient` 参数
- 标记 ❌ 的 Skill 不需要 LLM，可直接调用
