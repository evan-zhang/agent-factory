#!/usr/bin/env python3
"""归档前报告验证脚本。

检查报告是否包含必要 section，输出 JSON 结果。
用法: python3 scripts/validate_report.py <report_file> [--mode full|short]
"""

import json
import re
import sys
from pathlib import Path

# full 模式必须存在的 section（H2 级别）
FULL_REQUIRED = [
    "概述",
    "核心功能",
    "技术栈",
    "Claim 验证",
    "局限性",
    "个人洞察",
]

# full 模式建议存在的 section（缺失时列为 warning）
FULL_RECOMMENDED = [
    "关键数据",
    "对比分析",
    "应用场景",
    "隐含项目发现",
]

# short 模式必须存在的 section
SHORT_REQUIRED = [
    "摘要",
    "来源",
]

# Claim 验证表必须包含结论符号
CLAIM_CONCLUSION_PATTERN = re.compile(r"[✅⚠️❌]")


def extract_sections(text: str) -> dict:
    """提取所有 H2 section 及其内容。"""
    sections = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+)", line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return {k: "\n".join(v) for k, v in sections.items()}


def check_claim_table(content: str) -> list[str]:
    """检查 Claim 验证 section 是否有有效结论。"""
    warnings = []
    if "Claim 验证" not in content:
        return warnings
    claim_section = ""
    lines = content.splitlines()
    in_claim = False
    for line in lines:
        if re.match(r"^##\s+Claim 验证", line):
            in_claim = True
            continue
        if in_claim and re.match(r"^##\s+", line):
            break
        if in_claim:
            claim_section += line + "\n"
    if not claim_section.strip():
        warnings.append("Claim 验证 section 为空")
    elif not CLAIM_CONCLUSION_PATTERN.search(claim_section):
        warnings.append("Claim 验证表缺少结论符号（✅⚠️❌）")
    return warnings


def validate(report_path: str, mode: str) -> dict:
    """验证报告并返回结构化结果。"""
    path = Path(report_path)
    if not path.exists():
        return {"ok": False, "missing": [f"文件不存在: {report_path}"], "warnings": []}

    text = path.read_text(encoding="utf-8")
    sections = extract_sections(text)
    section_names = set(sections.keys())

    missing = []
    warnings = []

    if mode == "full":
        for s in FULL_REQUIRED:
            # 模糊匹配：section 名可能包含额外文字
            found = any(s in name for name in section_names)
            if not found:
                missing.append(s)
        for s in FULL_RECOMMENDED:
            found = any(s in name for name in section_names)
            if not found:
                warnings.append(f"建议补充: {s}")
        warnings.extend(check_claim_table(text))
    else:
        for s in SHORT_REQUIRED:
            found = any(s in name for name in section_names)
            if not found:
                missing.append(s)

    return {
        "ok": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
    }


def main():
    if len(sys.argv) < 2:
        print("用法: python3 validate_report.py <report_file> [--mode full|short]",
              file=sys.stderr)
        sys.exit(1)

    report_file = sys.argv[1]
    mode = "full"

    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]

    if mode not in ("full", "short"):
        print(f"未知模式: {mode}，支持 full/short", file=sys.stderr)
        sys.exit(1)

    result = validate(report_file, mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
