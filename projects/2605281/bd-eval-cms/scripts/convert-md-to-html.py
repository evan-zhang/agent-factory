#!/usr/bin/env python3
"""
CMS 投前评估报告 Markdown → HTML 转换器
使用风格 12（CMS Eval）骨架 + 配色方案

用法：python3 convert-md-to-html.py <报告目录> <配色名> [输出路径]
示例：python3 convert-md-to-html.py /path/to/MB-001-Mage-Biologics mckinsey-navy
"""
import sys, os, re, json
import markdown
from pathlib import Path

def find_style_dir():
    """查找风格12模板目录（优先本地，其次 doc-viewer skill）"""
    script_dir = Path(__file__).parent
    # 优先：scripts/style-12/（skill 自包含）
    local = script_dir / "style-12"
    if (local / "skeleton.html").exists():
        return local
    # 其次：doc-viewer/templates/style-12/
    doc_viewer = Path.home() / ".agents/skills/doc-viewer/templates/style-12"
    if (doc_viewer / "skeleton.html").exists():
        return doc_viewer
    print("❌ 找不到风格12模板目录")
    sys.exit(1)

STYLE_DIR = find_style_dir()

def load_color_theme(theme_name):
    """加载配色方案 yml 文件"""
    theme_path = STYLE_DIR / "color-themes" / f"{theme_name}.yml"
    if not theme_path.exists():
        print(f"❌ 配色文件不存在: {theme_path}")
        sys.exit(1)
    with open(theme_path) as f:
        # 跳过 YAML front matter 中的 description
        content = f.read()
    # 解析 YAML
    theme = {}
    in_tokens = False
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('---') or line.startswith('name:') or line.startswith('label:') or line.startswith('description:') or line.startswith('note:'):
            if line == '---':
                continue
            continue
        if ':' in line and not line.startswith('-'):
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                theme[key] = val
    return theme

def load_skeleton():
    """加载骨架模板"""
    script_dir = Path(__file__).parent
    skeleton_path = STYLE_DIR / "skeleton.html"
    with open(skeleton_path) as f:
        return f.read()

def replace_tokens(html, theme):
    """替换所有 {{TOKEN}} 占位符"""
    def replacer(match):
        token = match.group(1)
        if token in theme:
            return theme[token]
        # 未知 token 保留原样
        print(f"⚠ 未找到 token: {token}")
        return match.group(0)
    return re.sub(r'\{\{([^}]+)\}\}', replacer, html)

def load_state(report_dir):
    """加载 state.json 获取封面元信息"""
    state_path = Path(report_dir) / "state.json"
    if state_path.exists():
        with open(state_path) as f:
            return json.load(f)
    return {}

def extract_cover_info(report_dir, state, md_content):
    """从 state.json 和 Markdown 内容提取封面信息"""
    case_code = state.get('case_code', '')
    skill_code = state.get('skill_code', '')
    business_unit = state.get('business_entity', '')
    date = state.get('evaluation_date', '')

    # 从 Markdown 头部元信息提取
    product_code = ''
    product_name = ''
    company_name = ''

    for line in md_content.split('\n')[:20]:
        if '评估品种' in line and '：' in line:
            # **评估品种**：MB-001 (Mage Biologics)
            val = line.split('：', 1)[-1].strip()
            product_code = val
            # 同时作为产品名
            product_name = val
        if '评估日期' in line and '：' in line:
            date = date or line.split('：', 1)[-1].strip()

    if not product_code:
        product_code = state.get('species_id', 'MB-001')
        product_name = product_code

    # 从 discovery 章节提取公司名
    disc_match = re.search(r'\*\*原研公司\*\*[：:]\s*(.+)', md_content)
    if disc_match:
        company_name = disc_match.group(1).strip()
        # 去掉 Markdown 加粗标记
        company_name = re.sub(r'\*+', '', company_name)

    # 评级
    rating = ''
    rating_short = ''
    summary_match = re.search(r'综合评估结论(.*?)(?=\n##|\Z)', md_content, re.DOTALL)
    if summary_match:
        summary_text = summary_match.group(1)
        if '停止' in summary_text or '不推荐' in summary_text:
            rating = '停止（STOP）'
            rating_short = 'STOP'
        elif '条件通过' in summary_text or '附条件' in summary_text:
            rating = '条件通过（CONDITIONAL）'
            rating_short = 'COND'
        elif '通过' in summary_text:
            rating = '通过（PASS）'
            rating_short = 'PASS'

    if not rating:
        rating = '条件通过（CONDITIONAL）'
        rating_short = 'COND'

    return {
        'TITLE': f'{product_code} CMS投前评估报告',
        'PRODUCT_CODE': product_code or 'MB-001',
        'PRODUCT_EN': product_name or 'Mage Biologics',
        'PRODUCT_CN': '',
        'COMPANY_NAME': company_name or 'Mage Biologics Inc.',
        'CASE_CODE': case_code or '2605-3001',
        'SKILL_CODE': skill_code or 'A-1',
        'BUSINESS_UNIT': business_unit or '深康',
        'DATE': date or '2026-05-30',
        'RATING': rating,
        'RATING_SHORT': rating_short,
    }

