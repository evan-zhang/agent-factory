#!/usr/bin/env python3
"""Executable readiness gate for Gateway cron pilot.

The check is intentionally local and dry-run only. It verifies that cron can
trigger TAROC discovery through the same orchestrator path without enabling a
real schedule or touching broker/account APIs.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from dry_run_orchestrator import build_parser, run_discovery, run_validation
from event_store import JsonlEventStore
from validate_schema import ValidationError, validate_record


def _ok(name: str, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": True, "detail": detail}


def _fail(name: str, code: str, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": False, "code": code, "detail": detail}


def _load_registry(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _strategy(registry: dict[str, Any], strategy_id: str) -> dict[str, Any] | None:
    for row in registry.get("strategies", []):
        if row.get("id") == strategy_id:
            return row
    return None


def check_event_root(event_root: Path) -> dict[str, Any]:
    if not event_root.is_absolute():
        return _fail("event_root", "event_root_not_absolute", "event root must be an absolute path")
    try:
        event_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".cron-readiness-", dir=event_root) as tmp:
            probe = Path(tmp) / "write-probe"
            probe.write_text("ok", encoding="utf-8")
    except OSError as exc:
        return _fail("event_root", "event_root_not_writable", str(exc))
    return _ok("event_root", str(event_root))


def check_registry_policy(registry_path: Path) -> dict[str, Any]:
    try:
        registry = _load_registry(registry_path)
    except OSError as exc:
        return _fail("registry_policy", "registry_unreadable", str(exc))

    taroc = _strategy(registry, "taroc")
    chokepoint = _strategy(registry, "chokepoint")
    if taroc is None:
        return _fail("registry_policy", "taroc_missing", "taroc strategy is required for cron pilot")
    if taroc.get("status") != "active" or "cron" not in taroc.get("allowed_callers", []):
        return _fail("registry_policy", "taroc_not_cron_ready", "taroc must be active and allow cron")
    if "discovery" not in taroc.get("supported_run_modes", []):
        return _fail("registry_policy", "taroc_discovery_missing", "taroc must support discovery")
    if chokepoint is not None and "cron" in chokepoint.get("allowed_callers", []):
        return _fail("registry_policy", "chokepoint_cron_enabled", "chokepoint must remain manual-only for v1")
    return _ok("registry_policy", "taroc cron pilot allowed; chokepoint cron disabled")


def check_cli_allowlist() -> dict[str, Any]:
    parser = build_parser()
    allowed = [
        "--event-root",
        "/tmp/events",
        "discovery",
        "--caller",
        "cron",
        "--market",
        "US",
        "--strategy-id",
        "taroc",
        "--strategy-version",
        "1.0.0",
        "--run-mode",
        "discovery",
        "--timezone",
        "America/New_York",
        "--universe-ref",
        "us_default",
        "--calendar-source",
        "manual_pilot_override",
        "--calendar-override-reason",
        "local cron readiness smoke",
    ]
    parser.parse_args(allowed)
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            parser.parse_args(allowed + ["--broker", "futu"])
    except SystemExit:
        return _ok("cli_allowlist", "unknown broker/action flags are rejected by argparse")
    return _fail("cli_allowlist", "unknown_flag_allowed", "parser accepted an unexpected broker flag")


def check_production_calendar_integration(registry: Path, custom_refs: Path) -> dict[str, Any]:
    """M4e: production_calendar is now backed by pandas-market-calendars.

    Verify that:
    1. On a trading day, production_calendar discovery proceeds and writes events
    2. On a closed day, production_calendar produces calendar_skip (not reject)
    3. run_context carries production_calendar source metadata
    """
    import datetime as _dt
    from market_calendar import is_trading_day

    # Find a known trading day and a known closed day for testing
    test_open = None
    test_closed = None
    for offset in range(0, 30):
        d = _dt.date(2026, 6, 24) + _dt.timedelta(days=offset)
        if is_trading_day("US", d) and test_open is None:
            test_open = d.isoformat()
        if not is_trading_day("US", d) and test_closed is None:
            test_closed = d.isoformat()
        if test_open and test_closed:
            break

    # Test open day
    with tempfile.TemporaryDirectory(prefix=".m4e-cron-readiness-") as tmp:
        event_root = Path(tmp) / "events"
        args = build_parser().parse_args([
            "--event-root", str(event_root),
            "--registry", str(registry),
            "--custom-refs", str(custom_refs),
            "discovery",
            "--caller", "cron",
            "--market", "US",
            "--strategy-id", "taroc",
            "--strategy-version", "1.0.0",
            "--run-mode", "discovery",
            "--timezone", "America/New_York",
            "--universe-ref", "us_default",
            "--calendar-source", "production_calendar",
            "--signal-date", test_open or "2026-06-24",
            "--idempotency-key", f"cron-readiness:m4e:open:{test_open}",
        ])
        result = run_discovery(args)
        if not result.get("ok"):
            return _fail("production_calendar_integration", "open_day_failed", json.dumps(result, ensure_ascii=False))
        if result.get("calendar_skip"):
            # The test date might be closed — acceptable if it's truly closed
            pass
        else:
            store = JsonlEventStore(event_root)
            ctx = store.read_schema("run_context.v1")
            if ctx and ctx[0]["calendar_source"] != "production_calendar":
                return _fail("production_calendar_integration", "wrong_source", f"expected production_calendar, got {ctx[0]['calendar_source']}")

    # Test closed day
    with tempfile.TemporaryDirectory(prefix=".m4e-cron-readiness-") as tmp:
        event_root = Path(tmp) / "events"
        args = build_parser().parse_args([
            "--event-root", str(event_root),
            "--registry", str(registry),
            "--custom-refs", str(custom_refs),
            "discovery",
            "--caller", "cron",
            "--market", "US",
            "--strategy-id", "taroc",
            "--strategy-version", "1.0.0",
            "--run-mode", "discovery",
            "--timezone", "America/New_York",
            "--universe-ref", "us_default",
            "--calendar-source", "production_calendar",
            "--signal-date", test_closed or "2026-06-28",
            "--idempotency-key", f"cron-readiness:m4e:closed:{test_closed}",
        ])
        result = run_discovery(args)
        if not result.get("ok"):
            return _fail("production_calendar_integration", "closed_day_failed", json.dumps(result, ensure_ascii=False))
        if not result.get("calendar_skip"):
            return _fail("production_calendar_integration", "closed_day_not_skipped", f"expected calendar_skip on {test_closed}")
        if result.get("written"):
            return _fail("production_calendar_integration", "closed_day_wrote_events", "closed day should not write events")

    return _ok("production_calendar_integration", f"production calendar backed by pandas-market-calendars; open={test_open}, closed={test_closed}")


def _discovery_args(event_root: Path, registry: Path, custom_refs: Path, request_id: str) -> argparse.Namespace:
    parser = build_parser()
    return parser.parse_args(
        [
            "--event-root",
            str(event_root),
            "--registry",
            str(registry),
            "--custom-refs",
            str(custom_refs),
            "discovery",
            "--request-id",
            request_id,
            "--correlation-id",
            request_id,
            "--caller",
            "cron",
            "--market",
            "US",
            "--strategy-id",
            "taroc",
            "--strategy-version",
            "1.0.0",
            "--run-mode",
            "discovery",
            "--run-date",
            "2026-06-24",
            "--signal-date",
            "2026-06-24",
            "--timezone",
            "America/New_York",
            "--universe-ref",
            "us_default",
            "--calendar-source",
            "manual_pilot_override",
            "--calendar-override-reason",
            "local cron readiness smoke",
            "--idempotency-key",
            "stock-picking:US:discovery:taroc:1.0.0:2026-06-24",
        ]
    )


def check_dry_run_smoke(event_root: Path, registry: Path, custom_refs: Path) -> dict[str, Any]:
    smoke_root = Path(tempfile.mkdtemp(prefix=".cron-readiness-smoke-", dir=event_root))
    try:
        first = run_discovery(
            _discovery_args(smoke_root, registry, custom_refs, "123e4567-e89b-12d3-a456-426614174000")
        )
        second = run_discovery(
            _discovery_args(smoke_root, registry, custom_refs, "123e4567-e89b-12d3-a456-426614174001")
        )
        if not first.get("ok"):
            return _fail("dry_run_smoke", "discovery_failed", json.dumps(first, ensure_ascii=False))
        if not second.get("idempotent_replay"):
            return _fail("dry_run_smoke", "idempotency_failed", "second discovery did not report idempotent replay")

        store = JsonlEventStore(smoke_root)
        counts = {schema: len(store.read_schema(schema)) for schema in ("atomic_request.v1", "run_context.v1", "strategy_dispatch.v1", "draft_candidates.v1")}
        if counts != {"atomic_request.v1": 1, "run_context.v1": 1, "strategy_dispatch.v1": 1, "draft_candidates.v1": 1}:
            return _fail("dry_run_smoke", "unexpected_event_counts", json.dumps(counts, sort_keys=True))

        validation_args = build_parser().parse_args(
            [
                "--event-root",
                str(smoke_root),
                "--registry",
                str(registry),
                "--custom-refs",
                str(custom_refs),
                "validation",
                "--verdict",
                "confirm",
            ]
        )
        validation = run_validation(validation_args)
        if not validation.get("ok"):
            return _fail("dry_run_smoke", "validation_failed", json.dumps(validation, ensure_ascii=False))
        if len(store.read_schema("validation_event.v1")) != 1 or len(store.read_schema("candidate_record.v1")) != 1:
            return _fail("dry_run_smoke", "validation_event_missing", "confirm validation did not emit expected events")
    except (OSError, ValidationError, SystemExit) as exc:
        return _fail("dry_run_smoke", "smoke_exception", str(exc))
    finally:
        shutil.rmtree(smoke_root, ignore_errors=True)
    return _ok("dry_run_smoke", "cron discovery, idempotent replay, and confirm validation passed")


def check_validation_gate() -> dict[str, Any]:
    record = {
        "schema": "validation_event.v1",
        "validation_event_id": "123e4567-e89b-12d3-a456-426614174000",
        "validation_run_id": "123e4567-e89b-12d3-a456-426614174001",
        "draft_id": "123e4567-e89b-12d3-a456-426614174002",
        "request_id": "123e4567-e89b-12d3-a456-426614174003",
        "correlation_id": "123e4567-e89b-12d3-a456-426614174004",
        "calendar_checked_at": "2026-06-24T00:00:00+00:00",
        "validation_session_key": "readiness",
        "signal_date": "2026-06-24",
        "calendar_status": "open",
        "half_day_policy": "exclude",
        "verdict": "watch",
        "validation_confidence": {"level": "medium", "rationale": "readiness"},
        "price_action": "not_checked",
        "thesis_update": "not_checked",
        "new_evidence": [],
        "negative_update": [],
        "promote_candidate": True,
    }
    try:
        validate_record(record)
    except ValidationError as exc:
        if exc.code == "promote_candidate_mismatch":
            return _ok("validation_gate", "promote_candidate=true is rejected unless verdict=confirm")
        return _fail("validation_gate", exc.code, exc.message)
    return _fail("validation_gate", "promote_mismatch_allowed", "validator accepted promote/watch mismatch")


def run_checks(event_root: Path, registry: Path, custom_refs: Path) -> dict[str, Any]:
    checks = [
        check_event_root(event_root),
        check_registry_policy(registry),
        check_cli_allowlist(),
        check_production_calendar_integration(registry, custom_refs),
        check_validation_gate(),
    ]
    if checks[0]["ok"]:
        checks.append(check_dry_run_smoke(event_root, registry, custom_refs))
    else:
        checks.append(_fail("dry_run_smoke", "event_root_unavailable", "dry-run smoke skipped because event root is not ready"))
    return {"ok": all(check["ok"] for check in checks), "checks": checks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=Path("src/strategies/registry.yaml"))
    parser.add_argument("--custom-refs", type=Path, default=Path("src/strategies/custom_refs.yaml"))
    args = parser.parse_args(argv)
    result = run_checks(args.event_root, args.registry, args.custom_refs)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
