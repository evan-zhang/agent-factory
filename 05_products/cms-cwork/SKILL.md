---
name: cwork
description: 工作协同 Skill 包，提供汇报、任务、决策、闭环、分析、LLM 六大能力域，共 64 个 Skill
---

## 能力域概览

| 能力域 | 目录 | 说明 |
|--------|------|------|
| **shared** | `./shared/` | 数据获取层，9个基础查询 Skill，无需 LLM |
| **reports** | `./reports/` | 汇报能力域，19个 Skill（发送、回复、查询、未读、提醒、AI问答、事项管理等） |
| **tasks** | `./tasks/` | 任务能力域，12个 Skill（创建、查询、管理者仪表盘、反馈列表等） |
| **decisions** | `./decisions/` | 决策能力域，6个 Skill（结论提炼、摘要生成等） |
| **closure** | `./closure/` | 闭环能力域，5个 Skill（状态判断、催办提示等） |
| **analysis** | `./analysis/` | 分析能力域，6个 Skill（重点提炼、趋势分析等） |
| **contacts** | `./contacts/` | 联系人分组能力域，4个 Skill（列出/创建/重命名/成员管理） |
| **llm** | `./llm/` | LLM 能力域，1个 Skill（多源汇总） |

## Skill 数量统计

- **L1 数据获取**：9 个（无需 LLM）
- **L2 核心业务**：28 个（部分需要 LLM）
- **L3 辅助支持**：14 个（部分需要 LLM）
- **总计**：68 个

## 核心原则

**Skill 不带 LLM 凭证，由调用方注入。**

所有需要 LLM 的 Skill 函数签名为：
```typescript
async function skillName(input, { llmClient }) { ... }
```

调用方负责创建和传入 `llmClient`，Skill 内部不创建 LLM 实例。

## 安装方式

```bash
# 复制到 OpenClaw skills 目录
cp -r workspace-cwork ~/.openclaw/skills/cwork
```

或通过 ClawHub 安装：
```bash
clawhub install cwork
```

## 环境变量配置

```bash
# CWork API 配置（必须）
export CWORK_APP_KEY="your-app-key"
export CWORK_BASE_URL="https://your-cwork-api.example.com"

# SSE 超时（可选）
export SSE_TIMEOUT=60000
export SSE_MAX_REPORTS=20

# 分页配置（可选）
export PAGINATION_DEFAULT=20
export PAGINATION_MAX=50
```

## 快速开始

```typescript
import { empSearch } from './shared/emp-search.js';
import { draftGen } from './reports/draft-gen.js';
import { reportSubmit } from './reports/report-submit.js';
import { fileUpload } from './reports/file-upload.js';
import { reportSubmitWithAttachments } from './reports/report-submit-with-attachments.js';
import { reportPrepare } from './reports/report-prepare.js';
import { reportValidateReceivers } from './reports/report-validate-receivers.js';
import { taskListQuery } from './shared/task-list-query.js';
import { taskChainGet } from './shared/task-chain-get.js';
import { taskMyAssigned } from './tasks/task-my-assigned.js';
import { taskMyCreated } from './tasks/task-my-created.js';
import { taskManagerDashboard } from './tasks/task-manager-dashboard.js';
import { reportRemind } from './reports/report-remind.js';
import { todoComplete } from './decisions/todo-complete.js';
import { reportReply } from './reports/report-reply.js';
import { templateList } from './reports/template-list.js';
import { reportReadMark } from './reports/report-read-mark.js';
import { unreadReportList } from './reports/unread-report-list.js';
import { reportIsRead } from './reports/report-is-read.js';
import { aiReportChat } from './reports/ai-report-chat.js';
import { templateInfoBatch } from './reports/template-info-batch.js';
import { myFeedbackList } from './tasks/my-feedback-list.js';

// 1. 搜索员工（不需要 LLM）
const emp = await empSearch({ name: '张三' });

// 2. 生成汇报草稿（需要 LLM client）
const draft = await draftGen({
  rawContent: '完成了登录功能开发',
  reportType: '日报',
}, { llmClient });

// 3. 提交汇报（不需要 LLM，可带附件）
await reportSubmit({
  main: draft.data.title,
  contentHtml: '<p>...</p>',
  fileVOList: [
    { fileId: upload.data.fileId, name: '产品需求文档.md', type: 'file', fsize: upload.data.fileSize },
  ]
});

// 4. 上传文件（不需要 LLM）
const upload = await fileUpload({ file: myFile });

// 5. 一站式发送多附件汇报（推荐，自动处理上传+提交，建议不超过10个附件）
const result = await reportSubmitWithAttachments({
  main: '项目完整汇报',
  contentHtml: '<p>详见附件</p>',
  acceptEmpIdList: ['1512393035869810690'],
  filePaths: ['/path/附件1.pdf', '/path/附件2.xlsx'],
  fileNames: ['附件1.pdf', '附件2.xlsx'],
});
```

## 子域 SKILL.md

每个子域目录下都有独立的 `SKILL.md`，包含：
- 该子域的所有 Skill 列表
- 触发条件说明
- 使用示例
- LLM 依赖标记

请查阅各子域的 `SKILL.md` 获取详细信息：
- `./shared/SKILL.md`
- `./reports/SKILL.md`
- `./tasks/SKILL.md`
- `./decisions/SKILL.md`
- `./closure/SKILL.md`
- `./analysis/SKILL.md`
- `./llm/SKILL.md`

## 目录结构

```
workspace-cwork/
├── SKILL.md                    ← 主包入口
├── config/
│   └── index.ts              ← CWork API 配置（无 LLM 凭证）
├── shared/
│   ├── SKILL.md
│   ├── types.ts              ← 通用类型定义
│   ├── cwork-client.ts       ← CWork API 客户端
│   ├── sse-client.ts          ← SSE 客户端
│   ├── emp-search.ts
│   ├── inbox-query.ts
│   ├── outbox-query.ts
│   ├── report-get-by-id.ts
│   ├── task-list-query.ts
│   ├── todo-list-query.ts
│   ├── task-chain-get.ts
│   └── sse-client.ts          ← SSE Skill
├── reports/
│   └── SKILL.md
├── tasks/
│   └── SKILL.md
├── decisions/
│   └── SKILL.md
├── closure/
│   └── SKILL.md
├── analysis/
│   └── SKILL.md
└── llm/
    └── SKILL.md
```