def convert_gate_cards(html_content):
    """识别 Markdown 中的结论卡并转换为 HTML gate-card 组件"""
    # Gate 结论卡模式：## Gate N 结论卡 后跟内容
    pattern = r'## Gate (\d+) 结论卡\n(.*?)(?=\n## |\Z)'

    def gate_card_replacer(match):
        gate_num = match.group(1)
        content = match.group(2).strip()

        # 判定状态
        status = 'conditional'  # 默认
        if '停止' in content or '未达标' in content or 'STOP' in content:
            status = 'stop'
        elif '条件通过' in content or '附条件' in content or 'CONDITIONAL' in content:
            status = 'conditional'
        elif '通过' in content and '条件' not in content:
            status = 'pass'

        status_label = {'pass': '通过', 'conditional': '条件通过', 'stop': '未达标/停止'}[status]

        # 转换内容中的 Markdown 表格为 HTML
        content_html = md_to_html_basic(content)

        return f'''<div class="gate-card gate-{status}">
  <div class="gate-title">Gate {gate_num} 结论卡</div>
  <div class="gate-label">结论：{status_label}</div>
  <div class="gate-body">{content_html}</div>
</div>'''

    return re.sub(pattern, gate_card_replacer, html_content, flags=re.DOTALL)

def convert_battle_sections(html_content):
    """识别 Battle 对抗审查段落"""
    # 审查层
    html_content = re.sub(
        r'### BATTLE-R1-AUDITOR\n(.*?)(?=\n### BATTLE|\n## 第|\Z)',
        lambda m: f'<div class="battle-auditor"><h3>审查层异议清单</h3>{md_to_html_basic(m.group(1))}</div>',
        html_content, flags=re.DOTALL
    )
    # 执行层
    html_content = re.sub(
        r'### BATTLE-R1-EXECUTOR\n(.*?)(?=\n## 第|\n## 附录|\Z)',
        lambda m: f'<div class="battle-executor"><h3>执行层逐条回应</h3>{md_to_html_basic(m.group(1))}</div>',
        html_content, flags=re.DOTALL
    )
    return html_content

def convert_conflict_boxes(html_content):
    """识别信息冲突标记（支持 blockquote 和行内两种格式）"""
    # blockquote 格式：> ⚠ **信息冲突**：...
    html_content = re.sub(
        r'>\s*⚠\s*\*\*信息冲突\*\*[：:]\s*(.+?)(?=\n(?!>)|\n##|\Z)',
        lambda m: f'<div class="conflict-box">⚠ 信息冲突：{m.group(1).strip()}</div>',
        html_content, flags=re.DOTALL
    )
    # 行内格式：**信息冲突**：...
    html_content = re.sub(
        r'\*\*信息冲突\*\*[：:]\s*(.+?)(?=\n\n|\n##|\Z)',
        lambda m: f'<div class="conflict-box">⚠ 信息冲突：{m.group(1)}</div>',
        html_content, flags=re.DOTALL
    )
    return html_content

