#!/usr/bin/env python3
"""Analyze S5 pilot discovery output for coverage and research quality."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from event_store import JsonlEventStore
from market_data import DEFAULT_UNIVERSE_FILE, load_universe_symbols


def latest_draft(store: JsonlEventStore, market: str | None = None) -> dict[str, Any] | None:
    drafts = store.read_schema("draft_candidates.v1")
    if market:
        drafts = [draft for draft in drafts if draft.get("market") == market]
    return drafts[-1] if drafts else None


def analyze_pilot(
    store: JsonlEventStore,
    market: str,
    expected_symbols: list[str] | None = None,
    candidate_limit: int | None = 3,
) -> dict[str, Any]:
    draft = latest_draft(store, market)
    if draft is None:
        return {
            "ok": False,
            "market": market,
            "reject": {"code": "draft_not_found", "message": f"no draft_candidates.v1 event found for {market}"},
        }

    evidence_by_id = {record.get("evidence_id"): record for record in store.read_schema("evidence_ref.v1") if record.get("evidence_id")}
    claims = [
        claim
        for claim in store.read_schema("claim.v1")
        if claim.get("request_id") == draft.get("request_id") and _claim_market(claim) == market
    ]
    claim_symbols = {_claim_symbol(claim) for claim in claims if _claim_symbol(claim)}

    candidates = draft.get("candidates") or []
    candidate_symbols = [str(candidate.get("stock_code")) for candidate in candidates if candidate.get("stock_code")]
    expected_set = set(expected_symbols or [])
    non_selected_expected = sorted(expected_set - set(candidate_symbols)) if expected_set else []
    unexpected_candidates = sorted(set(candidate_symbols) - expected_set) if expected_set else []
    target_candidate_count = min(len(expected_set), candidate_limit or len(expected_set)) if expected_set else None
    candidate_count_gap = target_candidate_count is not None and len(candidate_symbols) < target_candidate_count

    missing_positive: list[str] = []
    missing_negative_search: list[str] = []
    quote_evidence_count = 0
    positive_evidence_count = 0
    negative_evidence_count = 0

    for candidate in candidates:
        symbol = str(candidate.get("stock_code") or "")
        source_ids = candidate.get("source_evidence") or []
        negative_ids = candidate.get("negative_evidence") or []
        quote_ids = [evidence_id for evidence_id in source_ids if _is_quote_evidence(evidence_by_id.get(evidence_id))]
        research_positive_ids = [evidence_id for evidence_id in source_ids if evidence_id not in quote_ids]
        quote_evidence_count += len(quote_ids)
        positive_evidence_count += len(research_positive_ids)
        negative_evidence_count += len(negative_ids)
        if not research_positive_ids:
            missing_positive.append(symbol)
        if not candidate.get("negative_evidence_searched"):
            missing_negative_search.append(symbol)

    warnings: list[str] = []
    if candidate_count_gap:
        warnings.append("candidate_count_gap")
    if unexpected_candidates:
        warnings.append("unexpected_candidate_symbol")
    if missing_positive:
        warnings.append("positive_research_gap")
    if missing_negative_search:
        warnings.append("negative_search_gap")
    if not claims:
        warnings.append("claim_gap")

    return {
        "ok": not missing_negative_search and not missing_positive and not candidate_count_gap and not unexpected_candidates and bool(candidates),
        "market": market,
        "request_id": draft.get("request_id"),
        "produced_at": draft.get("produced_at"),
        "candidate_count": len(candidates),
        "target_candidate_count": target_candidate_count,
        "expected_symbol_count": len(expected_set) if expected_set else None,
        "candidate_symbols": candidate_symbols,
        "non_selected_expected_symbols": non_selected_expected,
        "unexpected_candidate_symbols": unexpected_candidates,
        "quote_evidence_count": quote_evidence_count,
        "positive_evidence_count": positive_evidence_count,
        "negative_evidence_count": negative_evidence_count,
        "claim_count": len(claims),
        "claim_symbols": sorted(claim_symbols),
        "missing_positive_research": sorted(missing_positive),
        "missing_negative_search": sorted(missing_negative_search),
        "draft_warnings": draft.get("warnings") or [],
        "warnings": warnings,
    }


def render_text(result: dict[str, Any]) -> str:
    if not result.get("ok") and result.get("reject"):
        reject = result["reject"]
        return f"PILOT_ANALYSIS_REJECT {result.get('market')}: {reject.get('code')} - {reject.get('message')}"

    lines = [
        f"S5 pilot analysis {result.get('market')} | {result.get('produced_at')}",
        f"request: {result.get('request_id')}",
        f"candidates: {result.get('candidate_count')} / target: {result.get('target_candidate_count')} / universe: {result.get('expected_symbol_count')}",
        f"evidence: quote={result.get('quote_evidence_count')} positive={result.get('positive_evidence_count')} negative={result.get('negative_evidence_count')}",
        f"claims: {result.get('claim_count')}",
        "status: PASS" if result.get("ok") else "status: WATCH",
    ]
    for key, label in (
        ("unexpected_candidate_symbols", "unexpected candidates"),
        ("missing_positive_research", "missing positive research"),
        ("missing_negative_search", "missing negative search"),
        ("warnings", "warnings"),
    ):
        values = result.get(key) or []
        if values:
            lines.append(f"{label}: " + ", ".join(str(value) for value in values))
    non_selected = result.get("non_selected_expected_symbols") or []
    if non_selected:
        lines.append("not selected: " + ", ".join(str(value) for value in non_selected[:8]))
    return "\n".join(lines)


def _is_quote_evidence(evidence: dict[str, Any] | None) -> bool:
    return bool(evidence and evidence.get("source_type") == "broker_data")


def _claim_market(claim: dict[str, Any]) -> str | None:
    scope = claim.get("scope") if isinstance(claim.get("scope"), dict) else {}
    return scope.get("market")


def _claim_symbol(claim: dict[str, Any]) -> str | None:
    scope = claim.get("scope") if isinstance(claim.get("scope"), dict) else {}
    return scope.get("symbol")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-root", type=Path, required=True)
    parser.add_argument("--market", choices=["US", "HK", "CN"], required=True)
    parser.add_argument("--universe-file", type=Path, default=DEFAULT_UNIVERSE_FILE)
    parser.add_argument("--universe-ref", default="default")
    parser.add_argument("--candidate-limit", type=int, default=3)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    expected_symbols = load_universe_symbols(args.universe_file, args.market, args.universe_ref)
    result = analyze_pilot(JsonlEventStore(args.event_root), args.market, expected_symbols, args.candidate_limit)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
