# Target Pool Flow

目标池只表达“可准备审批的候选”，不表达“已下单”。

## 输入

- `candidate_record.v1`，状态为 `active` 或 `promote_suggested`
- 最近一次 `validation_event.v1`
- 支撑证据与负面证据搜索记录
- sizing 输入，或明确 `awaiting_sizing`

## 步骤

1. 校验候选来源：必须能追溯到 draft、strategy identity、registry record hash。
2. 校验 validation：最近验证不能是 `reject`、`overheated`、`thesis_broken`。
3. 计算或接收 entry、stop、target、position amount。
4. 生成 `target_pool_item.v1`。
5. 写 diff audit ref，说明从 candidate 到 target pool 的字段变化。

## 拒绝

- 无 candidate provenance。
- 缺少 source evidence。
- 负面证据未搜索。
- active build-ready 项缺 entry/stop/target。
- `position_amount=0` 且不是 `awaiting_sizing`。

## 输出

返回目标池摘要、deadline、缺失 sizing 项和下一步审批提示。
