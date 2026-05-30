#!/usr/bin/env python3
"""
cms-report-to-html.py — CMS 投前评估报告 Markdown → HTML 生成器
照搬 style-03 琥珀金风格，适配 CMS 报告结构

用法:
  python3 scripts/cms-report-to-html.py <品种目录> [--upload] [--doc-id DOC_ID]

流程:
  1. 读取 state.json 获取封面元数据
  2. 读取 04-final-report.md
  3. 按 ## 第X章 拆分章节
  4. 自动生成目录（TOC）
  5. Markdown → HTML 转换
  6. 替换 skeleton-cms.html 所有 token
  7. 验证零残留
  8. 输出 REPORT.html
  9. 可选上传到 doc.20100706.xyz
"""

import sys
import os
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

# ============================================================
# 路径常量
# ============================================================
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = PROJECT_DIR / "templates"
SKELETON_PATH = TEMPLATES_DIR / "skeleton-cms.html"
AMBER_YML_PATH = Path(os.path.expanduser("~/.agents/skills/doc-viewer/templates/style-03/color-themes/amber.yml"))

# ============================================================
# CSS 变量加载（从 amber.yml）
# ============================================================
def load_css_vars(yml_path: Path) -> dict:
    """从 amber.yml 加载所有 CSS token（跳过 YAML frontmatter）"""
    tokens = {}
    in_frontmatter = False
    with open(yml_path, 'r') as f:
        for line in f:
            stripped = line.strip()
            if stripped == '---':
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                continue
            if ':' in stripped and not stripped.startswith('#'):
                key, _, val = stripped.partition(':')
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and val:
                    tokens[f'{{{{{key}}}}}'] = val
    return tokens


# ============================================================
# Markdown → HTML 转换
# ============================================================
def md_table_to_html(table_lines: list[str]) -> str:
    """将 markdown 表格转为 HTML table"""
    if len(table_lines) < 2:
        return ''.join(table_lines)

    def parse_row(line):
        cells = [c.strip() for c in line.strip('|').split('|')]
        return cells

    header_cells = parse_row(table_lines[0])

    # 检查是否是分隔行（第二行全是 ---）
    has_separator = all(re.match(r'^[-:]+$', c.strip()) for c in parse_row(table_lines[1]))
    data_start = 2 if has_separator else 1

    html = '<div class="table-wrap">\n<table>\n'
    html += '<thead><tr>' + ''.join(f'<th>{c}</th>' for c in header_cells) + '</tr></thead>\n'
    html += '<tbody>\n'

    for line in table_lines[data_start:]:
        cells = parse_row(line)
        html += '<tr>' + ''.join(f'<td>{inline_md_to_html(c)}</td>' for c in cells) + '</tr>\n'

    html += '</tbody>\n</table>\n</div>\n'
    return html


def inline_md_to_html(text: str) -> str:
    """行内 Markdown → HTML"""
    # 粗体
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 斜体
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # 行内代码
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # 链接
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    return text


