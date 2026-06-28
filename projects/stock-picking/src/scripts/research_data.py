#!/usr/bin/env python3
"""Normalize TAROC research inputs into evidence and claim events."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from market_data import CROCKFORD, evidence_id_from_hash


class ResearchDataError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class SymbolResearch:
    symbol: str
    positive: list[dict[str, Any]]
    negative: list[dict[str, Any]]
    negative_search_query: str
    negative_search_performed: bool


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_research_file(path: Path) -> list[SymbolResearch]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchDataError("invalid_research_file", str(exc)) from exc
    return normalize_research(value)


def normalize_research(value: Any) -> list[SymbolResearch]:
    if isinstance(value, dict):
        items = value.get("items", [])
    elif isinstance(value, list):
        items = value
    else:
        raise ResearchDataError("invalid_research_shape", "research input must be an object or list")
    if not isinstance(items, list):
        raise ResearchDataError("invalid_research_items", "research items must be a list")

    results: list[SymbolResearch] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ResearchDataError("invalid_research_item", f"item {index} must be an object")
        symbol = str(item.get("symbol") or "")
        if not symbol:
            raise ResearchDataError("missing_symbol", f"item {index} missing symbol")
        positive = _evidence_list(item.get("positive", []), "positive", symbol)
        negative = _evidence_list(item.get("negative", []), "negative", symbol)
        negative_search_query = str(item.get("negative_search_query") or f"{symbol} risk negative bear case")
        negative_search_performed = bool(item.get("negative_search_performed", bool(negative)))
        results.append(
            SymbolResearch(
                symbol=symbol,
                positive=positive,
                negative=negative,
                negative_search_query=negative_search_query,
                negative_search_performed=negative_search_performed,
            )
        )
    return results


def _evidence_list(value: Any, label: str, symbol: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ResearchDataError("invalid_evidence_list", f"{symbol}.{label} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ResearchDataError("invalid_evidence_item", f"{symbol}.{label}.{index} must be an object")
    return value


def build_research_records(
    request: dict[str, Any],
    researches: list[SymbolResearch],
    created_at: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    created = created_at or now_utc()
    records: list[dict[str, Any]] = []
    by_symbol: dict[str, dict[str, Any]] = {}
    for research in researches:
        positive_ids: list[str] = []
        negative_ids: list[str] = []
        for item in research.positive:
            evidence = evidence_record(item, request, research.symbol, "positive", created)
            positive_ids.append(evidence["evidence_id"])
            records.append(evidence)
        for item in research.negative:
            evidence = evidence_record(item, request, research.symbol, "negative", created)
            negative_ids.append(evidence["evidence_id"])
            records.append(evidence)

        claim_records: list[dict[str, Any]] = []
        if positive_ids:
            claim_records.append(
                claim_record(
                    request,
                    research.symbol,
                    "catalyst",
                    "positive",
                    "Positive catalyst evidence found for TAROC discovery.",
                    positive_ids,
                    research.negative_search_performed,
                    research.negative_search_query,
                    created,
                    severity="info",
                )
            )
        if negative_ids:
            claim_records.append(
                claim_record(
                    request,
                    research.symbol,
                    "risk",
                    "negative",
                    "Negative or risk evidence found during mandatory bear-case search.",
                    negative_ids,
                    research.negative_search_performed,
                    research.negative_search_query,
                    created,
                    severity="warning",
                )
            )
        records.extend(claim_records)
        by_symbol[research.symbol] = {
            "positive_evidence": positive_ids,
            "negative_evidence": negative_ids,
            "claims": [record["claim_id"] for record in claim_records],
            "negative_search_performed": research.negative_search_performed,
            "negative_search_query": research.negative_search_query,
        }
    return records, by_symbol


def evidence_record(item: dict[str, Any], request: dict[str, Any], symbol: str, polarity: str, created_at: str) -> dict[str, Any]:
    raw = {
        "symbol": symbol,
        "polarity": polarity,
        "title": item.get("title"),
        "url": item.get("url"),
        "publisher": item.get("publisher"),
        "excerpt": item.get("excerpt"),
    }
    raw_text = json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    source_type = item.get("source_type") or "news"
    source_subtype = item.get("source_subtype") or ("news" if source_type == "news" else "other")
    return {
        "schema": "evidence_ref.v1",
        "evidence_id": evidence_id_from_hash(digest),
        "created_at": created_at,
        "created_by": "node_3_taroc",
        "source_url": str(item.get("url") or ""),
        "source_id": str(item.get("source_id") or symbol),
        "source_type": source_type,
        "source_subtype": source_subtype,
        "title": str(item.get("title") or f"{symbol} {polarity} evidence"),
        "excerpt": str(item.get("excerpt") or ""),
        "publisher": str(item.get("publisher") or "unknown"),
        "fetched_at": created_at,
        "observed_at": str(item.get("observed_at") or created_at),
        "language": str(item.get("language") or "unknown"),
        "snapshot_ref": str(item.get("snapshot_ref") or f"research:{symbol}:{request['signal_date']}:{polarity}"),
        "claim_hash": digest,
        "publisher_authority": float(item.get("publisher_authority", 0.5)),
        "ai_classified_quality": float(item.get("ai_classified_quality", 0.5)),
        "classification_method": item.get("classification_method") or "llm_judge",
        "source_quality": item.get("source_quality") or "medium",
        "status": item.get("status") or "active",
        "content_hash": "sha256:" + digest,
        "raw_snapshot_path": item.get("raw_snapshot_path"),
    }


def claim_record(
    request: dict[str, Any],
    symbol: str,
    claim_kind: str,
    polarity: str,
    text: str,
    evidence_ids: list[str],
    negative_search_performed: bool,
    negative_search_query: str,
    created_at: str,
    severity: str | None,
) -> dict[str, Any]:
    raw_text = json.dumps(
        {
            "symbol": symbol,
            "claim_kind": claim_kind,
            "polarity": polarity,
            "evidence_ids": evidence_ids,
            "request_id": request["request_id"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    return {
        "schema": "claim.v1",
        "claim_id": claim_id_from_hash(digest),
        "created_at": created_at,
        "created_by": "node_3_taroc",
        "scope": {"symbol": symbol, "market": request["market"], "strategy_id": request["strategy_id"]},
        "request_id": request["request_id"],
        "correlation_id": request["correlation_id"],
        "claim_text": text,
        "claim_kind": claim_kind,
        "polarity": polarity,
        "thesis_broken": False,
        "severity": severity,
        "confidence": {"level": "medium", "source": "research_adapter"},
        "evidence_ids": evidence_ids,
        "negative_search_performed": negative_search_performed,
        "negative_search_query": negative_search_query,
        "valid_until": _iso_days_after(request["signal_date"], 14),
        "status": "active",
    }


def claim_id_from_hash(hex_digest: str) -> str:
    number = int(hex_digest[:32], 16)
    chars: list[str] = []
    for _ in range(26):
        number, remainder = divmod(number, 32)
        chars.append(CROCKFORD[remainder])
    return "cl_" + "".join(reversed(chars))


def _iso_days_after(date_value: str, days: int) -> str:
    date_obj = dt.date.fromisoformat(date_value)
    return dt.datetime.combine(date_obj + dt.timedelta(days=days), dt.time(23, 59), dt.timezone.utc).isoformat()
