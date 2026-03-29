---
name: cwork-reports
description: 汇报能力域，包含汇报生成、改写、提交、查询、回复、事项管理、AI 问答等 Skill
---

## Skills

| Skill | 说明 | LLM 依赖 |
|-------|------|----------|
| draft-gen | 将零散内容整理为结构化汇报草稿 | ✅ |
| outline-gen | 生成汇报大纲结构 | ✅ |
| report-rewrite | 对现有草稿进行结构/表达优化 | ✅ |
| report-submit | 将确认后的汇报草稿正式提交，支持附件 | ❌ |
| file-upload | 上传本地文件，获取 fileId 供汇报附件使用 | ❌ |
| report-submit-with-attachments | 一站式发送带有多附件的汇报，自动上传文件（失败重试3次）后提交，建议附件不超过10个 | ❌ |
| report-prepare | 准备汇报内容供用户确认，生成确认Prompt（不调用API） | ❌ |
| report-validate-receivers | 按姓名模糊搜索，校验接收人是否存在，返回匹配列表供用户确认 | ❌ |
| report-reply | 对指定汇报进行回复，支持 @ 人员 | ❌ |
| template-list | 查询最近处理过的事项列表（创建任务时选关联事项） | ❌ |
| template-info-batch | 批量查询事项详情（根据 templateId 列表） | ❌ |
| report-read-mark | 标记指定汇报为已读，清除未读通知 | ❌ |
| unread-report-list | 获取当前用户的未读汇报列表 | ❌ |
| report-is-read | 判断指定员工是否已读某汇报 | ❌ |
| ai-report-chat | 对指定汇报集合进行 AI 问答（SSE 流式） | ❌ |
| draft-save | 保存或更新汇报草稿（5.24），返回草稿汇报 ID | ❌ |
| draft-list | 查询草稿箱列表，返回草稿 ID / 汇报 ID / 标题 | ❌ |
| draft-detail | 查看草稿详情（接收人/附件/正文真实内容），用于所见即所得确认 | ❌ |
| draft-delete | 删除草稿箱中的草稿（放弃发送时清理） | ❌ |
| report-complete | 补齐汇报中缺失的常见字段 | ✅ |
| report-tone-adapt | 根据汇报对象调整表达口径 | ✅ |
| report-format | 按模板格式化汇报内容 | ❌ |
| report-formality-adjust | 调整汇报的正式程度 | ✅ |

## 触发条件

- 需要生成、修改、提交工作汇报
- 需要对汇报进行回复、查询、催办
- 需要管理事项和任务
- 需要对汇报内容进行 AI 问答

## 使用方式

