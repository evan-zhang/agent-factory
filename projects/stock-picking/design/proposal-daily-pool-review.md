# Design Proposal: Daily Rolling Pool Review

> 提出时间：2026-06-25 17:51 | 提出者：Evan | 审计请求：factory-reviewer

## 背景

S7 原计划"4 周观察"定义为独立的 weekly-review 流程，与每日 discovery cron 割裂。Evan 指出问题：观察应该是动态的，每日 discovery 时同时检查已在池中接近/超过 4 周的标的，决定保留或移除。

## 当前设计缺陷

1. **观察不动态**：每日 discovery cron 只从 universe 选新候选，不知道 target pool 里已有什么、呆了多久
2. **W4+ 检查延后**：只在"周复盘"时检查老候选，不是每天
3. **universe 与 target pool 无联动**：新候选与老候选互不影响，池子不滚动

## 提议方案

### 核心变更：daily cron 追加 pool review 步骤

每日 discovery cron 在完成新候选 discovery + pilot analysis 之后，追加一步 **pool review**：

1. 读取 target pool 中该市场的 active items
2. 按 `created_date` 计算入池天数，筛出 W3+（≥21 天）的标的
3. 对每个 W3+ 标的：
   - 拉 latest quote（复用 market_data.py）
   - 执行一次快速 web_search（正面+负面），评估 thesis 是否仍然成立
   - 生成 `tracking_event.v1`（event_type=weekly_review，week_id 按实际计算）
4. 根据评估结果给出建议：
   - **保留**：thesis 仍成立，价格在预期区间
   - **观察**：thesis 有变化但不足以移除，延长观察
   - **建议移除**：thesis break、价格严重偏离、或已入池 >W6 仍未升级
5. W4+ 的"建议移除"推送 human decision request 到频道

### 受影响的组件

| 组件 | 变更类型 | 说明 |
|------|----------|------|
| `discovery_job.py` | 追加步骤 | discovery + pilot analysis 后调用 pool review |
| 新增 `pool_reviewer.py` | 新模块 | 读取 target pool、计算 age、拉 quote、执行 thesis check |
| `pilot_analyzer.py` | 无变更 | 仍只管本轮 discovery 质量 |
| `weekly-review.md` | 重写 | 从独立流程降级为 daily cron 的 pool review 子步骤 |
| `gateway-cron.md` | 更新 prompt | 三档 cron payload 追加 pool review 步骤 |
| `tracking_event.v1` | 无 schema 变更 | event_type 已含 weekly_review |
| `target_pool_item.v1` | 无 schema 变更 | created_date + status 已足够 |

### cron payload 变化（每档市场）

```
# 现有步骤 1-6 不变（plan → research → validate → discovery_job → pilot_analyzer）
# 新增步骤 7：
PYTHONPATH=src/scripts python3 src/scripts/pool_reviewer.py \
  --event-root $STOCK_PICKING_EVENT_ROOT \
  --market CN \
  --universe-file src/config/universe.yaml \
  --universe-ref default \
  --review-threshold-weeks 3 \
  --remove-threshold-weeks 6
```

### 不变的部分

- `weekly-review.md` 仍然作为 SOP 参考，但不再是独立 cron job
- target pool 的写入仍只通过 discovery → draft → target-pool flow
- execution guard 仍阻断一切真实交易
- tracking_event 仍只写建议，不自动移除

### 风险

1. **cron 耗时增加**：如果 pool 有 10+ 个 W3+ 标的，每个都要 quote + web_search，timeout 可能不够
2. **web_search rate limit**：pool review 的搜索与 discovery 的研究搜索叠加
3. **target pool 持久化**：当前 target pool 的存储方式是 CSV projection（migrate_legacy_csv.py），pool_reviewer 需要读取它
4. **并发安全**：pool review 读 target pool 时 discovery 可能正在写 event store（同一进程顺序执行，无并发）

### 待 reviewer 审计的问题

1. 这个方案是否与现有 schema（tracking_event.v1, target_pool_item.v1, draft_candidates.v1）兼容？
2. pool_reviewer 放在 discovery_job.py 内部还是独立脚本更合理？
3. W3/W6 阈值是否合理？还是应该 W2/W4？
4. 每日生成 tracking_event 会不会导致 event store 膨胀？
5. 是否需要在 cron payload 中限制 pool review 的最大标的数（避免 timeout）？
