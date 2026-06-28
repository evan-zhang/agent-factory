# Data Schema Baseline

Status: S3 draft freeze
Date: 2026-06-24

This file replaces the old CSV field list as the P0 schema baseline. Legacy CSV files remain compatibility projections or migration inputs; they are not canonical event storage.

## Schema Changelog

This changelog reconciles S3 schema freeze with `REQ-01.md` Node 13. M4a validators must implement the schema below, not the pre-review drifted draft.

- 2026-06-24: `evidence_ref.v1.evidence_id` keeps the REQ-01 `ev_<ulid>` prefix. This avoids confusion with plain UUID entities such as candidates, drafts, approvals, and risk events.
- 2026-06-24: `evidence_ref.v1.source_type` keeps `community` and `unverified` from REQ-01 and adds explicit institutional sources (`regulatory`, `broker_data`, `company_filing`, `news`, `analyst`, `internal_note`). `unverified` remains a first-class value; do not collapse it into `analyst` or `source_quality=unknown`.
- 2026-06-24: `evidence_ref.v1` restores the REQ-01 dual quality fields (`publisher_authority`, `ai_classified_quality`, `classification_method`) and keeps `source_quality` only as a derived compatibility bucket.
- 2026-06-24: `claim.v1` restores the REQ-01 two-axis model (`claim_kind` + `polarity`) and `valid_until`. `claim_type` is not canonical in v1 because it loses cases such as a positive catalyst with a negative risk attached.
- 2026-06-24: `risk_event.v1.source=strategy_tracking` and `event_type=thesis_broken` are S3 extensions. They represent promotion of a tracking or claim break into the risk stream and must be documented in emitted event audit fields.

## Global Rules

All P0 records must include:

- `schema`
- `request_id`
- `correlation_id`
- `created_at` or a schema-specific timestamp
- source node or producer

All investment claims must reference `evidence_ref.v1` or explicitly mark the content as AI inference. AI inference cannot be presented as source fact.

Unknown critical enum values must fail validation. Optional extension fields must live under `extensions`.

## Schema Index

P0:

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

Compatibility:

- `legacy_csv_projection.v1`

## `atomic_request.v1`

```yaml
schema: atomic_request.v1
request_id: uuid
correlation_id: uuid
caller: manual | cron | sop
requested_at: ISO8601
market: US | HK | CN
strategy_id: taroc | chokepoint | custom
strategy_version: semver | null
custom_ref: string | null
run_mode: discovery | validation | tracking
run_date: YYYY-MM-DD
signal_date: YYYY-MM-DD
timezone: Asia/Shanghai | Asia/Hong_Kong | America/New_York
universe_ref: string
dry_run: true
priority: low | normal | high
idempotency_key: string
```

Reject:

- list-valued market or strategy
- `run_mode=full`
- `run_mode=monitor`
- `dry_run=false` in v1
- `custom_ref` free text or path traversal

## `run_context.v1`

```yaml
schema: run_context.v1
request_id: uuid
correlation_id: uuid
decision: proceed | skip | needs_override | fail
calendar_status: open | closed | half_day | emergency_closed | unknown
market_session: premarket | regular | postmarket | closed | outside_session | unknown
session_open_at: ISO8601 | null
session_close_at: ISO8601 | null
next_open_at: ISO8601 | null
calendar_skip_reason: none | weekend | holiday | half_day_policy | emergency_closure | outside_session | calendar_unavailable | invalid_context
failure_code: null | INVALID_TIMEZONE | INVALID_MARKET_DATE | CALENDAR_SOURCE_ERROR | UNSUPPORTED_MARKET | AMBIGUOUS_CONTEXT
calendar_source: string
calendar_source_version: string
calendar_checked_at: ISO8601
override_id: string | null
override_reason: string | null
override_expires_at: ISO8601 | null
context_warnings: string[]
```

Closed, holiday, weekend, unknown cron, invalid timezone, and unsupported market must not proceed to strategy dispatch.

## `strategy_dispatch.v1`

