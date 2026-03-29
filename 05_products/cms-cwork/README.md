# CWork Skill 包使用说明

> 版本：1.0.0  
> 名称：cms-cwork  
> 用途：工作协同系统 AI 能力接入包

---

## 一、安装

### 方式1：通过命令行安装（推荐）

```bash
# 安装到本地
clawhub install cms-cwork

# 安装到指定目录
clawhub install cms-cwork --dir /your/path
```

### 方式2：手动复制

将 `workspace-cwork/` 目录复制到目标机器即可使用。

---

## 二、包含内容

cms-cwork 提供 **6 大能力域，共 41 个 Skill**：

| 能力域 | 说明 | 代表性 Skill |
|--------|------|-------------|
| **reports**（汇报） | 汇报的生成、提交、改写 | 草稿生成、大纲生成、汇报提交 |
| **tasks**（任务） | 任务的创建、查询、跟踪 | 任务创建、任务列表、待办抽取 |
| **decisions**（决策） | 决策结论的提炼和确认 | 结论提炼、已决/待决区分、决策提交 |
| **closure**（闭环） | 事项闭环状态跟踪 | 闭环判断、未闭环识别、催办提醒 |
| **analysis**（分析） | 汇报内容的智能分析 | 风险识别、问题识别、趋势总结 |
| **llm**（多源汇总） | 多汇报内容的智能汇总 | 多源数据聚合汇总 |

### 数据获取类（shared，无需 LLM）

| Skill | 说明 |
|-------|------|
| `empSearch` | 按姓名搜索员工，获取 empId |
| `inboxQuery` | 查询收件箱汇报列表 |
| `outboxQuery` | 查询发件箱汇报列表 |
| `reportGetById` | 获取单条汇报内容和回复列表 |
| `taskListQuery` | 查询任务列表 |
| `todoListQuery` | 查询待办列表 |
| `taskChainGet` | 获取任务及所有跟进汇报链路 |

---

## 三、快速开始

### 初始化（只需一次）

```typescript
import { setup } from 'cms-cwork';

setup({
  appKey: '你的工作协同 appKey',           // 必填
  baseUrl: 'https://your-domain.com',       // 可选，默认生产环境
});
```

### 基础调用示例

```typescript
import { empSearch, inboxQuery, draftGen } from 'cms-cwork';

// 搜索员工
const emp = await empSearch({ name: '张三' });
console.log(emp.data.inside.empList[0].id);

// 查询收件箱
const inbox = await inboxQuery({ pageSize: 10 });
console.log(`共 ${inbox.data.total} 条汇报`);

// 生成日报草稿（需要 LLM）
const draft = await draftGen({
  rawContent: '今天完成了API对接，修复了2个bug',
  reportType: '日报',
});
console.log(draft.data.content);
```

---

## 四、Skill 列表

### reports（汇报）

| Skill | 说明 |
|-------|------|
| `draftGen` | 根据工作内容生成日报/周报草稿 |
| `outlineGen` | 生成汇报大纲 |
| `reportRewrite` | 改写优化已有汇报内容 |
| `reportSubmit` | 提交汇报到工作协同平台 |
| `reportComplete` | 补全汇报中的缺失部分 |
| `reportToneAdapt` | 调整汇报语气（正式/简洁/详细） |
| `reportFormat` | 格式化汇报内容 |
| `reportFormalityAdjust` | 调整汇报风格 |

### tasks（任务）

| Skill | 说明 |
|-------|------|
| `taskCreate` | 创建新任务 |
| `taskListQuery` | 查询任务列表 |
| `taskChainGet` | 获取任务及其所有跟进汇报链路 |
| `taskBlockerIdentify` | 识别任务卡点 |
| `todoExtract` | 从汇报内容中抽取待办事项 |
| `taskBlockerTip` | 生成任务卡点提示 |

### decisions（决策）

| Skill | 说明 |
|-------|------|
| `decisionConcludeExtract` | 提炼讨论中的决策结论 |
| `decisionResolvedPending` | 区分已决事项和待确认事项 |
| `decisionSummaryGen` | 生成决策摘要 |
| `todoComplete` | 完成待办（建议/决策） |
| `discussionThread` | 串联多轮讨论脉络 |
| `decisionFormatStandardize` | 标准化决策表达格式 |

### closure（闭环）

| Skill | 说明 |
|-------|------|
| `judgeClosureStatus` | 判断事项是否已闭环 |
| `identifyUnclosedItems` | 识别未闭环事项 |
| `generateUnclosedList` | 生成未闭环清单 |
| `reminderTip` | 生成待办催办提醒 |
| `summarizeFollowupStatus` | 总结跟进状态 |

### analysis（分析）

| Skill | 说明 |
|-------|------|
| `aiHighlightExtract` | 提取汇报中的重点内容 |
| `aiProblemIdentify` | 识别汇报中的问题 |
| `aiRiskIdentify` | 识别汇报中的风险信号 |
| `aiCompareReports` | 对比分析多条汇报 |
| `summaryTrends` | 总结汇报趋势 |
| `formatAnalysisOutput` | 格式化分析输出 |

### llm（多源汇总）

| Skill | 说明 |
|-------|------|
| `multiSourceAgg` | 多汇报内容智能聚合汇总 |

---

## 五、LLM 说明

部分 Skill（如 `draftGen`、`aiRiskIdentify`）需要大语言模型支持。

调用时传入 LLM 客户端：

```typescript
import { draftGen } from 'cms-cwork';

const result = await draftGen(input, {
  llmClient: yourLLMClient,  // 支持 OpenAI / Claude / GLM 等标准接口
});
```

如不传 LLM 客户端，Skill 会返回友好提示。

---

## 六、注意事项

1. **初始化**：`setup()` 只需调用一次，之后所有 Skill 均可使用
2. **appKey 必填**：未配置 appKey 会抛出错误
3. **LLM 选传**：数据查询类 Skill 不需要 LLM，只有生成/分析类需要
4. **错误处理**：所有 Skill 返回 `{ success, message, data }` 结构，请检查 `success` 字段

---

## 七、联系方式

如有问题请联系开发人员。
