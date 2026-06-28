# Gateway Cron Design

Status: S5f dry-run production pilot with output analysis
Date: 2026-06-25

`stock-picking` does not own cron schedules. Gateway cron is an external trigger that submits an auditable dry-run request into the skill. The skill remains responsible for request validation, calendar/context checks, registry dispatch, event writes, and user-facing summaries.

## Responsibilities

Gateway cron owns:

- schedule cadence
- target conversation or notification route
- environment selection
- retry policy for trigger delivery only
- operator-visible run metadata

`stock-picking` owns:

- `atomic_request.v1`
- `run_context.v1`
- `strategy_dispatch.v1`
- dry-run strategy output events
- append-only event store writes
- rejection and skip summaries

Gateway cron must not:

- call broker APIs
- mutate target pool, approvals, or positions directly
- bypass `dry_run_orchestrator.py`
- infer strategy fallback when registry dispatch rejects
- restart or terminate Life Gateway from inside a triggered run

## Initial Schedules

Current v1 schedules are conservative and dry-run only:

- CN discovery: 09:00 Asia/Shanghai, Monday-Friday
- HK discovery: 09:08 Asia/Shanghai, Monday-Friday; intentionally staggered after CN to reduce Longbridge rate-limit collisions
- US discovery: 21:30 Asia/Shanghai, Monday-Friday
- validation: manual or operator-triggered after at least one `draft_candidates.v1` event exists

Do not schedule Chokepoint through cron in v1. Registry policy rejects `caller=cron` for experimental strategies.

## Trigger Contract

Gateway discovery cron should trigger the equivalent of:

```bash
PYTHONPATH=src/scripts python3 src/scripts/research_protocol.py plan \
  --market US \
  --universe-file src/config/universe.yaml \
  --universe-ref default \
  --run-date "$(date +%Y-%m-%d)"

# The isolated cron agent must run web_search for every positive_query and
# negative_query, write /tmp/stock-picking-research-US-YYYY-MM-DD.json, then:
PYTHONPATH=src/scripts python3 src/scripts/research_protocol.py validate \
  /tmp/stock-picking-research-US-$(date +%Y-%m-%d).json \
  --market US \
  --universe-file src/config/universe.yaml \
  --universe-ref default

PYTHONPATH=src/scripts python3 src/scripts/discovery_job.py \
  --event-root "$STOCK_PICKING_EVENT_ROOT" \
  --registry src/strategies/registry.yaml \
  --custom-refs src/strategies/custom_refs.yaml \
  discovery \
  --caller cron \
  --market US \
  --strategy-id taroc \
  --strategy-version 1.0.0 \
  --run-mode discovery \
  --timezone America/New_York \
  --universe-ref default \
  --universe-file src/config/universe.yaml \
  --calendar-source production_calendar \
  --market-data-source longbridge_quote \
  --candidate-limit 3 \
  --research-file /tmp/stock-picking-research-US-$(date +%Y-%m-%d).json \
  --idempotency-key "stock-picking:US:discovery:taroc:1.0.0:$(date +%Y-%m-%d)"

# If discovery_job.py did not return HEARTBEAT_OK, run pilot analysis:
PYTHONPATH=src/scripts python3 src/scripts/pilot_analyzer.py \
  --event-root "$STOCK_PICKING_EVENT_ROOT" \
  --market US \
  --universe-file src/config/universe.yaml \
  --universe-ref default
```

Cron callers must use an explicit argument allowlist. For M4b pilot design, allowed flags are:

- Global: `--event-root`, `--registry`, `--custom-refs`
- Discovery: `discovery`, `--request-id`, `--correlation-id`, `--caller`, `--market`, `--strategy-id`, `--strategy-version`, `--run-mode`, `--run-date`, `--signal-date`, `--timezone`, `--universe-ref`, `--universe-file`, `--priority`, `--idempotency-key`, `--calendar-status`, `--calendar-source`, `--calendar-override-reason`, `--market-data-source`, `--universe-symbols`, `--candidate-limit`, `--longbridge-env`, `--market-data-timeout`, `--research-file`
- Validation: `validation`, `--draft-file`, `--verdict`

Gateway cron must set `--caller cron` for discovery. It must not pass shell fragments, raw paths through `--custom-ref`, unknown flags, broker/action flags, or environment-derived strategy fallbacks. Validation `--draft-file` is allowed only for an operator-supplied JSON/JSONL draft fixture and is schema-validated before any validation events are written.

### Parameter Source Constraints

Gateway cron arguments must come only from an owner-approved schedule definition or operator-approved deployment config. Gateway must not copy user-supplied chat/message fields directly into `--strategy-id`, `--strategy-version`, `--custom-ref`, `--universe-ref`, `--calendar-source`, `--calendar-status`, or `--draft-file`.

For scheduled discovery in v1:

- `--strategy-id` is pinned to `taroc`.
- `--strategy-version` is pinned to an exact reviewed semver.
- `--custom-ref` is omitted unless the value is already present in `src/strategies/custom_refs.yaml` and reviewed in the design/change log.
- `--universe-file` is pinned to `src/config/universe.yaml`; `--universe-ref` is selected from that file, not free text.
- `calendar_source` is `production_calendar` (now backed by pandas-market-calendars as of M4e) or `manual_pilot_override` for dry-run pilots.
- `--calendar-status` is omitted unless the schedule is a local dry-run fixture; production status must come from the calendar source, not from user input.

The isolated cron agent must not skip negative research. `research_protocol.py validate` is the gate: every configured symbol must have `negative_search_performed=true` and the actual `negative_search_query` used, even when the negative result list is empty.

After a non-heartbeat discovery run, the isolated cron agent must run `pilot_analyzer.py` and include its output in the channel report. S5f analysis checks:

