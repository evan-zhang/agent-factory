#!/usr/bin/env python3
"""Execution guard proxy for broker-affecting stock-picking actions."""

from __future__ import annotations

import datetime as dt
import functools
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


GUARD_VERSION = "m4a-0.1.0"
REAL_ACTIONS = {"buy", "sell", "cancel"}
ALLOWLIST = {"buy", "sell", "cancel", "quote", "reconcile"}


class ExecutionBlockedError(RuntimeError):
    def __init__(self, decision: dict[str, Any]):
        self.decision = decision
        super().__init__(decision.get("block_code") or "execution_blocked")


@dataclass
class InMemoryAuditSink:
    decisions: list[dict[str, Any]] = field(default_factory=list)
    broker_api_calls: int = 0

    def write(self, decision: dict[str, Any]) -> None:
        self.decisions.append(decision)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def _decision(
    request: dict[str, Any],
    action_request: dict[str, Any],
    decision: str,
    block_code: str | None,
    approval: dict[str, Any] | None,
    pretrade_check: dict[str, Any] | None,
    checks: list[str],
) -> dict[str, Any]:
    return {
        "schema": "execution_guard_decision.v1",
        "decision_id": str(uuid.uuid4()),
        "request_id": request.get("request_id"),
        "correlation_id": request.get("correlation_id"),
        "action": action_request.get("action"),
        "decision": decision,
        "block_code": block_code,
        "approval_id": approval.get("approval_id") if approval else None,
        "pretrade_check_id": pretrade_check.get("pretrade_check_id") if pretrade_check else None,
        "broker": action_request.get("broker", "unknown"),
        "market": action_request.get("market"),
        "created_at": _now(),
        "audit": {"guard_version": GUARD_VERSION, "checks": checks},
    }


def evaluate_execution(
    atomic_request: dict[str, Any],
    run_context: dict[str, Any],
    action_request: dict[str, Any],
    approval: dict[str, Any] | None,
    pretrade_check: dict[str, Any] | None,
) -> dict[str, Any]:
    checks: list[str] = []
    action = action_request.get("action")

    if action not in ALLOWLIST:
        return _decision(atomic_request, action_request, "block", "unknown_broker_action", approval, pretrade_check, checks)
    checks.append("action_allowlist")

    if action not in REAL_ACTIONS or atomic_request.get("dry_run", True):
        return _decision(atomic_request, action_request, "dry_run", None, approval, pretrade_check, checks + ["dry_run"])

    if run_context.get("decision") != "proceed":
        return _decision(atomic_request, action_request, "block", "run_context_not_proceed", approval, pretrade_check, checks)
    checks.append("run_context_proceed")

    if action_request.get("market") != run_context.get("market", atomic_request.get("market")):
        return _decision(atomic_request, action_request, "block", "market_mismatch", approval, pretrade_check, checks)
    checks.append("market_match")

    if action == "sell":
        return _decision(atomic_request, action_request, "block", "sell_disabled_v1", approval, pretrade_check, checks)

    if action != "buy":
        return _decision(atomic_request, action_request, "block", "real_action_disabled_v1", approval, pretrade_check, checks)

    if not approval:
        return _decision(atomic_request, action_request, "block", "approval_missing", approval, pretrade_check, checks)
    if approval.get("approval_state") != "approved":
        return _decision(atomic_request, action_request, "block", "approval_not_approved", approval, pretrade_check, checks)
    if approval.get("approved_by") != "Evan":
        return _decision(atomic_request, action_request, "block", "approval_not_by_evan", approval, pretrade_check, checks)
    if approval.get("pool_item_id") != action_request.get("pool_item_id"):
        return _decision(atomic_request, action_request, "block", "approval_pool_item_mismatch", approval, pretrade_check, checks)
    expires_at = _parse_time(approval.get("expires_at"))
    if expires_at is None or expires_at <= dt.datetime.now(dt.timezone.utc):
        return _decision(atomic_request, action_request, "block", "approval_expired", approval, pretrade_check, checks)
    checks.append("approval_valid")

    if not pretrade_check:
        return _decision(atomic_request, action_request, "block", "pretrade_check_missing", approval, pretrade_check, checks)
    if pretrade_check.get("status") != "pass":
        return _decision(atomic_request, action_request, "block", "pretrade_check_failed", approval, pretrade_check, checks)
    checks.append("pretrade_check_pass")

    return _decision(atomic_request, action_request, "allow", None, approval, pretrade_check, checks)


def guard_broker_action(
    audit_sink: InMemoryAuditSink,
    atomic_request: dict[str, Any],
    run_context: dict[str, Any],
    action_request: dict[str, Any],
    approval: dict[str, Any] | None = None,
    pretrade_check: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            decision = evaluate_execution(atomic_request, run_context, action_request, approval, pretrade_check)
            audit_sink.write(decision)
            if decision["decision"] != "allow":
                raise ExecutionBlockedError(decision)
            audit_sink.broker_api_calls += 1
            return func(*args, **kwargs)

        return wrapper

    return decorator
