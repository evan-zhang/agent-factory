#!/usr/bin/env python3
"""Tests for S5a read-only market data integration."""

from __future__ import annotations

import datetime as dt
import sys
import tempfile
from types import SimpleNamespace
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import dry_run_orchestrator
import market_data
import research_data
from event_store import JsonlEventStore


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = PROJECT_ROOT / "src" / "strategies" / "registry.yaml"
CUSTOM_REFS = PROJECT_ROOT / "src" / "strategies" / "custom_refs.yaml"


def test_parse_json_prefix_ignores_cli_notice():
    value = market_data.parse_json_prefix('[{"symbol":"AAPL.US","last":"1"}]\n\nNew version available')
    assert value == [{"symbol": "AAPL.US", "last": "1"}]


def test_normalize_quotes_requires_symbol_and_last():
    quotes = market_data.normalize_quotes(
        [
            {
                "symbol": "AAPL.US",
                "last": "299.59",
                "change_percentage": "1.80",
                "turnover": "3621073562.267",
                "volume": 12216072,
                "status": "Normal",
            }
        ]
    )
    assert quotes[0].symbol == "AAPL.US"
    assert str(quotes[0].last) == "299.59"


def test_quote_evidence_has_valid_schema():
    quote = market_data.normalize_quotes([{"symbol": "AAPL.US", "last": "299.59", "status": "Normal"}])[0]
    evidence = market_data.quote_to_evidence(
        quote,
        {"request_id": "123e4567-e89b-12d3-a456-426614174000", "correlation_id": "123e4567-e89b-12d3-a456-426614174000", "signal_date": "2026-06-24"},
        created_at="2026-06-24T00:00:00+00:00",
    )
    result = dry_run_orchestrator.validate_record(evidence)
    assert result["ok"] is True
    assert evidence["source_type"] == "broker_data"


