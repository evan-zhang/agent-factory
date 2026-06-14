#!/usr/bin/env python3
"""
CMS BD 通用模板内核 Style A1 渲染器
v0.9.3 起收敛为单一 A-1 profile（覆盖历史 A-1/A-5/A-7 全部业务场景）

用法：python3 render.py <报告目录> [配色名] [输出路径] [profile]
示例：python3 render.py /path/to/MB-001-Mage-Biologics mckinsey-navy /tmp/report.html A-1
向后兼容：python3 render.py /path/to/MB-001-Mage-Biologics mckinsey-navy /tmp/report.html
       （省略 profile 参数时默认 A-1）
"""

import sys
import os
import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

def load_registry():
    """加载 profile registry"""
    script_dir = Path(__file__).parent
    registry_path = script_dir / "profiles" / "registry.json"

    if not registry_path.exists():
        print(f"❌ Registry 不存在: {registry_path}")
        sys.exit(1)

    with open(registry_path) as f:
        return json.load(f)

def load_schema():
    """加载 profile schema"""
    script_dir = Path(__file__).parent
    schema_path = script_dir / "profiles" / "schema.json"

    if not schema_path.exists():
        print(f"❌ Schema 不存在: {schema_path}")
        sys.exit(1)

    with open(schema_path) as f:
        return json.load(f)

