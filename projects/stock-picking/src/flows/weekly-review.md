# Weekly Review Flow

Weekly review 负责把候选池和跟踪事件汇总为周度建议。它只能建议保留、观察、移除或升级审批，不能自动删除候选或执行交易。

## 输入

- `candidate_record.v1`
- `tracking_event.v1`
- latest validation events
- quote snapshots
- risk events
- evidence refs and claims

## 步骤

1. 确认本周是否有可复盘交易日；整周无交易则生成 skip summary。
2. 按 candidate age / week id 分组。
3. 拉取或引用最新行情证据。
4. 检查新增催化、风险、thesis break。
5. 生成 `tracking_event.v1`。
6. 对 W4+ 候选生成 human decision request，而不是自动移除。

## 分组

- W1：新入池，关注入场观察区间。
- W2-W3：持续跟踪，检查 thesis 是否强化或减弱。
- W4+：必须给出保留、移除建议或继续观察理由。

## 输出内容

- 本周新增、确认、淘汰建议数量。
- 每个候选的当前状态、价格变化、证据变化。
- 风险事件摘要。
- W4+ 人工决策列表。
- 下周关注事项。

## 通知

message 推送是可选 presentation layer。通知内容必须来自已生成的事件摘要，不得绕过 schema 直接输出不可追溯建议。
