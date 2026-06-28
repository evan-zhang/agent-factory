# Validation Flow

Validation 负责验证 draft thesis 是否仍然成立，并产出 `validation_event.v1`。它不是重新完整跑一轮 TAROC，也不直接把候选写入持仓或目标池。

## 输入

- `draft_candidates.v1`
- latest market data
- fresh evidence refs
- prior validation events

## 步骤

1. 选择仍在有效窗口内的 draft。
2. 获取最新报价和关键新闻/公告证据。
3. 复核原 thesis 是否仍成立。
4. 强制检查新增负面证据。
5. 生成 `validation_event.v1`。
6. 当满足确认规则时，生成或更新 `candidate_record.v1`。

## 判定

- `confirm`：原逻辑成立，无重大新负面，盘面未明显过热。
- `watch`：逻辑仍在，但需要更多证据或等待价格。
- `reject`：逻辑减弱或风险收益不再成立。
- `overheated`：逻辑成立但短期追高风险过大。
- `thesis_broken`：关键前提被证据否定。
- `validation_skipped`：日历、数据源或上下文不允许验证。

## 入候选池

入池是 `candidate_record.v1` 状态变化，不是 CSV append。

要求：

- 至少 2 次有效 confirm，或后续设计明确的替代规则。
- source evidence 和 negative evidence 都可追溯。
- candidate record 保留 origin draft、strategy identity、confidence 和 state event id。

## 淘汰

过期或被否定的 draft 生成 validation event，不删除历史。AI 可建议移除候选，但最终 `removed` 状态必须由 human actor 写入。

## 输出

返回 validation verdict、证据变化、是否建议入池、是否需要人工判断、下一步。
