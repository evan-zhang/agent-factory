# stock-picking S3 Design

status: changed-after-review
baseline_review: reviews/GRV-battle-round3-M3.5-review-2026-06-24.md
baseline_time: 2026-06-24
last_design_change: 2026-06-24

## 1. 产品目标

`stock-picking` v1.0.0 是股票研究与候选生命周期的 SOP 编排层，不是自动交易系统，也不是 TAROC 单策略 skill 的改名版本。

S3 的目标是把 `REQ-01.md` 与 `design/GRV.md` 固化为可实现、可审查的 baseline：

- Node 0-13 有明确模块边界、输入输出、失败行为和审计链。
- 策略层只产结构化研究输出，不写候选池、不推消息、不触达券商。
- 统一数据契约、registry、execution guard 先冻结，再进入 S4 实施。
- M4a 先实现安全与验证底座，M4b 再拆业务模块。

成功标准：

- 任何 atomic run 都能从 `request_id/correlation_id` 追溯到策略、候选、证据、审批和风险事件。
- `dry_run=false` 或 broker action 无法绕过 approval artifact 与 execution guard。
- registry 选择过程可复算、可审计、无 fallback。
- 旧 CSV 只作为兼容投影，不再是 canonical event store。

## 2. 非目标与边界

不做：

- 不在 skill 内写 cron schedule；Gateway/外部 SOP 负责调度。
- 不自动买入，不自动卖出。
- 不把 Chokepoint v1 接入 cron/sop。
- 不把 Serenity 履历、战绩、粉丝量作为信号或权重。
- 不在 S4 边写边改 P0 schema；变更必须进 Decision Log。
- 不把 CSV 当 canonical 存储。
- 不做图数据库、RAG、实时 webhook 或组合自动清仓。

边界：

- `stock-picking` 只编排流程和契约。
- TAROC / Chokepoint 是策略插件。
- validation / tracker / target pool / approval / reconcile / monitor 是可复用模块。
- `market-calendar`、registry validator、schema validator、evidence store 是共享基础设施候选。

## 3. S3 Baseline 技术方案

### 3.1 数据流

```text
Node 0 atomic_request
  -> Node 1 run_context
  -> Node 2 strategy_dispatch
  -> Node 3/4 strategy output
  -> Node 5 draft_candidates
  -> Node 6 validation_event
  -> Node 7 candidate_record
  -> Node 8 tracking_event
  -> Node 9 target_pool_item
  -> Node 10 approval
  -> Node 11 reconcile_report
  -> Node 12 risk_event / trade_log_event / execution_guard_decision
  -> Node 13 evidence_ref / claim
```

Canonical writes are append-only JSON/JSONL events under the future `data/events/` layout. CSV files remain read-only import sources or compatibility projections until migration is complete.

Every event must carry:

- `schema`
- `request_id`
- `correlation_id`
- `created_at` or equivalent timestamp
- source node or producer
- evidence refs where the event makes a factual or investment claim

### 3.2 Module Boundaries

| Module | Owns | Must Not Own |
|---|---|---|
| `sop-orchestrator` | Node order, skip/fail routing, output formatting | Strategy logic, cron, broker calls |
| `market-calendar` | `run_context.v1` | Strategy selection, universe search |
| `strategy-selector` | Registry lookup and `strategy_dispatch.v1` | Strategy execution, fallback, ranking |
| `strategies/taroc` | TAROC research output | CSV writes, validation, pool, broker action |
| `strategies/chokepoint` | Theme research and promoter-eligible draft output | cron/sop, tracking, position actions |
| `draft-emitter` | Normalizing strategy output to `draft_candidates.v1` | Validation state |
| `selection-validation` | `validation_event.v1` | Draft mutation, candidate deletion |
| `candidate-store` | Candidate state machine | Tracking timeline |
| `position-tracker` | `tracking_event.v1`, weekly review | Human removal execution |
| `target-pool-manager` | Build-ready target pool queue | Broker order placement |
| `buy-approval-gate` | Machine-checkable approval artifact | Pretrade checks implementation |
| `execution-guard` | Broker action hard gate and audit | Strategy decisions |
| `position-reconcile` | Read-only broker/local reconciliation | Ledger mutation |
| `position-monitor` | Risk event generation | Unguarded sell/buy execution |
| `evidence-store` | Evidence refs, claims, dedup, source quality | Claim generation without sources |

### 3.3 Interface Specs

P0 schema names are frozen in `src/references/data-schema.md`:

- `atomic_request.v1`
- `run_context.v1`
- `strategy_dispatch.v1`
- `draft_candidates.v1`
- `theme_research.v1`
- `validation_event.v1`
- `candidate_record.v1`
- `tracking_event.v1`
- `target_pool_item.v1`
- `approval.v1`
- `reconcile_report.v1`
- `risk_event.v1`
- `trade_log_event.v1`
- `execution_guard_decision.v1`
- `evidence_ref.v1`
- `claim.v1`

