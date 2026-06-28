#!/usr/bin/env python3
"""Offline validators for stock-picking S3/M4a event contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except ImportError:  # pragma: no cover - CI/local dependency guard
    yaml = None


UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
EVIDENCE_ID_RE = re.compile(r"^ev_[0-9A-HJKMNP-TV-Z]{26}$")
CLAIM_ID_RE = re.compile(r"^cl_[0-9A-HJKMNP-TV-Z]{26}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T.+")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$|^[0-9a-f]{64}$")

MARKETS = {"US", "HK", "CN"}
BROKERS = {"futu", "longbridge", "guosen", "manual", "unknown"}
EVIDENCE_SOURCE_TYPES = {
    "primary",
    "secondary",
    "community",
    "regulatory",
    "broker_data",
    "company_filing",
    "news",
    "analyst",
    "internal_note",
    "ai_inference",
    "unverified",
}


class ValidationError(Exception):
    def __init__(self, path: str, code: str, message: str):
        self.path = path
        self.code = code
        self.message = message
        super().__init__(f"{path}: {code}: {message}")


@dataclass(frozen=True)
class SchemaSpec:
    required: tuple[str, ...]
    enums: dict[str, set[Any]]
    checks: tuple[Callable[[dict[str, Any]], None], ...] = ()


def _get(record: dict[str, Any], path: str) -> Any:
    value: Any = record
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValidationError(path, "missing_required", "required field is absent")
        value = value[part]
    return value


def _has(record: dict[str, Any], path: str) -> bool:
    try:
        _get(record, path)
        return True
    except ValidationError:
        return False


def _require_uuid(record: dict[str, Any], path: str) -> None:
    value = _get(record, path)
    if not isinstance(value, str) or not UUID_RE.match(value):
        raise ValidationError(path, "invalid_uuid", "expected UUID string")


def _require_semver(record: dict[str, Any], path: str, nullable: bool = False) -> None:
    value = _get(record, path)
    if nullable and value is None:
        return
    if not isinstance(value, str) or not SEMVER_RE.match(value):
        raise ValidationError(path, "invalid_semver", "expected semantic version")


def _require_iso(record: dict[str, Any], path: str, nullable: bool = False) -> None:
    value = _get(record, path)
    if nullable and value is None:
        return
    if not isinstance(value, str) or not ISO_RE.match(value):
        raise ValidationError(path, "invalid_iso8601", "expected ISO8601-ish timestamp")


def _require_date(record: dict[str, Any], path: str) -> None:
    value = _get(record, path)
    if not isinstance(value, str) or not DATE_RE.match(value):
        raise ValidationError(path, "invalid_date", "expected YYYY-MM-DD")


def _require_bool(record: dict[str, Any], path: str) -> None:
    if not isinstance(_get(record, path), bool):
        raise ValidationError(path, "invalid_boolean", "expected boolean")


def _check_common(record: dict[str, Any]) -> None:
    _require_uuid(record, "request_id")
    _require_uuid(record, "correlation_id")


def _check_atomic_request(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_semver(record, "strategy_version", nullable=True)
    _require_date(record, "run_date")
    _require_date(record, "signal_date")
    _require_bool(record, "dry_run")
    if record["dry_run"] is False:
        raise ValidationError("dry_run", "dry_run_required", "dry_run=false is rejected in v1 atomic requests")
    custom_ref = record.get("custom_ref")
    if custom_ref and (".." in custom_ref or "/" in custom_ref or "\\" in custom_ref):
        raise ValidationError("custom_ref", "custom_ref_invalid", "raw paths and traversal are rejected")


def _check_run_context(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_iso(record, "calendar_checked_at")


def _check_strategy_dispatch(record: dict[str, Any]) -> None:
    _check_common(record)
    dispatch = _get(record, "strategy_dispatch")
    if record.get("decision") == "reject":
        return
    if not dispatch.get("registry_record_hash"):
        raise ValidationError("strategy_dispatch.registry_record_hash", "missing_hash", "record hash is required")
    _require_semver(dispatch, "strategy_version")


def _check_draft_candidates(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_iso(record, "produced_at")
    _require_semver(record, "produced_by.strategy_version")
    for index, candidate in enumerate(record.get("candidates", [])):
        if not candidate.get("source_evidence"):
            raise ValidationError(f"candidates.{index}.source_evidence", "evidence_required", "source evidence is required")
        if candidate.get("negative_evidence_searched") is not True:
            raise ValidationError(
                f"candidates.{index}.negative_evidence_searched",
                "negative_evidence_required",
                "negative evidence search must be explicit",
            )
        if not candidate.get("strategy_id") or not candidate.get("strategy_version"):
            raise ValidationError(f"candidates.{index}.strategy_id", "strategy_identity_required", "strategy identity is required")


def _check_theme_research(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_uuid(record, "research_id")
    _require_semver(record, "strategy_version")
    if record.get("uncertainty_level") == "high" and record.get("promotion_status") == "eligible_for_draft":
        raise ValidationError("promotion_status", "high_uncertainty_cannot_promote", "high uncertainty cannot promote directly")


def _check_validation_event(record: dict[str, Any]) -> None:
    _require_uuid(record, "validation_event_id")
    _require_uuid(record, "validation_run_id")
    _require_uuid(record, "draft_id")
    _check_common(record)
    _require_bool(record, "promote_candidate")
    should_promote = record.get("verdict") == "confirm"
    if record.get("promote_candidate") is not should_promote:
        raise ValidationError(
            "promote_candidate",
            "promote_candidate_mismatch",
            "promote_candidate must be true only when verdict is confirm",
        )


def _check_candidate_record(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_uuid(record, "candidate_id")
    if record.get("state") == "removed" and record.get("actor") != "human":
        raise ValidationError("actor", "human_required", "removed state requires human actor")


def _check_tracking_event(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_uuid(record, "tracking_event_id")
    _require_uuid(record, "candidate_id")
    _require_uuid(record, "origin_draft_id")


def _check_target_pool_item(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_uuid(record, "pool_item_id")
    if record.get("status") == "active":
        for field in ("entry_price", "stop_loss", "target_price", "decision_deadline"):
            _get(record, field)
        if not record.get("position_amount") and record.get("sizing_state") != "awaiting_sizing":
            raise ValidationError("position_amount", "sizing_required", "active items need size or awaiting_sizing")


def _check_approval(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_uuid(record, "approval_id")
    _require_uuid(record, "pool_item_id")
    _require_uuid(record, "pretrade_check_id")
    _require_iso(record, "expires_at")
    if record.get("approval_state") == "approved":
        if record.get("approved_by") != "Evan":
            raise ValidationError("approved_by", "evan_approval_required", "approved buys require Evan")
        _require_iso(record, "approved_at")


def _check_reconcile_report(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_uuid(record, "reconcile_run_id")


def _check_risk_event(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_uuid(record, "risk_event_id")
    if record.get("execution_allowed") is not False:
        raise ValidationError("execution_allowed", "execution_not_allowed", "risk events never allow execution in v1")


def _check_trade_log_event(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_uuid(record, "trade_event_id")


def _check_execution_guard_decision(record: dict[str, Any]) -> None:
    _check_common(record)
    _require_uuid(record, "decision_id")
    if _get(record, "audit.guard_version") == "":
        raise ValidationError("audit.guard_version", "guard_version_required", "guard version is required")


def _check_evidence_ref(record: dict[str, Any]) -> None:
    value = _get(record, "evidence_id")
    if not isinstance(value, str) or not EVIDENCE_ID_RE.match(value):
        raise ValidationError("evidence_id", "invalid_evidence_id", "expected ev_<ulid>")
    _require_iso(record, "created_at")
    _require_iso(record, "fetched_at")
    _require_iso(record, "observed_at")
    for field in ("publisher_authority", "ai_classified_quality"):
        score = _get(record, field)
        if not isinstance(score, (int, float)) or not 0 <= score <= 1:
            raise ValidationError(field, "invalid_quality_score", "quality score must be 0..1")
    if not SHA256_RE.match(str(_get(record, "content_hash"))):
        raise ValidationError("content_hash", "invalid_sha256", "expected sha256 hash")


def _check_claim(record: dict[str, Any]) -> None:
    value = _get(record, "claim_id")
    if not isinstance(value, str) or not CLAIM_ID_RE.match(value):
        raise ValidationError("claim_id", "invalid_claim_id", "expected cl_<ulid>")
    _check_common(record)
    if "claim_type" in record:
        raise ValidationError("claim_type", "noncanonical_field", "claim_type is not canonical in v1")
    evidence_ids = _get(record, "evidence_ids")
    if not isinstance(evidence_ids, list):
        raise ValidationError("evidence_ids", "invalid_list", "expected list")
    for index, evidence_id in enumerate(evidence_ids):
        if not isinstance(evidence_id, str) or not EVIDENCE_ID_RE.match(evidence_id):
            raise ValidationError(f"evidence_ids.{index}", "invalid_evidence_id", "expected ev_<ulid>")


def _check_legacy_projection(record: dict[str, Any]) -> None:
    if "legacy_files" in record and not isinstance(record["legacy_files"], list):
        raise ValidationError("legacy_files", "invalid_list", "expected list")


SCHEMAS: dict[str, SchemaSpec] = {
    "atomic_request.v1": SchemaSpec(
        ("schema", "request_id", "correlation_id", "caller", "requested_at", "market", "strategy_id", "strategy_version", "custom_ref", "run_mode", "run_date", "signal_date", "timezone", "universe_ref", "dry_run", "priority", "idempotency_key"),
        {"caller": {"manual", "cron", "sop"}, "market": MARKETS, "strategy_id": {"taroc", "chokepoint", "custom"}, "run_mode": {"discovery", "validation", "tracking"}, "timezone": {"Asia/Shanghai", "Asia/Hong_Kong", "America/New_York"}, "priority": {"low", "normal", "high"}},
        (_check_atomic_request,),
    ),
    "run_context.v1": SchemaSpec(
        ("schema", "request_id", "correlation_id", "decision", "calendar_status", "market_session", "calendar_skip_reason", "failure_code", "calendar_source", "calendar_source_version", "calendar_checked_at", "context_warnings"),
        {"decision": {"proceed", "skip", "needs_override", "fail"}, "calendar_status": {"open", "closed", "half_day", "emergency_closed", "unknown"}, "market_session": {"premarket", "regular", "postmarket", "closed", "outside_session", "unknown"}, "calendar_skip_reason": {"none", "weekend", "holiday", "half_day_policy", "emergency_closure", "outside_session", "calendar_unavailable", "invalid_context"}},
        (_check_run_context,),
    ),
    "strategy_dispatch.v1": SchemaSpec(("schema", "request_id", "correlation_id", "node_id", "decision", "strategy_dispatch", "reject", "warnings", "audit"), {"decision": {"dispatch", "reject"}}, (_check_strategy_dispatch,)),
    "draft_candidates.v1": SchemaSpec(("schema", "draft_candidates_version", "produced_by", "produced_at", "request_id", "correlation_id", "market", "run_mode", "universe_ref", "themes", "candidates", "warnings", "partial", "failure"), {"market": MARKETS, "run_mode": {"discovery", "validation"}}, (_check_draft_candidates,)),
    "theme_research.v1": SchemaSpec(("schema", "theme_research_version", "research_id", "request_id", "correlation_id", "strategy_id", "strategy_version", "produced_at", "market", "theme", "signals", "evidence", "negative_evidence", "break_conditions", "uncertainty_level", "risk_flags", "upgrade_triggers", "promotion_status", "reject_reason"), {"strategy_id": {"chokepoint"}, "market": {"US"}, "uncertainty_level": {"low", "medium", "high"}, "promotion_status": {"observe", "eligible_for_draft", "rejected"}}, (_check_theme_research,)),
    "validation_event.v1": SchemaSpec(("schema", "validation_event_id", "validation_run_id", "draft_id", "request_id", "correlation_id", "calendar_checked_at", "validation_session_key", "signal_date", "calendar_status", "half_day_policy", "verdict", "validation_confidence", "price_action", "thesis_update", "new_evidence", "negative_update", "promote_candidate"), {"calendar_status": {"open", "half_day"}, "half_day_policy": {"exclude", "allow"}, "verdict": {"confirm", "watch", "reject", "overheated", "thesis_broken", "validation_skipped"}}, (_check_validation_event,)),
    "candidate_record.v1": SchemaSpec(("schema", "candidate_id", "origin_draft_id", "request_id", "correlation_id", "source_drafts", "stock_code", "market", "state", "actor", "aggregate_thesis", "aggregate_thesis_kind", "created_at", "expires_at", "last_state_event_id"), {"market": MARKETS, "state": {"active", "watching", "promote_suggested", "expired", "removed"}, "actor": {"system", "agent", "human"}, "aggregate_thesis_kind": {"concatenation", "summary"}}, (_check_candidate_record,)),
    "tracking_event.v1": SchemaSpec(("schema", "tracking_event_id", "candidate_id", "origin_draft_id", "request_id", "correlation_id", "week_id", "event_type", "actor", "suggested_reason", "supporting_evidence", "state_transition", "created_at"), {"event_type": {"catalyst_update", "risk_update", "price_action", "promote_suggested", "remove_suggested", "weekly_review"}, "actor": {"system", "agent", "human"}}, (_check_tracking_event,)),
    "target_pool_item.v1": SchemaSpec(("schema", "pool_item_id", "candidate_id", "origin_draft_id", "request_id", "correlation_id", "stock_code", "market", "entry_price", "stop_loss", "target_price", "position_amount", "sizing_state", "promotion_reason", "status", "created_date", "decision_deadline", "diff_audit_ref", "created_at"), {"market": MARKETS, "sizing_state": {"sized", "awaiting_sizing"}, "status": {"active", "deferred", "rejected", "built", "expired"}}, (_check_target_pool_item,)),
    "approval.v1": SchemaSpec(("schema", "approval_id", "pool_item_id", "candidate_id", "request_id", "correlation_id", "action", "approval_state", "approved_by", "approved_at", "approval_note", "pretrade_check_id", "expires_at", "created_at"), {"action": {"buy"}, "approval_state": {"requested", "approved", "rejected", "expired", "manual_ledger_restored"}}, (_check_approval,)),
    "reconcile_report.v1": SchemaSpec(("schema", "reconcile_run_id", "request_id", "correlation_id", "generated_at", "summary", "mismatches"), {}, (_check_reconcile_report,)),
    "risk_event.v1": SchemaSpec(("schema", "risk_event_id", "request_id", "correlation_id", "source", "stock_code", "event_type", "severity", "recommended_action", "execution_allowed", "thesis_broken", "evidence", "created_at"), {"source": {"position_monitor", "reconcile", "portfolio_risk", "execution_guard", "strategy_tracking"}, "event_type": {"stop_loss_breach", "drawdown_breach", "quote_failed", "reconcile_mismatch", "execution_blocked", "thesis_broken"}, "severity": {"info", "warning", "critical"}, "recommended_action": {"observe", "notify", "request_human_decision", "execute_guarded_sell"}}, (_check_risk_event,)),
    "trade_log_event.v1": SchemaSpec(("schema", "trade_event_id", "request_id", "correlation_id", "action", "mode", "stock_code", "market", "approval_id", "execution_guard_decision_id", "broker", "status", "created_at", "expires_at"), {"action": {"buy", "sell", "cancel", "dry_run_entry", "blocked"}, "mode": {"dry_run", "real"}, "market": MARKETS, "broker": BROKERS, "status": {"pending", "executed", "blocked", "failed", "expired"}}, (_check_trade_log_event,)),
    "execution_guard_decision.v1": SchemaSpec(("schema", "decision_id", "request_id", "correlation_id", "action", "decision", "block_code", "approval_id", "pretrade_check_id", "broker", "market", "created_at", "audit"), {"action": {"buy", "sell", "cancel", "quote", "reconcile"}, "decision": {"allow", "block", "dry_run"}, "broker": BROKERS, "market": MARKETS}, (_check_execution_guard_decision,)),
    "evidence_ref.v1": SchemaSpec(("schema", "evidence_id", "created_at", "created_by", "source_url", "source_id", "source_type", "source_subtype", "title", "excerpt", "publisher", "fetched_at", "observed_at", "language", "snapshot_ref", "claim_hash", "publisher_authority", "ai_classified_quality", "classification_method", "source_quality", "status", "content_hash", "raw_snapshot_path"), {"created_by": {"node_3_taroc", "node_4_chokepoint", "node_6_validation", "node_8_tracker", "node_11_reconcile", "human"}, "source_type": EVIDENCE_SOURCE_TYPES, "source_subtype": {"filing", "press_release", "patent", "earnings_call", "broker_report", "news", "social", "other"}, "classification_method": {"publisher_table", "llm_judge", "human"}, "source_quality": {"high", "medium", "low", "unknown"}, "status": {"active", "superseded", "disputed", "retracted", "access_lost"}}, (_check_evidence_ref,)),
    "claim.v1": SchemaSpec(("schema", "claim_id", "created_at", "created_by", "scope", "request_id", "correlation_id", "claim_text", "claim_kind", "polarity", "thesis_broken", "severity", "confidence", "evidence_ids", "negative_search_performed", "negative_search_query", "valid_until", "status"), {"claim_kind": {"support", "refute", "risk", "catalyst", "break_condition", "neutral_context"}, "polarity": {"positive", "negative", "mixed", "neutral"}, "severity": {"info", "warning", "critical", None}, "status": {"active", "superseded", "retracted"}}, (_check_claim,)),
    "legacy_csv_projection.v1": SchemaSpec(("schema", "legacy_files"), {}, (_check_legacy_projection,)),
}


def record_id(record: dict[str, Any]) -> str | None:
    for key in (
        "evidence_id",
        "claim_id",
        "candidate_id",
        "draft_id",
        "approval_id",
        "decision_id",
        "risk_event_id",
        "trade_event_id",
        "tracking_event_id",
        "validation_event_id",
        "reconcile_run_id",
        "request_id",
    ):
        if key in record:
            return str(record[key])
    return None


def validate_record(record: dict[str, Any]) -> dict[str, Any]:
    schema_name = record.get("schema")
    if schema_name not in SCHEMAS:
        raise ValidationError("schema", "unknown_schema", f"unsupported schema {schema_name!r}")

    spec = SCHEMAS[schema_name]
    for field in spec.required:
        _get(record, field)
    for path, allowed in spec.enums.items():
        value = _get(record, path)
        if value not in allowed:
            raise ValidationError(path, "invalid_enum", f"{value!r} is not allowed")
    for check in spec.checks:
        check(record)
    return {"ok": True, "schema": schema_name, "record_id": record_id(record)}


def load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if path.suffix == ".json":
        value = json.loads(text)
    elif yaml is not None:
        value = yaml.safe_load(text)
    else:
        raise RuntimeError("PyYAML is required for YAML inputs")
    return value if isinstance(value, list) else [value]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", help="emit JSON result lines")
    args = parser.parse_args(argv)

    exit_code = 0
    for file_path in args.files:
        for record in load_records(file_path):
            try:
                result = validate_record(record)
            except ValidationError as exc:
                exit_code = 1
                result = {
                    "ok": False,
                    "schema": record.get("schema"),
                    "record_id": record_id(record),
                    "failure_path": exc.path,
                    "reject_code": exc.code,
                    "message": exc.message,
                }
            print(json.dumps(result, ensure_ascii=False) if args.json else result)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
