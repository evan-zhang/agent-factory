#!/usr/bin/env python3
import json
import sys

KEYWORDS_FULL = ["github", "star", "open source", "repo", "tutorial", "对比", "教程", "开源"]
KEYWORDS_SHORT = ["news", "新闻", "热点", "观点", "commentary"]


def decide(text: str) -> str:
    t = text.lower()
    if any(k in t for k in KEYWORDS_FULL):
        return "full"
    if any(k in t for k in KEYWORDS_SHORT):
        return "short"
    return "ask"


def main() -> int:
    text = " ".join(sys.argv[1:]).strip()
    if not text:
        print(json.dumps({"ok": False, "error": "missing input"}, ensure_ascii=False))
        return 1
    mode = decide(text)
    print(json.dumps({"ok": True, "mode": mode}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
