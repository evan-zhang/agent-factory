#!/usr/bin/env python3
"""Tests for S5f pilot output analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import pilot_analyzer
from event_store import JsonlEventStore


UUID = "123e4567-e89b-12d3-a456-426614174000"
ISO = "2026-06-25T00:00:00+00:00"


def _write_schema(root: Path, schema: str, records: list[dict]):
    path = root / f"{schema}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def _seed_pilot_events(root: Path, include_positive: bool = True, negative_searched: bool = True):
    source_evidence = ["ev_quote"]
    evidence = [
        {
            "schema": "evidence_ref.v1",
            "evidence_id": "ev_quote",
            "source_type": "broker_data",
            "title": "Quote",
            "source_id": "AAPL.US",
        }
    ]
    claims = []
    if include_positive:
        source_evidence.append("ev_positive")
        evidence.append(
            {
                "schema": "evidence_ref.v1",
                "evidence_id": "ev_positive",
                "source_type": "news",
                "title": "Catalyst",
                "source_id": "AAPL.US",
            }
        )
        claims.append(
            {
                "schema": "claim.v1",
                "claim_id": "cl_positive",
                "request_id": UUID,
                "scope": {"symbol": "AAPL.US", "market": "US", "strategy_id": "taroc"},
            }
        )

    _write_schema(root, "evidence_ref.v1", evidence)
    _write_schema(root, "claim.v1", claims)
    _write_schema(
        root,
        "draft_candidates.v1",
        [
            {
                "schema": "draft_candidates.v1",
                "produced_at": ISO,
                "request_id": UUID,
                "market": "US",
                "warnings": ["live_quote_with_research"],
                "candidates": [
                    {
                        "stock_code": "AAPL.US",
                        "source_evidence": source_evidence,
                        "negative_evidence": [],
                        "negative_evidence_searched": negative_searched,
                    }
                ],
            }
        ],
    )


def test_analyze_pilot_passes_when_universe_and_research_are_present(tmp_path):
    event_root = tmp_path / "events"
    _seed_pilot_events(event_root)

    result = pilot_analyzer.analyze_pilot(JsonlEventStore(event_root), "US", ["AAPL.US"])

    assert result["ok"] is True
    assert result["candidate_count"] == 1
    assert result["target_candidate_count"] == 1
    assert result["quote_evidence_count"] == 1
    assert result["positive_evidence_count"] == 1
    assert result["claim_count"] == 1


def test_analyze_pilot_flags_missing_positive_research(tmp_path):
    event_root = tmp_path / "events"
    _seed_pilot_events(event_root, include_positive=False)

    result = pilot_analyzer.analyze_pilot(JsonlEventStore(event_root), "US", ["AAPL.US"])

    assert result["ok"] is False
    assert result["missing_positive_research"] == ["AAPL.US"]
    assert "positive_research_gap" in result["warnings"]


def test_analyze_pilot_allows_non_selected_universe_symbols_when_limit_is_met(tmp_path):
    event_root = tmp_path / "events"
    _seed_pilot_events(event_root)

    result = pilot_analyzer.analyze_pilot(JsonlEventStore(event_root), "US", ["AAPL.US", "MSFT.US"], candidate_limit=1)

    assert result["ok"] is True
    assert result["non_selected_expected_symbols"] == ["MSFT.US"]


def test_analyze_pilot_flags_candidate_count_gap(tmp_path):
    event_root = tmp_path / "events"
    _seed_pilot_events(event_root)

    result = pilot_analyzer.analyze_pilot(JsonlEventStore(event_root), "US", ["AAPL.US", "MSFT.US"], candidate_limit=2)

    assert result["ok"] is False
    assert result["non_selected_expected_symbols"] == ["MSFT.US"]
    assert "candidate_count_gap" in result["warnings"]


def test_analyze_pilot_rejects_when_no_draft_exists(tmp_path):
    result = pilot_analyzer.analyze_pilot(JsonlEventStore(tmp_path / "events"), "US", ["AAPL.US"])

    assert result["ok"] is False
    assert result["reject"]["code"] == "draft_not_found"
