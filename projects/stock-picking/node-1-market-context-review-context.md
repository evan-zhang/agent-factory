# Node 1 Review Context — 交易日与运行上下文检查

## Project

`stock-picking` is being redesigned from a monolithic stock-picking skill into a modular SOP orchestration layer.

Current confirmed Node 0:
- External trigger accepts only one atomic run: single market + single strategy + single run mode.
- Batch or full workflows are expanded outside Node 0 and correlated by `correlation_id`.
- Node 0 validates and audits; it does not own cron, market calendar, strategies, or trade execution.
- v1 rejects multi-market input, `mixed`, `full`, `monitor`, and `dry_run: false`.

## Node 1 To Review

Node 1: `交易日与运行上下文检查`

Baseline text in `REQ-01.md`:
- Old `stock-picking-v2` reads `holidays/{market}.yaml`; when closed it returns `HEARTBEAT_OK`.
- Current `holidays/*.yaml` look more like textual notes than strict structured calendars.
- Static files are fragile for make-up workdays, half-days, HK typhoon/black rain closures, US daylight saving time, and ad-hoc suspensions.
- If every module checks trading days independently, behavior will drift.
- Suggested direction: extract `market-calendar` or shared infra.
- Output should include `is_trading_day`, `market_session`, `skip_reason`, `next_open_at`.
- Keep manual override for HK emergency closures and US half-day sessions.

## Main Proposal Draft

Recommended boundary:
- Node 1 owns pre-run normalization and context gating.
- Node 1 does not own long-term calendar data maintenance as business logic.
- Calendar data should be a shared infrastructure dependency, preferably `market-calendar`.
- Strategy modules should not decide whether the market is open; they consume normalized run context from Node 1.

Recommended input:
- Atomic Node 0 request:
  - `market`
  - `run_date`
  - `signal_date`
  - `timezone`
  - `caller`
  - `run_mode`
  - `request_id`
  - `correlation_id`
  - `universe`

Recommended output:
```yaml
request_id: uuid
correlation_id: uuid
market: US | HK | CN
run_date: YYYY-MM-DD
timezone: IANA

calendar_status: open | closed | half_day | unknown | overridden
market_session: premarket | regular | postmarket | closed | unknown
is_runnable: true | false
skip_reason: holiday | weekend | emergency_closure | outside_session | calendar_unavailable | invalid_context | none
next_open_at: ISO8601 | null
session_close_at: ISO8601 | null
calendar_source: string
calendar_source_version: string
override_id: string | null
context_warnings: string[]
```

Recommended behavior:
- If `calendar_status=closed`, return `HEARTBEAT_OK` with structured `skip_reason`; no downstream strategy call.
- If `calendar_status=half_day`, allow discovery/validation/tracking but tag `context_warnings`.
- If `calendar_status=unknown` or calendar source is unavailable:
  - manual caller: allow only with explicit override.
  - cron caller: fail closed or return skipped with `calendar_unavailable`.
  - SOP caller: propagate `NEEDS_OVERRIDE`.
- If `timezone` does not match `market`, fail before downstream work.
- `run_date` should be market-local trade date.
- `signal_date` is the date of source signals/news/price data; it may differ from `run_date` for cross-timezone US runs.

Questions:
1. Should Node 1 allow manual override in v1, or only document it for later?
2. Should `validation` and `tracking` run on closed days using latest available data, or also skip by default?
3. Should `market_session` matter for end-of-day research, or is date-level gating enough for v1?

## Requested Review Output

Please provide:
- recommended boundary,
- proposed input/output contract changes,
- failure/skip behavior,
- risks and missing cases,
- acceptance criteria,
- disagreements with the main proposal.
