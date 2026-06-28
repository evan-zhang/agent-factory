#!/usr/bin/env python3

from __future__ import annotations

import copy
import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validate_schema = load_module("validate_schema", ROOT / "src/scripts/validate_schema.py")
validate_registry = load_module("validate_registry", ROOT / "src/scripts/validate_registry.py")
execution_guard = load_module("execution_guard", ROOT / "src/scripts/execution_guard.py")
event_store = load_module("event_store", ROOT / "src/scripts/event_store.py")
migrate_legacy_csv = load_module("migrate_legacy_csv", ROOT / "src/scripts/migrate_legacy_csv.py")
dry_run_orchestrator = load_module("dry_run_orchestrator", ROOT / "src/scripts/dry_run_orchestrator.py")
cron_readiness = load_module("cron_readiness", ROOT / "src/scripts/cron_readiness.py")
operator_notification = load_module("operator_notification", ROOT / "src/scripts/operator_notification.py")


UUID = "123e4567-e89b-12d3-a456-426614174000"
UUID2 = "123e4567-e89b-12d3-a456-426614174001"
ISO = "2026-06-24T00:00:00+00:00"
FUTURE = "2999-01-01T00:00:00+00:00"
EV = "ev_01ARZ3NDEKTSV4RRFFQ69G5FAV"
CL = "cl_01ARZ3NDEKTSV4RRFFQ69G5FAV"
SHA = "0" * 64


