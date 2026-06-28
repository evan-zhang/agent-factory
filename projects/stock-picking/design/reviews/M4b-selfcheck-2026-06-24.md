# M4b Selfcheck - 2026-06-24

Status: WARN reviewed; B001/M001-M004 remediated

## Scope

M4b completed the first executable business slice after the M4a safety/validation base:

- `src/SKILL.md` rewritten as a SOP orchestration skill, not a CSV monolith.
- `src/flows/` expanded for discovery, validation, weekly review, target pool, approval, reconcile, and risk monitor.
- `src/scripts/event_store.py` added as append-only JSONL event storage.
- `src/scripts/migrate_legacy_csv.py` added as read-only legacy projection skeleton.
- `src/scripts/dry_run_orchestrator.py` added for offline discovery and validation dry-runs.
- `src/references/gateway-cron.md` added as external Gateway cron design.

## Executable Path

Discovery dry-run writes:

- `atomic_request.v1`
- `run_context.v1`
- `strategy_dispatch.v1`
- `draft_candidates.v1`

Validation dry-run reads the latest `draft_candidates.v1` from the event store and writes:

- `validation_event.v1`
- `candidate_record.v1` when verdict is `confirm`

The orchestrator is intentionally offline. It does not fetch market data, inspect accounts, send messages, or touch broker APIs.

## Verification

Commands run:

```bash
python3 -m unittest discover -s tests -v
```

Result:

```text
Ran 17 tests
OK
```

Smoke run:

```bash
tmp=$(mktemp -d)
python3 src/scripts/dry_run_orchestrator.py --event-root "$tmp/events" discovery \
  --request-id 123e4567-e89b-12d3-a456-426614174000 \
  --correlation-id 123e4567-e89b-12d3-a456-426614174001 \
  --run-date 2026-06-24 \
  --signal-date 2026-06-24
python3 src/scripts/dry_run_orchestrator.py --event-root "$tmp/events" validation
```

The smoke run produced JSONL files for request, context, dispatch, draft candidates, validation event, and candidate record.

## Known Boundaries

- Calendar is still an offline fixture in M4b.
- Discovery candidate content is a fixture used to validate wiring, not market research.
- Validation verdict is caller-selected and does not yet evaluate live price/news evidence.
- Discovery idempotency key replay is enforced for `atomic_request.v1`.
- Cron design is documentation only; no Gateway cron was created.
- Chokepoint remains manual-only and registry rejects cron/sop use.

## Reviewer Follow-up Closure

- B001/M001: `validation_event.v1` now rejects `promote_candidate=true` unless `verdict=confirm`, with a negative regression test.
- M002: discovery idempotency replay now returns cached request metadata without appending duplicate event chains, with event-store and CLI tests.
- M003: `gateway-cron.md` now includes an explicit CLI argument allowlist and cron-specific constraints.
- M004: `--draft-file` content is schema-validated as `draft_candidates.v1` before validation events can be written.

## Review Questions

- Does the orchestrator preserve S3/S4 boundaries by avoiding strategy/network/broker responsibilities?
- Are fixture outputs acceptable for M4b as long as they are schema-valid and clearly marked?
- Is `gateway-cron.md` enough to move S4 toward a deployment pilot, or should a formal operator runbook be required first?
