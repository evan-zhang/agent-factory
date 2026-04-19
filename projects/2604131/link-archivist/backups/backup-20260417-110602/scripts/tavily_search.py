#!/usr/bin/env python3
"""Tavily search script for Link Archivist.

Reads API key from:
1. ~/.openclaw/link-archivist-config.json (tavily_api_key field)
2. TAVILY_API_KEY environment variable (fallback)

Usage:
    python3 scripts/tavily_search.py "<query>" [max_results]
"""
import json
import os
import sys
from pathlib import Path


def get_config_path() -> Path:
    if os.getenv("OPENCLAW_ROOT"):
        return Path.home() / ".openclaw"
    elif os.getenv("HERMES_ROOT"):
        return Path.home() / ".hermes"
    else:
        return Path.home() / ".config"


def get_tavily_key() -> str | None:
    config_path = get_config_path() / "link-archivist-config.json"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            key = cfg.get("tavily_api_key")
            if key:
                return key
        except Exception:
            pass
    return os.getenv("TAVILY_API_KEY")


def search(query: str, max_results: int = 5) -> dict:
    key = get_tavily_key()
    if not key:
        return {
            "ok": False,
            "error": "Tavily API key not configured. "
                      "Set tavily_api_key in link-archivist-config.json "
                      "or export TAVILY_API_KEY env var."
        }

    try:
        from tavily import TavilyClient
    except ImportError:
        return {"ok": False, "error": "tavily package not installed. Run: pip install tavily-python"}

    client = TavilyClient(api_key=key)
    result = client.search(query=query, max_results=max_results)
    return {
        "ok": True,
        "results": result.get("results", []),
        "answer": result.get("answer"),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({
            "ok": False,
            "error": "usage: tavily_search.py <query> [max_results]"
        }, ensure_ascii=False))
        return 1

    query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    result = search(query, max_results)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
