#!/usr/bin/env python3
"""Tests for S5e configurable market universes."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import market_data
import research_protocol


PROJECT_ROOT = Path(__file__).resolve().parent.parent
UNIVERSE = PROJECT_ROOT / "src" / "config" / "universe.yaml"


def test_load_universe_symbols_from_yaml():
    symbols = market_data.load_universe_symbols(UNIVERSE, "US", "default")
    assert symbols[:3] == ["AAPL.US", "MSFT.US", "NVDA.US"]
    assert len(symbols) >= 6


def test_load_universe_symbols_supports_legacy_default_ref():
    assert market_data.load_universe_symbols(UNIVERSE, "HK", "hk_default")[0] == "9988.HK"


def test_load_universe_symbols_rejects_unknown_ref():
    try:
        market_data.load_universe_symbols(UNIVERSE, "US", "unknown")
    except market_data.MarketDataError as exc:
        assert exc.code == "unknown_universe_ref"
    else:
        raise AssertionError("expected MarketDataError")


def test_research_plan_uses_universe_config_by_default():
    plan = research_protocol.build_research_plan("CN", run_date="2026-06-25", universe_file=UNIVERSE)
    symbols = [item["symbol"] for item in plan["items"]]
    assert "600519.SH" in symbols
    assert "002594.SZ" in symbols


def test_research_protocol_validate_can_use_universe_symbols(tmp_path):
    path = tmp_path / "research.json"
    path.write_text(
        """
{
  "items": [
    {
      "symbol": "AAPL.US",
      "negative_search_performed": true,
      "negative_search_query": "AAPL.US risks bear case",
      "positive": [{"title": "t", "url": "https://example.test/a", "publisher": "p", "excerpt": "e"}],
      "negative": []
    },
    {
      "symbol": "MSFT.US",
      "negative_search_performed": true,
      "negative_search_query": "MSFT.US risks bear case",
      "positive": [{"title": "t", "url": "https://example.test/m", "publisher": "p", "excerpt": "e"}],
      "negative": []
    },
    {
      "symbol": "NVDA.US",
      "negative_search_performed": true,
      "negative_search_query": "NVDA.US risks bear case",
      "positive": [{"title": "t", "url": "https://example.test/n", "publisher": "p", "excerpt": "e"}],
      "negative": []
    },
    {
      "symbol": "AMZN.US",
      "negative_search_performed": true,
      "negative_search_query": "AMZN.US risks bear case",
      "positive": [{"title": "t", "url": "https://example.test/am", "publisher": "p", "excerpt": "e"}],
      "negative": []
    },
    {
      "symbol": "GOOGL.US",
      "negative_search_performed": true,
      "negative_search_query": "GOOGL.US risks bear case",
      "positive": [{"title": "t", "url": "https://example.test/g", "publisher": "p", "excerpt": "e"}],
      "negative": []
    },
    {
      "symbol": "META.US",
      "negative_search_performed": true,
      "negative_search_query": "META.US risks bear case",
      "positive": [{"title": "t", "url": "https://example.test/me", "publisher": "p", "excerpt": "e"}],
      "negative": []
    },
    {
      "symbol": "TSLA.US",
      "negative_search_performed": true,
      "negative_search_query": "TSLA.US risks bear case",
      "positive": [{"title": "t", "url": "https://example.test/t", "publisher": "p", "excerpt": "e"}],
      "negative": []
    }
  ]
}
""",
        encoding="utf-8",
    )
    symbols = market_data.load_universe_symbols(UNIVERSE, "US", "default")
    result = research_protocol.validate_research_file(path, symbols)
    assert result["ok"] is True
    assert result["positive_count"] == len(symbols)
