# Node 2 Review Context — 策略选择器

## Project

`stock-picking` is being redesigned from a monolithic stock-picking skill into a modular SOP orchestration layer.

Confirmed Node 0:
- External trigger accepts only one atomic run: single market + single strategy + single run mode.
- Batch/full workflows are expanded outside Node 0 and correlated by `correlation_id`.
- Node 0 validates and audits; it does not own cron, market calendar, strategies, or trade execution.
- v1 rejects multi-market input, `mixed`, `full`, `monitor`, and `dry_run: false`.

Confirmed Node 1:
- Node 1 emits normalized `run_context`.
- Node 1 owns market-local date/timezone/session gating and structured decisions.
- Node 1 emits `decision: proceed | skip | needs_override | fail`.
- Downstream strategy modules only run when Node 1 returns `decision=proceed`.
- Calendar unknown/manual override semantics are handled in Node 1, not in strategies.

## Node 2 To Review

Node 2: `策略选择器`

Baseline text in `REQ-01.md`:
- Old version assumes TAROC as the default strategy.
- User can run “discovery only / validation only / weekly review”, but strategy choice is not a plugin contract.
- Serenity/chokepoint has not been formally plugged in yet.
- Suggested direction: define unified strategy interface; each strategy outputs a draft list with `strategy_id`, `strategy_version`, evidence, negative evidence, and confidence.

## Main Proposal Draft

Recommended boundary:
- Node 2 is a strategy registry and router, not a strategy engine.
- Node 2 validates that the requested `strategy_id` is installed, allowed for the requested `market`, and compatible with `run_mode`.
- Node 2 binds the canonical strategy implementation and version, then dispatches exactly one strategy for the atomic run.
- Node 2 does not perform strategy fusion, score normalization, candidate ranking, evidence interpretation, fallback substitution, or portfolio risk work.
- Multi-strategy orchestration remains outside Node 2. Each atomic run calls one strategy.

Recommended input:
- Atomic Node 0 request.
- Node 1 `run_context` with `decision=proceed`.
- `strategy_id: taroc | chokepoint | custom`.
- `strategy_version`.
- `market`.
- `run_mode: discovery | validation | tracking`.
- `universe`.
- `dry_run: true`.

Recommended registry fields:
```yaml
strategy_id: taroc | chokepoint | custom
strategy_name: string
strategy_version: semver
entrypoint: path_or_skill_ref
supported_markets: [US, HK, CN]
supported_run_modes: [discovery, validation, tracking]
required_inputs: string[]
output_schema_version: semver
status: active | experimental | deprecated | disabled
owner: string
last_reviewed_at: ISO8601
```

Recommended output:
```yaml
request_id: uuid
correlation_id: uuid
strategy_id: string
strategy_version: semver
strategy_entrypoint: string
strategy_status: active | experimental | deprecated | disabled
dispatch_decision: dispatch | reject | needs_review
reject_reason: none | strategy_not_found | unsupported_market | unsupported_run_mode | version_not_found | strategy_disabled | custom_ref_invalid | schema_mismatch
expected_output_schema: draft_candidates.v1
selector_warnings: string[]
```

Recommended behavior:
- `strategy_id=taroc`: dispatch to TAROC strategy when market/run_mode are supported.
- `strategy_id=chokepoint`: dispatch to Chokepoint strategy when market/run_mode are supported.
- `strategy_id=custom`: require a resolvable `custom_strategy_ref` approved in registry or local config; reject free-text strategies.
- `strategy_version` should be explicit. If omitted in a manual call, Node 2 may resolve to registry default and emit a warning; cron/sop should be strict.
- Deprecated strategies may run for manual caller with warning; disabled strategies reject.
- If a strategy is unavailable, Node 2 should reject. It should not silently substitute TAROC or another fallback.
- Node 2 may expose registry metadata for observability, but should not call downstream modules when dispatch rejects.

Key questions:
1. Should v1 support `strategy_version=latest`, or require exact semver?
2. Should `validation` and `tracking` be run modes of strategy modules, or should they belong entirely to later generic modules?
3. Should Chokepoint v1 be `experimental` and manual-only until output schema is proven?
4. Should a strategy registry live in `src/strategies/registry.yaml`, or in the SOP text first?

## Requested Independent Proposal / Review Output

Please provide:
- recommended boundary,
- proposed input/output contract changes,
- registry design,
- failure/reject behavior,
- risks and missing cases,
- acceptance criteria,
- disagreements with the main proposal.
