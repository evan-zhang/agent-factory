#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "usage: archive_report.py <src> <dst_dir>"}, ensure_ascii=False))
        return 1
    src = Path(sys.argv[1]).expanduser()
    dst_dir = Path(sys.argv[2]).expanduser()
    if not src.exists():
        print(json.dumps({"ok": False, "error": f"missing source: {src}"}, ensure_ascii=False))
        return 1
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    shutil.copy2(src, dst)
    print(json.dumps({"ok": True, "dst": str(dst)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