class SchemaValidatorTests(unittest.TestCase):
    def assert_valid(self, record):
        self.assertTrue(validate_schema.validate_record(record)["ok"])

    def assert_invalid(self, record, code):
        with self.assertRaises(validate_schema.ValidationError) as caught:
            validate_schema.validate_record(record)
        self.assertEqual(caught.exception.code, code)

    def test_all_declared_schemas_have_positive_fixture(self):
        fixtures = {
            "atomic_request.v1": {
                "schema": "atomic_request.v1",
                "request_id": UUID,
                "correlation_id": UUID2,
                "caller": "manual",
                "requested_at": ISO,
                "market": "US",
                "strategy_id": "taroc",
                "strategy_version": "1.0.0",
                "custom_ref": None,
                "run_mode": "discovery",
                "run_date": "2026-06-24",
                "signal_date": "2026-06-24",
                "timezone": "Asia/Shanghai",
                "universe_ref": "sp500",
                "dry_run": True,
                "priority": "normal",
                "idempotency_key": "k",
            },
            "run_context.v1": {
                "schema": "run_context.v1",
                "request_id": UUID,
                "correlation_id": UUID2,
                "decision": "proceed",
                "calendar_status": "open",
                "market_session": "regular",
                "calendar_skip_reason": "none",
                "failure_code": None,
                "calendar_source": "fixture",
                "calendar_source_version": "1",
                "calendar_checked_at": ISO,
                "context_warnings": [],
            },
            "strategy_dispatch.v1": {
                "schema": "strategy_dispatch.v1",
                "request_id": UUID,
                "correlation_id": UUID2,
                "node_id": "node_2_strategy_selector",
                "decision": "dispatch",
                "strategy_dispatch": {
                    "strategy_id": "taroc",
                    "strategy_version": "1.0.0",
                    "entrypoint": "x:y",
                    "output_schema": "draft_candidates.v1",
                    "registry_version": "1",
                    "registry_snapshot_hash": "sha256:" + SHA,
                    "registry_record_hash": "sha256:" + SHA,
                    "policy_flags": [],
                },
                "reject": {"code": None, "message": None},
                "warnings": [],
                "audit": {"selected_at": ISO, "custom_ref": None},
            },
            "draft_candidates.v1": {
                "schema": "draft_candidates.v1",
                "draft_candidates_version": "1.0.0",
                "produced_by": {"strategy_id": "taroc", "strategy_version": "1.0.0", "registry_record_hash": "sha256:" + SHA},
                "produced_at": ISO,
                "request_id": UUID,
                "correlation_id": UUID2,
                "market": "US",
                "run_mode": "discovery",
                "universe_ref": "u",
                "themes": [],
                "candidates": [{"strategy_id": "taroc", "strategy_version": "1.0.0", "source_evidence": [EV], "negative_evidence_searched": True}],
                "warnings": [],
                "partial": False,
                "failure": {"code": None, "message": None},
            },
            "theme_research.v1": {
                "schema": "theme_research.v1",
                "theme_research_version": "1.0.0",
                "research_id": UUID,
                "request_id": UUID,
                "correlation_id": UUID2,
                "strategy_id": "chokepoint",
                "strategy_version": "0.1.0",
                "produced_at": ISO,
                "market": "US",
                "theme": {},
                "signals": [],
                "evidence": [],
                "negative_evidence": [],
                "break_conditions": [],
                "uncertainty_level": "medium",
                "risk_flags": {},
                "upgrade_triggers": [],
                "promotion_status": "observe",
                "reject_reason": None,
            },
            "validation_event.v1": {
                "schema": "validation_event.v1",
                "validation_event_id": UUID,
                "validation_run_id": UUID2,
                "draft_id": UUID,
                "request_id": UUID,
                "correlation_id": UUID2,
                "calendar_checked_at": ISO,
                "validation_session_key": "s",
                "signal_date": "2026-06-24",
                "calendar_status": "open",
                "half_day_policy": "exclude",
                "verdict": "confirm",
                "validation_confidence": {"level": "high", "rationale": "fixture"},
                "price_action": "ok",
                "thesis_update": "ok",
                "new_evidence": [],
                "negative_update": [],
                "promote_candidate": True,
            },
            "candidate_record.v1": {
                "schema": "candidate_record.v1",
                "candidate_id": UUID,
                "origin_draft_id": UUID2,
                "request_id": UUID,
                "correlation_id": UUID2,
                "source_drafts": [],
                "stock_code": "AAPL",
                "market": "US",
                "state": "active",
                "actor": "system",
                "aggregate_thesis": "x",
                "aggregate_thesis_kind": "summary",
                "created_at": ISO,
                "expires_at": ISO,
                "last_state_event_id": UUID,
            },
            "tracking_event.v1": {
                "schema": "tracking_event.v1",
                "tracking_event_id": UUID,
                "candidate_id": UUID,
                "origin_draft_id": UUID2,
                "request_id": UUID,
                "correlation_id": UUID2,
                "week_id": "2026-W26",
                "event_type": "weekly_review",
                "actor": "agent",
                "suggested_reason": None,
                "supporting_evidence": [],
                "state_transition": {"from_state": None, "to_state": None},
                "created_at": ISO,
            },
            "target_pool_item.v1": {
                "schema": "target_pool_item.v1",
                "pool_item_id": UUID,
                "candidate_id": UUID,
                "origin_draft_id": UUID2,
                "request_id": UUID,
                "correlation_id": UUID2,
                "stock_code": "AAPL",
                "market": "US",
                "entry_price": 1,
                "stop_loss": 0.8,
                "target_price": 1.5,
                "position_amount": 100,
                "sizing_state": "sized",
                "promotion_reason": "x",
                "status": "active",
                "created_date": "2026-06-24",
                "decision_deadline": "2026-06-25",
                "diff_audit_ref": "d",
                "created_at": ISO,
            },
            "approval.v1": {
                "schema": "approval.v1",
                "approval_id": UUID,
                "pool_item_id": UUID2,
                "candidate_id": UUID,
                "request_id": UUID,
                "correlation_id": UUID2,
                "action": "buy",
                "approval_state": "approved",
                "approved_by": "Evan",
                "approved_at": ISO,
                "approval_note": "ok",
                "pretrade_check_id": UUID,
                "expires_at": FUTURE,
                "created_at": ISO,
            },
            "reconcile_report.v1": {
                "schema": "reconcile_report.v1",
                "reconcile_run_id": UUID,
                "request_id": UUID,
                "correlation_id": UUID2,
                "generated_at": ISO,
                "summary": {},
                "mismatches": [],
            },
            "risk_event.v1": {
                "schema": "risk_event.v1",
                "risk_event_id": UUID,
                "request_id": UUID,
                "correlation_id": UUID2,
                "source": "strategy_tracking",
                "stock_code": None,
                "event_type": "thesis_broken",
                "severity": "warning",
                "recommended_action": "notify",
                "execution_allowed": False,
                "thesis_broken": True,
                "evidence": [],
                "created_at": ISO,
            },
            "trade_log_event.v1": {
                "schema": "trade_log_event.v1",
                "trade_event_id": UUID,
                "request_id": UUID,
                "correlation_id": UUID2,
                "action": "buy",
                "mode": "dry_run",
                "stock_code": "AAPL",
                "market": "US",
                "approval_id": None,
                "execution_guard_decision_id": None,
                "broker": "futu",
                "status": "pending",
                "created_at": ISO,
                "expires_at": None,
            },
            "execution_guard_decision.v1": {
                "schema": "execution_guard_decision.v1",
                "decision_id": UUID,
                "request_id": UUID,
                "correlation_id": UUID2,
                "action": "buy",
                "decision": "block",
                "block_code": "approval_missing",
                "approval_id": None,
                "pretrade_check_id": None,
                "broker": "futu",
                "market": "US",
                "created_at": ISO,
                "audit": {"guard_version": "x", "checks": []},
            },
            "evidence_ref.v1": {
                "schema": "evidence_ref.v1",
                "evidence_id": EV,
                "created_at": ISO,
                "created_by": "human",
                "source_url": None,
                "source_id": "s",
                "source_type": "unverified",
                "source_subtype": "other",
                "title": "t",
                "excerpt": "e",
                "publisher": None,
                "fetched_at": ISO,
                "observed_at": ISO,
                "language": "en",
                "snapshot_ref": None,
                "claim_hash": SHA,
                "publisher_authority": 0.1,
                "ai_classified_quality": 0.2,
                "classification_method": "human",
                "source_quality": "unknown",
                "status": "active",
                "content_hash": SHA,
                "raw_snapshot_path": None,
            },
            "claim.v1": {
                "schema": "claim.v1",
                "claim_id": CL,
                "created_at": ISO,
                "created_by": "human",
                "scope": {"market": "US", "stock_code": "AAPL", "theme_id": None, "candidate_id": None, "draft_id": None},
                "request_id": UUID,
                "correlation_id": UUID2,
                "claim_text": "x",
                "claim_kind": "support",
                "polarity": "positive",
                "thesis_broken": False,
                "severity": None,
                "confidence": {"source": "human", "level": "high"},
                "evidence_ids": [EV],
                "negative_search_performed": True,
                "negative_search_query": None,
                "valid_until": None,
                "status": "active",
            },
            "legacy_csv_projection.v1": {"schema": "legacy_csv_projection.v1", "legacy_files": []},
        }
        self.assertEqual(set(fixtures), set(validate_schema.SCHEMAS))
        for record in fixtures.values():
            self.assert_valid(record)

    def test_rejects_noncanonical_evidence_and_claim_ids(self):
        evidence = {
            "schema": "evidence_ref.v1",
            "evidence_id": "bad",
            "created_at": ISO,
            "created_by": "human",
            "source_url": None,
            "source_id": "s",
            "source_type": "unverified",
            "source_subtype": "other",
            "title": "t",
            "excerpt": "e",
            "publisher": None,
            "fetched_at": ISO,
            "observed_at": ISO,
            "language": "en",
            "snapshot_ref": None,
            "claim_hash": SHA,
            "publisher_authority": 0.1,
            "ai_classified_quality": 0.2,
            "classification_method": "human",
            "source_quality": "unknown",
            "status": "active",
            "content_hash": SHA,
            "raw_snapshot_path": None,
        }
        self.assert_invalid(evidence, "invalid_evidence_id")
        claim = {
            "schema": "claim.v1",
            "claim_id": "bad",
            "created_at": ISO,
            "created_by": "human",
            "scope": {},
            "request_id": UUID,
            "correlation_id": UUID2,
            "claim_text": "x",
            "claim_kind": "support",
            "polarity": "positive",
            "thesis_broken": False,
            "severity": None,
            "confidence": {},
            "evidence_ids": [EV],
            "negative_search_performed": True,
            "negative_search_query": None,
            "valid_until": None,
            "status": "active",
        }
        self.assert_invalid(claim, "invalid_claim_id")

    def test_unknown_critical_enum_fails(self):
        record = {
            "schema": "atomic_request.v1",
            "request_id": UUID,
            "correlation_id": UUID2,
            "caller": "cron",
            "requested_at": ISO,
            "market": "JP",
            "strategy_id": "taroc",
            "strategy_version": "1.0.0",
            "custom_ref": None,
            "run_mode": "discovery",
            "run_date": "2026-06-24",
            "signal_date": "2026-06-24",
            "timezone": "Asia/Shanghai",
            "universe_ref": "u",
            "dry_run": True,
            "priority": "normal",
            "idempotency_key": "k",
        }
        self.assert_invalid(record, "invalid_enum")

    def test_validation_event_rejects_promote_verdict_mismatch(self):
        record = {
            "schema": "validation_event.v1",
            "validation_event_id": UUID,
            "validation_run_id": UUID2,
            "draft_id": UUID,
            "request_id": UUID,
            "correlation_id": UUID2,
            "calendar_checked_at": ISO,
            "validation_session_key": "s",
            "signal_date": "2026-06-24",
            "calendar_status": "open",
            "half_day_policy": "exclude",
            "verdict": "reject",
            "validation_confidence": {"level": "high", "rationale": "fixture"},
            "price_action": "bad",
            "thesis_update": "broken",
            "new_evidence": [],
            "negative_update": [],
            "promote_candidate": True,
        }
        self.assert_invalid(record, "promote_candidate_mismatch")


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = ROOT / "src/strategies/registry.yaml"
        self.custom_refs = ROOT / "src/strategies/custom_refs.yaml"
        self.request = {
            "request_id": UUID,
            "correlation_id": UUID2,
            "strategy_id": "taroc",
            "strategy_version": "1.0.0",
            "caller": "manual",
            "market": "US",
            "run_mode": "discovery",
            "dry_run": True,
            "custom_ref": None,
            "selected_at": ISO,
        }
        self.context = {"decision": "proceed", "market": "US"}

    def dispatch(self, **updates):
        request = copy.deepcopy(self.request)
        request.update(updates)
        return validate_registry.select_dispatch(request, self.context, self.registry, self.custom_refs)

    def test_supported_exact_request_dispatches_with_hashes(self):
        result = self.dispatch()
        self.assertEqual(result["decision"], "dispatch")
        self.assertEqual(result["strategy_dispatch"]["entrypoint"], "strategies.taroc:run")
        self.assertTrue(result["strategy_dispatch"]["registry_snapshot_hash"].startswith("sha256:"))
        self.assertTrue(result["strategy_dispatch"]["registry_record_hash"].startswith("sha256:"))
        self.assertTrue(validate_schema.validate_record(result)["ok"])

    def test_required_rejects(self):
        self.assertEqual(self.dispatch(strategy_id="missing")["reject"]["code"], "strategy_not_found")
        self.assertEqual(self.dispatch(market="JP")["reject"]["code"], "unsupported_market")
        self.assertEqual(self.dispatch(run_mode="tracking")["reject"]["code"], "unsupported_run_mode")
        self.assertEqual(self.dispatch(caller="cron", strategy_version=None)["reject"]["code"], "version_required")
        self.assertEqual(self.dispatch(strategy_id="chokepoint", strategy_version="0.1.0", caller="cron")["reject"]["code"], "experimental_not_allowed")
        self.assertEqual(self.dispatch(custom_ref="../x")["reject"]["code"], "custom_ref_invalid")
        context = {"decision": "skip", "market": "US"}
        result = validate_registry.select_dispatch(self.request, context, self.registry, self.custom_refs)
        self.assertEqual(result["reject"]["code"], "upstream_not_proceed")

    def test_disabled_strategy_rejects_without_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "registry.yaml"
            custom_path = Path(tmp) / "custom_refs.yaml"
            data = yaml.safe_load(self.registry.read_text())
            data["strategies"][0]["status"] = "disabled"
            registry_path.write_text(yaml.safe_dump(data), encoding="utf-8")
            custom_path.write_text(self.custom_refs.read_text(), encoding="utf-8")
            result = validate_registry.select_dispatch(self.request, self.context, registry_path, custom_path)
            self.assertEqual(result["reject"]["code"], "strategy_disabled")
            self.assertEqual(result["strategy_dispatch"]["strategy_id"], "taroc")


