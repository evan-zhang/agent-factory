#!/usr/bin/env python3
"""Operator notification route contract for stock-picking cron pilots.

This module validates notification route config and builds auditable payloads.
It intentionally does not send messages; Gateway owns delivery.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CHANNELS = {"discord", "telegram", "email", "local_log"}
SEVERITIES = {"info", "warning", "critical"}
SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}
REQUIRED_FIELDS = {"request_id", "correlation_id", "reject_code", "event_root", "run_mode", "market", "strategy_id"}


class OperatorRouteError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise OperatorRouteError("route_not_object", "route config must be a JSON object")
    return value


def validate_route(route: dict[str, Any]) -> dict[str, Any]:
    if route.get("schema") != "operator_notification_route.v1":
        raise OperatorRouteError("invalid_schema", "schema must be operator_notification_route.v1")
    for field in ("route_id", "channel", "target", "severity_min", "include_fields", "dry_run_only"):
        if field not in route:
            raise OperatorRouteError("missing_required", f"{field} is required")
    if route["channel"] not in CHANNELS:
        raise OperatorRouteError("invalid_channel", "unsupported notification channel")
    if route["severity_min"] not in SEVERITIES:
        raise OperatorRouteError("invalid_severity", "severity_min must be info, warning, or critical")
    if not isinstance(route["target"], str) or not route["target"]:
        raise OperatorRouteError("invalid_target", "target must be a non-empty string")
    if route.get("dry_run_only") is not True and route.get("dry_run_only") is not False:
        raise OperatorRouteError("dry_run_only_required", "dry_run_only must be explicitly true or false")
    include_fields = route["include_fields"]
    if not isinstance(include_fields, list) or not all(isinstance(field, str) for field in include_fields):
        raise OperatorRouteError("invalid_include_fields", "include_fields must be a string list")
    missing = sorted(REQUIRED_FIELDS - set(include_fields))
    if missing:
        raise OperatorRouteError("missing_payload_fields", "include_fields missing: " + ", ".join(missing))
    return {"ok": True, "route_id": route["route_id"], "channel": route["channel"], "target": route["target"]}


def _result_severity(run_result: dict[str, Any]) -> str:
    reject = run_result.get("reject") or {}
    severity = reject.get("severity") or run_result.get("severity") or "warning"
    if severity not in SEVERITIES:
        raise OperatorRouteError("invalid_result_severity", "run result severity must be info, warning, or critical")
    return severity


def build_failure_payload(route: dict[str, Any], run_result: dict[str, Any], event_root: Path) -> dict[str, Any]:
    validate_route(route)
    reject = run_result.get("reject") or {}
    severity = _result_severity(run_result)
    if SEVERITY_RANK[severity] < SEVERITY_RANK[route["severity_min"]]:
        return {
            "schema": "operator_notification_payload.v1",
            "route_id": route["route_id"],
            "severity": severity,
            "dry_run": True,
            "suppressed": True,
            "suppress_reason": "severity_below_min",
            "fields": {},
        }
    payload_source = {
        "request_id": run_result.get("request_id"),
        "correlation_id": run_result.get("correlation_id"),
        "reject_code": reject.get("code"),
        "reject_message": reject.get("message"),
        "event_root": str(event_root),
        "run_mode": run_result.get("mode"),
        "market": run_result.get("market"),
        "strategy_id": run_result.get("strategy_id"),
    }
    return {
        "schema": "operator_notification_payload.v1",
        "route_id": route["route_id"],
        "severity": severity,
        "dry_run": True,
        "suppressed": False,
        "fields": {field: payload_source.get(field) for field in route["include_fields"]},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--event-root", type=Path, required=True)
    parser.add_argument("--run-result", type=Path)
    args = parser.parse_args(argv)

    route = load_json(args.route)
    try:
        if args.run_result:
            result = load_json(args.run_result)
            output = build_failure_payload(route, result, args.event_root)
        else:
            output = validate_route(route)
    except OperatorRouteError as exc:
        output = {"ok": False, "reject": {"code": exc.code, "message": exc.message}}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
