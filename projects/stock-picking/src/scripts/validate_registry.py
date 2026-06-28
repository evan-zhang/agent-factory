#!/usr/bin/env python3
"""Strategy registry validator and Node 2 dispatch selector."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
ALLOWED_OUTPUT_SCHEMAS = {"draft_candidates.v1", "theme_research.v1"}
REJECT_CODES = {
    "upstream_not_proceed",
    "strategy_not_found",
    "version_required",
    "version_not_found",
    "ambiguous_version",
    "unsupported_market",
    "unsupported_run_mode",
    "caller_not_allowed",
    "strategy_disabled",
    "experimental_not_allowed",
    "custom_ref_invalid",
    "output_schema_unsupported",
    "dry_run_required",
    "registry_invalid",
}


class RegistryError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return _sha256_bytes(encoded)


def _load_yaml_snapshot(path: Path) -> tuple[dict[str, Any], str]:
    data = path.read_bytes()
    return yaml.safe_load(data) or {}, _sha256_bytes(data)


def _reject(request: dict[str, Any], code: str, message: str, snapshot_hash: str | None = None) -> dict[str, Any]:
    if code not in REJECT_CODES:
        code = "registry_invalid"
    return {
        "schema": "strategy_dispatch.v1",
        "request_id": request.get("request_id"),
        "correlation_id": request.get("correlation_id"),
        "node_id": "node_2_strategy_selector",
        "decision": "reject",
        "strategy_dispatch": {
            "strategy_id": request.get("strategy_id"),
            "strategy_version": request.get("strategy_version"),
            "entrypoint": None,
            "output_schema": None,
            "registry_version": None,
            "registry_snapshot_hash": snapshot_hash,
            "registry_record_hash": None,
            "policy_flags": [],
        },
        "reject": {"code": code, "message": message},
        "warnings": [],
        "audit": {"selected_at": request.get("selected_at"), "custom_ref": request.get("custom_ref")},
    }


def _validate_registry(registry: dict[str, Any]) -> None:
    if not isinstance(registry.get("strategies"), list):
        raise RegistryError("registry_invalid", "strategies must be a list")
    seen: set[tuple[str, str]] = set()
    for index, record in enumerate(registry["strategies"]):
        for field in ("id", "version", "entrypoint", "output_schema", "supported_markets", "supported_run_modes", "status", "allowed_callers"):
            if field not in record:
                raise RegistryError("registry_invalid", f"strategies.{index}.{field} is required")
        key = (str(record["id"]), str(record["version"]))
        if key in seen:
            raise RegistryError("registry_invalid", f"duplicate strategy/version {key}")
        seen.add(key)
        if not SEMVER_RE.match(str(record["version"])):
            raise RegistryError("registry_invalid", f"invalid semver at strategies.{index}.version")
        if record["output_schema"] not in ALLOWED_OUTPUT_SCHEMAS:
            raise RegistryError("output_schema_unsupported", f"unsupported output schema {record['output_schema']}")


def _validate_custom_refs(custom_refs: dict[str, Any], custom_ref: str | None) -> None:
    refs = custom_refs.get("refs", [])
    if not isinstance(refs, list):
        raise RegistryError("custom_ref_invalid", "refs must be a list")
    if not custom_ref:
        return
    if ".." in custom_ref or "/" in custom_ref or "\\" in custom_ref:
        raise RegistryError("custom_ref_invalid", "custom_ref must not be a raw path")
    if custom_ref not in {entry.get("id") for entry in refs if isinstance(entry, dict)}:
        raise RegistryError("custom_ref_invalid", "custom_ref is not whitelisted")


def select_dispatch(
    request: dict[str, Any],
    run_context: dict[str, Any],
    registry_path: Path,
    custom_refs_path: Path,
) -> dict[str, Any]:
    registry, snapshot_hash = _load_yaml_snapshot(registry_path)
    custom_refs, _custom_hash = _load_yaml_snapshot(custom_refs_path)
    try:
        _validate_registry(registry)
        _validate_custom_refs(custom_refs, request.get("custom_ref"))
    except RegistryError as exc:
        return _reject(request, exc.code, exc.message, snapshot_hash)

    if run_context.get("decision") != "proceed":
        return _reject(request, "upstream_not_proceed", "run_context.decision is not proceed", snapshot_hash)
    if request.get("dry_run") is False:
        return _reject(request, "dry_run_required", "registry selector v1 requires dry_run", snapshot_hash)

    strategy_id = request.get("strategy_id")
    requested_version = request.get("strategy_version")
    caller = request.get("caller")
    market = request.get("market")
    run_mode = request.get("run_mode")

    records = [copy.deepcopy(row) for row in registry["strategies"] if row["id"] == strategy_id]
    if not records:
        return _reject(request, "strategy_not_found", "requested strategy is not registered", snapshot_hash)

    warnings: list[str] = []
    if requested_version in (None, ""):
        if caller in {"cron", "sop"}:
            return _reject(request, "version_required", "cron/sop require exact semver", snapshot_hash)
        default_version = (registry.get("defaults") or {}).get(strategy_id)
        if not default_version:
            return _reject(request, "version_required", "manual default is not configured", snapshot_hash)
        requested_version = str(default_version)
        warnings.append("manual_default_version_used")
    elif requested_version == "latest" or not SEMVER_RE.match(str(requested_version)):
        return _reject(request, "version_required", "exact semver is required", snapshot_hash)

    matches = [row for row in records if str(row["version"]) == str(requested_version)]
    if not matches:
        return _reject(request, "version_not_found", "requested strategy version is not registered", snapshot_hash)
    if len(matches) > 1:
        return _reject(request, "ambiguous_version", "strategy version resolves to multiple records", snapshot_hash)

    record = matches[0]
    if record.get("status") == "disabled":
        return _reject(request, "strategy_disabled", "strategy is disabled", snapshot_hash)
    if market not in record.get("supported_markets", []):
        return _reject(request, "unsupported_market", "market is not supported by strategy", snapshot_hash)
    if run_mode not in record.get("supported_run_modes", []):
        return _reject(request, "unsupported_run_mode", "run mode is not supported by strategy", snapshot_hash)
    if record.get("status") == "experimental" and caller in {"cron", "sop"}:
        return _reject(request, "experimental_not_allowed", "experimental strategies are manual-only in v1", snapshot_hash)
    if caller not in record.get("allowed_callers", []):
        return _reject(request, "caller_not_allowed", "caller is not allowed for strategy", snapshot_hash)

    normalized = {key: record[key] for key in sorted(record)}
    record_hash = _stable_hash(normalized)
    return {
        "schema": "strategy_dispatch.v1",
        "request_id": request.get("request_id"),
        "correlation_id": request.get("correlation_id"),
        "node_id": "node_2_strategy_selector",
        "decision": "dispatch",
        "strategy_dispatch": {
            "strategy_id": record["id"],
            "strategy_version": str(record["version"]),
            "entrypoint": record["entrypoint"],
            "output_schema": record["output_schema"],
            "registry_version": str(registry.get("registry_version")),
            "registry_snapshot_hash": snapshot_hash,
            "registry_record_hash": record_hash,
            "policy_flags": [f"status:{record.get('status')}"],
        },
        "reject": {"code": None, "message": None},
        "warnings": warnings,
        "audit": {"selected_at": request.get("selected_at"), "custom_ref": request.get("custom_ref")},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--custom-refs", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--run-context", type=Path, required=True)
    args = parser.parse_args(argv)

    request = yaml.safe_load(args.request.read_text(encoding="utf-8"))
    run_context = yaml.safe_load(args.run_context.read_text(encoding="utf-8"))
    result = select_dispatch(request, run_context, args.registry, args.custom_refs)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["decision"] == "dispatch" else 1


if __name__ == "__main__":
    sys.exit(main())