```yaml
schema: strategy_dispatch.v1
request_id: uuid
correlation_id: uuid
node_id: node_2_strategy_selector
decision: dispatch | reject
strategy_dispatch:
  strategy_id: string
  strategy_version: semver
  entrypoint: string
  output_schema: draft_candidates.v1 | theme_research.v1
  registry_version: string
  registry_snapshot_hash: string
  registry_record_hash: string
  policy_flags: string[]
reject:
  code: string | null
  message: string | null
warnings: string[]
audit:
  selected_at: ISO8601
  custom_ref: string | null
```

Reject when:

- upstream `run_context.decision != proceed`
- cron/sop omit exact semver
- unsupported market/run mode/caller
- strategy disabled or invalid
- Chokepoint experimental called by cron/sop
- dispatch lacks `registry_record_hash`

## `draft_candidates.v1`

```yaml
schema: draft_candidates.v1
draft_candidates_version: "1.0.0"
produced_by:
  strategy_id: string
  strategy_version: semver
  registry_record_hash: string
produced_at: ISO8601
request_id: uuid
correlation_id: uuid
market: US | HK | CN
run_mode: discovery | validation
universe_ref: string
themes:
  - theme_id: string
    theme_label: string
    propagation_phase: 1 | 2 | 3 | 4 | null
    window_remaining_days: int | null
    theme_score: number | null
    crowdedness_score: number | null
    sources: evidence_ref[]
candidates:
  - draft_id: uuid
    strategy_run_id: uuid
    strategy_id: string
    strategy_version: semver
    source_research_id: uuid | null
    stock_code: string
    stock_name: string
    market: US | HK | CN
    price: number
    thesis_summary: string
    confidence:
      source: strategy_self_rated
      level: high | medium | low
      score: number | null
    tracking_horizon:
      kind: short_event | quarterly | structural
      default_window_sessions: int
    source_evidence: evidence_ref[]
    negative_evidence: evidence_ref[]
    negative_evidence_searched: boolean
    expires_at: ISO8601
    next_step: validation
warnings: string[]
partial: boolean
failure:
  code: null | BUDGET_EXHAUSTED | TIMEOUT | NEGATIVE_EVIDENCE_MISSING | UNIVERSE_EMPTY | UPSTREAM_ERROR
  message: string | null
```

Reject as valid draft when evidence refs are missing, negative evidence search is missing, or strategy identity/hash is absent.

## `theme_research.v1`

```yaml
schema: theme_research.v1
theme_research_version: "1.0.0"
research_id: uuid
request_id: uuid
correlation_id: uuid
strategy_id: chokepoint
strategy_version: semver
produced_at: ISO8601
market: US
theme:
  theme_name: string
  one_liner: string
  lead_source: lead_scanner | reverse_engine | manual
  bom_tree_ref: string
  chokepoint_layer: string
  supplier_count: int | null
  trend_anchor:
    trend_type: tech_transition | penetration_inflection | policy_mandate | geopolitics
    trend_size: string
    trend_persistence: short | medium | long
signals:
  - signal: price | lead_time | capital | patent | talent | regulation
    strength: number
    source_evidence: evidence_ref[]
evidence: evidence_ref[]
negative_evidence: evidence_ref[]
break_conditions:
  - condition: string
    trigger_evidence: string
    severity: thesis_breaking | position_breaking
uncertainty_level: low | medium | high
risk_flags:
  single_path_dependency: boolean
  micro_cap_stampede_risk: boolean
  data_provenance_weak: boolean
  consensus_overlap: boolean
upgrade_triggers:
  - condition: string
    required_evidence: string
promotion_status: observe | eligible_for_draft | rejected
reject_reason: string | null
```

High uncertainty cannot promote directly to draft.

## `validation_event.v1`

```yaml
schema: validation_event.v1
validation_event_id: uuid
validation_run_id: uuid
draft_id: uuid
request_id: uuid
correlation_id: uuid
calendar_checked_at: ISO8601
validation_session_key: string
signal_date: YYYY-MM-DD
calendar_status: open | half_day
half_day_policy: exclude | allow
verdict: confirm | watch | reject | overheated | thesis_broken | validation_skipped
validation_confidence:
  level: high | medium | low
  rationale: string
price_action: string
thesis_update: string
new_evidence: evidence_ref[]
negative_update: evidence_ref[]
promote_candidate: boolean
```