The S4 validator may implement these as JSON Schema, Pydantic, Zod, or equivalent, but the validator must preserve field names and reject unknown critical enums.

### 3.4 Registry Design

Registry file:

```text
src/strategies/registry.yaml
```

Registry schema and selector design:

```text
src/references/registry-design.md
```

Selector atomicity:

1. Read `registry.yaml` bytes once.
2. Compute `registry_snapshot_hash` from those bytes.
3. Parse and validate the in-memory snapshot.
4. Resolve default or exact semver from the same snapshot.
5. Compute `registry_record_hash` from the selected normalized record.
6. Emit `strategy_dispatch.v1` with both hashes.

The selector must not re-read `registry.yaml` between steps 1-6. S4 can implement this as copy-on-read in a single process; no filesystem transaction is required for v1 as long as the selector never mixes two snapshots.

Version policy:

- cron/sop require exact semver.
- manual may omit version only when `defaults.<strategy_id>` exists and points to a unique active or allowed record; emit warning.
- `latest` is not supported.
- No fallback to TAROC or any other strategy.

`custom_ref` policy:

- Whitelist file lives at `src/strategies/custom_refs.yaml`.
- The whitelist is loaded in the same snapshot phase as registry validation.
- Entries must point to registry-approved strategy records or signed internal references, never raw paths or free text.
- Every whitelist change must be recorded in `design/DESIGN.md` Decision Log or a future migration/change log before S4 use.

### 3.5 Chokepoint Maturity Gate

Chokepoint v1 remains:

- `status=experimental`
- `market=US`
- `caller=manual`
- `run_mode=discovery`

Exit criteria use AND logic:

- at least 6 calendar months since first accepted manual run
- at least 10 completed manual runs
- zero major thesis break events during the evaluation window
- factory-reviewer approval before any HK/CN, tracking, sop, or cron expansion

Major thesis break definition:

- any `risk_event.v1` or `claim.v1` tagged `thesis_broken=true` and `severity in {warning, critical}`
- or a human review event marking `thesis_breaking`
- or evidence that invalidates the core supply-chain bottleneck, trend anchor, or scarcity premise

### 3.6 File Structure

Target S4 structure:

```text
src/
  SKILL.md
  flows/
    discovery.md
    validation.md
    weekly-review.md
    target-pool.md
    approval.md
    reconcile.md
    risk-monitor.md
  references/
    data-schema.md
    registry-design.md
    execution-guard.md
    gateway-cron.md
    migration-plan.md
    taroc-methodology.md
  strategies/
    registry.yaml
    custom_refs.yaml
    taroc.md
    chokepoint.md
  scripts/
    validate_schema.py
    validate_registry.py
    dry_run_orchestrator.py
    event_store.py
    cron_readiness.py
    operator_notification.py
    migrate_legacy_csv.py
```

S4 may add implementation files, but it must not collapse these responsibilities back into one monolithic `SKILL.md`.

### 3.7 User Experience And Error Fallback

User-facing results should be concise:

- `proceed`: summarize market, strategy, run mode, produced drafts/events, evidence coverage, warnings.
- `skip`: heartbeat with calendar reason and next open time.
- `needs_override`: show exact override reason needed; do not continue.
- `fail/reject`: show reject code, source node, and remediation.
- `execution_blocked`: show blocked action, missing artifact/check, and audit id.

Internal errors must become structured events where possible. A failure must never be silently converted to “no candidates”.

### 3.8 Failure Behavior

Hard fail / reject:

- non-atomic request
- `dry_run=false` at Node 0 in v1
- `run_context.decision != proceed` before strategy dispatch
- unknown strategy or unsupported market/run_mode
- registry invalid or hash cannot be computed
- missing required evidence refs
- `removed` written by non-human actor
- real broker action without valid approval and execution guard pass

Skip:

- closed market, weekend, holiday, known non-runnable session

Needs override:

- manual/sop with unknown calendar
- explicit user override path with expiry

Warning:

- manual strategy version omitted and default used
- half-day allowed by policy
- Chokepoint consensus overlap or high uncertainty that does not block theme research

### 3.9 Granularity Decision

S4 should start as one skill package with separated references/scripts, not many published skills. Reason:

- P0 schema and registry need one baseline.
- The existing stock-picking-v2 assets are still a single package.
- Premature multi-skill publishing would make M3.5 and S5 harder to gate.

Future split candidates after S5:

- `market-calendar`
- `evidence-store`
- `execution-guard`
- `position-reconcile`
- `position-monitor`