```typescript
import { draftGen } from './draft-gen.js';
import { reportSubmit } from './report-submit.js';
import { fileUpload } from './file-upload.js';
import { reportSubmitWithAttachments } from './report-submit-with-attachments.js';
import { reportPrepare } from './report-prepare.js';
import { reportValidateReceivers } from './report-validate-receivers.js';
import { reportReply } from './report-reply.js';
import { templateList } from './template-list.js';
import { templateInfoBatch } from './template-info-batch.js';
import { reportReadMark } from './report-read-mark.js';
import { unreadReportList } from './unread-report-list.js';
import { reportIsRead } from './report-is-read.js';
import { aiReportChat } from './ai-report-chat.js';

// =============================================================================
// 场景一：发送汇报（完整流程）
// =============================================================================

// 步骤1：生成草稿（需要 LLM）
const draft = await draftGen({
  rawContent: '完成了登录功能开发，修复了3个bug',
  reportType: '日报',
}, { llmClient });

// 步骤2：按姓名校验接收人
const validate = await reportValidateReceivers({ names: ['张三', '李四'] });
if (!validate.success) { console.error(validate.message); return; }
console.log(validate.data.confirmPrompt); // 展示给用户，用户回复"是"确认
const confirmedIds = validate.data.confirmedEmployees.map(e => e.empId);

// 步骤3：准备确认内容（不调 API）
const prepare = await reportPrepare({
  main: draft.data.title,
  contentHtml: draft.data.contentHtml,
  reportLevelList: [
    { level: 1, type: 'read', nodeName: '接收人', levelUserList: [{ empId: confirmedIds[0] }] },
  ],
});

// 步骤4：用户确认后正式提交
if (userConfirmed) {
  await reportSubmit({
    main: draft.data.title,
    contentHtml: draft.data.contentHtml,
    reportLevelList: prepare.data.confirmInfo.reportLevelList,
  });
}

// =============================================================================
// 场景二：一站式发送（附件 + 多接收人）
// =============================================================================
const result = await reportSubmitWithAttachments({
  main: '本周工作汇报',
  contentHtml: '<p>详见附件</p>',
  reportLevelList: [
    { level: 1, type: 'read', nodeName: '接收人', levelUserList: [{ empId: 'empId1' }] },
    { level: 2, type: 'suggest', nodeName: '建议人', levelUserList: [{ empId: 'empId2' }] },
  ],
  filePaths: ['/path/文档.pdf', '/path/表格.xlsx'],
  fileNames: ['文档.pdf', '表格.xlsx'],
});

// =============================================================================
// 场景三：回复汇报
// =============================================================================
const reply = await reportReply({
  reportRecordId: '1234567890',  // 汇报 ID
  contentHtml: '<p>已收到，我会尽快处理</p>',
  addEmpIdList: ['empId_被@的人'],  // 可选，@ 某人
});
console.log(`回复成功，replyId: ${reply.data.replyId}`);

// =============================================================================
// 场景四：查询未读汇报 + 标记已读
// =============================================================================
const unread = await unreadReportList({ pageSize: 20, pageIndex: 1 });
console.log(`共 ${unread.data.total} 条未读汇报`);
for (const item of unread.data.list) {
  console.log(`- [${item.reportRecordType}] ${item.main}`);
}

// 看完后标记为已读
await reportReadMark({ reportId: unread.data.list[0].id });

// =============================================================================
// 场景五：查询某人是否已读某汇报
// =============================================================================
const isRead = await reportIsRead({ reportId: '123', employeeId: 'empId_员工' });
console.log(isRead.data.status); // "已读" 或 "未读"

// =============================================================================
// 场景六：查询事项列表
// =============================================================================
const templates = await templateList({ limit: 50 });
console.log(`最近 ${templates.data.total} 个事项：`);
for (const t of templates.data.list) {
  console.log(`- ${t.main} (id: ${t.templateId})`);
}

// =============================================================================
// 场景七：批量查事项详情
// =============================================================================
const details = await templateInfoBatch({ templateIds: ['1001', '1002'] });
for (const d of details.data.list) {
  console.log(`- ${d.main}`);
}

// =============================================================================
// 场景八：AI 问答（对汇报内容提问）
// =============================================================================
const chat = await aiReportChat({
  reportIdList: ['1234567890', '1234567891'],
  userContent: '这几条汇报的关键风险点是什么？',
});
// chat.data.stream 是 SSE 流式响应，需要消费 stream 读取内容
```

## 附件数量与边界说明

| 条件 | 说明 |
|------|------|
| 建议上限 | 单次提交附件不超过 **10个** |
| 超时处理 | 文件上传失败自动重试最多 **3次**，间隔 1s/2s/3s |
| 路径要求 | filePaths 必须为**本地绝对路径** |
| 文件名 | fileNames 与 filePaths **数量必须一致** |
| 失败处理 | 任意文件上传失败，整个提交中止并返回错误信息 |

## 汇报节点类型说明

| type | 节点名称 | 说明 |
|------|----------|------|
| `read` | 接收人 | 接收汇报，传阅 |
| `suggest` | 建议人 | 可发表建议意见 |
| `decide` | 决策人 | 需做决策（同意/不同意） |

**level 为层级顺序**，数字越小越先收到，从 1 开始。

## 汇报类型（reportRecordType）

| 值 | 说明 |
|----|------|
| 1 | 工作交流 |
| 2 | 工作指引 |
| 3 | 文件签批 |
| 4 | AI 汇报 |
| 5 | 工作汇报 |

## 注意事项

- 标记 ✅ 的 Skill 需要传入 `llmClient` 参数
- 标记 ❌ 的 Skill 不需要 LLM，可直接调用
