---
name: cms-tbs-scene-generate
description: TBS场景创建 Step4.1：基于已确认信息生成产品知识主题（用户确认+匹配），以及场景上下文（doctorOnlyContext/coachOnlyContext）。纯 AI 生成 + 知识匹配，无脚本调用。
skillcode: cms-tbs-scene-generate
version: 2.0.0
---

# cms-tbs-scene-generate（场景生成与知识匹配）

## 核心定位
基于 collect 阶段的已确认信息，完成两件事：
1. 生成产品知识主题 → 用户逐条确认 → 精确/模糊匹配 → 缺失走上报
2. 生成场景上下文（doctorOnlyContext / coachOnlyContext）

## 输入（从 state.json 读取）
- `state.collect`（全部已确认信息）
- `state.config.productKnowledges`（知识主数据，用于匹配）

## 执行流程

### Phase 1：产品知识主题生成
基于「医生核心顾虑 + 代表目标」，生成 2-4 条产品知识主题短语。

生成原则：
1. 围绕医生为什么不接受/担心什么
2. 围绕希望推动的行为变化
3. 围绕产品临床价值/定位/适用患者
4. 围绕院外可及性/患者衔接/合规边界

禁止：
- 不得复述医生顾虑原文
- 不得输出空泛占位词（如"产品核心信息""常见问题"）
- 不得编造疗效/指南结论
- 主题只做短语，不写正文

### Phase 2：用户确认主题
回显顺序：
1. 此前已确认的完整信息清单（不丢字段）
2. 本次待确认的产品知识主题

用户可修改主题。修改后重复回显，直到确认无误。

### Phase 3：知识匹配
基于确认后的主题到 `state.config.productKnowledges` 匹配：

**第一轮：精确匹配**
- 条件：`drugId` 一致 + `title` trim 后精确匹配
- 命中：写入 `knowledgeIds`

**第二轮：模糊匹配降级**（仅对精确未命中的主题）
- 条件：`drugId` 一致 + `title` 双向包含匹配（忽略空格和标点差异）
- 命中：写入 `knowledgeIds`

**仍未命中**：
- 不写入 `knowledgeIds`
- 提示用户该主题未找到
- 记入 `missingKnowledgeTopics`

### Phase 4：处理缺失
若有缺失主题：
- 不继续生成场景上下文
- 输出上报草稿（科室/品种/缺失主题/缺失原因/场景摘要/期望补充信息）
- 等待编排 Skill 决定后续动作

若无缺失：进入 Phase 5。

### Phase 5：生成场景上下文

**doctorOnlyContext（对练对象侧）**
必须是 Markdown 字符串，包含 6 个二级标题（按固定顺序）：
1. `## 已知背景`
2. `## 核心顾虑`（1-2 条 `-` 开头要点）
3. `## 今日状态`
4. `## 终止条件`（可自定义若干条）
5. `## 输出要求`（固定 A，逐行原样拷贝，不得改写）
6. `## 对话结束规则（强制）`（固定 B，逐行原样拷贝，放在全文最后）

固定 A：
```
- 输出长度控制：每次回复控制在30-50字左右，保持真实医生沟通的自然简洁；每轮最多聚焦1个核心点。
- 单问原则：每轮最多提出1个核心问题（问号≤1）。如果想到第二个问题，必须留到下一轮再问。
- 语言要求：以中文自然对话为主；允许必要的医学缩写/单位/符号，但不得滥用英文；严禁出现与医学沟通无关的英文单词。
- 纯文本要求（强制）：只输出纯文本对话，不要使用任何加粗/斜体/标题/代码符号等格式化写法。
- 提问后必须等待代表回答：提问后必须收住，不得在同一轮连续追问，更不得在提问后追加结束标记。
- 避免臆造数据（强制）：不得凭空编造背景之外的具体数值/比例/研究结论；不确定就说明需回去核对资料。
```

固定 B：
```
- 只有对练对象角色可结束：仅在本轮末尾追加 [对话结束]，且必须放在全文最后。
- 允许结束：已触发终止条件，或系统明确要求本轮结束（最后一轮/轮次已满）。
- 互斥（执行检查）：若本轮出现问号或疑问词，则必须删除 [对话结束]。
- 互斥（执行检查）：若本轮要输出 [对话结束]，则全文不得出现任何问号或疑问词，且不得出现提问意图。
- 结束语边界：结束语必须是纯陈述句，不得提问，也不得安排任何后续动作或要求。
```

**coachOnlyContext（教练侧）**
必须包含 5 个节标题：
- `## 期望代表行为`
- `## 评分重点`
- `## 终止条件`
- `## 最佳实践`（必须包含用户提供的开场话术/回应问题话术/推荐建议）
- `## 输出要求`

要求：可观察、可评估；避免出现 `[对话结束]` 字面量。

## 输出（写入 state.json）
- `state.generate.productKnowledgeNeeds`：确认后的主题列表
- `state.generate.knowledgeIds`：匹配成功的 ID 列表
- `state.generate.missingKnowledgeTopics`：缺失的主题（如有）
- `state.generate.doctorOnlyContext`：对练对象上下文
- `state.generate.coachOnlyContext`：教练上下文
- `state.generate.repBriefing`：代表简报

## 成功判定
- `state.generate.knowledgeIds` 非空
- `state.generate.doctorOnlyContext` 和 `coachOnlyContext` 非空
- `state.generate.missingKnowledgeTopics` 为空

## 配置与授权
- 无需 access-token
- 无需额外配置

## 问题反馈
- Issue 地址：https://github.com/xgjk/xg-skills/issues
- 标题格式：`[cms-tbs-scene-generate] 简要描述问题`
- 建议包含：生成的内容、匹配结果、缺失主题列表