def test_longbridge_quote_treats_stderr_error_as_failure(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("LONGBRIDGE_APP_KEY=x\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="", stderr="Error: API error (code 429002): api request is limited")

    monkeypatch.setattr(market_data.subprocess, "run", fake_run)
    try:
        market_data.run_longbridge_quote(["AAPL.US"], env_file)
    except market_data.MarketDataError as exc:
        assert exc.code == "longbridge_quote_failed"
        assert "429002" in exc.message
    else:
        raise AssertionError("expected MarketDataError")


def test_live_quote_discovery_writes_evidence_and_drafts(monkeypatch):
    def fake_run_longbridge_quote(symbols, env_file, timeout_seconds):
        return market_data.normalize_quotes(
            [
                {
                    "symbol": symbols[0],
                    "last": "299.59",
                    "change_percentage": "1.80",
                    "turnover": "3621073562.267",
                    "volume": 12216072,
                    "status": "Normal",
                }
            ]
        )

    monkeypatch.setattr(dry_run_orchestrator, "run_longbridge_quote", fake_run_longbridge_quote)

    with tempfile.TemporaryDirectory(prefix=".s5-market-data-") as tmp:
        event_root = Path(tmp) / "events"
        args = dry_run_orchestrator.build_parser().parse_args(
            [
                "--event-root",
                str(event_root),
                "--registry",
                str(REGISTRY),
                "--custom-refs",
                str(CUSTOM_REFS),
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
                "production_calendar",
                "--signal-date",
                "2026-06-24",
                "--idempotency-key",
                f"test:s5:us:{dt.date.today()}",
                "--market-data-source",
                "longbridge_quote",
                "--universe-symbols",
                "AAPL.US",
            ]
        )
        result = dry_run_orchestrator.run_discovery(args)
        assert result["ok"] is True

        store = JsonlEventStore(event_root)
        evidence = store.read_schema("evidence_ref.v1")
        drafts = store.read_schema("draft_candidates.v1")
        assert len(evidence) == 1
        assert len(drafts) == 1
        assert drafts[0]["candidates"][0]["source_evidence"] == [evidence[0]["evidence_id"]]
        assert drafts[0]["candidates"][0]["stock_code"] == "AAPL.US"


def test_research_file_builds_valid_evidence_and_claims():
    research = research_data.normalize_research(
        {
            "items": [
                {
                    "symbol": "AAPL.US",
                    "negative_search_performed": True,
                    "negative_search_query": "AAPL.US bear case risk",
                    "positive": [
                        {
                            "title": "Apple catalyst",
                            "url": "https://example.test/apple-catalyst",
                            "publisher": "Example News",
                            "excerpt": "Positive catalyst summary",
                            "source_type": "news",
                        }
                    ],
                    "negative": [
                        {
                            "title": "Apple risk",
                            "url": "https://example.test/apple-risk",
                            "publisher": "Example News",
                            "excerpt": "Negative risk summary",
                            "source_type": "news",
                        }
                    ],
                }
            ]
        }
    )
    request = {
        "request_id": "123e4567-e89b-12d3-a456-426614174000",
        "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
        "signal_date": "2026-06-24",
        "market": "US",
        "strategy_id": "taroc",
    }
    records, by_symbol = research_data.build_research_records(request, research, created_at="2026-06-24T00:00:00+00:00")
    assert len(records) == 4
    assert len(by_symbol["AAPL.US"]["positive_evidence"]) == 1
    assert len(by_symbol["AAPL.US"]["negative_evidence"]) == 1
    for record in records:
        assert dry_run_orchestrator.validate_record(record)["ok"] is True


def test_live_quote_discovery_with_research_enriches_draft(monkeypatch, tmp_path):
    def fake_run_longbridge_quote(symbols, env_file, timeout_seconds):
        return market_data.normalize_quotes(
            [
                {
                    "symbol": symbols[0],
                    "last": "299.59",
                    "change_percentage": "1.80",
                    "turnover": "3621073562.267",
                    "volume": 12216072,
                    "status": "Normal",
                }
            ]
        )

    monkeypatch.setattr(dry_run_orchestrator, "run_longbridge_quote", fake_run_longbridge_quote)
    research_file = tmp_path / "research.json"
    research_file.write_text(
        """
{
  "items": [
    {
      "symbol": "AAPL.US",
      "negative_search_performed": true,
      "negative_search_query": "AAPL.US risks bear case",
      "positive": [
        {
          "title": "Apple catalyst",
          "url": "https://example.test/apple-catalyst",
          "publisher": "Example News",
          "excerpt": "Positive catalyst summary",
          "source_type": "news"
        }
      ],
      "negative": [
        {
          "title": "Apple risk",
          "url": "https://example.test/apple-risk",
          "publisher": "Example News",
          "excerpt": "Negative risk summary",
          "source_type": "news"
        }
      ]
    }
  ]
}
""",
        encoding="utf-8",
    )

    event_root = tmp_path / "events"
    args = dry_run_orchestrator.build_parser().parse_args(
        [
            "--event-root",
            str(event_root),
            "--registry",
            str(REGISTRY),
            "--custom-refs",
            str(CUSTOM_REFS),
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
            "production_calendar",
            "--signal-date",
            "2026-06-24",
            "--idempotency-key",
            "test:s5b:us:research",
            "--market-data-source",
            "longbridge_quote",
            "--universe-symbols",
            "AAPL.US",
            "--research-file",
            str(research_file),
        ]
    )
    result = dry_run_orchestrator.run_discovery(args)
    assert result["ok"] is True

    store = JsonlEventStore(event_root)
    evidence = store.read_schema("evidence_ref.v1")
    claims = store.read_schema("claim.v1")
    drafts = store.read_schema("draft_candidates.v1")
    assert len(evidence) == 3
    assert len(claims) == 2
    candidate = drafts[0]["candidates"][0]
    assert len(candidate["source_evidence"]) == 2
    assert len(candidate["negative_evidence"]) == 1
    assert candidate["negative_evidence_searched"] is True
    assert drafts[0]["warnings"] == ["live_quote_with_research", "requires_human_review_before_trade"]
