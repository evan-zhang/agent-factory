#!/usr/bin/env python3
"""
打包 Skill 目录为 ZIP 文件

用途：将指定的 Skill 目录打包成 .zip 文件，用于后续上传到七牛

使用方式：
  python3 create-xgjk-skill/scripts/skill-management/pack_skill.py <skill-dir> [--output <output.zip>]

参数说明：
  skill-dir     Skill 目录路径（必须）
  --output      输出 ZIP 文件路径（可选，默认为 <skill-name>.zip）

示例：
  python3 create-xgjk-skill/scripts/skill-management/pack_skill.py ./im-robot
  python3 create-xgjk-skill/scripts/skill-management/pack_skill.py ./im-robot --output ./dist/im-robot-v1.zip

说明：
  无需登录 token。
"""

import sys
import os
import argparse
import zipfile


def pack_skill(skill_dir: str, output_path: str) -> str:
    """将 Skill 目录打包为 ZIP"""
    skill_dir = os.path.abspath(skill_dir)
    if not os.path.isdir(skill_dir):
        raise FileNotFoundError(f"目录不存在: {skill_dir}")

    # 检查 SKILL.md 是否存在
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        raise FileNotFoundError(f"不是有效的 Skill 目录（缺少 SKILL.md）: {skill_dir}")

    skill_name = os.path.basename(skill_dir)
    output_path = os.path.abspath(output_path)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    file_count = 0
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(skill_dir):
            # 跳过隐藏目录和 __pycache__
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for f in files:
                if f.startswith(".") or f.endswith(".pyc"):
                    continue
                full_path = os.path.join(root, f)
                arc_name = os.path.join(skill_name, os.path.relpath(full_path, skill_dir))
                zf.write(full_path, arc_name)
                file_count += 1

    size_kb = os.path.getsize(output_path) / 1024
    print(f"打包完成: {output_path}", file=sys.stderr)
    print(f"文件数: {file_count}，大小: {size_kb:.1f} KB", file=sys.stderr)

    # 输出 ZIP 路径到 stdout（方便管道传给下一步）
    print(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="打包 Skill 目录为 ZIP 文件")
    parser.add_argument("skill_dir", help="Skill 目录路径")
    parser.add_argument("--output", default="", help="输出 ZIP 文件路径")
    args = parser.parse_args()

    output = args.output
    if not output:
        skill_name = os.path.basename(os.path.abspath(args.skill_dir))
        output = f"{skill_name}.zip"

    pack_skill(args.skill_dir, output)


if __name__ == "__main__":
    main()
