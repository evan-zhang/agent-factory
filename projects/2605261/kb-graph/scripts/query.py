#!/usr/bin/env python3
"""KB Graph 查询层：基于 entries.json 的关键词 + 向量查询"""
import json
import re
from pathlib import Path

def load_entries(root):
    """从 .kb-workdir/entries.json 加载所有条目"""
    entries_path = Path(root) / ".kb-workdir" / "entries.json"
    if not entries_path.exists():
        return {}
    with open(entries_path) as f:
        return json.load(f)

def search_by_keyword(root, query_str):
    """关键词搜索：title / summary / tags / entities"""
    entries = load_entries(root)
    results = []
    q = query_str.lower()
    for rel_path, entry in entries.items():
        title = entry.get("title", "").lower()
        summary = entry.get("summary", "").lower()
        tags = " ".join([t.lower() for t in entry.get("tags", [])])
        entities = " ".join([e.lower() for e in entry.get("entities", [])])
        score = 0
        if q in title:
            score += 10
        if q in summary:
            score += 5
        if q in tags:
            score += 3
        if q in entities:
            score += 3
        if score > 0:
            results.append({"score": score, "entry": entry, "rel_path": rel_path})
    results.sort(key=lambda x: -x["score"])
    return results[:10]

def query(query_str, root):
    """主查询入口"""
    results = search_by_keyword(root, query_str)
    return {
        "ok": True,
        "results": [r["entry"] for r in results],
        "stats": [{"path": r["rel_path"], "score": r["score"]} for r in results],
        "method": "keyword" if results else "none",
        "query": query_str,
        "total": len(results),
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="KB Graph 查询")
    parser.add_argument("--query", required=True)
    parser.add_argument("--dir", required=True, help="知识库根目录")
    args = parser.parse_args()

    result = query(args.query, args.dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
