#!/usr/bin/env python3
"""Render latest discovery events into a concise channel report."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from event_store import JsonlEventStore


def latest_draft(store: JsonlEventStore, market: str | None = None) -> dict[str, Any] | None:
    drafts = store.read_schema("draft_candidates.v1")
    if market:
        drafts = [draft for draft in drafts if draft.get("market") == market]
    return drafts[-1] if drafts else None


def _index_by_id(records: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(record.get(key)): record for record in records if record.get(key)}


def render_report(store: JsonlEventStore, market: str | None = None) -> str:
    draft = latest_draft(store, market)
    if draft is None:
        return "HEARTBEAT_OK\n没有发现新的 discovery draft。"

    evidence_by_id = _index_by_id(store.read_schema("evidence_ref.v1"), "evidence_id")
    claims = store.read_schema("claim.v1")
    claims_by_symbol: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        scope = claim.get("scope") if isinstance(claim.get("scope"), dict) else {}
        symbol = scope.get("symbol")
        if symbol:
            claims_by_symbol.setdefault(symbol, []).append(claim)

    lines = [
        f"TAROC discovery {draft.get('market')} | {draft.get('produced_at')}",
        f"request: {draft.get('request_id')}",
        f"candidates: {len(draft.get('candidates', []))}",
    ]
    warnings = draft.get("warnings") or []
    if warnings:
        lines.append("warnings: " + ", ".join(str(item) for item in warnings))

    for index, candidate in enumerate(draft.get("candidates", []), start=1):
        symbol = candidate.get("stock_code")
        price = candidate.get("price")
        positive = candidate.get("source_evidence") or []
        negative = candidate.get("negative_evidence") or []
        symbol_claims = claims_by_symbol.get(symbol, [])
        lines.extend(
            [
                "",
                f"{index}. {symbol} @ {price}",
                f"   confidence: {candidate.get('confidence', {}).get('level')}",
                f"   evidence: +{len(positive)} / -{len(negative)} | claims: {len(symbol_claims)}",
                f"   thesis: {candidate.get('thesis_summary')}",
            ]
        )
        first_negative = _first_title(negative, evidence_by_id)
        if first_negative:
            lines.append(f"   first risk: {first_negative}")
    lines.append("")
    lines.append("dry_run only; no trade action triggered.")
    return "\n".join(lines)


def _first_title(evidence_ids: list[str], evidence_by_id: dict[str, dict[str, Any]]) -> str | None:
    for evidence_id in evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence:
            return str(evidence.get("title") or evidence.get("excerpt") or evidence_id)
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-root", type=Path, required=True)
    parser.add_argument("--market", choices=["US", "HK", "CN"])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(render_report(JsonlEventStore(args.event_root), args.market))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
