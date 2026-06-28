# M4d Operator And Calendar Selfcheck

Date: 2026-06-24
Status: PASS for dry-run pilot contract; production cron remains BLOCKED

## Scope

M4d adds two cron-pilot prerequisites:

- `operator_notification.py`: validates an operator notification route and builds bounded dry-run failure payloads.
- explicit calendar source labels in `dry_run_orchestrator.py`: `dry_run_fixture`, `manual_pilot_override`, and reserved hard-rejected `production_calendar`.

## Contract Decisions

- The skill does not send Discord, Telegram, email, or log messages. Gateway owns delivery.
- M4d notification routes must be `dry_run_only=true`.
- `manual_pilot_override` must include `--calendar-override-reason`.
- `production_calendar` is a reserved label until a real market-calendar source is integrated; current dry-run orchestrator rejects it before writing events.
- Gateway cron parameters must come from owner-approved schedule/config and must not directly pass user-supplied `strategy_id`, `custom_ref`, or `universe_ref`.
- `severity_min` is an executable notification threshold, not documentation-only metadata.

## Tests

```text
python3 -m unittest discover -s tests -v
Ran 27 tests
OK
```

Additional checks:

- `python3 -m py_compile src/scripts/*.py`
- `python3 src/scripts/cron_readiness.py --event-root /tmp/<tmpdir> --registry src/strategies/registry.yaml --custom-refs src/strategies/custom_refs.yaml`

## Remaining Blockers

- Production cron cannot be enabled until `production_calendar` is backed by a real market-calendar source and re-reviewed.
