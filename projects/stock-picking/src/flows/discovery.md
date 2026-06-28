# Discovery Flow

Discovery 负责把一次市场研究请求产成 `draft_candidates.v1`。它不写 canonical CSV，不推送未经审计的交易建议，不触达券商。

TAROC 完整方法论见 `references/taroc-methodology.md`。

## 输入

- `atomic_request.v1`
- `run_context.v1`
- `strategy_dispatch.v1`
- evidence refs and claims

## 前置检查

1. `run_context.decision` 必须是 `proceed`。
2. `strategy_dispatch.decision` 必须是 `dispatch`。
3. registry record hash 必须存在。
4. market/run_mode 必须与 atomic request 一致。

## TAROC 摘要

### Phase T: Theme Discovery

发现 5-8 个候选赛道，记录来源为 `evidence_ref.v1`。搜索或数据来源必须被保存为证据引用；如果只是 AI inference，必须显式标记。

### Phase A: Analysis

对赛道做结构化评分：

- trend strength
- catalyst clarity
- policy or capital support
- valuation sanity
- crowdedness risk

评分只是 strategy-local signal，不直接写入 target pool。

### Phase R: Research

对候选个股生成研究摘要：

- 基本面和催化
- 正面证据
- 负面证据
- bear case search result
- 数据来源质量

`negative_evidence_searched` 必须为 true，否则 draft invalid。

S5b 起，Discovery CLI 支持通过 `--research-file` 注入外层研究结果。文件格式：

```json
{
  "items": [
    {
      "symbol": "AAPL.US",
      "negative_search_performed": true,
      "negative_search_query": "AAPL.US risks bear case",
      "positive": [{"title": "...", "url": "...", "publisher": "...", "excerpt": "...", "source_type": "news"}],
      "negative": [{"title": "...", "url": "...", "publisher": "...", "excerpt": "...", "source_type": "news"}]
    }
  ]
}
```

`research_data.py` 会把 positive / negative 条目规范化为 `evidence_ref.v1`，并生成对应的 `claim.v1`。外层 agent 负责执行 web/news 搜索；Python orchestrator 只消费结果文件，不直接联网。

S5d 起，外层 agent 必须先运行：

```bash
PYTHONPATH=src/scripts python3 src/scripts/research_protocol.py plan \
  --market US \
  --universe-file src/config/universe.yaml \
  --universe-ref default
```

然后对每个 `positive_query` 与 `negative_query` 执行搜索，写入 research JSON，再运行：

```bash
PYTHONPATH=src/scripts python3 src/scripts/research_protocol.py validate /tmp/research.json \
  --market US \
  --universe-file src/config/universe.yaml \
  --universe-ref default
```

只有 validate 通过后，才允许把该文件传给 discovery：`--research-file /tmp/research.json`。即使负面搜索没有结果，也必须写 `negative_search_performed=true` 和实际使用的 `negative_search_query`。

S5e 起，默认股票池来自 `src/config/universe.yaml`。cron 只传 `--universe-file src/config/universe.yaml --universe-ref default`，不再在调度 payload 里硬编码 symbol 列表。扩容、剔除、分层测试都应优先编辑 universe 配置。

### Phase O: Odds

估算上行、下行、入场观察区间和 stop reference。这里产生研究字段，不产生下单动作。

### Phase C: Conviction

有 TradingAgents 时可运行多空辩论；没有时用同 LLM 正反抗辩。输出必须保留 bull/bear evidence refs。

## 输出

生成 `draft_candidates.v1`：

- `produced_by.strategy_id`
- `produced_by.strategy_version`
- `produced_by.registry_record_hash`
- candidates with source evidence and negative evidence
- `next_step=validation`
- warnings / partial / failure

Legacy CSV projection 可由后续 migration/projection 模块生成；Discovery 本身不把 CSV 当 source of truth。

## 用户反馈

返回简洁摘要：

- market / strategy / run mode
- 候选数量
- evidence coverage
- negative evidence status
- warnings
- reject/failure code, if any

S5c 起，cron 应优先调用 `src/scripts/discovery_job.py`。该 wrapper 会：

- 执行 discovery；
- 本次写入 `draft_candidates.v1` 时渲染 `discovery_report.py`；
- 休市或无新 draft 时输出 `HEARTBEAT_OK`，避免误读历史 draft。
