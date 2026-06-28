#!/usr/bin/env python3
"""Tests for S5d outer-agent research protocol."""

from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import research_protocol


def test_research_plan_includes_positive_and_negative_queries():
    plan = research_protocol.build_research_plan("US", ["AAPL.US"], "2026-06-25")
    assert plan["schema"] == "taroc_research_plan.v1"
    item = plan["items"][0]
    assert item["symbol"] == "AAPL.US"
    assert "catalyst" in item["positive_query"]
    assert "bear case" in item["negative_query"]
    assert plan["requirements"]["negative_search_required"] is True


def test_validate_research_file_accepts_negative_search_with_zero_negative_results(tmp_path):
    path = tmp_path / "research.json"
    path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "symbol": "AAPL.US",
                        "negative_search_performed": True,
                        "negative_search_query": "AAPL.US risks bear case",
                        "positive": [
                            {
                                "title": "Apple catalyst",
                                "url": "https://example.test/apple-catalyst",
                                "publisher": "Example",
                                "excerpt": "Positive evidence",
                                "source_type": "news",
                            }
                        ],
                        "negative": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    result = research_protocol.validate_research_file(path, ["AAPL.US"])
    assert result["ok"] is True
    assert result["positive_count"] == 1
    assert result["negative_count"] == 0


def test_validate_research_file_rejects_missing_negative_search(tmp_path):
    path = tmp_path / "research.json"
    path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "symbol": "AAPL.US",
                        "negative_search_performed": False,
                        "positive": [
                            {
                                "title": "Apple catalyst",
                                "url": "https://example.test/apple-catalyst",
                                "publisher": "Example",
                                "excerpt": "Positive evidence",
                                "source_type": "news",
                            }
                        ],
                        "negative": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    try:
        research_protocol.validate_research_file(path, ["AAPL.US"])
    except research_protocol.ResearchProtocolError as exc:
        assert exc.code == "research_contract_failed"
    else:
        raise AssertionError("expected ResearchProtocolError")


def test_validate_research_file_rejects_missing_symbol(tmp_path):
    path = tmp_path / "research.json"
    path.write_text('{"items":[]}', encoding="utf-8")
    try:
        research_protocol.validate_research_file(path, ["AAPL.US"])
    except research_protocol.ResearchProtocolError as exc:
        assert exc.code == "missing_research_symbol"
    else:
        raise AssertionError("expected ResearchProtocolError")