Idempotency key:

```text
(draft_id, validation_run_id, calendar_checked_at, validation_session_key)
```

`signal_date` is retained for reporting but must not be the sole idempotency anchor.

## `candidate_record.v1`

```yaml
schema: candidate_record.v1
candidate_id: uuid
origin_draft_id: uuid
request_id: uuid
correlation_id: uuid
source_drafts:
  - draft_id: uuid
    strategy_id: string
    strategy_version: semver
    confidence:
      level: high | medium | low
stock_code: string
market: US | HK | CN
state: active | watching | promote_suggested | expired | removed
actor: system | agent | human
aggregate_thesis: string
aggregate_thesis_kind: concatenation | summary
created_at: ISO8601
expires_at: ISO8601
last_state_event_id: uuid
```

Reject when `state=removed` and `actor != human`.

## `tracking_event.v1`

```yaml
schema: tracking_event.v1
tracking_event_id: uuid
candidate_id: uuid
origin_draft_id: uuid
request_id: uuid
correlation_id: uuid
week_id: YYYY-Www
event_type: catalyst_update | risk_update | price_action | promote_suggested | remove_suggested | weekly_review
actor: system | agent | human
suggested_reason: string | null
supporting_evidence: evidence_ref[]
state_transition:
  from_state: string | null
  to_state: string | null
created_at: ISO8601
```

AI may write suggestions, not final human removals.

## `target_pool_item.v1`

```yaml
schema: target_pool_item.v1
pool_item_id: uuid
candidate_id: uuid
origin_draft_id: uuid
request_id: uuid
correlation_id: uuid
stock_code: string
market: US | HK | CN
entry_price: number
stop_loss: number
target_price: number
position_amount: number
sizing_state: sized | awaiting_sizing
promotion_reason: string
status: active | deferred | rejected | built | expired
created_date: YYYY-MM-DD
decision_deadline: YYYY-MM-DD
diff_audit_ref: string
created_at: ISO8601
```

Active build-ready rows require entry, stop, target, nonzero size or explicit `awaiting_sizing`, and deadline.

## `approval.v1`

```yaml
schema: approval.v1
approval_id: uuid
pool_item_id: uuid
candidate_id: uuid
request_id: uuid
correlation_id: uuid
action: buy
approval_state: requested | approved | rejected | expired | manual_ledger_restored
approved_by: Evan | null
approved_at: ISO8601 | null
approval_note: string
pretrade_check_id: uuid
expires_at: ISO8601
created_at: ISO8601
```

Real buy requires `approval_state=approved`, `approved_by=Evan`, non-expired approval, and passed pretrade check.

## `reconcile_report.v1`

```yaml
schema: reconcile_report.v1
reconcile_run_id: uuid
request_id: uuid
correlation_id: uuid
generated_at: ISO8601
summary:
  matched: int
  missing_local_record: int
  broker_missing_position: int
  quantity_mismatch: int
  ledger_only: int
mismatches:
  - stock_code: string
    broker: futu | longbridge | guosen | manual | unknown
    status: matched | missing_local_record | broker_missing_position | quantity_mismatch | ledger_only
    reconcile_resolution: null | acknowledged | ledger_corrected | broker_corrected | will_not_fix
```

API brokers use broker truth; manual/guosen accounts may be `ledger_only`.

## `risk_event.v1`

```yaml
schema: risk_event.v1
risk_event_id: uuid
request_id: uuid
correlation_id: uuid
source: position_monitor | reconcile | portfolio_risk | execution_guard | strategy_tracking
stock_code: string | null
event_type: stop_loss_breach | drawdown_breach | quote_failed | reconcile_mismatch | execution_blocked | thesis_broken
severity: info | warning | critical
recommended_action: observe | notify | request_human_decision | execute_guarded_sell
execution_allowed: false
thesis_broken: boolean
evidence: evidence_ref[]
created_at: ISO8601
```