class ExecutionGuardTests(unittest.TestCase):
    def setUp(self):
        self.atomic = {"request_id": UUID, "correlation_id": UUID2, "dry_run": False, "market": "US"}
        self.context = {"decision": "proceed", "market": "US"}
        self.action = {"action": "buy", "broker": "futu", "market": "US", "pool_item_id": UUID}
        self.approval = {
            "approval_id": UUID,
            "pool_item_id": UUID,
            "approval_state": "approved",
            "approved_by": "Evan",
            "expires_at": FUTURE,
        }
        self.pretrade = {"pretrade_check_id": UUID2, "status": "pass"}

    def decision(self, **updates):
        approval = updates.pop("approval", self.approval)
        pretrade = updates.pop("pretrade", self.pretrade)
        action = copy.deepcopy(self.action)
        action.update(updates)
        return execution_guard.evaluate_execution(self.atomic, self.context, action, approval, pretrade)

    def test_refusal_codes(self):
        self.assertEqual(self.decision(approval=None)["block_code"], "approval_missing")
        expired = dict(self.approval, expires_at="2000-01-01T00:00:00+00:00")
        self.assertEqual(self.decision(approval=expired)["block_code"], "approval_expired")
        wrong_user = dict(self.approval, approved_by="SomeoneElse")
        self.assertEqual(self.decision(approval=wrong_user)["block_code"], "approval_not_by_evan")
        self.assertEqual(self.decision(pretrade=None)["block_code"], "pretrade_check_missing")
        self.assertEqual(self.decision(market="HK")["block_code"], "market_mismatch")
        self.assertEqual(self.decision(action="wire")["block_code"], "unknown_broker_action")
        atomic = dict(self.atomic, dry_run=True)
        dry_run = execution_guard.evaluate_execution(atomic, self.context, self.action, None, None)
        self.assertEqual(dry_run["decision"], "dry_run")

    def test_proxy_blocks_before_broker_and_allows_after_checks(self):
        sink = execution_guard.InMemoryAuditSink()
        blocked = execution_guard.guard_broker_action(sink, self.atomic, self.context, self.action, None, self.pretrade)(lambda: "called")
        with self.assertRaises(execution_guard.ExecutionBlockedError):
            blocked()
        self.assertEqual(sink.broker_api_calls, 0)
        self.assertEqual(sink.decisions[-1]["block_code"], "approval_missing")

        allowed = execution_guard.guard_broker_action(sink, self.atomic, self.context, self.action, self.approval, self.pretrade)(lambda: "called")
        self.assertEqual(allowed(), "called")
        self.assertEqual(sink.broker_api_calls, 1)
        self.assertEqual(sink.decisions[-1]["decision"], "allow")


