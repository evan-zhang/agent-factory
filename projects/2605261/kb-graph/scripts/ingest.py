#!/usr/bin/env python3
"""KB Graph 采集层：扫描目录、检测变更（不含缓存写入）"""
import hashlib
import json
from pathlib import Path

CACHE_FILE = ".kb-workdir/kb_cache.json"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_cache(root):
    cache_path = Path(root) / CACHE_FILE
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)
    return {}

def save_cache(root, cache):
    cache_path = Path(root) / CACHE_FILE
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

def scan_directory(root_dir):
    """返回文件列表和当前缓存。缓存由调用方决定何时写入。"""
    root = Path(root_dir)
    cache = load_cache(root)
    files = []

    for md in root.rglob("*.md"):
        rel = md.relative_to(root).as_posix()
        if md.name in (".kb-schema.md", ".kb-index.md", ".kb-workdir"):
            continue
        try:
            s = sha256(md)
        except Exception:
            continue
        cached = cache.get(rel, {})
        cached_sha = cached.get("source_sha256") if isinstance(cached, dict) else cached

        if rel not in cache:
            status = "new"
        elif cached_sha != s:
            status = "modified"
        else:
            cached_status = cached.get("status") if isinstance(cached, dict) else "success"
            status = "unchanged" if cached_status == "success" else "retry"
        files.append({"path": str(md), "rel": rel, "sha256": s, "status": status})

    deleted = []
    for rel in list(cache.keys()):
        if not (root / rel).exists():
            deleted.append(rel)
    for rel in deleted:
        files.append({"path": rel, "rel": rel, "status": "deleted"})

    return files, cache

def update_cache_on_success(root, rel, sha256):
    """编译成功后更新缓存"""
    cache = load_cache(root)
    cache[rel] = {
        "source_sha256": sha256,
        "status": "success",
    }
    save_cache(root, cache)

def update_cache_on_failure(root, rel, sha256, error):
    """编译失败后更新缓存（标记为 failed，下次仍重试）"""
    cache = load_cache(root)
    cache[rel] = {
        "source_sha256": sha256,
        "status": "failed",
        "error": str(error)[:200],
    }
    save_cache(root, cache)

def mark_deleted_in_cache(root, rel):
    """删除文件后从缓存移除"""
    cache = load_cache(root)
    if rel in cache:
        del cache[rel]
        save_cache(root, cache)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", required=True)
    args = parser.parse_args()

    files, _ = scan_directory(args.scan)
    print(json.dumps({"ok": True, "files": files}))

if __name__ == "__main__":
    main()