`execution_allowed` is always false in v1 risk events.

## `trade_log_event.v1`

```yaml
schema: trade_log_event.v1
trade_event_id: uuid
request_id: uuid
correlation_id: uuid
action: buy | sell | cancel | dry_run_entry | blocked
mode: dry_run | real
stock_code: string
market: US | HK | CN
approval_id: uuid | null
execution_guard_decision_id: uuid | null
broker: futu | longbridge | guosen | manual | unknown
status: pending | executed | blocked | failed | expired
created_at: ISO8601
expires_at: ISO8601 | null
```

Pending dry-run entries older than 7 days must be flagged or expired.

## `execution_guard_decision.v1`

```yaml
schema: execution_guard_decision.v1
decision_id: uuid
request_id: uuid
correlation_id: uuid
action: buy | sell | cancel | quote | reconcile
decision: allow | block | dry_run
block_code: string | null
approval_id: uuid | null
pretrade_check_id: uuid | null
broker: futu | longbridge | guosen | manual | unknown
market: US | HK | CN
created_at: ISO8601
audit:
  guard_version: string
  checks: string[]
```

Rejected real broker paths must not invoke the broker API.

## `evidence_ref.v1`

```yaml
schema: evidence_ref.v1
evidence_id: ev_<ulid>
created_at: ISO8601
created_by: node_3_taroc | node_4_chokepoint | node_6_validation | node_8_tracker | node_11_reconcile | human
source_url: string | null
source_id: string | null
source_type: primary | secondary | community | regulatory | broker_data | company_filing | news | analyst | internal_note | ai_inference | unverified
source_subtype: filing | press_release | patent | earnings_call | broker_report | news | social | other
title: string
excerpt: string
publisher: string | null
fetched_at: ISO8601
observed_at: ISO8601
language: string
snapshot_ref: string | null
claim_hash: string
publisher_authority: number
ai_classified_quality: number
classification_method: publisher_table | llm_judge | human
source_quality: high | medium | low | unknown
status: active | superseded | disputed | retracted | access_lost
content_hash: sha256
raw_snapshot_path: string | null
```

`source_url + claim_hash` duplicate writes must deduplicate.

## `claim.v1`

```yaml
schema: claim.v1
claim_id: cl_<ulid>
created_at: ISO8601
created_by: string
scope:
  market: US | HK | CN | null
  stock_code: string | null
  theme_id: string | null
  candidate_id: uuid | null
  draft_id: uuid | null
request_id: uuid
correlation_id: uuid
claim_text: string
claim_kind: support | refute | risk | catalyst | break_condition | neutral_context
polarity: positive | negative | mixed | neutral
thesis_broken: boolean
severity: info | warning | critical | null
confidence:
  source: strategy | validation | human | llm_judge
  level: high | medium | low
evidence_ids: string[]
negative_search_performed: true | false
negative_search_query: string | null
valid_until: ISO8601 | null
status: active | superseded | retracted
```

Break conditions and negative evidence are first-class claims.

## `legacy_csv_projection.v1`

Legacy CSV files:

- `drafts_{market}.csv`
- `candidates_{market}.csv`
- `four_week_tracker_{market}.csv`
- `target_pool.csv`
- `positions.csv`
- `trade_log.csv`

Compatibility rules:

- CSV imports must produce event records with migration audit ids.
- CSV projections must not be treated as source of truth after event migration.
- Free-text `reason` may become a claim only when tied to evidence or marked as historical note.
- Migration must preserve original row content and row hash for rollback.

## Verification

M4a must produce an executable schema validator before any business module depends on these records.

Required acceptance:

- Validator covers all 16 P0 schemas plus `legacy_csv_projection.v1`.
- Positive and negative fixtures exist for every critical enum and required identifier format, including `ev_<ulid>` and `cl_<ulid>`.
- Unknown critical enum values fail validation; optional extensions are accepted only under `extensions`.
- `validate_schema.py` can run locally without broker credentials or network access.
- Validator output includes schema name, record id when present, failure path, and machine-readable reject code.
