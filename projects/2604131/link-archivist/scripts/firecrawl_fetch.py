#!/usr/bin/env python3
"""Firecrawl fetch — 抓取单个 URL，输出 Markdown + 元数据。

用法：
  python3 scripts/firecrawl_fetch.py <url>
  python3 scripts/firecrawl_fetch.py <url> --json          # 输出完整 JSON（含 metadata）
  python3 scripts/firecrawl_fetch.py <url> --max-chars 50000  # 截断输出

配置：
  配置文件中需要有 firecrawl_api_key，或环境变量 FIRECRAWL_API_KEY。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

CONFIG_PATHS = [
    Path.home() / ".openclaw" / "link-archivist-config.json",
    Path.home() / ".hermes" / "link-archivist-config.json",
    Path.home() / ".config" / "link-archivist-config.json",
]

API_ENDPOINT = "https://api.firecrawl.dev/v2/scrape"


def _load_api_key() -> str:
    """从配置文件或环境变量读取 Firecrawl API key。"""
    # 1. 环境变量
    key = os.environ.get("FIRECRAWL_API_KEY", "")
    if key:
        return key

    # 2. 配置文件
    for config_path in CONFIG_PATHS:
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
                key = config.get("firecrawl_api_key", "")
                if key:
                    return key
            except (json.JSONDecodeError, OSError):
                continue

    return ""


def fetch(url: str, api_key: str, timeout: int = 60) -> dict:
    """调用 Firecrawl v2 scrape API。

    Returns:
        dict with keys: ok, markdown, title, metadata, error
    """
    import requests

    try:
        resp = requests.post(
            API_ENDPOINT,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "url": url,
                "formats": ["markdown"],
            },
            timeout=timeout,
        )
        data = resp.json()

        if not data.get("success"):
            error_msg = data.get("error", "Unknown Firecrawl error")
            return {"ok": False, "markdown": "", "title": "", "metadata": {}, "error": error_msg}

        page_data = data.get("data", {})
        markdown = page_data.get("markdown", "")
        metadata = page_data.get("metadata", {})
        title = metadata.get("title", "") or metadata.get("og:title", "")

        return {
            "ok": True,
            "markdown": markdown,
            "title": title,
            "metadata": metadata,
            "error": "",
        }

    except requests.exceptions.Timeout:
        return {"ok": False, "markdown": "", "title": "", "metadata": {}, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "markdown": "", "title": "", "metadata": {}, "error": str(e)}


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: firecrawl_fetch.py <url> [--json] [--max-chars N]"}, ensure_ascii=False))
        return 1

    url = ""
    output_json = False
    max_chars = 0

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--json":
            output_json = True
        elif arg == "--max-chars" and i + 1 < len(sys.argv):
            try:
                max_chars = int(sys.argv[i + 1])
            except ValueError:
                pass
        elif not arg.startswith("-"):
            url = arg

    if not url:
        print(json.dumps({"ok": False, "error": "missing URL"}, ensure_ascii=False))
        return 1

    api_key = _load_api_key()
    if not api_key:
        print(json.dumps({"ok": False, "error": "firecrawl_api_key not configured"}, ensure_ascii=False))
        return 1

    result = fetch(url, api_key)

    if not result["ok"]:
        print(json.dumps(result, ensure_ascii=False))
        return 1

    markdown = result["markdown"]
    if max_chars and len(markdown) > max_chars:
        markdown = markdown[:max_chars] + "\n\n[... truncated by firecrawl_fetch.py ...]"
        result["markdown"] = markdown
        result["truncated"] = True

    if output_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        # 纯 Markdown 输出（兼容 LA 现有的 curl 管道）
        if result["title"]:
            print(f"# {result['title']}\n")
        print(markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
