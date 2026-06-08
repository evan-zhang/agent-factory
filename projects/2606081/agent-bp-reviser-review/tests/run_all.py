#!/usr/bin/env python3
"""
统一测试入口：运行 tests/ 下所有 unittest 风格测试

注意：test_fixes.py / test_all_fixes.py 是早期脚本式测试（顶层 print），
不是 unittest.TestCase，单独运行即可，不纳入本 runner。

用法：
    python3 tests/run_all.py
"""

import sys
import os
import unittest

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

# unittest 风格测试模块（显式列出，避免误抓脚本式遗留测试）
UNITTEST_MODULES = [
    "test_standard_injection",
    "test_evidence_scoping",
    "test_revision_gating",
    "test_writeback_consistency",
    "test_bp_api_integration",
]


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for mod in UNITTEST_MODULES:
        suite.addTests(loader.loadTestsFromName(mod))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