def md_to_html(md_text: str) -> str:
    """将 Markdown 文本转为 HTML（不处理章节标题）"""
    lines = md_text.split('\n')
    html_parts = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 空行
        if not stripped:
            i += 1
            continue

        # HTML 注释
        if stripped.startswith('<!--'):
            # 跳过注释块（可能跨行）
            while i < len(lines) and '-->' not in lines[i]:
                i += 1
            i += 1
            continue

        # 已有 HTML 标签（直接透传）
        if stripped.startswith('<'):
            # 收集连续 HTML 行
            html_block = []
            while i < len(lines) and (lines[i].strip().startswith('<') or not lines[i].strip()):
                html_block.append(lines[i])
                i += 1
            html_parts.append('\n'.join(html_block))
            continue

        # 表格
        if '|' in stripped and stripped.count('|') >= 2:
            table_lines = []
            while i < len(lines) and '|' in lines[i] and lines[i].strip().count('|') >= 2:
                table_lines.append(lines[i])
                i += 1
            html_parts.append(md_table_to_html(table_lines))
            continue

        # 标题（h2-h4，h1 由章节包裹处理）
        if stripped.startswith('#### '):
            html_parts.append(f'<h4>{inline_md_to_html(stripped[5:])}</h4>')
            i += 1
            continue
        if stripped.startswith('### '):
            html_parts.append(f'<h3>{inline_md_to_html(stripped[4:])}</h3>')
            i += 1
            continue
        if stripped.startswith('## '):
            html_parts.append(f'<h2>{inline_md_to_html(stripped[3:])}</h2>')
            i += 1
            continue

        # 引用块
        if stripped.startswith('> '):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('> '):
                quote_lines.append(lines[i].strip()[2:])
                i += 1
            quote_html = ''.join(f'<p>{inline_md_to_html(q)}</p>' for q in quote_lines)
            html_parts.append(f'<blockquote>{quote_html}</blockquote>')
            continue

        # 代码块
        if stripped.startswith('```'):
            code_lines = []
            lang = stripped[3:].strip()
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code_text = '\n'.join(code_lines)
            html_parts.append(f'<pre><code>{code_text}</code></pre>')
            continue

        # 无序列表
        if stripped.startswith('- ') or stripped.startswith('* '):
            list_items = []
            while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('* ')):
                item_text = lines[i].strip()[2:]
                list_items.append(f'<li>{inline_md_to_html(item_text)}</li>')
                i += 1
            html_parts.append('<ul>\n' + '\n'.join(list_items) + '\n</ul>')
            continue

        # 有序列表
        if re.match(r'^\d+\.\s', stripped):
            list_items = []
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                item_text = re.sub(r'^\d+\.\s', '', lines[i].strip())
                list_items.append(f'<li>{inline_md_to_html(item_text)}</li>')
                i += 1
            html_parts.append('<ol>\n' + '\n'.join(list_items) + '\n</ol>')
            continue

        # 水平线
        if stripped == '---' or stripped == '***' or stripped == '___':
            html_parts.append('<hr>')
            i += 1
            continue

        # 普通段落
        html_parts.append(f'<p>{inline_md_to_html(stripped)}</p>')
        i += 1

    return '\n'.join(html_parts)


# ============================================================
# 章节拆分与 TOC 生成
# ============================================================
def split_chapters(md_text: str) -> list[tuple[str, str]]:
    """
    按 ## 第X章 或 ## 第一章 拆分章节
    返回 [(标题, 内容md), ...]
    """
    chapters = []
    # 匹配 ## 第X章 或 ## 第一章 模式
    # 也匹配 ## 附录 等特殊章节
    pattern = re.compile(r'^## (第[一二三四五六七八九十\d]+章[：:].+|附录[：:].+)', re.MULTILINE)
    matches = list(pattern.finditer(md_text))

    if not matches:
        # 没有章节标题，整篇作为一个章节
        return [('报告正文', md_text)]

    # 封面部分（第一个 ## 之前的内容）跳过
    for idx, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(md_text)
        content = md_text[start:end].strip()
        chapters.append((title, content))

    return chapters


def chapter_title_to_toc(title: str, index: int) -> tuple[str, str]:
    """
    章节标题 → TOC 编号和标题
    返回 (num, title)
    """
    # 尝试提取 "第X章" 中的编号
    m = re.match(r'第(\d+)章[：:]\s*(.+)', title)
    if m:
        return (m.group(1), m.group(2).strip())

    # 中文数字
    cn_map = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
              '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
    m = re.match(r'第([一二三四五六七八九十]+)章[：:]\s*(.+)', title)
    if m:
        cn = m.group(1)
        num = cn_map.get(cn, str(index))
        return (num, m.group(2).strip())

    # 附录
    if title.startswith('附录'):
        m = re.match(r'附录[：:]\s*(.+)', title)
        if m:
            return ('附', m.group(1).strip())
        return ('附', title)

    return (str(index), title)


