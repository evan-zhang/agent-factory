#!/usr/bin/env python3
"""S5d protocol for outer-agent TAROC research collection."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from market_data import DEFAULT_UNIVERSE_FILE, load_universe_symbols
from research_data import ResearchDataError, normalize_research


class ResearchProtocolError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def build_research_plan(
    market: str,
    symbols: list[str] | None = None,
    run_date: str | None = None,
    universe_file: Path = DEFAULT_UNIVERSE_FILE,
    universe_ref: str = "default",
) -> dict[str, Any]:
    selected_symbols = symbols or load_universe_symbols(universe_file, market, universe_ref)
    year = (run_date or dt.date.today().isoformat())[:4]
    # Market-specific query templates for better search coverage
    market_query_templates = {
        "CN": {
            "positive": f"{{symbol}} {year} 业绩 催化剂 公告 利好 增长 订单",
            "negative": f"{{symbol}} {year} 风险 利空 下调 减持 处罚 质疑",
        },
        "HK": {
            "positive": f"{{symbol}} {year} 业绩 催化 公告 利好 growth catalyst earnings",
            "negative": f"{{symbol}} {year} 风险 利空 下调 risk bear case downgrade {year}",
        },
        "US": {
            "positive": f"{{symbol}} news catalyst earnings guidance product order {year}",
            "negative": f"{{symbol}} risk negative bear case downgrade lawsuit problem {year}",
        },
    }
    templates = market_query_templates.get(market, market_query_templates["US"])
    return {
        "schema": "taroc_research_plan.v1",
        "market": market,
        "run_date": run_date or dt.date.today().isoformat(),
        "requirements": {
            "positive_search_min_results": 1,
            "negative_search_required": True,
            "negative_search_min_results": 0,
            "output_schema": "taroc_research_file.v1",
            "write_json_only": True,
        },
        "items": [
            {
                "symbol": symbol,
                "positive_query": templates["positive"].format(symbol=symbol),
                "negative_query": templates["negative"].format(symbol=symbol),
            }
            for symbol in selected_symbols
        ],
        "output_template": {
            "items": [
                {
                    "symbol": "<symbol>",
                    "negative_search_performed": True,
                    "negative_search_query": "<negative_query used>",
                    "positive": [
                        {
                            "title": "<source title>",
                            "url": "<source url>",
                            "publisher": "<publisher>",
                            "excerpt": "<short relevant excerpt or summary>",
                            "source_type": "news",
                        }
                    ],
                    "negative": [],
                }
            ]
        },
    }


def validate_research_file(path: Path, symbols: list[str] | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        researches = normalize_research(value)
    except (OSError, json.JSONDecodeError, ResearchDataError) as exc:
        raise ResearchProtocolError("invalid_research_file", str(exc)) from exc

    expected = set(symbols or [item.symbol for item in researches])
    actual = {item.symbol for item in researches}
    missing = sorted(expected - actual)
    if missing:
        raise ResearchProtocolError("missing_research_symbol", "missing symbols: " + ", ".join(missing))

    failures: list[str] = []
    for item in researches:
        if item.symbol not in expected:
            continue
        if not item.negative_search_performed:
            failures.append(f"{item.symbol}: negative_search_performed=false")
        if not item.negative_search_query:
            failures.append(f"{item.symbol}: negative_search_query missing")
        if len(item.positive) < 1:
            failures.append(f"{item.symbol}: positive_search_min_results=1 not met (got 0)")
        for entry in [*item.positive, *item.negative]:
            for field in ("title", "url", "publisher", "excerpt"):
                if not entry.get(field):
                    failures.append(f"{item.symbol}: evidence missing {field}")
    if failures:
        raise ResearchProtocolError("research_contract_failed", "; ".join(failures))
    return {
        "ok": True,
        "symbols": sorted(actual & expected),
        "positive_count": sum(len(item.positive) for item in researches if item.symbol in expected),
        "negative_count": sum(len(item.negative) for item in researches if item.symbol in expected),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan")
    plan.add_argument("--market", choices=["US", "HK", "CN"], required=True)
    plan.add_argument("--symbols", nargs="+")
    plan.add_argument("--run-date")
    plan.add_argument("--universe-file", type=Path, default=DEFAULT_UNIVERSE_FILE)
    plan.add_argument("--universe-ref", default="default")

    validate = sub.add_parser("validate")
    validate.add_argument("file", type=Path)
    validate.add_argument("--symbols", nargs="+")
    validate.add_argument("--market", choices=["US", "HK", "CN"])
    validate.add_argument("--universe-file", type=Path, default=DEFAULT_UNIVERSE_FILE)
    validate.add_argument("--universe-ref", default="default")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "plan":
            result = build_research_plan(args.market, args.symbols, args.run_date, args.universe_file, args.universe_ref)
        else:
            symbols = args.symbols
            if symbols is None and args.market:
                symbols = load_universe_symbols(args.universe_file, args.market, args.universe_ref)
            result = validate_research_file(args.file, symbols)
    except ResearchProtocolError as exc:
        result = {"ok": False, "reject": {"code": exc.code, "message": exc.message}}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
