#!/usr/bin/env python3
"""KB Graph 集成测试"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入脚本 - 使用绝对路径
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"


def test_build_basic():
    """测试基本构建功能"""
    test_dir = tempfile.mkdtemp()

    try:
        # 创建测试文件
        (Path(test_dir) / "doc1.md").write_text("# 测试文档1\n内容1")
        (Path(test_dir) / "doc2.md").write_text("# 测试文档2\n内容2")

        # 运行构建
        os.system(f'python3 {SCRIPT_DIR}/kb_graph.py build {test_dir} --test-mode')

        # 验证结果
        cache_file = Path(test_dir) / ".kb-workdir" / "kb_cache.json"
        entries_file = Path(test_dir) / ".kb-workdir" / "entries.json"
        index_file = Path(test_dir) / ".kb-index.md"

        if cache_file.exists() and entries_file.exists() and index_file.exists():
            print(json.dumps({"ok": True, "test": "build_basic", "result": "pass"}))
            return 0
        else:
            print(json.dumps({"ok": False, "test": "build_basic", "error": "Missing files"}))
            return 1

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_incremental_update():
    """测试增量更新功能"""
    test_dir = tempfile.mkdtemp()

    try:
        # 创建测试文件
        (Path(test_dir) / "doc1.md").write_text("# 测试文档1\n内容1")

        # 第一次构建
        os.system(f'python3 {SCRIPT_DIR}/kb_graph.py build {test_dir} --test-mode > /dev/null 2>&1')

        # 修改文件
        (Path(test_dir) / "doc1.md").write_text("# 测试文档1\n内容1\n新增内容")

        # 增量更新
        result = os.popen(f'python3 {SCRIPT_DIR}/kb_graph.py update {test_dir} --test-mode').read()
        data = json.loads(result)

        if data.get("ok") and data.get("updated", 0) > 0:
            print(json.dumps({"ok": True, "test": "incremental_update", "result": "pass"}))
            return 0
        else:
            print(json.dumps({"ok": False, "test": "incremental_update", "error": "Update failed"}))
            return 1

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_query():
    """测试查询功能"""
    test_dir = tempfile.mkdtemp()

    try:
        # 创建测试文件
        (Path(test_dir) / "doc1.md").write_text("# AI 人工智能\nAI内容")

        # 构建
        os.system(f'python3 {SCRIPT_DIR}/kb_graph.py build {test_dir} --test-mode > /dev/null 2>&1')

        # 查询
        result = os.popen(f'python3 {SCRIPT_DIR}/query.py --query "AI" --dir {test_dir}').read()
        data = json.loads(result)

        if data.get("ok") and data.get("total", 0) > 0:
            print(json.dumps({"ok": True, "test": "query", "result": "pass"}))
            return 0
        else:
            print(json.dumps({"ok": False, "test": "query", "error": "Query failed"}))
            return 1

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def main():
    """运行所有测试"""
    print(json.dumps({"ok": True, "status": "starting"}))

    tests = [
        test_build_basic,
        test_incremental_update,
        test_query,
    ]

    results = []

    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(json.dumps({"ok": False, "test": test.__name__, "error": str(e)}))
            results.append(1)

    # 汇总结果
    passed = sum(1 for r in results if r == 0)
    total = len(results)

    print(json.dumps({
        "ok": all(r == 0 for r in results),
        "passed": passed,
        "failed": total - passed,
        "total": total
    }))

    return 0 if all(r == 0 for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())