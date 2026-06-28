# Reconcile Flow

对账是只读流程，不修正券商、不写交易执行。

## 输入

- local target pool / position projection
- broker read-only holdings
- manual ledger rows

## 步骤

1. 读取本地 projection，不把 CSV 当 canonical truth。
2. 读取 broker holdings；API broker 以 broker truth 为准。
3. 对比 stock code、broker、quantity、market。
4. 生成 `reconcile_report.v1`。
5. 对 mismatch 生成 `risk_event.v1`，`execution_allowed=false`。

## 拒绝

- broker credentials unavailable：返回 structured failure，不猜测仓位。
- market/currency 无法归一：标记 mismatch，不自动修复。
- manual ledger 与 broker API 冲突：生成 human decision request。

## 输出

返回 matched/mismatch summary、需要人工确认的项目和风险事件引用。