def convert_highlight_boxes(html_content):
    """识别核心结论框标记，转为 highlight-box 组件。
    
    匹配格式：> **核心结论**：...
    """
    html_content = re.sub(
        r'>\s*\*\*核心结论\*\*[：:]\s*(.+?)(?=\n(?!>)|\n##|\Z)',
        lambda m: f'<div class="highlight-box"><p><strong>核心结论：</strong>{m.group(1).strip()}</p></div>',
        html_content, flags=re.DOTALL
    )
    return html_content

def convert_gate_boxes(html_content):
    """识别新版 blockquote 格式的 Gate 结论卡，转为 gate-box 组件。
    
    支持两种格式：
    1. blockquote 格式（新版）：
       > **【Gate N：XXX门】**
       > 结论：通过 / 条件通过 / 停止
       > ...
    2. 旧版格式：由 convert_gate_cards 处理
    """
    # 匹配 blockquote 中的 Gate 结论卡
    # Markdown blockquote 转换后可能已经是 <blockquote> 或仍是 > 行
    # 此函数在 markdown 解析前工作，匹配原始 > 开头的行
    pattern = (
        r'(?:^>\s*\*\*【Gate\s*(\d+)[:：]\s*(.+?)】\*\*\s*\n)'
        r'((?:>\s*.*\n?)*)'
    )

    def gate_box_replacer(match):
        gate_num = match.group(1)
        gate_name = match.group(2).strip()
        body_lines = match.group(3)

        # 解析 body 行（去掉 > 前缀）
        lines = []
        for line in body_lines.strip().split('\n'):
            line = re.sub(r'^>\s*', '', line).strip()
            if line:
                lines.append(line)

        body_html = ''
        for line in lines:
            # 结论行：转换为 conclusion-tag
            concl_match = re.match(r'(?:\*\*)?结论(?:\*\*)?[：:]\s*(.+)', line)
            if concl_match:
                concl_text = concl_match.group(1).strip()
                concl_html = _convert_conclusion_tag(concl_text)
                body_html += f'<p><strong>结论：</strong>{concl_html}</p>\n'
            else:
                # 其他行：基础 markdown 转换
                line_html = md_to_html_basic(line)
                body_html += line_html + '\n'

        return (
            f'<div class="gate-box">\n'
            f'  <div class="gate-title">Gate {gate_num}：{gate_name}</div>\n'
            f'  {body_html}'
            f'</div>'
        )

    return re.sub(pattern, gate_box_replacer, html_content, flags=re.MULTILINE)

def _convert_conclusion_tag(text):
    """将结论文本转为 conclusion-tag span。"""
    text = text.strip()
    # 去掉可能的 markdown 加粗
    text = re.sub(r'\*+', '', text)
    # 匹配各种结论格式
    if re.search(r'[✅✔✓]|通过', text) and not re.search(r'条件', text):
        label = re.sub(r'[✅✔✓]\s*', '', text).strip() or '通过'
        return f'<span class="conclusion-tag pass">{label}</span>'
    elif re.search(r'[⚠⚠️]|条件通过', text):
        label = re.sub(r'[⚠⚠️]\s*', '', text).strip() or '条件通过'
        return f'<span class="conclusion-tag conditional">{label}</span>'
    elif re.search(r'[❌✖]|停止', text):
        label = re.sub(r'[❌✖]\s*', '', text).strip() or '停止'
        return f'<span class="conclusion-tag stop">{label}</span>'
    elif re.search(r'[⏳⏸]|待验证', text):
        label = re.sub(r'[⏳⏸]\s*', '', text).strip() or '待验证'
        return f'<span class="conclusion-tag pending">{label}</span>'
    else:
        # 无法识别的结论文本，根据关键词猜测
        if '通过' in text and '条件' not in text:
            return f'<span class="conclusion-tag pass">{text}</span>'
        elif '条件' in text or '附条件' in text:
            return f'<span class="conclusion-tag conditional">{text}</span>'
        elif '停止' in text or '不推荐' in text:
            return f'<span class="conclusion-tag stop">{text}</span>'
        else:
            return f'<span class="conclusion-tag pending">{text}</span>'

