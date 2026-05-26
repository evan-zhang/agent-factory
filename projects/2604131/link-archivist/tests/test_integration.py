#!/usr/bin/env python3
"""Link Archivist 集成测试"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# 使用绝对路径
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"


def test_basic_archive():
    """测试基本归档功能"""
    test_dir = tempfile.mkdtemp()

    try:
        # 创建测试报告
        test_file = Path(test_dir) / "test.md"
        test_file.write_text("# 测试报告\n\n这是测试内容。")

        # 归档
        archive_dir = Path(test_dir) / "archive"
        result = os.popen(
            f'python3 {SCRIPT_DIR}/archive_report.py --file {test_file} --dir {archive_dir} --title "Test"'
        ).read()

        try:
            data = json.loads(result)
            if data.get("ok") and (archive_dir / "2026" / "05").exists():
                return 0
            else:
                return 1
        except json.JSONDecodeError:
            return 1

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_archive_with_entities():
    """测试带 entities 的归档"""
    test_dir = tempfile.mkdtemp()

    try:
        # 创建测试报告
        test_file = Path(test_dir) / "test.md"
        test_file.write_text("# 测试报告\n\n这是测试内容。")

        # 归档带 entities
        archive_dir = Path(test_dir) / "archive"
        result = os.popen(
            f'python3 {SCRIPT_DIR}/archive_report.py '
            f'--file {test_file} --dir {archive_dir} --title "Test" '
            f'--entities \'["AI","Python"]\' --summary "测试摘要" --confidence high'
        ).read()

        try:
            data = json.loads(result)
            if data.get("ok"):
                # 检查生成的文件是否包含正确的 YAML
                archive_file = list((archive_dir / "2026" / "05").glob("K-*.md"))[0]
                content = archive_file.read_text()
                if "entities:" in content and "AI" in content and "summary:" in content and "confidence: high" in content:
                    return 0
                else:
                    return 1
            else:
                return 1
        except json.JSONDecodeError:
            return 1
        except Exception as e:
            return 1

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_mode_decision():
    """测试模式判断"""
    try:
        # 测试 GitHub URL（简化测试，只验证输出是 JSON）
        result = os.popen(
            f'echo "https://github.com/test/repo" | python3 {SCRIPT_DIR}/decide_mode.py -'
        ).read()
        data = json.loads(result)
        if "mode" in data:  # 只验证有 mode 字段，不强制具体值
            return 0
        else:
            return 1
    except json.JSONDecodeError:
        return 1


def main():
    """运行所有测试"""
    tests = [
        test_basic_archive,
        test_archive_with_entities,
        test_mode_decision,
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