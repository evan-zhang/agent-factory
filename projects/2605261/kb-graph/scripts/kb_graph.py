#!/usr/bin/env python3
"""KB Graph 主入口 CLI（采集/编译/图谱/查询/维护五层统一入口）"""
import argparse
import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import ingest, compile, build_graph, lint, query

INDEX_FILE = ".kb-index.md"

def get_index_path(root):
    """返回根目录的 .kb-index.md 路径"""
    return root / INDEX_FILE

def load_index(root):
    """从 JSON sidecar 加载 entries，返回 {rel_path: entry} 的 dict"""
    entries_path = root / ".kb-workdir" / "entries.json"
    if not entries_path.exists():
        return {}
    with open(entries_path) as f:
        return json.load(f)

def save_index_entry(root, entry, rel_path):
    """写入 entries JSON + 重建 YAML 索引文件"""
    entries = load_index(root)
    entries[rel_path] = entry
    entries_path = root / ".kb-workdir" / "entries.json"
    entries_path.parent.mkdir(parents=True, exist_ok=True)
    with open(entries_path, "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    _rebuild_yaml_index(root, entries)

def _rebuild_yaml_index(root, entries):
    """从 entries dict 重建 .kb-index.md"""
    import datetime
    idx_path = get_index_path(root)
    lines = [
        "# 知识库索引\n",
        f"生成时间：{datetime.datetime.now().isoformat()}\n",
        f"文件数：{len(entries)}\n",
    ]
    for rel, e in sorted(entries.items()):
        lines.append(f"### {e.get('title', rel)}\n")
        lines.append("```yaml\n")
        lines.append(f"title: {e.get('title', '')}\n")
        lines.append(f"type: file-summary\n")
        lines.append(f"path: {rel}\n")
        summary = e.get('summary', '').replace('\n', ' ').strip()
        lines.append(f"summary: {summary}\n")
        entities = e.get('entities', [])
        if entities:
            for ent in entities:
                lines.append(f"- {ent}\n")
        else:
            lines.append("entities: []\n")
        tags = e.get('tags', [])
        if tags:
            lines.append("tags:\n")
            for tag in tags:
                lines.append(f"  - {tag}\n")
        else:
            lines.append("tags: []\n")
        relationships = e.get('relationships', [])
        if relationships:
            lines.append("relationships:\n")
            for rel in relationships:
                lines.append(f"  - type: {rel.get('type', 'unknown')}\n")
                lines.append(f"    target: {rel.get('target', '')}\n")
                lines.append(f"    description: {rel.get('description', '')}\n")
        else:
            lines.append("relationships: []\n")
        lines.append(f"sha256: {e.get('sha256', '')}\n")
        lines.append(f"confidence: {e.get('confidence', 'low')}\n")
        confidence_score = e.get('confidence_score', 0)
        lines.append(f"confidence_score: {confidence_score}\n")
        lines.append("---\n\n")
    idx_path.write_text("".join(lines))

def remove_index_entry(root, rel_path):
    """从索引中删除指定文件的条目"""
    entries = load_index(root)
    if rel_path in entries:
        del entries[rel_path]
        entries_path = root / ".kb-workdir" / "entries.json"
        with open(entries_path, "w") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        _rebuild_yaml_index(root, entries)

def cmd_build(args):
    """全量构建"""
    root = Path(args.dir)
    files, _ = ingest.scan_directory(str(root))
    test_mode = getattr(args, 'test_mode', False)
    results = {"ok": True, "built": 0, "skipped": 0, "errors": [], "failed_files": []}

    for f in files:
        if f["status"] == "unchanged":
            results["skipped"] += 1
        elif f["status"] == "deleted":
            remove_index_entry(root, f["rel"])
            ingest.mark_deleted_in_cache(str(root), f["rel"])
        else:
            try:
                entry = compile.compile_with_llm(f["path"], test_mode=test_mode)
                save_index_entry(root, entry, f["rel"])
                ingest.update_cache_on_success(str(root), f["rel"], f["sha256"])
                results["built"] += 1
            except Exception as e:
                ingest.update_cache_on_failure(str(root), f["rel"], f["sha256"], e)
                results["errors"].append({"file": f["path"], "error": str(e)[:200]})
                results["failed_files"].append(f["path"])

    print(json.dumps(results, indent=2))
    return 0 if not results["errors"] else 1

def cmd_update_single(args):
    """增量更新（单文件）"""
    root = Path(args.dir) if args.dir else Path(args.file).parent
    rel = Path(args.file).relative_to(root).as_posix()
    test_mode = getattr(args, 'test_mode', False)
    try:
        entry = compile.compile_with_llm(args.file, test_mode=test_mode)
        save_index_entry(root, entry, rel)
        ingest.update_cache_on_success(str(root), rel, entry["sha256"])
        print(json.dumps({"ok": True, "entry": entry}))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)[:200]}))
        return 1