def convert_conclusion_tags_in_html(html_content):
    """在已转换为 HTML 的内容中，查找结论行中的结论文本并转为 conclusion-tag。
    
    处理 convert_gate_cards（旧版 Gate 结论卡）中的结论标签行。
    """
    # 匹配旧版 gate-card 中的结论标签行
    # 格式如: <div class="gate-label">结论：通过</div>
    # 或: 结论：✅通过 / 结论：⚠条件通过 / 结论：❌停止 / 结论：⏳待验证
    def tag_replacer(match):
        prefix = match.group(1)  # 结论：
        text = match.group(2).strip()
        tag_html = _convert_conclusion_tag(text)
        return f'{prefix}{tag_html}'

    # 在 gate-label div 内替换
    html_content = re.sub(
        r'(结论[：:])\s*([^<]+?)(?=</div>)',
        tag_replacer,
        html_content
    )
    return html_content

def convert_red_flags(html_content):
    """识别红旗标记，转为 red-flag 组件。
    
    支持格式：
    > 🚩 **红旗**：...
    > 🚩 **最高优先级红旗**：...
    """
    # 匹配 blockquote 中的红旗标记
    # > 🚩 **红旗**：... 或 > 🚩 **最高优先级红旗**：...
    # 第一行：捕获标题和首行内容
    # 后续行：以 > 开头但不以 🚩 开头的续行
    first_line_pat = r'^>\s*🚩\s*\*\*(.+?)\*\*[：:]\s*(.+)'  
    continuation_pat = r'((?:\n>\s*(?!🚩).*)*)'
    pattern = first_line_pat + continuation_pat

    def red_flag_replacer(match):
        flag_title = match.group(1).strip()
        first_line = match.group(2).strip()
        rest_lines = match.group(3) if match.lastindex and match.lastindex >= 3 else ''

        # 收集续行
        lines = [first_line]
        if rest_lines:
            for line in rest_lines.strip().split('\n'):
                line = re.sub(r'^>\s*', '', line).strip()
                if line:
                    lines.append(line)

        body = ' '.join(lines)
        # 基础 markdown 转换
        body_html = md_to_html_basic(body)

        return (
            f'<div class="red-flag">\n'
            f'  <p><strong>🚩 {flag_title}：</strong>{body_html}</p>\n'
            f'</div>'
        )

    html_content = re.sub(pattern, red_flag_replacer, html_content, flags=re.MULTILINE)

    # 也处理非 blockquote 格式（行内红旗）
    # 🚩 **红旗**：... 或 🚩 **最高优先级红旗**：...
    html_content = re.sub(
        r'🚩\s*\*\*(.+?)\*\*[：:]\s*(.+?)(?=\n\n|\n##|\n>|\Z)',
        lambda m: f'<div class="red-flag">\n  <p><strong>🚩 {m.group(1).strip()}：</strong>{m.group(2).strip()}</p>\n</div>',
        html_content, flags=re.DOTALL
    )

    return html_content

def convert_veto_boxes(html_content):
    """识别一票否决标记"""
    html_content = re.sub(
        r'## (?:一票否决|否决核查)\n(.*?)(?=\n## |\Z)',
        lambda m: f'<div class="veto-box"><strong>一票否决核查</strong>{md_to_html_basic(m.group(1))}</div>',
        html_content, flags=re.DOTALL
    )
    return html_content

def convert_stage_tags(html_content):
    """转换阶段标签"""
    html_content = html_content.replace('[阶段A]', '<span class="stage-tag stage-a">阶段A</span>')
    html_content = html_content.replace('[阶段B]', '<span class="stage-tag stage-b">阶段B</span>')
    return html_content