def validate_profile_schema(profile_data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """轻量级 profile schema 校验

    返回: (是否有效, 错误列表)
    """
    errors = []

    # 基本字段检查
    if 'version' not in profile_data:
        errors.append("缺少 version 字段")
    elif profile_data['version'] != '0.9.1':
        errors.append(f"版本不匹配: {profile_data.get('version', 'missing')}，要求 0.9.1")

    if 'profile_type' not in profile_data:
        errors.append("缺少 profile_type 字段")
    elif profile_data['profile_type'] not in ['common', 'skill']:
        errors.append(f"无效的 profile_type: {profile_data['profile_type']}")

    # required_components 检查
    if 'required_components' not in profile_data:
        errors.append("缺少 required_components 字段")
    elif not isinstance(profile_data['required_components'], dict):
        errors.append("required_components 必须是对象")

    # coverage_requirements 检查
    if 'coverage_requirements' not in profile_data:
        errors.append("缺少 coverage_requirements 字段")
    else:
        coverage = profile_data['coverage_requirements']
        if 'minimum_coverage' not in coverage:
            errors.append("coverage_requirements 缺少 minimum_coverage")
        elif not isinstance(coverage['minimum_coverage'], int) or not (0 <= coverage['minimum_coverage'] <= 100):
            errors.append("minimum_coverage 必须是 0-100 之间的整数")

    # skill profile 特定检查
    if profile_data.get('profile_type') == 'skill':
        if 'skill_code' not in profile_data:
            errors.append("skill profile 缺少 skill_code 字段")
        if 'skill_name' not in profile_data:
            errors.append("skill profile 缺少 skill_name 字段")
        if 'extends' not in profile_data:
            errors.append("skill profile 缺少 extends 字段")
        elif profile_data['extends'] != 'common':
            errors.append(f"extends 必须是 'common'，当前为: {profile_data.get('extends')}")

    return len(errors) == 0, errors

def validate_profile_registration(profile_code: str, registry: Dict[str, Any]) -> Tuple[bool, Optional[str], List[str]]:
    """验证 profile 是否已注册且为 active 状态

    返回: (是否有效, 状态描述, 错误列表)
    """
    errors = []

    if 'profiles' not in registry:
        errors.append("Registry 缺少 profiles 字段")
        return False, None, errors

    profiles = registry['profiles']

    if profile_code not in profiles:
        # 检查是否在 planned_profiles 中
        planned = registry.get('planned_profiles', {})
        if profile_code in planned:
            errors.append(f"Profile '{profile_code}' 已规划但未实现")
            return False, 'planned', errors
        else:
            errors.append(f"Profile '{profile_code}' 未注册")
            # 提供候选 active profiles
            active_profiles = [k for k, v in profiles.items() if v.get('status') == 'active']
            if active_profiles:
                errors.append(f"可用的 active profiles: {', '.join(active_profiles)}")
            return False, 'unregistered', errors

    profile_info = profiles[profile_code]
    status = profile_info.get('status', '')

    if status != 'active':
        errors.append(f"Profile '{profile_code}' 状态为 '{status}'，要求 'active'")
        return False, status, errors

    return True, 'active', errors

def check_template_tokens(html: str) -> List[str]:
    """检查 HTML 中是否有未替换的模板变量

    返回: 未替换的模板变量列表
    """
    pattern = r'\{\{[^}]+\}\}'
    matches = re.findall(pattern, html)
    return list(set(matches))  # 去重

def component_exists(html: str, selector: str) -> bool:
    """检查组件 selector 是否存在。

    Profile 中的 selector 沿用 v0.9 的 CSS selector 表达（如 `.chapter:contains('Gate 1')`）。
    v0.9.1 strict 校验不能把 CSS selector 当正则直接搜，否则会误判正向 fixture 失败。
    这里优先用 BeautifulSoup CSS selector；对 `:contains()` 做兼容转换。
    """
    if not selector:
        return False

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        selectors_to_try = [selector]
        if ':contains(' in selector:
            # 先使用 SoupSieve 推荐的新语法，避免 Python 3.14 环境输出 FutureWarning。
            selectors_to_try = [selector.replace(':contains(', ':-soup-contains('), selector]

        for css_selector in selectors_to_try:
            try:
                if soup.select(css_selector):
                    return True
            except Exception:
                continue
    except Exception:
        pass

    # 兜底：支持最常见的 class selector，避免引入额外依赖时完全失效。
    if selector.startswith('.') and ':contains(' not in selector:
        class_name = selector[1:].split()[0].split('.')[0]
        return re.search(r'class=["\'][^"\']*\b' + re.escape(class_name) + r'\b', html, re.IGNORECASE) is not None

    return False


def validate_required_components(html: str, profile: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """验证必选组件是否存在

    返回: (是否通过, 缺失的必选组件, 缺失的关键组件)
    """
    missing_required = []
    missing_critical = []

    required_components = profile.get('required_components', {})
    coverage_requirements = profile.get('coverage_requirements', {})
    critical_components = set(coverage_requirements.get('critical_components', []))

    for category, components in required_components.items():
        for component_name, component_spec in components.items():
            if component_spec.get('required', False):
                selector = component_spec.get('selector', '')
                if selector and not component_exists(html, selector):
                    missing_required.append(f"{category}.{component_name}")
                    if component_name in critical_components:
                        missing_critical.append(component_name)

    return len(missing_required) == 0, missing_required, missing_critical

def generate_validation_report(profile_code: str, status: str, errors: List[str], warnings: List[str],
                               coverage: int = 0) -> Dict[str, Any]:
    """生成结构化校验报告"""
    return {
        "contract_version": "0.9.1",
        "profile": profile_code,
        "status": status,
        "coverage": coverage,
        "errors": errors,
        "warnings": warnings,
        "timestamp": datetime.now().isoformat()
    }

def load_color_theme(theme_name):
    """加载配色方案 yml 文件"""
    script_dir = Path(__file__).parent
    theme_path = script_dir / "color-themes" / f"{theme_name}.yml"
    if not theme_path.exists():
        print(f"❌ 配色文件不存在: {theme_path}")
        sys.exit(1)

    with open(theme_path) as f:
        content = f.read()

    # 解析 YAML（简化版，只解析键值对）
    theme = {}
    in_tokens = False
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('---'):
            continue
        if line.startswith('name:') or line.startswith('label:') or line.startswith('description:'):
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
    skeleton_path = script_dir / "skeleton.html"
    with open(skeleton_path) as f:
        return f.read()

def load_profile(profile_code: str, registry: Optional[Dict[str, Any]] = None, schema: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """加载 profile 配置文件并校验

    策略：fail-fast
    - 未注册 profile：失败
    - 非 active profile：失败
    - profile 文件不存在：失败
    - schema 校验失败：失败
    """
    script_dir = Path(__file__).parent
    profile_path = script_dir / "profiles" / f"{profile_code}.json"

    # 加载 registry 和 schema（如果未提供）
    if registry is None:
        registry = load_registry()
    if schema is None:
        schema = load_schema()

    # 1. 检查 profile 是否已注册且为 active
    is_registered, status, registration_errors = validate_profile_registration(profile_code, registry)
    if not is_registered:
        print(f"❌ Profile 校验失败:")
        for error in registration_errors:
            print(f"  - {error}")
        sys.exit(1)

    # 2. 检查 profile 文件是否存在
    if not profile_path.exists():
        print(f"❌ Profile 文件不存在: {profile_path}")
        print(f"  Profile '{profile_code}' 在 registry 中注册为 active，但文件缺失")
        sys.exit(1)

    # 3. 加载 profile 文件
    with open(profile_path) as f:
        profile_data = json.load(f)

    # 4. 校验 profile schema
    is_valid, schema_errors = validate_profile_schema(profile_data, schema)
    if not is_valid:
        print(f"❌ Profile schema 校验失败:")
        for error in schema_errors:
            print(f"  - {error}")
        sys.exit(1)

    return profile_data

def extract_profile_from_markdown(md_content):
    """从 Markdown 元数据提取 profile 信息"""
    # 尝试从第一行提取 skill 信息
    for line in md_content.split('\n')[:10]:
        if '# A-' in line or '# A-' in line:
            # 匹配 # A-1 或 # A-5 等
            match = re.search(r'#\s*([A]-\d+)', line)
            if match:
                return match.group(1)

    # 尝试从其他元数据行提取
    for line in md_content.split('\n')[:20]:
        if '评估报告' in line and 'A-' in line:
            match = re.search(r'([A]-\d+)', line)
            if match:
                return match.group(1)

    # v0.9.1 禁止 default_profile 自动 fallback；检测不到就返回 None，由调用方 fail-fast。
    return None

def replace_tokens(html, theme):
    """替换所有 {{TOKEN}} 占位符"""
    def replacer(match):
        token = match.group(1)
        if token in theme:
            return theme[token]
        # 可选 token 未提供，保持原样（后续会被残留检查捕获或使用默认值）
        return match.group(0)
    return re.sub(r'\{\{([^}]+)\}\}', replacer, html)

def load_state(report_dir):
    """加载 state.json 获取封面元信息"""
    state_path = Path(report_dir) / "state.json"
    if state_path.exists():
        with open(state_path) as f:
            return json.load(f)
    return {}

def extract_cover_info(report_dir, state, md_content, profile=None):
    """从 state.json 和 Markdown 内容提取封面信息"""
    case_code = state.get('case_code', '')

    # 优先从 profile 获取 skill_code，其次从 state，最后使用默认值
    if profile and 'skill_code' in profile:
        skill_code = profile['skill_code']
    else:
        skill_code = state.get('skill_code', 'A-1')

    business_unit = state.get('business_entity', '')
    date = state.get('evaluation_date', '')

    # 从 Markdown 头部元信息提取
    product_code = ''
    product_name = ''
    company_name = ''

    for line in md_content.split('\n')[:20]:
        if '评估品种' in line and '：' in line:
            val = line.split('：', 1)[-1].strip()
            product_code = val
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
        'SKILL_CODE': skill_code,
        'BUSINESS_UNIT': business_unit or '深康',
        'DATE': date or datetime.now().strftime('%Y-%m-%d'),
        'RATING': rating,
        'RATING_SHORT': rating_short,
    }

def convert_gate_cards(html_content):
    """识别 Markdown 中的结论卡并转换为 HTML gate-card 组件"""
    # Gate 结论卡模式
    pattern = r'## Gate (\d+) 结论卡\n(.*?)(?=\n## |\Z)'

    def gate_card_replacer(match):
        gate_num = match.group(1)
        content = match.group(2).strip()

        # 判定状态
        status = 'conditional'
        if '停止' in content or '未达标' in content or 'STOP' in content:
            status = 'stop'
        elif '条件通过' in content or '附条件' in content or 'CONDITIONAL' in content:
            status = 'conditional'
        elif '通过' in content and '条件' not in content:
            status = 'pass'

        status_label = {'pass': '通过', 'conditional': '条件通过', 'stop': '未达标/停止'}[status]

        # 转换内容中的 Markdown
        content_html = md_to_html_basic(content)

        return f'''<div class="gate-card gate-{status}">
  <div class="gate-title">Gate {gate_num} 结论卡</div>
  <div class="gate-label">结论：{status_label}</div>
  <div class="gate-body">{content_html}</div>
</div>'''

    return re.sub(pattern, gate_card_replacer, html_content, flags=re.DOTALL)

def convert_special_boxes(html_content):
    """识别特殊框并转换"""
    # 结论框 - 更灵活的匹配，支持有/无冒号
    html_content = re.sub(
        r'## 结论\s*[：:]?\s*\n+(.*?)(?=\n##|\n\n|$)',
        lambda m: f'<div class="conclusion-box"><strong>结论</strong>{md_to_html_basic(m.group(1))}</div>',
        html_content, flags=re.DOTALL
    )

    # 风险框
    html_content = re.sub(
        r'## 风险\s*[：:]?\s*\n+(.*?)(?=\n##|\n\n|$)',
        lambda m: f'<div class="risk-box"><strong>风险</strong>{md_to_html_basic(m.group(1))}</div>',
        html_content, flags=re.DOTALL
    )

    # 中立框
    html_content = re.sub(
        r'## 中立意见\s*[：:]?\s*\n+(.*?)(?=\n##|\n\n|$)',
        lambda m: f'<div class="neutral-box">{md_to_html_basic(m.group(1))}</div>',
        html_content, flags=re.DOTALL
    )

    # 一票否决框
    html_content = re.sub(
        r'## 一票否决项\s*[：:]?\s*\n+(.*?)(?=\n##|\n\n|$)',
        lambda m: f'<div class="veto-box"><strong>一票否决项</strong>{md_to_html_basic(m.group(1))}</div>',
        html_content, flags=re.DOTALL
    )

    # 冲突框
    html_content = re.sub(
        r'## 信息冲突\s*[：:]?\s*\n+(.*?)(?=\n##|\n\n|$)',
        lambda m: f'<div class="conflict-box">{md_to_html_basic(m.group(1))}</div>',
        html_content, flags=re.DOTALL
    )

    # 互斥规则约束框
    html_content = re.sub(
        r'## 业务主体互斥规则约束\s*[：:]?\s*\n+(.*?)(?=\n##|\n\n|$)',
        lambda m: f'<div class="exclusion-box">{md_to_html_basic(m.group(1))}</div>',
        html_content, flags=re.DOTALL
    )

    return html_content

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

def convert_stage_tags(html_content):
    """转换阶段标签。

    A-1 原始模板使用 tag-a/tag-b/tag-c 命名；本实现同时保留
    stage-a/stage-b/stage-c 作为语义别名，避免破坏已生成 fixture。
    """
    html_content = html_content.replace('[阶段A]', '<span class="stage-tag stage-a tag-a">阶段A</span>')
    html_content = html_content.replace('[阶段B]', '<span class="stage-tag stage-b tag-b">阶段B</span>')
    html_content = html_content.replace('[阶段C]', '<span class="stage-tag stage-c tag-c">阶段C</span>')
    return html_content

def convert_confidence_badges(html_content):
    """转换置信度标注"""
    html_content = re.sub(r'\[A级[‑\-]([^\]]+)\]', r'<span class="confidence-badge conf-a">A-\1</span>', html_content)
    html_content = re.sub(r'\[B级[‑\-]([^\]]+)\]', r'<span class="confidence-badge conf-b">B-\1</span>', html_content)
    html_content = re.sub(r'\[C级[‑\-]([^\]]+)\]', r'<span class="confidence-badge conf-c">C-\1</span>', html_content)
    html_content = re.sub(r'\[D级[‑\-]([^\]]+)\]', r'<span class="confidence-badge conf-d">D-\1</span>', html_content)
    return html_content

def convert_glossary_tables(html_content):
    """转换术语表"""
    pattern = r'## 术语与缩写表\s*[：:]?\s*\n+(.*?)\n*(?=\n##|$)'

    def glossary_replacer(match):
        content = match.group(1).strip()
        lines = [line.strip() for line in content.split('\n') if line.strip()]

        result = ['<table class="glossary-table">', '<thead><tr><th>术语</th><th>解释</th></tr></thead><tbody>']

        for idx, line in enumerate(lines):
            # 跳过分隔线（|------|------|）
            if re.match(r'^\|[\s\-:|]+\|$', line):
                continue
            # 跳过 Markdown 表头行（thead 已硬编码）
            if idx == 0:
                continue
            if '|' in line and not line.startswith('#'):
                # 去掉首尾空元素（"| BD | xxx |".split('|') → ['', ' BD ', ' xxx ', '']）
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if len(cells) >= 2:
                    result.append(f'<tr><td>{cells[0]}</td><td>{cells[1]}</td></tr>')

        result.append('</tbody></table>')
        return '\n'.join(result)

    return re.sub(pattern, glossary_replacer, html_content, flags=re.DOTALL)

def convert_one_pager(html_content):
    """转换 One-pager 结构"""
    # 匹配 "## One-pager 终局先立" 或类似的标题
    pattern = r'## One-pager\s+终局先立\s*[：:]?\s*\n+(.*?)(?=\n## 第|\Z)'

    def one_pager_replacer(match):
        content = match.group(1).strip()
        content_html = md_to_html_basic(content)

        return f'''<div class="one-pager">
  <div class="one-pager-header">One-pager 终局先立</div>
  {content_html}
</div>'''

    return re.sub(pattern, one_pager_replacer, html_content, flags=re.DOTALL)

def convert_role_tags(html_content):
    """转换职能层标签"""
    role_map = {
        'BD': 'role-bd',
        '技术': 'role-tech',
        '商务': 'role-comm',
        '支持': 'role-support',
        'AI': 'role-ai',
        '决策': 'role-decision',
        'PMO': 'role-pmo',
    }

    for role_cn, role_class in role_map.items():
        html_content = html_content.replace(f'[{role_cn}]', f'<span class="{role_class}">{role_cn}</span>')

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
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                stripped = lines[i].strip()
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

    for line in lines:
        if in_cover_meta:
            if re.match(r'^## 第[一二三四五六七八九十\d]+章', line):
                in_cover_meta = False
            else:
                continue

        if line.strip() == '---':
            continue

        ch_match = re.match(r'^## 第([一二三四五六七八九十\d]+)章[：:]\s*(.+)', line)
        if ch_match:
            if current_chapter:
                chapters_html.append(convert_chapter_content('\n'.join(current_chapter)))
                chapters_html.append('</div>')
                current_chapter = []

            chapter_num += 1
            ch_num_str = ch_match.group(1)
            ch_title = ch_match.group(2)

            cn_num_map = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
                         '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
                         '十一': '11', '十二': '12', '十三': '13', '十四': '14',
                         '十五': '15', '十六': '16', '十七': '17', '十八': '18',
                         '十九': '19', '二十': '20', '二十一': '21', '二十二': '22',
                         '二十三': '23', '二十四': '24', '二十五': '25', '二十六': '26',
                         '二十七': '27', '二十八': '28', '二十九': '29', '三十': '30'}
            num = cn_num_map.get(ch_num_str, ch_num_str)

            chapters_html.append(f'<div class="chapter"><h1>第{num}章 {ch_title}</h1>')
            toc_items.append(f'<div class="toc-item"><span class="toc-num">第{num}章</span><span class="toc-title">{ch_title}</span></div>')
        else:
            current_chapter.append(line)

    if current_chapter:
        chapters_html.append(convert_chapter_content('\n'.join(current_chapter)))
        chapters_html.append('</div>')

    return '\n'.join(chapters_html), '\n'.join(toc_items)

def convert_chapter_content(text):
    """转换单个章节内容"""
    # 先处理特殊组件
    text = convert_gate_cards(text)
    text = convert_battle_sections(text)
    text = convert_special_boxes(text)
    text = convert_stage_tags(text)
    text = convert_confidence_badges(text)
    text = convert_glossary_tables(text)
    text = convert_one_pager(text)
    text = convert_role_tags(text)

    # 表格转换
    text = convert_md_tables(text)

    # 标题转换
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## ((?!<).+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)

    # 加粗和斜体
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    # 段落和列表处理
    lines = text.split('\n')
    result = []
    in_list = False
    list_tag = 'ul'

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('<'):
            if in_list:
                result.append(f'</{list_tag}>')
                in_list = False
            result.append(stripped)
            continue

        if not stripped:
            if in_list:
                result.append(f'</{list_tag}>')
                in_list = False
            continue

        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list or list_tag != 'ul':
                if in_list:
                    result.append(f'</{list_tag}>')
                result.append('<ul>')
                in_list = True
                list_tag = 'ul'
            result.append(f'<li>{stripped[2:]}</li>')
            continue

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

        if not stripped.startswith('#'):
            result.append(f'<p>{stripped}</p>')

    if in_list:
        result.append(f'</{list_tag}>')

    return '\n'.join(result)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 render.py <报告目录> [配色名] [输出路径] [profile]")
        print("示例: python3 render.py ./MB-001-Mage-Biologics mckinsey-navy /tmp/report.html A-1")
        print("      python3 render.py ./MB-001-Mage-Biologics mckinsey-navy /tmp/report.html A-5")
        print("向后兼容: python3 render.py ./MB-001-Mage-Biologics mckinsey-navy /tmp/report.html")
        sys.exit(1)

    report_dir = Path(sys.argv[1])
    theme_name = sys.argv[2] if len(sys.argv) > 2 else 'mckinsey-navy'
    output_path = sys.argv[3] if len(sys.argv) > 3 else report_dir / 'REPORT.html'
    profile_code = sys.argv[4] if len(sys.argv) > 4 else None

    # 加载 registry 和 schema（预加载，用于 fail-fast 校验）
    try:
        registry = load_registry()
        schema = load_schema()
        print(f"📋 Registry 版本: {registry.get('version', 'unknown')}")
        print(f"📋 Schema 版本: {schema.get('$id', 'unknown')}")
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        sys.exit(1)

    # 读取报告
    report_path = report_dir / '04-final-report.md'
    if not report_path.exists():
        print(f"❌ 报告不存在: {report_path}")
        sys.exit(1)

    with open(report_path) as f:
        md_content = f.read()

    print(f"📄 报告: {report_path} ({len(md_content.splitlines())} 行)")

    # 确定使用的 profile
    if profile_code:
        print(f"🎯 指定 Profile: {profile_code}")
    else:
        # 从 Markdown 元数据自动检测
        profile_code = extract_profile_from_markdown(md_content)
        if not profile_code:
            # 自动检测失败，要求显式指定；不自动套用 default_profile。
            print(f"❌ 无法从 Markdown 自动检测 profile，请显式指定 profile 参数")
            print(f"  提示: 可用的 active profiles: {', '.join([k for k, v in registry.get('profiles', {}).items() if v.get('status') == 'active'])}")
            sys.exit(1)
        print(f"🔍 自动检测 Profile: {profile_code}")

    # 加载 profile 配置（包含严格校验）
    profile = load_profile(profile_code, registry, schema)
    if profile:
        print(f"📋 Profile 加载成功: {profile.get('description', '')}")
    else:
        print(f"❌ Profile 加载失败")
        sys.exit(1)

    # 加载骨架和配色
    skeleton = load_skeleton()
    theme = load_color_theme(theme_name)
    state = load_state(report_dir)

    print(f"🎨 配色: {theme_name} ({len(theme)} tokens)")
    print(f"🦴 骨架: {len(skeleton)} 字符")

    # 替换 CSS token
    html = replace_tokens(skeleton, theme)

    # 提取封面信息并替换
    cover = extract_cover_info(report_dir, state, md_content, profile)
    for key, val in cover.items():
        html = html.replace(f'{{{{{key}}}}}', val)

    # 转换章节内容
    chapters_html, toc_items = convert_chapters(md_content)

    # 替换内容占位符
    html = html.replace('{{TOC_ITEMS}}', toc_items)
    html = html.replace('{{CHAPTERS}}', chapters_html)

    # 严格校验阶段
    errors = []
    warnings = []

    # 1. 检查模板变量残留
    unreplaced_tokens = check_template_tokens(html)
    if unreplaced_tokens:
        errors.append(f"模板变量残留: {len(unreplaced_tokens)} 个")
        for token in unreplaced_tokens:
            errors.append(f"  - {token}")

    # 2. 验证必选组件
    if profile:
        components_valid, missing_required, missing_critical = validate_required_components(html, profile)
        if not components_valid:
            errors.append(f"必选组件缺失: {len(missing_required)} 个")
            for component in missing_required:
                errors.append(f"  - {component}")

        if missing_critical:
            errors.append(f"关键组件缺失: {len(missing_critical)} 个")
            for component in missing_critical:
                errors.append(f"  - {component}")

    # 3. 输出校验结果
    if errors:
        print(f"❌ 校验失败:")
        for error in errors:
            print(f"  {error}")
        print(f"\n生成结构化校验报告...")
        validation_report = generate_validation_report(
            profile_code=profile_code,
            status="fail",
            errors=errors,
            warnings=warnings,
            coverage=0
        )
        print(json.dumps(validation_report, indent=2, ensure_ascii=False))
        sys.exit(1)

    if warnings:
        print(f"⚠ 校验通过但有警告:")
        for warning in warnings:
            print(f"  {warning}")

    print("✅ 所有校验通过")

    # 写入文件
    try:
        with open(output_path, 'w') as f:
            f.write(html)
        print(f"📦 输出: {output_path} ({len(html.splitlines())} 行, {len(html):,} 字节)")
    except Exception as e:
        print(f"❌ 输出文件写入失败: {e}")
        sys.exit(1)

    # 检查输出文件是否生成
    if not Path(output_path).exists():
        print(f"❌ 输出文件未生成: {output_path}")
        sys.exit(1)

    print(f"✨ Profile: {profile_code}")

    # 输出成功校验报告
    validation_report = generate_validation_report(
        profile_code=profile_code,
        status="pass",
        errors=[],
        warnings=warnings,
        coverage=100
    )
    print(f"\n📊 校验报告:")
    print(json.dumps(validation_report, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