def cmd_update(args):
    """增量更新（目录）"""
    root = Path(args.dir)
    files, _ = ingest.scan_directory(args.dir)
    test_mode = getattr(args, 'test_mode', False)
    results = {"ok": True, "updated": 0, "skipped": 0, "errors": [], "failed_files": []}

    for f in files:
        if f["status"] not in ("new", "modified", "retry"):
            if f["status"] == "unchanged":
                results["skipped"] += 1
            continue
        try:
            entry = compile.compile_with_llm(f["path"], test_mode=test_mode)
            save_index_entry(root, entry, f["rel"])
            ingest.update_cache_on_success(str(root), f["rel"], f["sha256"])
            results["updated"] += 1
        except Exception as e:
            ingest.update_cache_on_failure(str(root), f["rel"], f["sha256"], e)
            results["errors"].append({"file": f["path"], "error": str(e)[:200]})
            results["failed_files"].append(f["path"])

    print(json.dumps(results, indent=2))
    return 0 if not results["errors"] else 1

def cmd_lint(args):
    """Lint 质量检查"""
    issues = []
    for idx in Path(args.dir).rglob(".kb-index.md"):
        result = lint.main_internal(str(idx))
        issues.extend(result.get("issues", []))
    print(json.dumps({"ok": True, "issues": issues}))
    return 0

def cmd_query(args):
    """查询"""
    result = query.query(args.query, args.dir)
    print(json.dumps(result))
    return 0

def cmd_status(args):
    """查看状态"""
    root = Path(args.dir)
    cache_path = root / ".kb-workdir" / "kb_cache.json"
    if cache_path.exists():
        with open(cache_path) as f:
            cache = json.load(f)
        success = sum(1 for v in cache.values() if v.get("status") == "success")
        failed = sum(1 for v in cache.values() if v.get("status") == "failed")
        print(json.dumps({
            "ok": True,
            "total_cached": len(cache),
            "success": success,
            "failed": failed,
            "cache_path": str(cache_path)
        }))
    else:
        print(json.dumps({"ok": True, "total_cached": 0, "status": "no_cache"}))
    return 0

def main():
    parser = argparse.ArgumentParser(description="KB Graph - 知识库图谱构建工具")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("build", help="全量构建")
    p.add_argument("dir", help="知识库根目录")
    p.add_argument("--test-mode", action="store_true", help="测试模式：跳过 LLM 调用")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("update-single", help="增量更新（单文件）")
    p.add_argument("file", help="文件路径")
    p.add_argument("--dir", dest="dir", default=None, help="知识库根目录（用于计算相对路径）")
    p.add_argument("--test-mode", action="store_true", help="测试模式：跳过 LLM 调用")
    p.set_defaults(fn=cmd_update_single)

    p = sub.add_parser("update", help="增量更新（目录）")
    p.add_argument("dir", help="目录路径")
    p.add_argument("--test-mode", action="store_true", help="测试模式：跳过 LLM 调用")
    p.set_defaults(fn=cmd_update)

    p = sub.add_parser("lint", help="Lint 质量检查")
    p.add_argument("dir", help="目录路径")
    p.set_defaults(fn=cmd_lint)

    p = sub.add_parser("query", help="查询")
    p.add_argument("query", help="查询内容")
    p.add_argument("--dir", required=True, help="知识库根目录")
    p.set_defaults(fn=cmd_query)

    p = sub.add_parser("status", help="查看状态")
    p.add_argument("dir", help="目录路径")
    p.set_defaults(fn=cmd_status)

    args = parser.parse_args()
    if args.cmd:
        return args.fn(args)
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
