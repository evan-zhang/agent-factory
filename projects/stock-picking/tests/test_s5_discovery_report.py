#!/usr/bin/env python3
"""Tests for S5c channel report rendering."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import discovery_report
from event_store import JsonlEventStore


UUID = "123e4567-e89b-12d3-a456-426614174000"
ISO = "2026-06-24T00:00:00+00:00"


def test_report_without_draft_is_heartbeat(tmp_path):
    report = discovery_report.render_report(JsonlEventStore(tmp_path / "events"), "US")
    assert report.startswith("HEARTBEAT_OK")


def test_report_renders_latest_draft_with_claim_counts(tmp_path):
    store = JsonlEventStore(tmp_path / "events")
    store.append_many(
        [
            {
                "schema": "evidence_ref.v1",
                "evidence_id": "ev_01ARZ3NDEKTSV4RRFFQ69G5FAV",
                "created_at": ISO,
                "created_by": "node_3_taroc",
                "source_url": "",
                "source_id": "AAPL.US",
                "source_type": "broker_data",
                "source_subtype": "other",
                "title": "Quote",
                "excerpt": "last=299.59",
                "publisher": "Longbridge",
                "fetched_at": ISO,
                "observed_at": ISO,
                "language": "en",
                "snapshot_ref": "longbridge:AAPL.US:2026-06-24",
                "claim_hash": "0" * 64,
                "publisher_authority": 0.8,
                "ai_classified_quality": 0.7,
                "classification_method": "publisher_table",
                "source_quality": "high",
                "status": "active",
                "content_hash": "sha256:" + "0" * 64,
                "raw_snapshot_path": None,
            },
            {
                "schema": "evidence_ref.v1",
                "evidence_id": "ev_01BRZ3NDEKTSV4RRFFQ69G5FAV",
                "created_at": ISO,
                "created_by": "node_3_taroc",
                "source_url": "",
                "source_id": "AAPL.US",
                "source_type": "news",
                "source_subtype": "news",
                "title": "Risk title",
                "excerpt": "risk",
                "publisher": "Example",
                "fetched_at": ISO,
                "observed_at": ISO,
                "language": "en",
                "snapshot_ref": "research:AAPL.US:2026-06-24:negative",
                "claim_hash": "1" * 64,
                "publisher_authority": 0.5,
                "ai_classified_quality": 0.5,
                "classification_method": "llm_judge",
                "source_quality": "medium",
                "status": "active",
                "content_hash": "sha256:" + "1" * 64,
                "raw_snapshot_path": None,
            },
            {
                "schema": "claim.v1",
                "claim_id": "cl_01ARZ3NDEKTSV4RRFFQ69G5FAV",
                "created_at": ISO,
                "created_by": "node_3_taroc",
                "scope": {"symbol": "AAPL.US", "market": "US", "strategy_id": "taroc"},
                "request_id": UUID,
                "correlation_id": UUID,
                "claim_text": "risk",
                "claim_kind": "risk",
                "polarity": "negative",
                "thesis_broken": False,
                "severity": "warning",
                "confidence": {"level": "medium"},
                "evidence_ids": ["ev_01BRZ3NDEKTSV4RRFFQ69G5FAV"],
                "negative_search_performed": True,
                "negative_search_query": "AAPL.US risk",
                "valid_until": "2026-07-08T23:59:00+00:00",
                "status": "active",
            },
            {
                "schema": "draft_candidates.v1",
                "draft_candidates_version": "1.0.0",
                "produced_by": {"strategy_id": "taroc", "strategy_version": "1.0.0", "registry_record_hash": "sha256:" + "2" * 64},
                "produced_at": ISO,
                "request_id": UUID,
                "correlation_id": UUID,
                "market": "US",
                "run_mode": "discovery",
                "universe_ref": "us_default",
                "themes": [],
                "candidates": [
                    {
                        "draft_id": UUID,
                        "strategy_run_id": UUID,
                        "strategy_id": "taroc",
                        "strategy_version": "1.0.0",
                        "source_research_id": None,
                        "stock_code": "AAPL.US",
                        "stock_name": "AAPL.US",
                        "market": "US",
                        "price": 299.59,
                        "thesis_summary": "fixture thesis",
                        "confidence": {"source": "strategy_self_rated", "level": "medium", "score": None},
                        "tracking_horizon": {"kind": "short_event", "default_window_sessions": 10},
                        "source_evidence": ["ev_01ARZ3NDEKTSV4RRFFQ69G5FAV"],
                        "negative_evidence": ["ev_01BRZ3NDEKTSV4RRFFQ69G5FAV"],
                        "negative_evidence_searched": True,
                        "expires_at": "2026-07-08T23:59:00+00:00",
                        "next_step": "validation",
                    }
                ],
                "warnings": ["live_quote_with_research"],
                "partial": False,
                "failure": {"code": None, "message": None},
            },
        ]
    )
    report = discovery_report.render_report(store, "US")
    assert "TAROC discovery US" in report
    assert "1. AAPL.US @ 299.59" in report
    assert "evidence: +1 / -1 | claims: 1" in report
    assert "first risk: Risk title" in report