class EventStoreAndProjectionTests(unittest.TestCase):
    def test_append_validates_and_reads_jsonl(self):
        record = {
            "schema": "candidate_record.v1",
            "candidate_id": UUID,
            "origin_draft_id": UUID2,
            "request_id": UUID,
            "correlation_id": UUID2,
            "source_drafts": [],
            "stock_code": "AAPL",
            "market": "US",
            "state": "active",
            "actor": "system",
            "aggregate_thesis": "x",
            "aggregate_thesis_kind": "summary",
            "created_at": ISO,
            "expires_at": ISO,
            "last_state_event_id": UUID,
        }
        with tempfile.TemporaryDirectory() as tmp:
            store = event_store.JsonlEventStore(Path(tmp))
            result = store.append(record)
            self.assertEqual(result["schema"], "candidate_record.v1")
            self.assertEqual(store.read_schema("candidate_record.v1"), [record])

            invalid = dict(record, state="removed", actor="agent")
            with self.assertRaises(validate_schema.ValidationError):
                store.append(invalid)

    def test_atomic_request_idempotency_does_not_duplicate(self):
        record = {
            "schema": "atomic_request.v1",
            "request_id": UUID,
            "correlation_id": UUID2,
            "caller": "manual",
            "requested_at": ISO,
            "market": "US",
            "strategy_id": "taroc",
            "strategy_version": "1.0.0",
            "custom_ref": None,
            "run_mode": "discovery",
            "run_date": "2026-06-24",
            "signal_date": "2026-06-24",
            "timezone": "Asia/Shanghai",
            "universe_ref": "sp500",
            "dry_run": True,
            "priority": "normal",
            "idempotency_key": "same-window",
        }
        with tempfile.TemporaryDirectory() as tmp:
            store = event_store.JsonlEventStore(Path(tmp))
            self.assertNotIn("idempotent_replay", store.append(record))
            replay = store.append(dict(record, request_id=UUID2, correlation_id=UUID))
            self.assertTrue(replay["idempotent_replay"])
            self.assertEqual(len(store.read_schema("atomic_request.v1")), 1)

    def test_legacy_projection_rows_are_derived_from_events(self):
        draft_event = {
            "schema": "draft_candidates.v1",
            "candidates": [
                {
                    "draft_id": UUID,
                    "strategy_run_id": UUID2,
                    "strategy_id": "taroc",
                    "strategy_version": "1.0.0",
                    "stock_code": "AAPL",
                    "stock_name": "Apple",
                    "market": "US",
                    "price": 1,
                    "thesis_summary": "x",
                    "confidence": {"level": "high"},
                    "negative_evidence_searched": True,
                    "expires_at": ISO,
                    "next_step": "validation",
                }
            ],
        }
        rows = migrate_legacy_csv.draft_rows([draft_event])
        self.assertEqual(rows[0]["stock_code"], "AAPL")
        self.assertEqual(rows[0]["confidence_level"], "high")


