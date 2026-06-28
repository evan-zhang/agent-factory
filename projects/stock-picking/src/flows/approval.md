# Approval Flow

审批流只生成机器可检查 artifact，不代表用户下单。

## 输入

- `target_pool_item.v1`
- human approval instruction
- pretrade check result

## 步骤

1. 确认目标池项仍未过期。
2. 确认审批人是 Evan。
3. 确认 action 只允许 `buy`。
4. 绑定 `pool_item_id`、`candidate_id`、`request_id`、`correlation_id`。
5. 写入 `approval.v1`，包含 `expires_at`。

## 拒绝

- 审批人不是 Evan。
- approval 已过期。
- approval 与 `pool_item_id` 不匹配。
- pretrade check 缺失或失败。
- 任何 sell approval；v1 sell disabled。

## 输出

返回 approval id、过期时间、pretrade check id 和 execution guard 下一步。
