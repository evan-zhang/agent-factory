# Execution Guard Design

## Purpose

`execution-guard` is the only allowed path from stock-picking workflow events to broker-affecting actions. v1 defaults to dry-run and blocks every real action unless a valid approval artifact and pretrade check are present.

## Guard Inputs

- `atomic_request.v1`
- `run_context.v1`
- target pool item or position action request
- `approval.v1`
- pretrade check result
- broker action request

## Minimum Checks

1. `dry_run` defaults to true.
2. `run_context.decision` must be `proceed`.
3. Market in action request must match run context.
4. Broker action must be in allowlist.
5. Real `buy` requires `approval_state=approved`, `approved_by=Evan`, non-expired `approved_at`, and matching `pool_item_id`.
6. Real `sell` remains disabled in v1 except as a blocked recommendation event.
7. `pretrade_check_id` must exist and pass.
8. Approval expiry must be enforced.
9. Every allow/block decision writes `execution_guard_decision.v1`.

## Refusal Tests

S4 must include tests or equivalent executable checks for:

- no approval rejects
- expired approval rejects
- approval not by Evan rejects
- missing pretrade check rejects
- `dry_run=false` without guard rejects
- market mismatch rejects
- unknown broker action rejects

## Observable Signals

The `futu_tool.py buy` fix is accepted only when real buy attempts pass through execution guard and produce an audit event. Broker API call count for rejected paths must be zero or provably blocked before the broker client is invoked.

## Implementation Hook

M4a should wrap broker-affecting entrypoints with an execution-guard decorator or proxy before the broker client is invoked. For example, `futu_tool.buy` and any future Longbridge order method should call guard evaluation first; blocked decisions raise `ExecutionBlockedError`, write `execution_guard_decision.v1`, and increment a guard-side block counter rather than a broker API counter.

## Output

`execution_guard_decision.v1`:

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
