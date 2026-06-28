# Strategy Registry Design

## Purpose

Node 2 is a registry selector. It validates a requested strategy and emits one `strategy_dispatch.v1` envelope. It does not execute strategy code, rank candidates, merge strategies, or fallback to another strategy.

## Files

- Registry: `src/strategies/registry.yaml`
- Custom reference whitelist: `src/strategies/custom_refs.yaml`
- Validator: `src/scripts/validate_registry.py` in S4

## Snapshot Atomicity

The selector must treat registry selection as one immutable snapshot:

1. Read registry bytes once.
2. Hash bytes as `registry_snapshot_hash`.
3. Parse and validate that in-memory snapshot.
4. Resolve exact version or manual default from the snapshot.
5. Normalize selected record and hash it as `registry_record_hash`.
6. Emit dispatch using the selected record and both hashes.

The selector must not read the registry again during the same selection. This prevents a dispatch whose version came from one file state and whose hash came from another.

## Version Policy

- `cron` and `sop` callers must provide exact semver.
- `manual` may omit version only when a default exists and resolves to one record.
- `latest` is invalid in v1.
- Disabled strategies always reject.
- Deprecated strategies may dispatch only for manual callers with explicit version.
- Experimental strategies dispatch only when `allowed_callers` includes the caller.

## Reject Codes

- `upstream_not_proceed`
- `strategy_not_found`
- `version_required`
- `version_not_found`
- `ambiguous_version`
- `unsupported_market`
- `unsupported_run_mode`
- `caller_not_allowed`
- `strategy_disabled`
- `experimental_not_allowed`
- `custom_ref_invalid`
- `output_schema_unsupported`
- `dry_run_required`
- `registry_invalid`

## Custom Ref Whitelist

`custom_ref` never accepts free text, raw paths, temporary scripts, or path traversal.

Whitelist entries live in `src/strategies/custom_refs.yaml` and must resolve to approved registry entries or signed internal references. The selector loads this whitelist during the same validation phase as the registry. Any whitelist change must be auditable through `design/DESIGN.md` Decision Log or a future change log.

## Output Schema

Registry `output_schema` records the strategy's primary output. Dispatch events must still report the actual schema emitted by the selected run.

Chokepoint v1 has `theme_research.v1` as its primary output. A later promotion from research to draft candidates is a separate event and must emit `draft_candidates.v1` with the same `request_id`, `correlation_id`, strategy identity, and registry record hash.

## Required Tests

- `run_context.decision=skip` rejects with `upstream_not_proceed`.
- Unknown strategy rejects without invoking any strategy.
- Unsupported market rejects with `unsupported_market`.
- Unsupported run mode rejects with `unsupported_run_mode`.
- Disabled strategy rejects for all callers.
- Experimental Chokepoint rejects for cron/sop.
- Manual TAROC without version dispatches only when default exists and warns.
- Cron TAROC without version rejects with `version_required`.
- Supported exact strategy/version/market/run_mode emits one dispatch with stable entrypoint and schema.
- Missing or invalid registry hash rejects with `registry_invalid`.
- No request ever falls back to TAROC when the requested strategy is unavailable.