class DryRunOrchestratorTests(unittest.TestCase):
    def run_cli(self, argv):
        with contextlib.redirect_stdout(io.StringIO()):
            return dry_run_orchestrator.main(argv)

    def test_discovery_writes_valid_event_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            event_root = Path(tmp) / "events"
            argv = [
                "--event-root",
                str(event_root),
                "--registry",
                str(ROOT / "src/strategies/registry.yaml"),
                "--custom-refs",
                str(ROOT / "src/strategies/custom_refs.yaml"),
                "discovery",
                "--request-id",
                UUID,
                "--correlation-id",
                UUID2,
                "--run-date",
                "2026-06-24",
                "--signal-date",
                "2026-06-24",
            ]
            self.assertEqual(self.run_cli(argv), 0)

            store = event_store.JsonlEventStore(event_root)
            self.assertEqual(len(store.read_schema("atomic_request.v1")), 1)
            self.assertEqual(len(store.read_schema("run_context.v1")), 1)
            self.assertEqual(len(store.read_schema("strategy_dispatch.v1")), 1)
            drafts = store.read_schema("draft_candidates.v1")
            self.assertEqual(len(drafts), 1)
            self.assertEqual(drafts[0]["candidates"][0]["next_step"], "validation")

    def test_discovery_reject_does_not_emit_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            event_root = Path(tmp) / "events"
            argv = [
                "--event-root",
                str(event_root),
                "--registry",
                str(ROOT / "src/strategies/registry.yaml"),
                "--custom-refs",
                str(ROOT / "src/strategies/custom_refs.yaml"),
                "discovery",
                "--request-id",
                UUID,
                "--correlation-id",
                UUID2,
                "--calendar-status",
                "closed",
            ]
            self.assertEqual(self.run_cli(argv), 1)

            store = event_store.JsonlEventStore(event_root)
            dispatches = store.read_schema("strategy_dispatch.v1")
            self.assertEqual(dispatches[0]["decision"], "reject")
            self.assertEqual(dispatches[0]["reject"]["code"], "upstream_not_proceed")
            self.assertEqual(store.read_schema("draft_candidates.v1"), [])

    def test_discovery_idempotency_key_replay_does_not_append(self):
        with tempfile.TemporaryDirectory() as tmp:
            event_root = Path(tmp) / "events"
            base = [
                "--event-root",
                str(event_root),
                "--registry",
                str(ROOT / "src/strategies/registry.yaml"),
                "--custom-refs",
                str(ROOT / "src/strategies/custom_refs.yaml"),
                "discovery",
                "--run-date",
                "2026-06-24",
                "--signal-date",
                "2026-06-24",
                "--idempotency-key",
                "stock-picking:US:discovery:taroc:1.0.0:2026-06-24",
            ]
            self.assertEqual(self.run_cli(base + ["--request-id", UUID, "--correlation-id", UUID2]), 0)
            self.assertEqual(self.run_cli(base + ["--request-id", UUID2, "--correlation-id", UUID]), 0)

            store = event_store.JsonlEventStore(event_root)
            self.assertEqual(len(store.read_schema("atomic_request.v1")), 1)
            self.assertEqual(len(store.read_schema("draft_candidates.v1")), 1)

    def test_validation_reads_latest_draft_and_promotes_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            event_root = Path(tmp) / "events"
            base = [
                "--event-root",
                str(event_root),
                "--registry",
                str(ROOT / "src/strategies/registry.yaml"),
                "--custom-refs",
                str(ROOT / "src/strategies/custom_refs.yaml"),
            ]
            self.assertEqual(
                self.run_cli(
                    base
                    + [
                        "discovery",
                        "--request-id",
                        UUID,
                        "--correlation-id",
                        UUID2,
                        "--run-date",
                        "2026-06-24",
                        "--signal-date",
                        "2026-06-24",
                    ]
                ),
                0,
            )
            self.assertEqual(self.run_cli(base + ["validation", "--verdict", "confirm"]), 0)

            store = event_store.JsonlEventStore(event_root)
            validations = store.read_schema("validation_event.v1")
            candidates = store.read_schema("candidate_record.v1")
            self.assertEqual(len(validations), 1)
            self.assertEqual(validations[0]["verdict"], "confirm")
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0]["origin_draft_id"], validations[0]["draft_id"])

    def test_validation_draft_file_is_schema_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            event_root = Path(tmp) / "events"
            draft_file = Path(tmp) / "bad-draft.json"
            draft_file.write_text(
                '{"schema":"draft_candidates.v1","request_id":"not-a-uuid","candidates":[]}',
                encoding="utf-8",
            )
            argv = [
                "--event-root",
                str(event_root),
                "--registry",
                str(ROOT / "src/strategies/registry.yaml"),
                "--custom-refs",
                str(ROOT / "src/strategies/custom_refs.yaml"),
                "validation",
                "--draft-file",
                str(draft_file),
            ]
            self.assertEqual(self.run_cli(argv), 1)
            self.assertEqual(event_store.JsonlEventStore(event_root).read_schema("validation_event.v1"), [])

    def test_manual_pilot_calendar_override_requires_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            event_root = Path(tmp) / "events"
            argv = [
                "--event-root",
                str(event_root),
                "--registry",
                str(ROOT / "src/strategies/registry.yaml"),
                "--custom-refs",
                str(ROOT / "src/strategies/custom_refs.yaml"),
                "discovery",
                "--calendar-source",
                "manual_pilot_override",
            ]
            self.assertEqual(self.run_cli(argv), 1)
            self.assertEqual(event_store.JsonlEventStore(event_root).read_schema("atomic_request.v1"), [])

    def test_manual_pilot_calendar_override_is_audited_in_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            event_root = Path(tmp) / "events"
            argv = [
                "--event-root",
                str(event_root),
                "--registry",
                str(ROOT / "src/strategies/registry.yaml"),
                "--custom-refs",
                str(ROOT / "src/strategies/custom_refs.yaml"),
                "discovery",
                "--request-id",
                UUID,
                "--correlation-id",
                UUID2,
                "--calendar-source",
                "manual_pilot_override",
                "--calendar-override-reason",
                "local test",
            ]
            self.assertEqual(self.run_cli(argv), 0)
            contexts = event_store.JsonlEventStore(event_root).read_schema("run_context.v1")
            self.assertEqual(contexts[0]["calendar_source"], "manual_pilot_override")
            self.assertIn("not_production_calendar", contexts[0]["context_warnings"])

    def test_production_calendar_is_integrated_and_writes_on_open_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            event_root = Path(tmp) / "events"
            argv = [
                "--event-root",
                str(event_root),
                "--registry",
                str(ROOT / "src/strategies/registry.yaml"),
                "--custom-refs",
                str(ROOT / "src/strategies/custom_refs.yaml"),
                "discovery",
                "--caller",
                "cron",
                "--calendar-source",
                "production_calendar",
                "--signal-date",
                "2026-06-24",
                "--idempotency-key",
                "test:m4a:production-calendar:20260624",
            ]
            self.assertEqual(self.run_cli(argv), 0)
            store = event_store.JsonlEventStore(event_root)
            self.assertEqual(len(store.read_schema("atomic_request.v1")), 1)
            contexts = store.read_schema("run_context.v1")
            self.assertEqual(len(contexts), 1)
            self.assertEqual(contexts[0]["calendar_source"], "production_calendar")


