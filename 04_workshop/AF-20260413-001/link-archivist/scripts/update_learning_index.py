#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROW = "| 019 | 2026-04-12 | AI_Toolbox | Link-Archivist v10 redesign | Skill设计, 结构化, CLI, 归档 | reports/link-archivist-v10-design-proposal-2026-04-12.md | Skill拆分为语义层+执行层+资源层。 |\n"


def main() -> int:
    index = Path("memory/LEARNING_INDEX.md")
    if not index.exists():
        print(json.dumps({"ok": False, "error": f"missing index: {index}"}, ensure_ascii=False))
        return 1
    text = index.read_text(encoding="utf-8")
    if "Link-Archivist v10 redesign" in text:
        print(json.dumps({"ok": True, "skipped": True}, ensure_ascii=False))
        return 0
    lines = text.splitlines(True)
    header_end = 0
    for i, line in enumerate(lines):
        if line.startswith("| 018 "):
            header_end = i
            break
    lines.insert(header_end, ROW)
    index.write_text("".join(lines), encoding="utf-8")
    print(json.dumps({"ok": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
