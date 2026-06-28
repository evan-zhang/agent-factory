#!/usr/bin/env python3
"""Minimal offline dry-run orchestrator for stock-picking M4b.

This intentionally avoids network, broker, and account access. It wires the
P0 contracts together so discovery and validation can be exercised end to end.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import uuid
from pathlib import Path
from typing import Any

from event_store import JsonlEventStore
from market_calendar import CALENDAR_VERSION as PMC_VERSION, get_calendar_status
from market_data import (
    DEFAULT_LONGBRIDGE_ENV,
    DEFAULT_UNIVERSE_FILE,
    MarketDataError,
    load_universe_symbols,
    quote_to_evidence,
    run_longbridge_quote,
    score_quotes,
)
from research_data import ResearchDataError, build_research_records, load_research_file
from validate_registry import select_dispatch
from validate_schema import ValidationError, validate_record


DEFAULT_EVIDENCE_ID = "ev_01ARZ3NDEKTSV4RRFFQ69G5FAV"
DRY_RUN_VERSION = "m4b-0.1.0"
PRODUCTION_CALENDAR_VERSION = PMC_VERSION


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


def _parse_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def _iso_days_after(date_value: str, days: int) -> str:
    return dt.datetime.combine(_parse_date(date_value) + dt.timedelta(days=days), dt.time(23, 59), dt.timezone.utc).isoformat()


def build_atomic_request(args: argparse.Namespace) -> dict[str, Any]:
    request_id = args.request_id or _uuid()
    correlation_id = args.correlation_id or request_id
    run_date = args.run_date or _today()
    signal_date = args.signal_date or run_date
    return {
        "schema": "atomic_request.v1",
        "request_id": request_id,
        "correlation_id": correlation_id,
        "caller": args.caller,
        "requested_at": _now(),
        "market": args.market,
        "strategy_id": args.strategy_id,
        "strategy_version": args.strategy_version,
        "custom_ref": args.custom_ref,
        "run_mode": args.run_mode,
        "run_date": run_date,
        "signal_date": signal_date,
        "timezone": args.timezone,
        "universe_ref": args.universe_ref,
        "dry_run": True,
        "priority": args.priority,
        "idempotency_key": args.idempotency_key or f"dry-run:{request_id}",
    }


def build_run_context(
    request: dict[str, Any],
    calendar_status: str = "open",
    calendar_source: str = "dry_run_fixture",
    calendar_override_reason: str | None = None,
    calendar_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    proceed = calendar_status in {"open", "half_day"}
    warnings: list[str] = [f"calendar_source:{calendar_source}"]
    if calendar_source in {"dry_run_fixture", "manual_pilot_override"}:
        warnings.append("not_production_calendar")
    if calendar_override_reason:
        warnings.append("calendar_override_reason_present")
    return {
        "schema": "run_context.v1",
        "request_id": request["request_id"],
        "correlation_id": request["correlation_id"],
        "decision": "proceed" if proceed else "skip",
        "calendar_status": calendar_status,
        "market_session": "regular" if calendar_status == "open" else ("half_day" if calendar_status == "half_day" else "closed"),
        "calendar_skip_reason": "none" if proceed else ("holiday" if calendar_status == "closed" else "unknown"),
        "failure_code": None,
        "calendar_source": calendar_source,
        "calendar_source_version": PRODUCTION_CALENDAR_VERSION if calendar_source == "production_calendar" else DRY_RUN_VERSION,
        "calendar_checked_at": _now(),
        "context_warnings": warnings,
        "market": request["market"],
        "calendar_details": calendar_details or {},
    }


def build_draft_candidates(request: dict[str, Any], dispatch: dict[str, Any]) -> dict[str, Any]:
    strategy = dispatch["strategy_dispatch"]
    draft_id = _uuid()
    strategy_run_id = _uuid()
    stock_code = {
        "US": "AAPL",
        "HK": "00700",
        "CN": "600519",
    }.get(request["market"], "DRYRUN")
    stock_name = {
        "US": "Apple",
        "HK": "Tencent",
        "CN": "Kweichow Moutai",
    }.get(request["market"], "Dry Run Candidate")
    return {
        "schema": "draft_candidates.v1",
        "draft_candidates_version": "1.0.0",
        "produced_by": {
            "strategy_id": strategy["strategy_id"],
            "strategy_version": strategy["strategy_version"],
            "registry_record_hash": strategy["registry_record_hash"],
        },
        "produced_at": _now(),
        "request_id": request["request_id"],
        "correlation_id": request["correlation_id"],
        "market": request["market"],
        "run_mode": request["run_mode"],
        "universe_ref": request["universe_ref"],
        "themes": [
            {
                "theme_id": "dry_run_theme",
                "theme_label": "Dry-run fixture theme",
                "propagation_phase": None,
                "window_remaining_days": None,
                "theme_score": None,
                "crowdedness_score": None,
                "sources": [DEFAULT_EVIDENCE_ID],
            }
        ],
        "candidates": [
            {
                "draft_id": draft_id,
                "strategy_run_id": strategy_run_id,
                "strategy_id": strategy["strategy_id"],
                "strategy_version": strategy["strategy_version"],
                "source_research_id": None,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "market": request["market"],
                "price": 1.0,
                "thesis_summary": "Offline dry-run candidate used to validate event wiring.",
                "confidence": {"source": "strategy_self_rated", "level": "medium", "score": None},
                "tracking_horizon": {"kind": "short_event", "default_window_sessions": 10},
                "source_evidence": [DEFAULT_EVIDENCE_ID],
                "negative_evidence": [],
                "negative_evidence_searched": True,
                "expires_at": _iso_days_after(request["signal_date"], 14),
                "next_step": "validation",
            }
        ],
        "warnings": ["dry_run_fixture_output"],
        "partial": False,
        "failure": {"code": None, "message": None},
    }


def build_quote_draft_candidates(
    request: dict[str, Any],
    dispatch: dict[str, Any],
    evidence_records: list[dict[str, Any]],
    research_by_symbol: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    strategy = dispatch["strategy_dispatch"]
    research_by_symbol = research_by_symbol or {}
    candidates: list[dict[str, Any]] = []
    for evidence in evidence_records:
        draft_id = _uuid()
        strategy_run_id = _uuid()
        symbol = evidence["source_id"]
        price = _quote_field(evidence["excerpt"], "last")
        research = research_by_symbol.get(symbol, {})
        positive_evidence = research.get("positive_evidence", [])
        negative_evidence = research.get("negative_evidence", [])
        negative_searched = research.get("negative_search_performed", False)
        source_evidence = [evidence["evidence_id"], *positive_evidence]
        thesis = (
            f"Longbridge live quote plus TAROC research evidence for {symbol}; "
            f"claims={len(research.get('claims', []))}, negative_evidence={len(negative_evidence)}."
            if research
            else f"Longbridge live quote candidate for {symbol}; requires TAROC news and negative-evidence validation before promotion."
        )
        candidates.append(
            {
                "draft_id": draft_id,
                "strategy_run_id": strategy_run_id,
                "strategy_id": strategy["strategy_id"],
                "strategy_version": strategy["strategy_version"],
                "source_research_id": None,
                "stock_code": symbol,
                "stock_name": symbol,
                "market": request["market"],
                "price": float(price) if price is not None else 0.0,
                "thesis_summary": thesis,
                "confidence": {"source": "strategy_self_rated", "level": "medium" if research else "low", "score": None},
                "tracking_horizon": {"kind": "short_event", "default_window_sessions": 10},
                "source_evidence": source_evidence,
                "negative_evidence": negative_evidence,
                "negative_evidence_searched": bool(negative_searched) or not research,
                "expires_at": _iso_days_after(request["signal_date"], 14),
                "next_step": "validation",
            }
        )
    warnings = ["live_quote_only", "taroc_news_and_negative_evidence_pending"]
    if research_by_symbol:
        warnings = ["live_quote_with_research", "requires_human_review_before_trade"]
    return {
        "schema": "draft_candidates.v1",
        "draft_candidates_version": "1.0.0",
        "produced_by": {
            "strategy_id": strategy["strategy_id"],
            "strategy_version": strategy["strategy_version"],
            "registry_record_hash": strategy["registry_record_hash"],
        },
        "produced_at": _now(),
        "request_id": request["request_id"],
        "correlation_id": request["correlation_id"],
        "market": request["market"],
        "run_mode": request["run_mode"],
        "universe_ref": request["universe_ref"],
        "themes": [
            {
                "theme_id": "live_quote_screen",
                "theme_label": "Longbridge live quote screen",
                "propagation_phase": None,
                "window_remaining_days": None,
                "theme_score": None,
                "crowdedness_score": None,
                "sources": [record["evidence_id"] for record in evidence_records],
            }
        ],
        "candidates": candidates,
        "warnings": warnings,
        "partial": False,
        "failure": {"code": None, "message": None},
    }


def _quote_field(excerpt: str, name: str) -> str | None:
    prefix = f"{name}="
    for part in excerpt.split(";"):
        item = part.strip()
        if item.startswith(prefix):
            return item[len(prefix):]
    return None


def _load_draft_records(store: JsonlEventStore, draft_file: Path | None) -> list[dict[str, Any]]:
    if draft_file:
        text = draft_file.read_text(encoding="utf-8")
        value = json.loads(text)
        records = value if isinstance(value, list) else [value]
        for record in records:
            validate_record(record)
            if record.get("schema") != "draft_candidates.v1":
                raise ValidationError("schema", "draft_schema_required", "draft-file must contain draft_candidates.v1 records")
        return records
    return store.read_schema("draft_candidates.v1")


def build_validation_events(draft: dict[str, Any], verdict: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    validation_run_id = _uuid()
    for candidate in draft.get("candidates", []):
        validation_event_id = _uuid()
        promote = verdict == "confirm"
        event = {
            "schema": "validation_event.v1",
            "validation_event_id": validation_event_id,
            "validation_run_id": validation_run_id,
            "draft_id": candidate["draft_id"],
            "request_id": draft["request_id"],
            "correlation_id": draft["correlation_id"],
            "calendar_checked_at": _now(),
            "validation_session_key": f"dry-run:{validation_run_id}",
            "signal_date": _today(),
            "calendar_status": "open",
            "half_day_policy": "exclude",
            "verdict": verdict,
            "validation_confidence": {"level": "medium", "rationale": "offline dry-run fixture"},
            "price_action": "not_checked_offline",
            "thesis_update": "not_checked_offline",
            "new_evidence": [],
            "negative_update": [],
            "promote_candidate": promote,
        }
        records.append(event)
        if promote:
            records.append(
                {
                    "schema": "candidate_record.v1",
                    "candidate_id": _uuid(),
                    "origin_draft_id": candidate["draft_id"],
                    "request_id": draft["request_id"],
                    "correlation_id": draft["correlation_id"],
                    "source_drafts": [candidate["draft_id"]],
                    "stock_code": candidate["stock_code"],
                    "market": candidate["market"],
                    "state": "active",
                    "actor": "system",
                    "aggregate_thesis": candidate["thesis_summary"],
                    "aggregate_thesis_kind": "summary",
                    "created_at": _now(),
                    "expires_at": candidate["expires_at"],
                    "last_state_event_id": validation_event_id,
                }
            )
    return records


def run_discovery(args: argparse.Namespace) -> dict[str, Any]:
    store = JsonlEventStore(args.event_root)
    request = build_atomic_request(args)

    # Resolve calendar source
    if args.calendar_source == "production_calendar":
        # M4e: use real market calendar from pandas-market-calendars
        cal_result = get_calendar_status(request["market"], request["signal_date"])
        calendar_status = cal_result["calendar_status"]
        calendar_details = cal_result.get("details", {})
        # If calendar is closed/unknown, return skip (not reject)
        if calendar_status in {"closed", "unknown"}:
            return {
                "ok": True,
                "mode": "discovery",
                "request_id": request["request_id"],
                "correlation_id": request["correlation_id"],
                "market": request["market"],
                "strategy_id": request["strategy_id"],
                "calendar_skip": True,
                "calendar_status": calendar_status,
                "calendar_skip_reason": cal_result.get("skip_reason", "holiday_or_weekend"),
                "written": [],
                "reject": None,
            }
    elif args.calendar_source == "manual_pilot_override" and not args.calendar_override_reason:
        return {
            "ok": False,
            "mode": "discovery",
            "request_id": request["request_id"],
            "correlation_id": request["correlation_id"],
            "market": request["market"],
            "strategy_id": request["strategy_id"],
            "reject": {"code": "calendar_override_reason_required", "message": "manual_pilot_override requires --calendar-override-reason"},
            "written": [],
        }
    else:
        calendar_status = args.calendar_status
        calendar_details = {}

    existing = store.find_atomic_request(request["idempotency_key"])
    if existing is not None:
        return {
            "ok": True,
            "mode": "discovery",
            "request_id": existing["request_id"],
            "correlation_id": existing["correlation_id"],
            "idempotent_replay": True,
            "written": [],
        }
    context = build_run_context(
        request,
        calendar_status=calendar_status,
        calendar_source=args.calendar_source,
        calendar_override_reason=args.calendar_override_reason,
        calendar_details=calendar_details,
    )
    dispatch_request = {
        **request,
        "selected_at": _now(),
    }
    dispatch = select_dispatch(dispatch_request, context, args.registry, args.custom_refs)
    records = [request, context, dispatch]
    if dispatch["decision"] == "dispatch":
        if args.market_data_source == "longbridge_quote":
            try:
                symbols = args.universe_symbols or load_universe_symbols(args.universe_file, request["market"], request["universe_ref"])
                quotes = score_quotes(run_longbridge_quote(symbols, args.longbridge_env, args.market_data_timeout), args.candidate_limit)
                evidence_records = [quote_to_evidence(quote, request) for quote in quotes]
                research_records: list[dict[str, Any]] = []
                research_by_symbol: dict[str, dict[str, Any]] = {}
                if args.research_file:
                    researches = load_research_file(args.research_file)
                    research_records, research_by_symbol = build_research_records(request, researches)
            except (MarketDataError, ResearchDataError) as exc:
                return {
                    "ok": False,
                    "mode": "discovery",
                    "request_id": request["request_id"],
                    "correlation_id": request["correlation_id"],
                    "market": request["market"],
                    "strategy_id": request["strategy_id"],
                    "reject": {"code": exc.code, "message": exc.message},
                    "written": [],
                }
            records.extend(evidence_records)
            records.extend(research_records)
            records.append(build_quote_draft_candidates(request, dispatch, evidence_records, research_by_symbol))
        else:
            records.append(build_draft_candidates(request, dispatch))
    results = store.append_many(records)
    return {
        "ok": dispatch["decision"] == "dispatch",
        "mode": "discovery",
        "request_id": request["request_id"],
        "correlation_id": request["correlation_id"],
        "market": request["market"],
        "strategy_id": request["strategy_id"],
        "written": results,
        "dispatch_decision": dispatch["decision"],
        "reject": dispatch.get("reject"),
    }


def run_validation(args: argparse.Namespace) -> dict[str, Any]:
    store = JsonlEventStore(args.event_root)
    try:
        drafts = _load_draft_records(store, args.draft_file)
    except (json.JSONDecodeError, OSError, ValidationError) as exc:
        return {
            "ok": False,
            "mode": "validation",
            "reject": {"code": "invalid_draft_file", "message": str(exc)},
        }
    if not drafts:
        return {"ok": False, "mode": "validation", "reject": {"code": "draft_not_found", "message": "no draft_candidates.v1 events found"}}
    records = build_validation_events(drafts[-1], args.verdict)
    if not records:
        return {"ok": False, "mode": "validation", "reject": {"code": "candidate_not_found", "message": "draft has no candidates"}}
    results = store.append_many(records)
    return {
        "ok": True,
        "mode": "validation",
        "request_id": drafts[-1]["request_id"],
        "correlation_id": drafts[-1]["correlation_id"],
        "verdict": args.verdict,
        "written": results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=Path("src/strategies/registry.yaml"))
    parser.add_argument("--custom-refs", type=Path, default=Path("src/strategies/custom_refs.yaml"))
    sub = parser.add_subparsers(dest="command", required=True)

    discovery = sub.add_parser("discovery")
    discovery.add_argument("--request-id")
    discovery.add_argument("--correlation-id")
    discovery.add_argument("--caller", choices=["manual", "cron", "sop"], default="manual")
    discovery.add_argument("--market", choices=["US", "HK", "CN"], default="US")
    discovery.add_argument("--strategy-id", choices=["taroc", "chokepoint", "custom"], default="taroc")
    discovery.add_argument("--strategy-version", default="1.0.0")
    discovery.add_argument("--custom-ref")
    discovery.add_argument("--run-mode", choices=["discovery", "validation", "tracking"], default="discovery")
    discovery.add_argument("--run-date")
    discovery.add_argument("--signal-date")
    discovery.add_argument("--timezone", choices=["Asia/Shanghai", "Asia/Hong_Kong", "America/New_York"], default="Asia/Shanghai")
    discovery.add_argument("--universe-ref", default="dry_run_universe")
    discovery.add_argument("--priority", choices=["low", "normal", "high"], default="normal")
    discovery.add_argument("--idempotency-key")
    discovery.add_argument("--calendar-status", choices=["open", "closed", "half_day", "emergency_closed", "unknown"], default="open")
    discovery.add_argument("--calendar-source", choices=["dry_run_fixture", "manual_pilot_override", "production_calendar"], default="dry_run_fixture")
    discovery.add_argument("--calendar-override-reason")
    discovery.add_argument("--market-data-source", choices=["dry_run_fixture", "longbridge_quote"], default="dry_run_fixture")
    discovery.add_argument("--universe-symbols", nargs="+")
    discovery.add_argument("--universe-file", type=Path, default=DEFAULT_UNIVERSE_FILE)
    discovery.add_argument("--candidate-limit", type=int, default=3)
    discovery.add_argument("--longbridge-env", type=Path, default=DEFAULT_LONGBRIDGE_ENV)
    discovery.add_argument("--market-data-timeout", type=int, default=30)
    discovery.add_argument("--research-file", type=Path)

    validation = sub.add_parser("validation")
    validation.add_argument("--draft-file", type=Path)
    validation.add_argument("--verdict", choices=["confirm", "watch", "reject", "overheated", "thesis_broken", "validation_skipped"], default="confirm")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "discovery":
        result = run_discovery(args)
    else:
        result = run_validation(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