- candidate count vs configured universe
- Longbridge quote evidence coverage
- positive research evidence coverage
- mandatory negative-search coverage
- claim count and claim symbols
- draft warnings that should inform universe tuning

For validation:

```bash
python3 src/scripts/dry_run_orchestrator.py \
  --event-root "$STOCK_PICKING_EVENT_ROOT" \
  validation \
  --verdict watch
```

The current M4d orchestrator supports three calendar source labels:

- `dry_run_fixture`: local tests only; never production cron
- `manual_pilot_override`: dry-run pilot only; requires `--calendar-override-reason`
- `production_calendar`: backed by pandas-market-calendars (v5.4.0+) as of M4e; queries XSHG/XHKG/NYSE exchange schedules for real trading-day detection

Production cron is authorized when `run_context.v1.calendar_source=production_calendar` is backed by the pandas-market-calendars integration (M4e). The orchestrator queries the real exchange schedule; closed days produce a `calendar_skip` (no events written, no reject), and open/half-day days proceed through full discovery.

## Operator Notification Route

Gateway owns delivery. `stock-picking` only defines and validates the route contract with:

```bash
python3 src/scripts/operator_notification.py --route route.json --event-root "$STOCK_PICKING_EVENT_ROOT"
```

Minimum route:

```json
{
  "schema": "operator_notification_route.v1",
  "route_id": "stock-picking-local",
  "channel": "local_log",
  "target": "/tmp/stock-picking-operator.log",
  "severity_min": "warning",
  "dry_run_only": true,
  "include_fields": [
    "request_id",
    "correlation_id",
    "reject_code",
    "event_root",
    "run_mode",
    "market",
    "strategy_id"
  ]
}
```

`severity_min` is an actual filter threshold. Payloads below the configured threshold must be marked `suppressed=true` and must not be delivered by Gateway.

M4d route validation is dry-run only and does not send Discord, Telegram, email, or log messages. Gateway must call its own delivery layer after validation.

## Event Root

`STOCK_PICKING_EVENT_ROOT` must be an explicit absolute path managed outside the skill package. Suggested layout:

```text
<workspace>/data/stock-picking/events/
  atomic_request.v1.jsonl
  run_context.v1.jsonl
  strategy_dispatch.v1.jsonl
  draft_candidates.v1.jsonl
  validation_event.v1.jsonl
  candidate_record.v1.jsonl
```

Do not write canonical events under `src/`, `tests/`, or the installed skill directory.

## Idempotency

Cron must provide a deterministic `idempotency_key` per schedule window:

```text
stock-picking:<market>:<run_mode>:<strategy_id>:<strategy_version>:<signal_date>
```

The event store treats an existing `atomic_request.v1.idempotency_key` as an idempotent replay and does not append a second discovery event chain. Retries should still be operator-visible, and intentional re-runs must use a new schedule window key.

## Failure Handling

If the orchestrator exits nonzero:

- preserve stdout/stderr in Gateway run logs
- notify the configured operator route with `request_id`, `correlation_id`, `reject.code`, and event paths when available
- do not retry strategy execution automatically unless the failure is clearly trigger delivery failure before the process started

Expected nonzero cases include:

- registry reject
- upstream `run_context.decision != proceed`
- no draft exists for validation
- schema validation failure

## Universe Config

Default discovery symbols live in `src/config/universe.yaml`.

- CN default currently covers six high-liquidity A-share leaders.
- HK default currently covers six high-liquidity HK leaders.
- US default currently covers seven high-liquidity US mega-cap / catalyst leaders.

Edit the universe file for expansion, removals, or test partitions. Do not duplicate symbol lists in cron payloads except for emergency one-off overrides.

## Pilot Analysis

Manual analysis command:

```bash
PYTHONPATH=src/scripts python3 src/scripts/pilot_analyzer.py \
  --event-root "$STOCK_PICKING_EVENT_ROOT" \
  --market US \
  --universe-file src/config/universe.yaml \
  --universe-ref default
```

`status: PASS` means the latest draft produced the target number of candidates (`min(universe size, candidate-limit)`), every candidate belongs to the configured universe, each candidate has quote evidence and positive research evidence, and negative search was recorded. `status: WATCH` means the pilot is usable but should be inspected before expanding the universe.

## Readiness Gate

Cron can move from design to pilot only after:

- `dry_run_orchestrator.py` has passing tests for discovery and validation
- validation events reject `promote_candidate=true` unless `verdict=confirm`
- discovery idempotency replay does not append duplicate events
- event root path is explicit and writable
- market-calendar source is production-backed (M4e: pandas-market-calendars) or the run is clearly marked fixture/manual pilot
- operator notification route is defined
- Chokepoint remains manual-only unless a future factory review changes registry maturity

M4c adds an executable local readiness check for the dry-run pilot gate:

```bash
python3 src/scripts/cron_readiness.py \
  --event-root "$STOCK_PICKING_EVENT_ROOT" \
  --registry src/strategies/registry.yaml \
  --custom-refs src/strategies/custom_refs.yaml
```

The checker verifies:

- `event_root` is an explicit absolute writable path
- TAROC is active and cron-allowed for discovery
- Chokepoint remains non-cron in registry policy
- unknown broker/action flags are rejected by the orchestrator CLI
- production calendar integration writes events on open days and skips closed days without writing stale reports
- discovery replay with the same cron idempotency key does not duplicate events
- confirm validation emits `validation_event.v1` and `candidate_record.v1`
- `promote_candidate=true` is rejected unless `verdict=confirm`

Passing this check means the local dry-run pilot gate is executable. It does not by itself authorize a production schedule; production cron still needs an operator notification route and a production-backed market-calendar source or an explicit fixture/manual-pilot label.
