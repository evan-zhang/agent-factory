#!/usr/bin/env python3
"""Fetch and normalize OpenRouter model catalog into local JSON."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import requests

API_URL = "https://openrouter.ai/api/v1/models"
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CATALOG_PATH = DATA_DIR / "model-catalog.json"


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _non_negative_float(value: Any) -> float | None:
    f = _to_float(value)
    if f is None or f < 0:
        return None
    return f


def _per_million(value: Any) -> float | None:
    f = _non_negative_float(value)
    if f is None:
        return None
    return round(f * 1_000_000, 12)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "supported"}
    return False


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _provider_from(raw: Dict[str, Any], model_id: str) -> str:
    if isinstance(raw.get("provider"), str) and raw.get("provider"):
        return raw["provider"]
    if isinstance(raw.get("owned_by"), str) and raw.get("owned_by"):
        return raw["owned_by"]
    if "/" in model_id:
        return model_id.split("/", 1)[0]
    return "unknown"


def _family_from(model_id: str, name: str) -> str:
    base = model_id.split("/", 1)[-1]
    for sep in (":", "-", "_"):
        if sep in base:
            return base.split(sep, 1)[0]
    if name:
        return name.split()[0].lower()
    return base


def _extract_modalities(raw: Dict[str, Any]) -> List[str]:
    modalities: set[str] = set()

    architecture = raw.get("architecture") or {}
    if isinstance(architecture, dict):
        for key in ("input_modalities", "output_modalities", "modalities"):
            vals = architecture.get(key)
            if isinstance(vals, list):
                for v in vals:
                    if isinstance(v, str):
                        modalities.add(v.lower())

    for key in ("modality", "modalities"):
        vals = raw.get(key)
        if isinstance(vals, list):
            for v in vals:
                if isinstance(v, str):
                    modalities.add(v.lower())
        elif isinstance(vals, str):
            modalities.add(vals.lower())

    if not modalities:
        modalities.add("text")

    return sorted(modalities)


def _extract_capabilities(raw: Dict[str, Any], modality: List[str]) -> Dict[str, bool]:
    supported = raw.get("supported_parameters") or []
    supported_set = {str(x).lower() for x in supported if isinstance(x, str)}

    architecture = raw.get("architecture") or {}
    if isinstance(architecture, dict):
        in_mod = architecture.get("input_modalities") or []
        out_mod = architecture.get("output_modalities") or []
    else:
        in_mod = []
        out_mod = []

    in_mod_set = {str(x).lower() for x in in_mod if isinstance(x, str)}
    out_mod_set = {str(x).lower() for x in out_mod if isinstance(x, str)}
    mod_set = set(modality)

    has_image_input = bool({"image", "vision"} & (in_mod_set | mod_set))
    has_image_output = bool({"image"} & (out_mod_set | mod_set)) and ("text" not in (out_mod_set | mod_set) or "image" in (out_mod_set | mod_set))
    has_audio_input = bool({"audio"} & (in_mod_set | mod_set))
    has_audio_output = bool({"audio"} & (out_mod_set | mod_set))

    text_cap = "text" in mod_set or not (has_image_input or has_audio_input)

    name_blob = " ".join([str(raw.get("id", "")), str(raw.get("name", "")), str(raw.get("description", ""))]).lower()
    code_cap = "code" in mod_set or any(k in name_blob for k in ["code", "coder", "coding", "programming"])

    tool_use = bool({"tools", "tool_choice", "function_calling", "functions"} & supported_set)
    structured_output = bool({"response_format", "json_schema", "structured_outputs", "structured_output"} & supported_set)
    json_mode = "response_format" in supported_set or "json_object" in supported_set or "json_mode" in supported_set

    return {
        "text": text_cap,
        "image_input": has_image_input,
        "image_output": has_image_output,
        "audio_input": has_audio_input,
        "audio_output": has_audio_output,
        "code": code_cap,
        "tool_use": tool_use,
        "structured_output": structured_output,
        "json_mode": json_mode,
    }


def normalize_model(raw: Dict[str, Any], checked_at: str) -> Dict[str, Any]:
    model_id = raw.get("id") or raw.get("slug") or raw.get("name") or "unknown/unknown"
    name = raw.get("name") or model_id
    provider = _provider_from(raw, model_id)

    top_provider = raw.get("top_provider") or {}
    pricing = raw.get("pricing") or {}

    modality = _extract_modalities(raw)

    record = {
        "id": model_id,
        "name": name,
        "provider": provider,
        "family": _family_from(model_id, name),
        "pricing": {
            "prompt_per_mtok": _per_million(pricing.get("prompt")),
            "completion_per_mtok": _per_million(pricing.get("completion")),
            "image_per_image": _non_negative_float(pricing.get("image")),
            "request_per_call": _non_negative_float(pricing.get("request")),
        },
        "context": {
            "max_input_tokens": _to_int(top_provider.get("context_length") or raw.get("context_length")),
            "max_output_tokens": _to_int(top_provider.get("max_completion_tokens") or raw.get("max_completion_tokens")),
            "reasoning_tokens": _to_bool(top_provider.get("reasoning_tokens")),
        },
        "capabilities": _extract_capabilities(raw, modality),
        "modality": modality,
        "latency": _to_float(raw.get("latency") or (raw.get("top_provider") or {}).get("latency")),
        "per_request_limits": copy.deepcopy(raw.get("per_request_limits")),
        "top_provider": copy.deepcopy(top_provider),
        "availability": {
            "is_available": _to_bool(raw.get("is_available", True)),
            "last_checked": checked_at,
        },
        "raw": raw,
    }
    return record


def _load_existing() -> List[Dict[str, Any]]:
    if not CATALOG_PATH.exists():
        return []
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return []


def _fetch_models(api_key: str | None = None) -> List[Dict[str, Any]]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    resp = requests.get(API_URL, headers=headers, timeout=60)
    resp.raise_for_status()

    payload = resp.json()
    models = payload.get("data", payload)
    if not isinstance(models, list):
        raise RuntimeError("Unexpected API response: expected list in 'data'")
    return [m for m in models if isinstance(m, dict)]


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def update_catalog(full: bool = False, api_key: str | None = None) -> Dict[str, int]:
    checked_at = _now_iso()
    remote_models = _fetch_models(api_key=api_key)
    normalized = [normalize_model(m, checked_at) for m in remote_models]

    existing = _load_existing()
    existing_map = {item.get("id"): item for item in existing if isinstance(item, dict) and item.get("id")}

    new_map: Dict[str, Dict[str, Any]] = {}
    added = 0
    changed = 0
    unchanged = 0

    for item in normalized:
        mid = item["id"]
        old = existing_map.get(mid)
        if old is None:
            added += 1
            new_map[mid] = item
            continue

        if full:
            changed += 1
            new_map[mid] = item
            continue

        old_cmp = dict(old)
        new_cmp = dict(item)
        old_cmp.pop("availability", None)
        new_cmp.pop("availability", None)

        if _canonical_json(old_cmp) == _canonical_json(new_cmp):
            unchanged += 1
            preserved = dict(old)
            preserved["availability"] = {
                "is_available": item.get("availability", {}).get("is_available", True),
                "last_checked": checked_at,
            }
            new_map[mid] = preserved
        else:
            changed += 1
            new_map[mid] = item

    # If model disappeared from remote list, mark unavailable but keep for incremental mode.
    if not full:
        remote_ids = {m["id"] for m in normalized}
        for mid, old in existing_map.items():
            if mid not in remote_ids:
                missing = dict(old)
                avail = dict(missing.get("availability") or {})
                avail["is_available"] = False
                avail["last_checked"] = checked_at
                missing["availability"] = avail
                new_map[mid] = missing

    catalog = [new_map[k] for k in sorted(new_map.keys())]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CATALOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return {
        "fetched": len(remote_models),
        "written": len(catalog),
        "added": added,
        "changed": changed,
        "unchanged": unchanged,
        "mode_full": int(full),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch OpenRouter model rankings data into local catalog")
    p.add_argument("--full", action="store_true", help="Full refresh (replace all current remote models)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    api_key = os.getenv("OPENROUTER_API_KEY")
    stats = update_catalog(full=args.full, api_key=api_key)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"Catalog written to: {CATALOG_PATH}")


if __name__ == "__main__":
    main()