class CronReadinessTests(unittest.TestCase):
    def test_readiness_gate_passes_with_absolute_event_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = cron_readiness.run_checks(
                Path(tmp) / "events",
                ROOT / "src/strategies/registry.yaml",
                ROOT / "src/strategies/custom_refs.yaml",
            )
            self.assertTrue(result["ok"], result)
            self.assertEqual(
                {check["name"] for check in result["checks"]},
                {"event_root", "registry_policy", "cli_allowlist", "production_calendar_integration", "dry_run_smoke", "validation_gate"},
            )

    def test_readiness_rejects_relative_event_root(self):
        result = cron_readiness.run_checks(
            Path("relative/events"),
            ROOT / "src/strategies/registry.yaml",
            ROOT / "src/strategies/custom_refs.yaml",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["checks"][0]["code"], "event_root_not_absolute")

    def test_readiness_rejects_chokepoint_cron_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "registry.yaml"
            data = yaml.safe_load((ROOT / "src/strategies/registry.yaml").read_text(encoding="utf-8"))
            for strategy in data["strategies"]:
                if strategy["id"] == "chokepoint":
                    strategy["allowed_callers"].append("cron")
            registry_path.write_text(yaml.safe_dump(data), encoding="utf-8")
            result = cron_readiness.run_checks(
                Path(tmp) / "events",
                registry_path,
                ROOT / "src/strategies/custom_refs.yaml",
            )
            policy = next(check for check in result["checks"] if check["name"] == "registry_policy")
            self.assertFalse(result["ok"])
            self.assertEqual(policy["code"], "chokepoint_cron_enabled")