def generate_toc(chapters: list[tuple[str, str]]) -> str:
    """生成 TOC HTML"""
    toc_items = []
    for idx, (title, _) in enumerate(chapters, 1):
        num, toc_title = chapter_title_to_toc(title, idx)
        toc_items.append(
            f'<div class="toc-item"><span class="toc-num">{num}</span>'
            f'<span class="toc-title">{inline_md_to_html(toc_title)}</span></div>'
        )
    return '\n    '.join(toc_items)


def generate_chapters_html(chapters: list[tuple[str, str]]) -> str:
    """生成章节 HTML"""
    parts = []
    for title, content in chapters:
        chapter_html = md_to_html(content)
        parts.append(
            f'<div class="chapter page-break">\n'
            f'<h1>{inline_md_to_html(title)}</h1>\n'
            f'{chapter_html}\n'
            f'</div>'
        )
    return '\n\n'.join(parts)


# ============================================================
# 封面元数据
# ============================================================
def extract_rating_short(conclusion: str) -> str:
    """从结论文本提取简短评级标签"""
    if not conclusion or conclusion == '待评估':
        return '待评估'
    # 优先匹配更具体的
    if '拒绝' in conclusion or '不推荐' in conclusion or 'Stop' in conclusion:
        return '🛑 Stop'
    if '附条件' in conclusion or 'Conditional' in conclusion:
        return '⚠️ Cond'
    if '推荐' in conclusion or 'Go' in conclusion:
        return '✅ Go'
    # 默认截取前6个字
    return conclusion[:6]

def extract_rating_full(conclusion: str) -> str:
    """从结论文本提取完整评级描述"""
    if not conclusion or conclusion == '待评估':
        return '待评估'
    # 取破折号前的部分作为评级
    if '—' in conclusion:
        return conclusion.split('—')[0].strip()
    if '—' in conclusion:
        return conclusion.split('—')[0].strip()
    if '-' in conclusion:
        return conclusion.split('-')[0].strip()
    return conclusion

def load_cover_metadata(state: dict) -> dict:
    """从 state.json 提取封面 token"""
    conclusion = state.get('conclusion', '待评估')
    rating_short = extract_rating_short(conclusion)
    rating_full = extract_rating_full(conclusion)

    return {
        '{{TITLE}}': f"{state.get('displayName', '未知')} — CMS投前评估报告",
        '{{PRODUCT_DISPLAY}}': state.get('displayName', '未知'),
        '{{BUSINESS_ENTITY}}': state.get('businessEntity', '待确认'),
        '{{CASE_CODE}}': state.get('caseCode', '未知'),
        '{{SKILL}}': state.get('routedSkill', '待路由'),
        '{{DATE}}': datetime.now().strftime('%Y-%m-%d'),
        '{{RATING}}': rating_full,
        '{{RATING_SHORT}}': rating_short,
    }


