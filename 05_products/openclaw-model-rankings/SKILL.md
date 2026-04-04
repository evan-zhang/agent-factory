---
name: openclaw-model-rankings
description: 本地化 OpenRouter 模型目录与问答筛选 Skill。用于"openrouter 模型选型/openrouter 价格对比/openrouter 模型排行/openrouter 模型推荐"等问题；触发词包括：openrouter 模型、模型预算选型、最便宜模型、支持 tool_use、支持 function calling、支持 JSON mode、128k 上下文、模型延迟、模型对比。当用户提到 openrouter 模型相关问题时触发。
homepage: https://github.com/evan-zhang/agent-factory/issues
---

# openclaw-model-rankings (v1.0.0)

维护一份本地标准化模型数据 `data/model-catalog.json`,供 Agent 直接读取并做筛选/排序/对比回答。

> 定位:**纯数据底座 + 互动问答**。不做报告生成,不做自动策略引擎。

## 快速开始

```bash
cd openclaw-model-rankings
python3 scripts/fetch-rankings.py --full
```

生成:`data/model-catalog.json`

## 数据更新频率

**按需更新**。无需定时任务,当需要做模型选型决策时运行一次即可。

## 数据更新命令

- 全量刷新:
```bash
python3 scripts/fetch-rankings.py --full
```

- 默认增量(仅更新变化模型,未变化仅刷新 `availability.last_checked`):
```bash
python3 scripts/fetch-rankings.py
```

- 可选 API Key:
```bash
OPENROUTER_API_KEY=xxx python3 scripts/fetch-rankings.py
```

## Agent 问答指南(基于本地 JSON)

1. **"X 场景推荐什么模型"**
   先按场景筛选 `capabilities`/`modality`,再按 `pricing.prompt_per_mtok`、`pricing.completion_per_mtok`、`context.max_input_tokens` 排序。

2. **"预算 Y 选谁"**
   用预算阈值筛选 `pricing`,再按性价比(低价优先、上下文更大优先)排序。

3. **"A vs B"**
   用双模型对比表输出:价格、上下文、输出上限、tool_use、structured_output、json_mode、latency。

4. **"延迟最低的前 N 个"**
   过滤 `latency != null`,按 `latency` 升序,返回前 N。

5. **"支持 128k 以上上下文且中文好"**
   先筛 `context.max_input_tokens >= 128000` + `modality` 含 text;中文效果无法从 API 直接得分时,明确说明"中文能力需结合实测或外部基准"。

6. **"支持 tool_use 的有哪些"**
   过滤 `capabilities.tool_use == true` 并排序输出。

7. **"最便宜的 coding 模型"**
   过滤 `capabilities.code == true`,按 `pricing.prompt_per_mtok`、`pricing.completion_per_mtok` 升序。

## 回答约束

- 不调用外部 LLM 生成排行结论。
- 直接读取 `data/model-catalog.json` 并给出可解释的筛选条件与排序依据。
- 如果字段缺失(如 latency),明确标注"该模型无公开延迟字段"。
