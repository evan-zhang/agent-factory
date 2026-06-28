#!/usr/bin/env python3
"""Append-only JSONL event store for stock-picking dry-run modules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from validate_schema import validate_record


class EventStoreError(RuntimeError):
    pass


class JsonlEventStore:
    def __init__(self, root: Path):
        self.root = root

    def _path_for_schema(self, schema: str) -> Path:
        if "/" in schema or "\\" in schema or ".." in schema:
            raise EventStoreError("invalid schema path")
        return self.root / f"{schema}.jsonl"

    def _idempotency_key(self, record: dict[str, Any]) -> tuple[Any, ...] | None:
        if record.get("schema") == "atomic_request.v1":
            return (record.get("idempotency_key"),)
        if record.get("schema") == "validation_event.v1":
            return (
                record.get("draft_id"),
                record.get("validation_run_id"),
                record.get("calendar_checked_at"),
                record.get("validation_session_key"),
            )
        return None

    def find_idempotent_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        key = self._idempotency_key(record)
        if key is None or any(value is None for value in key):
            return None
        for existing in self.read_schema(record["schema"]):
            if self._idempotency_key(existing) == key:
                return existing
        return None

    def find_atomic_request(self, idempotency_key: str) -> dict[str, Any] | None:
        for existing in self.read_schema("atomic_request.v1"):
            if existing.get("idempotency_key") == idempotency_key:
                return existing
        return None

    def append(self, record: dict[str, Any]) -> dict[str, Any]:
        result = validate_record(record)
        path = self._path_for_schema(record["schema"])
        existing = self.find_idempotent_record(record)
        if existing is not None:
            return result | {"event_path": str(path), "idempotent_replay": True}
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return result | {"event_path": str(path)}

    def append_many(self, records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.append(record) for record in records]

    def read_schema(self, schema: str) -> list[dict[str, Any]]:
        path = self._path_for_schema(schema)
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    value = json.loads(text)
    return value if isinstance(value, list) else [value]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-root", type=Path, required=True)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args(argv)

    store = JsonlEventStore(args.event_root)
    for file_path in args.files:
        for result in store.append_many(load_records(file_path)):
            print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
