#!/bin/bash
# bd-eval-cms 升级脚本
# 用法：bash scripts/upgrade-from-zip.sh "/path/to/CMS_xxx_vX.zip"
# 依赖：Python3（用于解压含中文文件名的zip）

set -e

ZIP_PATH="$1"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ -z "$ZIP_PATH" ]; then
  echo "用法：bash upgrade-from-zip.sh /path/to/CMS_xxx_vX.zip"
  exit 1
fi

if [ ! -f "$ZIP_PATH" ]; then
  echo "文件不存在：$ZIP_PATH"
  exit 1
fi

# 提取 zip 内层目录名（即版本标识）
INNER_DIR=$(python3 -c "
import zipfile
with zipfile.ZipFile('$ZIP_PATH', 'r') as z:
    names = [n for n in z.namelist() if n.endswith('/') and n.count('/') == 1]
    if names:
        print(names[0].rstrip('/'))
" 2>/dev/null || echo "unknown-version")

EXTRACT_DIR="/tmp/bd-eval-upgrade-$(date +%Y%m%d%H%M%S)"
echo "解压目录：$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"

# 解压（Python 处理中文文件名）
python3 -c "
import zipfile, os
z = '$ZIP_PATH'
out = '$EXTRACT_DIR'
with zipfile.ZipFile(z, 'r') as zh:
    for name in zh.namelist():
        if name.endswith('/'):
            continue
        safe = name.encode('cp437').decode('gbk') if '?' in name else name
        safe_name = os.path.basename(safe)
        outpath = os.path.join(out, safe_name)
        with zh.open(name) as src, open(outpath, 'wb') as dst:
            dst.write(src.read())
        print(f'OK: {safe_name}')
" 2>&1

echo ""
echo "=== 当前版本 ==="
CURRENT_VERSION=$(cat "$SKILL_DIR/VERSION" 2>/dev/null || echo "unknown")
echo "bd-eval-cms v$CURRENT_VERSION"
echo "references/ 文件数：$(ls "$SKILL_DIR/references/"*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "zip 包内 .md 文件数：$(ls "$EXTRACT_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')"

echo ""
echo "=== Diff 摘要 ==="
for f in "$EXTRACT_DIR"/*.md; do
  fname=$(basename "$f")
  local="$SKILL_DIR/references/$fname"
  if [ -f "$local" ]; then
    lines=$(diff "$local" "$f" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$lines" -gt 0 ]; then
      echo "$fname: $lines lines diff"
    fi
  else
    echo "NEW: $fname"
  fi
done

# 找出 zip 里新增的、但本地没有的文件
echo ""
echo "=== zip新增 / 本地缺失 ==="
for f in "$EXTRACT_DIR"/*.md; do
  fname=$(basename "$f")
  local="$SKILL_DIR/references/$fname"
  if [ ! -f "$local" ]; then
    # 也可能是根目录的 SKILL.md 或总规则
    if [ "$fname" = "SKILL.md" ] || [[ "$fname" == 00_* ]]; then
      echo "IMPORTANT_NEW: $fname ($(wc -l < "$f")行)"
    else
      echo "NEW: $fname ($(wc -l < "$f")行)"
    fi
  fi
done

# SKILL.md 单独 diff
if [ -f "$EXTRACT_DIR/SKILL.md" ]; then
  echo ""
  echo "=== SKILL.md diff ==="
  diff_lines=$(diff "$SKILL_DIR/SKILL.md" "$EXTRACT_DIR/SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
  echo "SKILL.md: $diff_lines lines diff"
fi

echo ""
echo "=== 升级类型判断 ==="
echo "检查中..."
python3 -c "
import os, re

skill_dir = '$SKILL_DIR'
extract_dir = '$EXTRACT_DIR'
current_ver = '$CURRENT_VERSION'

# 读取当前 version.json
import json
with open(os.path.join(skill_dir, 'version.json')) as f:
    current = json.load(f)

# 尝试读取 zip 里的 version 提示（从 SKILL.md frontmatter）
skill_md = os.path.join(extract_dir, 'SKILL.md')
version_hint = 'unknown'
if os.path.exists(skill_md):
    with open(skill_md) as f:
        content = f.read()
    m = re.search(r'version:\s*[\"\']?([0-9.]+)', content)
    if m:
        version_hint = m.group(1)

print(f'当前版本：{current.get(\"version\", \"unknown\")}')
print(f'zip 包版本提示：{version_hint}')

# 判断升级类型
major_changes = ['Gate 0', 'Gate Final', '体系Gate', '20个', '19个技能']
minor_changes = ['A-0', 'A-1', 'A-2', 'A-3', 'A-4', 'A-5', 'A-6', 'A-7', 'A-8',
                 'B-1', 'B-2', 'B-3', 'C-1', 'C-2', 'C-3', 'D-0', 'D-1', 'D-2', 'D-3', 'E-1']

# 简单判断：读取 zip 增补文件看版本
supplement = None
for f in os.listdir(extract_dir):
    if '增补' in f and f.endswith('.md'):
        supplement = f
        break

upgrade_type = 'Patch'
if supplement:
    with open(os.path.join(extract_dir, supplement)) as f:
        content = f.read()
    if any(k in content for k in major_changes):
        upgrade_type = 'Major'
    elif any(k in content for k in minor_changes):
        upgrade_type = 'Minor'
    print(f'增补文件：{supplement}')
    print(f'判断类型：{upgrade_type}')
else:
    print('未找到增补文件，基于文件数判断...')
    md_count = len([f for f in os.listdir(extract_dir) if f.endswith('.md')])
    print(f'zip 内 .md 文件数：{md_count}')
    if md_count > 23:
        upgrade_type = 'Minor'
    print(f'初步判断：{upgrade_type}')
" 2>/dev/null || echo "（版本判断需要更多上下文，请人工确认）"

echo ""
echo "✅ 预检完成。请查看上方 diff 摘要后，回复'确认'执行升级，或'取消'放弃。"
echo "如需查看某个文件的详细 diff，告诉我文件名。"
