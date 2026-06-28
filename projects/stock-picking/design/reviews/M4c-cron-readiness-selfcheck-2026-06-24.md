# M4c Cron Readiness Selfcheck

Date: 2026-06-24
Status: PASS for local dry-run pilot gate

## Scope

M4c turns the Gateway cron pilot design gate from `src/references/gateway-cron.md` into an executable local checker:

```text
src/scripts/cron_readiness.py
```

This does not enable production cron. It validates only the local dry-run pilot prerequisites.

## Checks Covered

- absolute writable `event_root`
- TAROC active and cron-allowed for discovery
- Chokepoint remains non-cron
- orchestrator CLI rejects unknown broker/action flags
- reserved `production_calendar` is rejected before any event write
- cron discovery writes one event chain
- repeated cron idempotency key does not append duplicate discovery events
- confirm validation emits `validation_event.v1` and `candidate_record.v1`
- `promote_candidate=true` remains invalid unless `verdict=confirm`

## Tests

```text
python3 -m unittest discover -s tests -v
Ran 27 tests
OK
```

Smoke:

```text
python3 src/scripts/cron_readiness.py --event-root /tmp/<tmpdir> --registry src/strategies/registry.yaml --custom-refs src/strategies/custom_refs.yaml
ok: true
```

## Remaining Risks

- Production schedule is still blocked until operator notification route is defined.
- Production schedule is still blocked until market calendar is production-backed; `production_calendar` is currently a hard reject until M4e.
- The readiness check uses offline dry-run fixture outputs; it does not validate real data-provider availability.
