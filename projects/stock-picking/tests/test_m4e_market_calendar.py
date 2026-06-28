#!/usr/bin/env python3
"""Tests for M4e: production market calendar integration.

Verifies that:
1. production_calendar is no longer hard-rejected
2. Real trading-day detection works for CN/HK/US
3. Holidays/weekends are correctly identified
4. Closed days produce calendar_skip (not reject)
5. Open days proceed through full discovery
6. cron_readiness.py updated checks pass
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import sys
import tempfile
from pathlib import Path

# Ensure src/scripts is importable
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from market_calendar import get_calendar_status, is_trading_day, CALENDAR_VERSION
from dry_run_orchestrator import build_parser, run_discovery, run_validation
from event_store import JsonlEventStore


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = PROJECT_ROOT / "src" / "strategies" / "registry.yaml"
CUSTOM_REFS = PROJECT_ROOT / "src" / "strategies" / "custom_refs.yaml"


def _discovery_args(event_root: Path, market: str, calendar_source: str = "production_calendar", **kwargs) -> list[str]:
    args = [
        "--event-root", str(event_root),
        "--registry", str(REGISTRY),
        "--custom-refs", str(CUSTOM_REFS),
        "discovery",
        "--caller", "cron",
        "--market", market,
        "--strategy-id", "taroc",
        "--strategy-version", "1.0.0",
        "--run-mode", "discovery",
        "--timezone", {"CN": "Asia/Shanghai", "HK": "Asia/Hong_Kong", "US": "America/New_York"}[market],
        "--universe-ref", {"CN": "cn_default", "HK": "hk_default", "US": "us_default"}[market],
        "--calendar-source", calendar_source,
        "--idempotency-key", kwargs.get("idempotency_key", f"test:{market}:{calendar_source}:{dt.date.today()}"),
    ]
    if calendar_source == "manual_pilot_override":
        args.extend(["--calendar-override-reason", "test override"])
    if "run_date" in kwargs:
        args.extend(["--run-date", kwargs["run_date"]])
    if "signal_date" in kwargs:
        args.extend(["--signal-date", kwargs["signal_date"]])
    return args


def test_calendar_version():
    """Calendar module exposes a version string."""
    assert CALENDAR_VERSION.startswith("pmc-")


def test_trading_day_cn_weekday():
    """2026-06-24 is a Wednesday — should be a CN trading day."""
    status = get_calendar_status("CN", "2026-06-24")
    assert status["calendar_status"] == "open", f"Expected open, got {status}"
    assert status["market_session"] == "regular"


def test_trading_day_hk_weekday():
    """2026-06-24 is a Wednesday — should be a HK trading day."""
    status = get_calendar_status("HK", "2026-06-24")
    assert status["calendar_status"] == "open", f"Expected open, got {status}"


def test_trading_day_us_weekday():
    """2026-06-24 is a Wednesday — should be a US trading day."""
    status = get_calendar_status("US", "2026-06-24")
    assert status["calendar_status"] == "open", f"Expected open, got {status}"


def test_weekend_closed():
    """2026-06-27 is a Saturday — all markets should be closed."""
    for market in ("CN", "HK", "US"):
        status = get_calendar_status(market, "2026-06-27")
        assert status["calendar_status"] == "closed", f"{market}: expected closed, got {status['calendar_status']}"


def test_cn_holiday():
    """2026-01-01 is New Year — CN should be closed."""
    status = get_calendar_status("CN", "2026-01-01")
    assert status["calendar_status"] == "closed", f"Expected closed, got {status}"


def test_hk_holiday():
    """2026-01-01 is New Year — HK should be closed."""
    status = get_calendar_status("HK", "2026-01-01")
    assert status["calendar_status"] == "closed", f"Expected closed, got {status}"


def test_us_holiday():
    """2026-01-01 is New Year — US should be closed."""
    status = get_calendar_status("US", "2026-01-01")
    assert status["calendar_status"] == "closed", f"Expected closed, got {status}"


def test_us_thanksgiving_2026():
    """2026-11-26 is Thanksgiving — US should be closed."""
    status = get_calendar_status("US", "2026-11-26")
    assert status["calendar_status"] == "closed", f"Expected closed, got {status}"


def test_is_trading_day_helper():
    """is_trading_day convenience function works."""
    assert is_trading_day("US", "2026-06-24") is True
    assert is_trading_day("US", "2026-06-28") is False  # Sunday


def test_production_calendar_not_rejected():
    """production_calendar should no longer be hard-rejected by orchestrator."""
    with tempfile.TemporaryDirectory(prefix=".m4e-test-") as tmp:
        event_root = Path(tmp) / "events"
        args = build_parser().parse_args(_discovery_args(event_root, "US"))
        result = run_discovery(args)
        assert not result.get("reject", {}).get("code") == "production_calendar_unavailable", \
            "production_calendar should not be rejected anymore"
        # On a trading day, discovery should proceed
        if result.get("calendar_skip"):
            # Today might be a weekend/holiday in test env — that's fine, skip is not reject
            assert result["ok"] is True
            assert result["calendar_skip"] is True
        else:
            assert result["ok"] is True
            store = JsonlEventStore(event_root)
            assert len(store.read_schema("atomic_request.v1")) == 1
            assert len(store.read_schema("run_context.v1")) == 1


def test_production_calendar_closed_day_skip():
    """On a closed day, production_calendar should produce a calendar_skip, not a reject."""
    with tempfile.TemporaryDirectory(prefix=".m4e-test-") as tmp:
        event_root = Path(tmp) / "events"
        args = build_parser().parse_args(
            _discovery_args(event_root, "US", signal_date="2026-01-01", idempotency_key="test:us:closed:20260101")
        )
        result = run_discovery(args)
        assert result["ok"] is True
        assert result.get("calendar_skip") is True
        assert result["calendar_status"] == "closed"
        # No events should be written on a skip
        assert result["written"] == []


def test_production_calendar_open_day_writes_events():
    """On a trading day, production_calendar should write full event chain."""
    with tempfile.TemporaryDirectory(prefix=".m4e-test-") as tmp:
        event_root = Path(tmp) / "events"
        args = build_parser().parse_args(
            _discovery_args(event_root, "US", signal_date="2026-06-24", idempotency_key="test:us:open:20260624")
        )
        result = run_discovery(args)
        assert result["ok"] is True
        assert not result.get("calendar_skip")
        store = JsonlEventStore(event_root)
        # atomic_request, run_context, strategy_dispatch, draft_candidates
        assert len(store.read_schema("atomic_request.v1")) == 1
        assert len(store.read_schema("run_context.v1")) == 1
        assert len(store.read_schema("strategy_dispatch.v1")) == 1
        assert len(store.read_schema("draft_candidates.v1")) == 1

        # Verify run_context has production calendar metadata
        ctx = store.read_schema("run_context.v1")[0]
        assert ctx["calendar_source"] == "production_calendar"
        assert "pmc-" in ctx["calendar_source_version"]
        assert "not_production_calendar" not in ctx.get("context_warnings", [])


def test_production_calendar_idempotency():
    """Repeated discovery with same idempotency key should be a replay."""
    with tempfile.TemporaryDirectory(prefix=".m4e-test-") as tmp:
        event_root = Path(tmp) / "events"
        key = "test:idempotency:us:20260624"
        args1 = build_parser().parse_args(
            _discovery_args(event_root, "US", signal_date="2026-06-24", idempotency_key=key)
        )
        r1 = run_discovery(args1)
        args2 = build_parser().parse_args(
            _discovery_args(event_root, "US", signal_date="2026-06-24", idempotency_key=key)
        )
        r2 = run_discovery(args2)
        if not r1.get("calendar_skip"):
            assert r2.get("idempotent_replay") is True


def test_manual_pilot_override_still_works():
    """manual_pilot_override path is unaffected by M4e changes."""
    with tempfile.TemporaryDirectory(prefix=".m4e-test-") as tmp:
        event_root = Path(tmp) / "events"
        args = build_parser().parse_args(
            _discovery_args(event_root, "US", calendar_source="manual_pilot_override",
                           idempotency_key="test:manual:us:20260624")
        )
        result = run_discovery(args)
        assert result["ok"] is True
        ctx = JsonlEventStore(event_root).read_schema("run_context.v1")[0]
        assert ctx["calendar_source"] == "manual_pilot_override"
        assert "not_production_calendar" in ctx["context_warnings"]


def test_three_markets_production_calendar():
    """All three markets can use production_calendar on a trading day."""
    with tempfile.TemporaryDirectory(prefix=".m4e-test-") as tmp:
        for market in ("CN", "HK", "US"):
            event_root = Path(tmp) / f"events_{market}"
            args = build_parser().parse_args(
                _discovery_args(event_root, market, signal_date="2026-06-24",
                               idempotency_key=f"test:3mkt:{market}:20260624")
            )
            result = run_discovery(args)
            assert result["ok"] is True, f"{market} failed: {result}"


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except Exception as exc:
            print(f"  ❌ {test.__name__}: {exc}")
            failed += 1
    print(f"\n{'='*60}")
    print(f"M4e tests: {passed} passed, {failed} failed, {len(tests)} total")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
