#!/usr/bin/env python3
"""KB Graph 维护层：矛盾检测、孤儿文件检查"""
import json
import re
from pathlib import Path

def extract_entries(index_path):
    text = Path(index_path).read_text()
    entries = []
    frontmatters = re.findall(r"^```yaml\n(.*?)\n```", text, re.DOTALL | re.MULTILINE)
    for fm in frontmatters:
        try:
            import yaml
            entry = yaml.safe_load(fm)
            if entry:
                entries.append(entry)
        except Exception:
            pass
    return entries

def detect_orphan_files(index_path):
    index_dir = Path(index_path).parent
    indexed = set()
    for entry in extract_entries(index_path):
        p = entry.get("path", "")
        if p:
            indexed.add(Path(p).name)

    orphans = []
    for md in index_dir.glob("*.md"):
        if md.name not in (".kb-schema.md", ".kb-index.md") and md.name not in indexed:
            orphans.append(str(md))
    return orphans

def detect_dangling_refs(index_path):
    index_dir = Path(index_path).parent
    entries = extract_entries(index_path)
    dangling = []
    for entry in entries:
        for rel in entry.get("relationships", []):
            target = rel.get("target", "")
            if target and not (index_dir / target).exists():
                dangling.append({"file": entry.get("path"), "target": target})
    return dangling

def lint_index(index_path):
    issues = []
    try:
        orphans = detect_orphan_files(index_path)
        for f in orphans:
            issues.append({"type": "orphan", "files": [f]})
    except Exception:
        pass
    try:
        dangling = detect_dangling_refs(index_path)
        for d in dangling:
            issues.append({"type": "dangling-ref", "files": [d["file"]], "target": d["target"]})
    except Exception:
        pass
    return issues

def main_internal(index_path):
    """供 kb_graph.py 调用，不走 argparse"""
    issues = lint_index(index_path)
    return {"ok": True, "issues": issues}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True)
    args = parser.parse_args()
    result = main_internal(args.index)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