def convert_confidence_badges(html_content):
    """转换置信度标注"""
    html_content = re.sub(r'\[A级[‑\-]([^\]]+)\]', r'<span class="confidence-badge conf-a">A-\1</span>', html_content)
    html_content = re.sub(r'\[B级[‑\-]([^\]]+)\]', r'<span class="confidence-badge conf-b">B-\1</span>', html_content)
    html_content = re.sub(r'\[C级[‑\-]([^\]]+)\]', r'<span class="confidence-badge conf-c">C-\1</span>', html_content)
    html_content = re.sub(r'\[D级[‑\-]([^\]]+)\]', r'<span class="confidence-badge conf-d">D-\1</span>', html_content)
    return html_content

def md_to_html_basic(text):
    """基础 Markdown → HTML 转换（用于组件内部）"""
    # 表格
    text = convert_md_tables(text)
    # 加粗
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 斜体
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # 列表
    lines = text.split('\n')
    in_list = False
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{stripped[2:]}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            if stripped:
                result.append(f'<p>{stripped}</p>')
    if in_list:
        result.append('</ul>')
    return '\n'.join(result)

def convert_md_tables(text):
    """将 Markdown 表格转为 HTML 表格"""
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if '|' in line and line.startswith('|'):
            # 收集连续的表格行
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                stripped = lines[i].strip()
                # 跳过分隔行
                if re.match(r'^\|[\s\-:|]+\|$', stripped):
                    i += 1
                    continue
                table_lines.append(stripped)
                i += 1

            if table_lines:
                html = '<div class="table-wrap"><table>\n'
                for idx, tl in enumerate(table_lines):
                    cells = [c.strip() for c in tl.split('|')[1:-1]]
                    tag = 'th' if idx == 0 else 'td'
                    html += '<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>\n'
                html += '</table></div>'
                result.append(html)
        else:
            result.append(lines[i])
            i += 1
    return '\n'.join(result)

def convert_chapters(md_content):
    """将 Markdown 章节转为 HTML 章节并生成目录"""
    lines = md_content.split('\n')
    chapters_html = []
    toc_items = []
    current_chapter = []
    chapter_num = 0
    in_cover_meta = True
    cover_meta_lines = []

    for line in lines:
        # 跳过封面元信息区域（到第一个章节标题之前的内容）
        if in_cover_meta:
            if re.match(r'^## 第[一二三四五六七八九十\d]+章', line):
                in_cover_meta = False
                # 不 continue，继续处理这一行
            else:
                continue

        # 跳过分隔线
        if line.strip() == '---':
            continue

        # 匹配章节标题（支持中文数字和阿拉伯数字）
        ch_match = re.match(r'^## 第([一二三四五六七八九十\d]+)章[：:]\s*(.+)', line)
        if ch_match:
            # 保存上一章
            if current_chapter:
                chapters_html.append(convert_chapter_content('\n'.join(current_chapter)))
                chapters_html.append('</div>')
                current_chapter = []

            chapter_num += 1
            ch_num_str = ch_match.group(1)
            ch_title = ch_match.group(2)

            # 统一章节编号
            cn_num_map = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
                         '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
            num = cn_num_map.get(ch_num_str, ch_num_str)

            chapters_html.append(f'<div class="chapter"><h1>第{num}章 {ch_title}</h1>')
            toc_items.append(f'<div class="toc-item"><span class="toc-num">第{num}章</span><span class="toc-title">{ch_title}</span></div>')
        else:
            current_chapter.append(line)

    # 最后一章
    if current_chapter:
        chapters_html.append(convert_chapter_content('\n'.join(current_chapter)))
        chapters_html.append('</div>')

    return '\n'.join(chapters_html), '\n'.join(toc_items)