## 4. 风险、约束与验收标准

### 4.1 Risks

- Registry drift during selection.
  - Mitigation: copy-on-read snapshot, snapshot hash, record hash, validator test.
- Schema drift during S4.
  - Mitigation: P0 schema freeze; changes require Decision Log.
- Execution guard only exists in docs.
  - Mitigation: M4a implements guard skeleton and refusal tests before broker path edits.
- Legacy CSV migration breaks history.
  - Mitigation: compatibility projection first, migration audit, rollback plan.
- Chokepoint becomes cron before mature.
  - Mitigation: registry caller restrictions and AND exit criteria.
- Validation idempotency breaks on rerun.
  - Mitigation: use `calendar_checked_at` and `validation_run_id`; do not rely only on `signal_date`.

### 4.2 Constraints

- No Gateway restart or process control from this project.
- No real buy/sell without Evan approval.
- All broker calls pass execution guard.
- Gateway cron arguments must come from owner-approved schedule/config, not directly from user-supplied message fields.
- `production_calendar` remains a hard reject until M4e backs it with a real market-calendar source and reviewer approval.
- All quant data path work must first read `DATA-PATHS.md`.
- Chokepoint v1 remains manual-only.
- Factory-reviewer performs M3.5 review before Ralph Loop / S4.

### 4.3 Acceptance Criteria

- `design/DESIGN.md` covers module boundaries, data flow, file structure, UX/error fallback, failure behavior, and granularity decision.
- `src/references/data-schema.md` freezes all P0 schema names and rejection rules.
- `src/strategies/registry.yaml` contains TAROC and Chokepoint records with caller/status restrictions.
- `src/references/registry-design.md` defines snapshot atomicity, hash policy, version policy, custom_ref whitelist, and reject codes.
- `src/references/execution-guard.md` defines minimum guard skeleton and refusal tests.
- Chokepoint exit criteria use explicit AND logic and define major thesis break.
- Validation idempotency avoids depending only on mutable `signal_date`.
- M3.5 review is requested before implementation.

## 5. Decision Log

- 2026-06-24: S3 baseline keeps one package with separated modules/references; defer multi-skill publishing until after S5.
- 2026-06-24: Registry selector uses copy-on-read snapshot atomicity for v1.
- 2026-06-24: `custom_ref` whitelist lives in `src/strategies/custom_refs.yaml` and is audited by design/change log.
- 2026-06-24: Chokepoint exit criteria are AND, not OR.
- 2026-06-24: M4a implements offline validators first: `validate_schema.py`, `validate_registry.py`, and `execution_guard.py`; broker integrations remain out of scope until guard tests pass.
- 2026-06-24: M4b keeps `stock-picking` as one skill package through S5, with modules separated as `flows/`, `references/`, and `scripts/`; published multi-skill split is deferred.
- 2026-06-24: M4c turns the Gateway cron pilot design gate into `src/scripts/cron_readiness.py`; this remains a local dry-run gate and does not authorize production schedules without operator route and calendar-source readiness.
- 2026-06-24: M4d keeps production cron blocked but allows explicit `manual_pilot_override` with a reason for local dry-run pilots; operator notification is a validated dry-run route contract, not an in-skill sender.
- 2026-06-24: After M4c/M4d WARN, `production_calendar` is hard-rejected until M4e, Gateway cron parameter sources are constrained to owner-approved schedule/config, and `severity_min` became an executable operator notification threshold.

## 6. Post-review Changes

- 2026-06-24: After M3.5 WARN, `data-schema.md` restored REQ-01 evidence/claim contracts and migration/registry/custom_ref/execution guard minor gaps were closed.
- 2026-06-24: M4a added executable schema validation for all 16 P0 schemas plus `legacy_csv_projection.v1`, registry dispatch validation with snapshot and record hashes, and execution guard refusal tests before broker path edits.
- 2026-06-24: Rewrote `src/SKILL.md` from the legacy CSV monolith into the SOP orchestration entrypoint and added event-schema flow docs for target pool, approval, reconcile, and risk monitor.
- 2026-06-24: Added append-only JSONL `event_store.py` and read-only `migrate_legacy_csv.py` projection skeleton so business modules can write validated events before any CSV compatibility output.
- 2026-06-24: Added `cron_readiness.py` and tests for absolute event root, registry cron policy, CLI allowlist, discovery idempotency, validation promotion gating, and dry-run pilot smoke.
- 2026-06-24: Added `operator_notification.py`, explicit calendar source labels, and manual pilot override reason enforcement.
- 2026-06-24: Closed M4c/M4d reviewer majors M001-M003 with production-calendar reject tests, Gateway parameter-source documentation, and severity threshold filtering.