class OperatorNotificationTests(unittest.TestCase):
    def route(self, **updates):
        base = {
            "schema": "operator_notification_route.v1",
            "route_id": "stock-picking-local",
            "channel": "local_log",
            "target": "/tmp/stock-picking-operator.log",
            "severity_min": "warning",
            "dry_run_only": True,
            "include_fields": [
                "request_id",
                "correlation_id",
                "reject_code",
                "event_root",
                "run_mode",
                "market",
                "strategy_id",
            ],
        }
        base.update(updates)
        return base

    def test_route_contract_accepts_dry_run_route(self):
        result = operator_notification.validate_route(self.route())
        self.assertEqual(result["route_id"], "stock-picking-local")

    def test_route_contract_rejects_missing_payload_fields_and_requires_explicit_mode(self):
        with self.assertRaises(operator_notification.OperatorRouteError) as missing:
            operator_notification.validate_route(self.route(include_fields=["request_id"]))
        self.assertEqual(missing.exception.code, "missing_payload_fields")

        result = operator_notification.validate_route(self.route(dry_run_only=False))
        self.assertEqual(result["route_id"], "stock-picking-local")

        with self.assertRaises(operator_notification.OperatorRouteError) as implicit_mode:
            operator_notification.validate_route(self.route(dry_run_only=None))
        self.assertEqual(implicit_mode.exception.code, "dry_run_only_required")

    def test_failure_payload_is_bounded_and_auditable(self):
        payload = operator_notification.build_failure_payload(
            self.route(),
            {
                "mode": "discovery",
                "request_id": UUID,
                "correlation_id": UUID2,
                "market": "US",
                "strategy_id": "taroc",
                "reject": {"code": "upstream_not_proceed", "message": "closed"},
            },
            Path("/tmp/events"),
        )
        self.assertEqual(payload["schema"], "operator_notification_payload.v1")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["suppressed"])
        self.assertEqual(payload["fields"]["reject_code"], "upstream_not_proceed")

    def test_failure_payload_respects_severity_min(self):
        payload = operator_notification.build_failure_payload(
            self.route(severity_min="critical"),
            {
                "mode": "discovery",
                "request_id": UUID,
                "correlation_id": UUID2,
                "market": "US",
                "strategy_id": "taroc",
                "reject": {"code": "upstream_not_proceed", "message": "closed", "severity": "warning"},
            },
            Path("/tmp/events"),
        )
        self.assertTrue(payload["suppressed"])
        self.assertEqual(payload["suppress_reason"], "severity_below_min")
        self.assertEqual(payload["fields"], {})

        critical = operator_notification.build_failure_payload(
            self.route(severity_min="critical"),
            {
                "mode": "discovery",
                "request_id": UUID,
                "correlation_id": UUID2,
                "market": "US",
                "strategy_id": "taroc",
                "reject": {"code": "calendar_unavailable", "message": "calendar down", "severity": "critical"},
            },
            Path("/tmp/events"),
        )
        self.assertFalse(critical["suppressed"])
        self.assertEqual(critical["severity"], "critical")


if __name__ == "__main__":
    unittest.main()
