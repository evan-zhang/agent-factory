#!/usr/bin/env python3
"""Decide mode: short / full / ask based on URL source and content keywords."""
import json
import sys
from urllib.parse import urlparse

# Source-based rules (highest priority)
FULL_SOURCES = {"youtube.com", "youtu.be", "m.youtube.com", "github.com", "gist.github.com"}
SHORT_SOURCES = set()  # none forced to short by source alone

# Content keywords
FULL_KEYWORDS = [
    "github", "star", "open source", "repo", "tutorial", "对比", "教程", "开源",
    "发布", "突破", "重磅", "深度", "分析", "评测", "框架", "工具", "模型", "论文",
    "architecture", "benchmark", "comparison", "deep dive", "release",
]
SHORT_KEYWORDS = [
    "news", "新闻", "热点", "观点", "commentary",
    "快讯", "简讯", "公告", "通知", "更新", "涨价", "降价",
]


def decide(url: str = "", text: str = "") -> str:
    # 1. Source-based check
    if url:
        try:
            host = urlparse(url).hostname or ""
            domain = host.replace("www.", "")
            if domain in FULL_SOURCES:
                return "full"
        except Exception:
            pass

    # 2. Content keyword check
    combined = f"{url} {text}".lower()
    if any(k in combined for k in FULL_KEYWORDS):
        return "full"
    if any(k in combined for k in SHORT_KEYWORDS):
        return "short"

    # 3. Default: ask
    return "ask"


def main() -> int:
    args = sys.argv[1:]
    url = ""
    text = ""
    for a in args:
        if a.startswith("http://") or a.startswith("https://"):
            url = a
        else:
            text += " " + a
    text = text.strip()
    if not url and not text:
        print(json.dumps({"ok": False, "error": "missing input (URL or text)"}, ensure_ascii=False))
        return 1
    mode = decide(url, text)
    print(json.dumps({"ok": True, "mode": mode}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