def convert_chapter_content(text):
    """转换单个章节内容"""
    # 先处理特殊组件（这些会生成 HTML div，后续不再处理）
    text = convert_gate_cards(text)
    text = convert_gate_boxes(text)       # 新版 blockquote Gate 结论卡
    text = convert_battle_sections(text)
    text = convert_conflict_boxes(text)
    text = convert_highlight_boxes(text)  # 核心结论框
    text = convert_red_flags(text)        # 红旗框
    text = convert_veto_boxes(text)
    text = convert_stage_tags(text)
    text = convert_confidence_badges(text)

    # 表格转换
    text = convert_md_tables(text)

    # 标题转换（h2, h3, h4）— 注意避开已转换的 HTML
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    # h2: 只匹配纯 Markdown 行（不以 < 开头的）
    text = re.sub(r'^## ((?!<).+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)

    # 加粗和斜体
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    # 处理 HTML 注释占位符
    text = re.sub(r'<!-- EXECUTIVE_SUMMARY_PLACEHOLDER -->',
                  '<div class="neutral-review"><p>（执行摘要将在所有 Gate 评估完成后由 AI 根据结论卡生成）</p></div>',
                  text)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # 段落和列表处理
    lines = text.split('\n')
    result = []
    in_list = False
    list_tag = 'ul'

    for line in lines:
        stripped = line.strip()

        # 跳过已经是 HTML 标签的行
        if stripped.startswith('<'):
            if in_list:
                result.append(f'</{list_tag}>')
                in_list = False
            result.append(stripped)
            continue

        # 空行
        if not stripped:
            if in_list:
                result.append(f'</{list_tag}>')
                in_list = False
            continue

        # 无序列表
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list or list_tag != 'ul':
                if in_list:
                    result.append(f'</{list_tag}>')
                result.append('<ul>')
                in_list = True
                list_tag = 'ul'
            result.append(f'<li>{stripped[2:]}</li>')
            continue

        # 编号列表
        num_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if num_match:
            if not in_list or list_tag != 'ol':
                if in_list:
                    result.append(f'</{list_tag}>')
                result.append('<ol>')
                in_list = True
                list_tag = 'ol'
            result.append(f'<li>{num_match.group(2)}</li>')
            continue

        if in_list:
            result.append(f'</{list_tag}>')
            in_list = False

        # 普通段落
        if not stripped.startswith('#'):
            result.append(f'<p>{stripped}</p>')

    if in_list:
        result.append(f'</{list_tag}>')

    return '\n'.join(result)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 convert-md-to-html.py <报告目录> [配色名] [输出路径]")
        print("示例: python3 convert-md-to-html.py ./MB-001-Mage-Biologics mckinsey-navy /tmp/report.html")
        sys.exit(1)

    report_dir = Path(sys.argv[1])
    theme_name = sys.argv[2] if len(sys.argv) > 2 else 'mckinsey-navy'
    output_path = sys.argv[3] if len(sys.argv) > 3 else report_dir / 'REPORT.html'

    # 读取报告
    report_path = report_dir / '04-final-report.md'
    if not report_path.exists():
        print(f"❌ 报告不存在: {report_path}")
        sys.exit(1)

    with open(report_path) as f:
        md_content = f.read()

    print(f"📄 报告: {report_path} ({len(md_content.splitlines())} 行)")

    # 加载骨架和配色
    skeleton = load_skeleton()
    theme = load_color_theme(theme_name)
    state = load_state(report_dir)

    print(f"🎨 配色: {theme_name} ({len(theme)} tokens)")
    print(f"🦴 骨架: {len(skeleton)} 字符")

    # 替换 CSS token
    html = replace_tokens(skeleton, theme)

    # 提取封面信息并替换
    cover = extract_cover_info(report_dir, state, md_content)
    for key, val in cover.items():
        html = html.replace(f'{{{{{key}}}}}', val)

    # 转换章节内容
    chapters_html, toc_items = convert_chapters(md_content)

    # 替换内容占位符
    html = html.replace('{{TOC_ITEMS}}', toc_items)
    html = html.replace('{{CHAPTERS}}', chapters_html)

    # 验证
    remaining = re.findall(r'\{\{[^}]+\}\}', html)
    if remaining:
        print(f"⚠ 未替换的占位符: {len(remaining)}")
        for r in set(remaining):
            print(f"  - {r}")
    else:
        print("✅ 所有占位符已替换")

    # 写入文件
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"📦 输出: {output_path} ({len(html.splitlines())} 行, {len(html):,} 字节)")

if __name__ == '__main__':
    main()
