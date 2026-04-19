# CAS 灰度收口报告（2026-03-27）

范围：AF-20260326-002 / cas-chat-archive  
阶段：S7 灰度验收（TESTING）

## 1) 本轮收口目标
- 关闭 P0 修复项并回归
- 形成四网关 E2E 红绿灯视图
- 明确转正式前最后缺口

## 2) 回归结果（已闭环）
- P0 修复后测试：`scripts/test_cas.py` **14/14 通过**（py3.14 + py3.10）
- 打包校验：`publish.py --dry-run` 通过，包内包含 hooks 关键文件
- 四网关 hook 配置：`life/ops/company/code` 均 enabled
- 四网关 hook 文件：handler.ts 均与仓库一致（synced）

## 3) 四网关 E2E 红绿灯（今日）

| Gateway | Hook启用 | 今日落盘 | in/out证据 | 结论 |
|---|---:|---:|---|---|
| life | ✅ | ✅ | in=48 / out=58 | 🟢 通过 |
| ops | ✅ | ✅ | in=3 / out=6 | 🟢 通过 |
| company | ✅ | ✅ | in=2 / out=2（含E2E-PROBE） | 🟢 通过 |
| code | ✅ | ❌ | in=0 / out=0 | ⚪ 本期延后（deferred） |

说明：
- company 已完成补验（检索命中 `[E2E-PROBE]` inbound/outbound）。
- code 由用户确认“本期不补验”，标记 deferred，不作为本次发布阻断项。

## 4) 收口结论
- **本轮代码收口完成**：P0问题已关闭，RC打包通过。
- **项目级收口（本期范围）已完成**：life/ops/company 已满足发布门槛。
- **双通道发布已完成**：ClawHub + Internal Market 均发布成功。

## 5) 下一步（最小动作）
1. 执行发布后观察（建议 3 天），期间维持 `CAS_SCOPE_MODE=gateway`。
2. 每日输出 report 并沉淀复盘建议（手动触发模式）。
3. 满足稳定门槛后评估切换 `CAS_SCOPE_MODE=agent`。
