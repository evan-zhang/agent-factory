# Risk Monitor Flow

风险监控只生成风险事件和建议，不执行卖出。

## 输入

- candidate / target pool / position projection
- latest quotes
- evidence and claims
- reconcile report, when available

## 步骤

1. 检查 quote freshness。
2. 检查 stop loss、drawdown、thesis break、reconcile mismatch。
3. 将 thesis break 证据提升为 `risk_event.v1` 或 `claim.v1`。
4. 对需要行动的项目生成 `recommended_action=request_human_decision`。
5. 如用户要求 broker action，先交给 execution guard。

## 拒绝

- quote unavailable：生成 `quote_failed` risk event。
- 证据不足：标记 `data_provenance_weak`，不得升级成事实断言。
- 任何自动清仓或自动卖出。

## 输出

返回风险等级、受影响候选/持仓、证据引用、建议动作和 execution guard 状态。
