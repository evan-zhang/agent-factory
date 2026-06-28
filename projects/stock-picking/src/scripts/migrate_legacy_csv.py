#!/usr/bin/env python3
"""Legacy CSV projection helpers.

This is intentionally a projection skeleton, not a migration runner that mutates
legacy files. It reads validated event records and emits CSV-compatible rows.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from event_store import JsonlEventStore


DRAFT_FIELDS = [
    "draft_id",
    "strategy_run_id",
    "strategy_id",
    "strategy_version",
    "stock_code",
    "stock_name",
    "market",
    "price",
    "thesis_summary",
    "confidence_level",
    "negative_evidence_searched",
    "expires_at",
    "next_step",
]

CANDIDATE_FIELDS = [
    "candidate_id",
    "origin_draft_id",
    "stock_code",
    "market",
    "state",
    "actor",
    "aggregate_thesis",
    "created_at",
    "expires_at",
]


def draft_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        for candidate in event.get("candidates", []):
            confidence = candidate.get("confidence") or {}
            rows.append(
                {
                    "draft_id": candidate.get("draft_id"),
                    "strategy_run_id": candidate.get("strategy_run_id"),
                    "strategy_id": candidate.get("strategy_id"),
                    "strategy_version": candidate.get("strategy_version"),
                    "stock_code": candidate.get("stock_code"),
                    "stock_name": candidate.get("stock_name"),
                    "market": candidate.get("market"),
                    "price": candidate.get("price"),
                    "thesis_summary": candidate.get("thesis_summary"),
                    "confidence_level": confidence.get("level"),
                    "negative_evidence_searched": candidate.get("negative_evidence_searched"),
                    "expires_at": candidate.get("expires_at"),
                    "next_step": candidate.get("next_step"),
                }
            )
    return rows


def candidate_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": event.get("candidate_id"),
            "origin_draft_id": event.get("origin_draft_id"),
            "stock_code": event.get("stock_code"),
            "market": event.get("market"),
            "state": event.get("state"),
            "actor": event.get("actor"),
            "aggregate_thesis": event.get("aggregate_thesis"),
            "created_at": event.get("created_at"),
            "expires_at": event.get("expires_at"),
        }
        for event in events
    ]


def emit_csv(rows: list[dict[str, Any]], fields: list[str]) -> None:
    writer = csv.DictWriter(sys.stdout, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-root", type=Path, required=True)
    parser.add_argument("--projection", choices=["drafts", "candidates"], required=True)
    args = parser.parse_args(argv)

    store = JsonlEventStore(args.event_root)
    if args.projection == "drafts":
        emit_csv(draft_rows(store.read_schema("draft_candidates.v1")), DRAFT_FIELDS)
    else:
        emit_csv(candidate_rows(store.read_schema("candidate_record.v1")), CANDIDATE_FIELDS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
