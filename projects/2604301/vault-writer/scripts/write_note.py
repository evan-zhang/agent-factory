#!/usr/bin/env python3
"""
vault-writer write_note.py
将已有的 md 文件同步到 Obsidian vault。

用法：
  python3 scripts/write_note.py --file <md文件路径> [--tags "tag1,tag2"] [--folder "子目录"]
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


def get_config_path() -> Path:
    """复用 init_config 的路径逻辑。"""
    openclaw_dir = Path.home() / ".openclaw"
    if openclaw_dir.exists():
        return openclaw_dir / "vault-writer-config.json"
    return Path.home() / ".config" / "vault-writer-config.json"


def load_config() -> dict:
    """加载配置，不存在则报错。"""
    config_path = get_config_path()
    if not config_path.exists():
        return {"error": f"配置不存在：{config_path}，请先运行 --init"}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def has_frontmatter(content: str) -> bool:
    """检查内容是否已有 YAML frontmatter。"""
    return content.startswith("---") and "\n---" in content[3:]


def inject_frontmatter(
    content: str,
    tags: list[str] | None = None,
    default_tags: list[str] | None = None,
) -> str:
    """
    注入/补充 YAML frontmatter。
    - 没有 frontmatter：添加 created_at + tags（来自参数 > default > 兜底）
    - 已有 frontmatter：补充缺失字段（created_at/tags），不覆盖已有值
    - 已有 tags 时：不传参数 → 保持；传参数 → 替换
    """
    now = datetime.now()
    timestamp_str = now.isoformat()
    effective_tags = tags or default_tags or ["agent-output"]
    tags_str = ", ".join(effective_tags)

    if not has_frontmatter(content):
        # 无 frontmatter，添加完整 frontmatter
        new_fm = f"created_at: {timestamp_str}\ntags: [{tags_str}]"
        return f"---\n{new_fm}\n---\n\n{content}"

    # 有 frontmatter，找到第二个 --- 的位置
    second_dash = content.index("\n---", 3)
    # frontmatter 内容：content[3:second_dash]，格式 "key: val\nkey2: val2"
    fm_content = content[3:second_dash]
    # 按行拆分
    fm_lines = []
    for line in fm_content.split("\n"):
        stripped = line.strip()
        if stripped:
            fm_lines.append(stripped)

    # 解析已有字段
    has_created_at = False
    has_tags = False
    tags_line_content = None
    tags_line_idx = None
    for i, line in enumerate(fm_lines):
        if line.startswith("created_at:"):
            has_created_at = True
        elif line.startswith("tags:"):
            has_tags = True
            tags_line_content = line
            tags_line_idx = i

    # 补充 created_at（已有则保持）
    if not has_created_at:
        fm_lines.insert(0, f"created_at: {timestamp_str}")

    # 处理 tags
    if tags is not None:
        # 传了 tags 参数：替换或补充
        if has_tags:
            fm_lines[tags_line_idx] = f"tags: [{tags_str}]"
        else:
            fm_lines.append(f"tags: [{tags_str}]")
    elif not has_tags:
        # 未传 tags 且原本无 tags：补充 default_tags
        fm_lines.append(f"tags: [{tags_str}]")
    # else: 已已有 tags 且未传参数 → 保持不变

    fm_str = "\n".join(fm_lines)
    body = content[second_dash + 4:]  # skip "\n---" (3 dashes + 1 newline)
    return f"---\n{fm_str}\n---\n{body}"




def write_note(
    file_path: str,
    folder: str | None = None,
    tags: str | None = None,
    date_subfolder: bool = True,
) -> dict:
    """
    将 md 文件同步到 Obsidian vault。
    - 文件名保持源文件原名
    - 日期子目录默认开启
    - 冲突时加序号，不覆盖
    """
    config = load_config()
    if "error" in config:
        return {"ok": False, "error": config["error"]}

    vault_path = config.get("vault_path", "")
    if not vault_path or not Path(vault_path).exists():
        return {"ok": False, "error": f"vault 路径无效：{vault_path}"}

    # 读取源文件
    source = Path(file_path).expanduser().resolve()
    if not source.exists():
        return {"ok": False, "error": f"源文件不存在：{source}"}
    if not source.suffix.lower() == ".md":
        return {"ok": False, "error": f"仅支持 .md 文件，收到：{source.suffix}"}

    content = source.read_text(encoding="utf-8")

    # 注入 frontmatter
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    default_tag_list = config.get("default_tags", ["agent-output"])
    content = inject_frontmatter(content, tag_list, default_tags=default_tag_list)

    # 计算目标路径
    base = Path(vault_path)
    sub = folder or config.get("default_folder", "")
    if sub:
        base = base / sub

    # 日期子目录
    if date_subfolder:
        base = base / datetime.now().strftime("%Y-%m-%d")

    # 文件名保持源文件原名
    filename = source.name
    target = base / filename

    # 目录穿越安全检查
    try:
        target.resolve().relative_to(Path(vault_path).resolve())
    except ValueError:
        return {"ok": False, "error": f"目标路径不在 vault 内：{target}"}

    # 冲突处理：加序号，不覆盖
    if target.exists():
        stem = source.stem
        ext = source.suffix
        counter = 2
        while counter <= 100:
            candidate = base / f"{stem}-{counter}{ext}"
            if not candidate.exists():
                target = candidate
                break
            counter += 1
        else:
            return {"ok": False, "error": "文件名冲突超过上限（100），请手动处理"}

    # 创建中间目录并写入
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    rel_path = target.relative_to(vault_path)
    return {
        "ok": True,
        "path": str(target),
        "vault_relative": str(rel_path),
        "filename": target.name,
    }


def main():
    parser = argparse.ArgumentParser(description="同步 md 文件到 Obsidian vault")
    parser.add_argument("--file", "-f", required=True, help="要同步的 md 文件路径")
    parser.add_argument("--folder", default=None, help="vault 内子目录（覆盖 default_folder）")
    parser.add_argument("--tags", default=None, help="标签，逗号分隔")
    parser.add_argument("--no-date-subfolder", action="store_true", help="不创建日期子目录")
    args = parser.parse_args()

    result = write_note(
        file_path=args.file,
        folder=args.folder,
        tags=args.tags,
        date_subfolder=not args.no_date_subfolder,
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