# ============================================================
# 主流程
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("用法: python3 cms-report-to-html.py <品种目录> [--upload] [--doc-id DOC_ID]")
        sys.exit(1)

    case_dir = Path(sys.argv[1]).resolve()
    do_upload = '--upload' in sys.argv
    doc_id = None
    if '--doc-id' in sys.argv:
        idx = sys.argv.index('--doc-id')
        if idx + 1 < len(sys.argv):
            doc_id = sys.argv[idx + 1]

    print(f"=== CMS 报告 HTML 生成 ===")
    print(f"品种目录: {case_dir}")

    # 1. 读取 state.json
    state_path = case_dir / 'state.json'
    if not state_path.exists():
        print(f"错误: state.json 不存在于 {case_dir}")
        sys.exit(1)

    with open(state_path, 'r') as f:
        state = json.load(f)
    print(f"品种: {state.get('displayName', '未知')}")

    # 2. 读取 markdown 报告
    report_md_path = case_dir / '04-final-report.md'
    if not report_md_path.exists():
        print(f"错误: 04-final-report.md 不存在于 {case_dir}")
        sys.exit(1)

    with open(report_md_path, 'r') as f:
        md_text = f.read()
    print(f"报告行数: {len(md_text.splitlines())}")

    # 3. 拆分章节
    chapters = split_chapters(md_text)
    print(f"章节数: {len(chapters)}")
    for title, _ in chapters:
        print(f"  - {title}")

    # 4. 生成 TOC
    toc_html = generate_toc(chapters)
    print(f"TOC 条目数: {len(chapters)}")

    # 5. 生成章节 HTML
    chapters_html = generate_chapters_html(chapters)

    # 6. 加载 skeleton
    if not SKELETON_PATH.exists():
        print(f"错误: skeleton-cms.html 不存在于 {TEMPLATES_DIR}")
        sys.exit(1)

    with open(SKELETON_PATH, 'r') as f:
        html = f.read()

    # 7. 替换 CSS 变量（从 amber.yml）
    css_tokens = load_css_vars(AMBER_YML_PATH)
    for token, val in css_tokens.items():
        html = html.replace(token, val)
    print(f"CSS token 替换: {len(css_tokens)} 个")

    # 8. 替换封面元数据
    cover_tokens = load_cover_metadata(state)
    for token, val in cover_tokens.items():
        html = html.replace(token, val)
    print(f"封面 token 替换: {len(cover_tokens)} 个")

    # 9. 替换 TOC 和章节
    html = html.replace('{{TOC_ITEMS}}', toc_html)
    html = html.replace('{{CHAPTERS}}', chapters_html)

    # 10. 验证零残留
    residual = re.findall(r'\{\{[A-Z_-]+\}\}', html)
    if residual:
        print(f"⚠️ 残留 token ({len(residual)} 个): {residual}")
        # 不退出，只警告
    else:
        print("✅ 零残留 token")

    # 11. 输出
    output_path = case_dir / 'REPORT.html'
    with open(output_path, 'w') as f:
        f.write(html)
    print(f"✅ HTML 已生成: {output_path}")
    print(f"   文件大小: {output_path.stat().st_size / 1024:.1f} KB")

    # 12. 可选上传
    if do_upload:
        upload_path = output_path
        if doc_id:
            cmd = ['curl', '-s', '-X', 'PUT',
                   f'https://doc.20100706.xyz/api/{doc_id}',
                   '-F', f'file=@{upload_path};filename=cms-report-amber.html']
            print(f"更新文档 (doc_id={doc_id})...")
        else:
            cmd = ['curl', '-s', '-X', 'POST',
                   'https://doc.20100706.xyz/upload',
                   '-F', f'file=@{upload_path};filename=cms-report-amber.html']
            print("上传新文档...")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                resp = json.loads(result.stdout)
                new_doc_id = resp.get('id', resp.get('doc_id', ''))
                raw_url = resp.get('raw_url', f'https://doc.20100706.xyz/raw/{new_doc_id}')
                view_url = resp.get('view_url', f'https://doc.20100706.xyz/view/{new_doc_id}')
                print(f"✅ 上传成功!")
                print(f"   Raw URL: {raw_url}")
                print(f"   View URL: {view_url}")
                print(f"   Doc ID: {new_doc_id}")

                # 更新 state.json
                if new_doc_id:
                    state['reportHtmlUrl'] = raw_url
                    state['reportViewUrl'] = view_url
                    state['htmlReportId'] = new_doc_id
                    with open(state_path, 'w') as f:
                        json.dump(state, f, ensure_ascii=False, indent=2)
                    print(f"   state.json 已更新")
            except json.JSONDecodeError:
                print(f"上传响应: {result.stdout[:200]}")
        else:
            print(f"❌ 上传失败: {result.stderr}")

    print("\n=== 生成完成 ===")


if __name__ == '__main__':
    main()
