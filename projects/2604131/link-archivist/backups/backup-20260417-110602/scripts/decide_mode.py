#!/usr/bin/env python3
"""Decide mode: short / full / ask based on URL source, user input, and content."""
import json
import sys
from urllib.parse import urlparse

# Source-based rules (highest priority, no content fetch needed)
FULL_SOURCES = {"youtube.com", "youtu.be", "m.youtube.com", "github.com", "gist.github.com"}
SHORT_SOURCES = set()  # none forced to short by source alone

# Content keywords
FULL_KEYWORDS = [
    "github", "star", "open source", "repo", "tutorial", "对比", "教程", "开源",
    "发布", "突破", "重磅", "深度", "分析", "评测", "框架", "工具", "模型", "论文",
    "architecture", "benchmark", "comparison", "deep dive", "release",
    "agent", "llm", "大模型", "智能体", "超级智能体", "字节跳动", "火山引擎",
]
SHORT_KEYWORDS = [
    "news", "新闻", "热点", "观点", "commentary",
    "快讯", "简讯", "公告", "通知", "更新", "涨价", "降价",
]


def _decide_fast(url: str, text: str) -> str:
    """Phase 1: Fast decision based on URL and user input only."""
    # 1. Source-based check (no fetch needed)
    if url:
        try:
            host = urlparse(url).hostname or ""
            domain = host.replace("www.", "")
            if domain in FULL_SOURCES:
                return "full"
        except Exception:
            pass

    # 2. User input keyword check
    combined = f"{url} {text}".lower()
    if any(k in combined for k in FULL_KEYWORDS):
        return "full"
    if any(k in combined for k in SHORT_KEYWORDS):
        return "short"

    # 3. Need content analysis
    return "ask"


def _decide_by_content(content: str) -> str:
    """Phase 2: Decision based on fetched content (title + body)."""
    if not content:
        return "ask"

    content_lower = content.lower()
    full_score = sum(1 for k in FULL_KEYWORDS if k in content_lower)
    short_score = sum(1 for k in SHORT_KEYWORDS if k in content_lower)

    if full_score >= 2:  # At least 2 full keywords
        return "full"
    if short_score >= 1:
        return "short"
    if full_score >= 1:
        return "full"

    return "ask"


def decide(url: str = "", text: str = "", content: str = "") -> str:
    """
    Decide mode: short / full / ask.

    Args:
        url: The URL to check
        text: User's additional text input
        content: Fetched content (title + body) for deeper analysis

    Returns:
        "full", "short", or "ask"
    """
    # Phase 1: Fast decision (no content fetch needed)
    mode = _decide_fast(url, text)
    if mode != "ask":
        return mode

    # Phase 2: Content-based decision (only if we have content)
    if content:
        return _decide_by_content(content)

    # Default: ask user
    return "ask"


def main() -> int:
    # Support both old and new argument formats
    url = ""
    text = ""
    content = ""
    content_arg_found = False

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--content" and i < len(sys.argv) - 1:
            content = sys.argv[i + 1]
            content_arg_found = True
        elif arg.startswith("http://") or arg.startswith("https://"):
            url = arg
        elif not content_arg_found:
            text += " " + arg

    text = text.strip()

    if not url and not text and not content:
        print(json.dumps({"ok": False, "error": "missing input (URL or text or --content)"}, ensure_ascii=False))
        return 1

    mode = decide(url, text, content)
    print(json.dumps({"ok": True, "mode": mode}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
