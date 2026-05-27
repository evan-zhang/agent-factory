#!/usr/bin/env python3
"""KB Graph 索引验证脚本"""
import json
import re
import sys
from pathlib import Path

def validate_index(index_path):
    errors = []
    warnings = []
    text = Path(index_path).read_text()

    graph_m = re.search(r"<!-- kb-graph -->(.*?)<!-- /kb-graph -->", text, re.DOTALL)
    if not graph_m:
        warnings.append("Graph data not found in HTML comments")
    else:
        try:
            json.loads(graph_m.group(1))
        except json.JSONDecodeError as e:
            errors.append(f"Graph JSON invalid: {e}")

    frontmatters = re.findall(r"^```yaml\n(.*?)\n```", text, re.DOTALL | re.MULTILINE)
    if not frontmatters:
        warnings.append("No YAML frontmatter entries found")

    return {"errors": errors, "warnings": warnings}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("index", nargs="?", default=".kb-index.md", help="索引文件路径")
    args = parser.parse_args()

    try:
        result = validate_index(args.index)
        print(json.dumps({"ok": len(result["errors"]) == 0, **result}))
    except FileNotFoundError:
        print(json.dumps({"ok": False, "errors": [f"Index file not found: {args.index}"], "warnings": []}))
    except Exception as e:
        print(json.dumps({"ok": False, "errors": [str(e)], "warnings": []}))

if __name__ == "__main__":
    main()
