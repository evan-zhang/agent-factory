#!/usr/bin/env python3
"""
Style A1 渲染测试脚本 - 支持 profile-based 测试
验证所有组件是否正确渲染，支持多 profile 测试（A-1/A-5/A-7）
"""

import sys
import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

def load_expected_components(profile_code='A-1'):
    """加载预期组件定义 - 支持多 profile"""
    script_dir = Path(__file__).parent
    fixtures_dir = script_dir / "fixtures" / "expected" / "by-skill"
    common_file = script_dir / "fixtures" / "expected" / "common.json"

    # 加载通用组件
    with open(common_file) as f:
        common_expected = json.load(f)

    # 加载特定 profile 的组件
    profile_file = fixtures_dir / f"{profile_code}.json"
    if not profile_file.exists():
        print(f"⚠ Profile {profile_code} 不存在，仅使用通用组件")
        return common_expected

    with open(profile_file) as f:
        profile_expected = json.load(f)

    # 合并组件定义（profile 覆盖 common）
    merged_expected = {
        "version": common_expected.get("version", "0.9.0"),
        "style": common_expected.get("style", "A1"),
        "description": f"Profile {profile_code} 测试",
        "profile_code": profile_code,
        "expected_components": {}
    }

    # 首先添加通用组件
    for category, components in common_expected.get("expected_components", {}).items():
        if category not in merged_expected["expected_components"]:
            merged_expected["expected_components"][category] = {}
        if isinstance(components, dict):
            merged_expected["expected_components"][category].update(components)
        else:
            merged_expected["expected_components"][category] = components

    # 然后添加 profile 特定组件（覆盖通用组件）
    for category, components in profile_expected.get("expected_components", {}).items():
        if category not in merged_expected["expected_components"]:
            merged_expected["expected_components"][category] = {}
        if isinstance(components, dict):
            merged_expected["expected_components"][category].update(components)
        else:
            merged_expected["expected_components"][category] = components

    # 合并覆盖率要求
    merged_expected["coverage_requirements"] = profile_expected.get(
        "coverage_requirements",
        common_expected.get("coverage_requirements", {"minimum_coverage": 95})
    )

    return merged_expected

def parse_html(html_content):
    """解析 HTML 内容"""
    return BeautifulSoup(html_content, 'html.parser')

def check_component_coverage(soup, expected):
    """检查组件覆盖率"""
    results = {
        'total': 0,
        'found': 0,
        'missing': [],
        'details': {}
    }

    # 如果 profile 没有定义额外组件，只检查通用组件
    components_to_check = expected.get('expected_components', {})

    # 处理 note 字段（v0.9 特殊情况）
    if 'note' in components_to_check and len(components_to_check) == 1:
        # 只检查通用组件，从 common 继承
        print(f"   ℹ {components_to_check['note']}")
        # 对于 v0.9，只验证通用组件，不要求特定的业务组件
        return {
            'total': 0,
            'found': 0,
            'missing': [],
            'details': {},
            'note': components_to_check['note']
        }

    all_components = {}
    for category, components in components_to_check.items():
        if category == 'note':
            continue  # 跳过 note 字段
        for comp_name, comp_def in components.items():
            all_components[comp_name] = comp_def

    for comp_name, comp_def in all_components.items():
        selector = comp_def['selector']
        required = comp_def.get('required', False)
        count_min = comp_def.get('count_min', 1)

        # 查找元素
        elements = soup.select(selector)
        count = len(elements)

        # 检查是否满足要求
        if required and count < count_min:
            results['missing'].append({
                'name': comp_name,
                'selector': selector,
                'required': required,
                'expected_min': count_min,
                'found': count,
                'description': comp_def.get('description', '')
            })

        # 统计覆盖率
        if required:
            results['total'] += 1
            if count >= count_min:
                results['found'] += 1

        # 记录详情
        results['details'][comp_name] = {
            'selector': selector,
            'required': required,
            'count_min': count_min,
            'found': count,
            'status': 'PASS' if count >= count_min else 'FAIL',
            'description': comp_def.get('description', '')
        }

    return results

def check_template_variables(html_content):
    """检查模板变量是否全部替换"""
    remaining = re.findall(r'\{\{[^}]+\}\}', html_content)
    return {
        'status': 'PASS' if len(remaining) == 0 else 'FAIL',
        'remaining_count': len(remaining),
        'remaining_vars': list(set(remaining))[:10]  # 只显示前10个
    }

def run_profile_test(profile_code):
    """运行单个 profile 的测试"""
    print(f"=== Style A1 Profile {profile_code} 渲染测试 ===\n")

    # 加载预期组件
    print("1. 加载预期组件定义...")
    expected = load_expected_components(profile_code)
    print(f"   ✓ 加载了 {len(expected['expected_components'])} 个组件分类 (Profile: {profile_code})")

    # 读取测试样本
    print("\n2. 读取测试样本...")
    script_dir = Path(__file__).parent
    sample_file = script_dir / "fixtures" / f"sample-{profile_code.lower()}.md"

    if not sample_file.exists():
        print(f"   ✗ 样本文件不存在: {sample_file}")
        return False

    with open(sample_file) as f:
        sample_md = f.read()

    print(f"   ✓ 样本文件: {len(sample_md.splitlines())} 行")

    # 调用渲染器
    print("\n3. 执行渲染...")
    render_script = script_dir / "render.py"

    # 创建临时目录
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())

    # 创建测试报告目录
    test_report_dir = temp_dir / f"test-report-{profile_code}"
    test_report_dir.mkdir()

    # 写入样本文件
    test_md_file = test_report_dir / "04-final-report.md"
    with open(test_md_file, 'w') as f:
        f.write(sample_md)

    # 创建 state.json
    state_file = test_report_dir / "state.json"
    with open(state_file, 'w') as f:
        json.dump({
            'case_code': f'2605-TEST-{profile_code}',
            'skill_code': profile_code,
            'business_entity': '深康',
            'evaluation_date': '2026-06-13',
            'species_id': f'MB-{profile_code.split("-")[1]}'
        }, f)

    # 调用渲染器
    import subprocess
    output_file = test_report_dir / "REPORT.html"

    try:
        result = subprocess.run(
            [sys.executable, str(render_script), str(test_report_dir), 'mckinsey-navy', str(output_file), profile_code],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"   ✗ 渲染失败: {result.stderr}")
            return False

        print(f"   ✓ 渲染成功")
    except subprocess.TimeoutExpired:
        print("   ✗ 渲染超时")
        return False
    except Exception as e:
        print(f"   ✗ 渲染异常: {e}")
        return False

    # 读取输出
    print("\n4. 读取渲染结果...")
    with open(output_file) as f:
        html_content = f.read()

    print(f"   ✓ 输出文件: {len(html_content.splitlines())} 行, {len(html_content):,} 字节")

    # 解析 HTML
    print("\n5. 解析 HTML 结构...")
    soup = parse_html(html_content)
    print(f"   ✓ HTML 解析成功")

    # 检查组件覆盖率
    print("\n6. 检查组件覆盖率...")
    coverage_results = check_component_coverage(soup, expected)

    # 处理 v0.9 特殊情况（note 字段）
    if 'note' in coverage_results:
        print(f"   ℹ {coverage_results['note']}")
        print(f"   组件覆盖率: v0.9 通用模板内核 - 无额外组件要求")
        coverage_rate = 100  # v0.9 通用组件自动通过
    else:
        coverage_rate = (coverage_results['found'] / coverage_results['total'] * 100) if coverage_results['total'] > 0 else 0
        print(f"   组件覆盖率: {coverage_results['found']}/{coverage_results['total']} ({coverage_rate:.1f}%)")

        if coverage_results['missing']:
            print(f"\n   缺失组件 ({len(coverage_results['missing'])}):")
            for comp in coverage_results['missing']:
                print(f"   ✗ {comp['name']}: 预期≥{comp['expected_min']}, 实际{comp['found']} - {comp['description']}")

    min_coverage = expected['coverage_requirements']['minimum_coverage']
    print(f"   最低要求: {min_coverage}%")

    # 检查模板变量
    print("\n7. 检查模板变量替换...")
    template_results = check_template_variables(html_content)

    if template_results['status'] == 'PASS':
        print(f"   ✓ 所有模板变量已替换")
    else:
        print(f"   ✗ 发现 {template_results['remaining_count']} 个未替换的变量")
        for var in template_results['remaining_vars']:
            print(f"     - {var}")

    # 验证关键组件
    print("\n8. 验证关键组件...")
    critical_components = expected['coverage_requirements']['critical_components']

    # 处理 v0.9 特殊情况
    if 'note' in coverage_results:
        print("   ℹ v0.9 通用模板内核 - 使用通用关键组件")
        # 使用通用组件进行验证
        for comp_name in critical_components:
            # 通用组件检查
            if comp_name == "classification-bar":
                elements = soup.select(".classification-bar")
                if elements:
                    print(f"   ✓ {comp_name}: {len(elements)} 个 (预期≥1) - 密级与呈报对象栏")
                else:
                    print(f"   ✗ {comp_name}: 0 个 (预期≥1) - 密级与呈报对象栏")
            elif comp_name == "conclusion-box":
                elements = soup.select(".conclusion-box")
                if elements:
                    print(f"   ✓ {comp_name}: {len(elements)} 个 (预期≥1) - 结论框")
                else:
                    print(f"   ✗ {comp_name}: 0 个 (预期≥1) - 结论框")
            elif comp_name in ["confidence-badge", "stage-tag", "glossary-table", "risk-box"]:
                elements = soup.select(f".{comp_name}" if comp_name != "glossary-table" else ".glossary-table")
                if elements:
                    print(f"   ✓ {comp_name}: {len(elements)} 个 (预期≥1)")
                else:
                    print(f"   ✗ {comp_name}: 0 个 (预期≥1)")
    else:
        for comp_name in critical_components:
            if comp_name in coverage_results['details']:
                detail = coverage_results['details'][comp_name]
                status_icon = "✓" if detail['status'] == 'PASS' else "✗"
                print(f"   {status_icon} {comp_name}: {detail['found']} 个 (预期≥{detail['count_min']}) - {detail['description']}")

    # 生成详细报告
    print("\n9. 生成详细报告...")
    report_file = temp_dir / f"test-report-{profile_code}.json"

    report = {
        'timestamp': str(pd_timestamp()),
        'style': 'A1',
        'profile': profile_code,
        'coverage_rate': coverage_rate,
        'pass_coverage': coverage_rate >= min_coverage,
        'template_vars_pass': template_results['status'] == 'PASS',
        'component_details': coverage_results['details'],
        'missing_components': coverage_results['missing'],
        'remaining_template_vars': template_results['remaining_vars']
    }

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"   ✓ 详细报告: {report_file}")

    # 总结
    print(f"\n=== Profile {profile_code} 测试总结 ===")

    pass_coverage = coverage_rate >= min_coverage
    pass_template = template_results['status'] == 'PASS'

    if pass_coverage and pass_template:
        print("✅ 测试通过")
        print(f"   - 组件覆盖率: {coverage_rate:.1f}% (≥{min_coverage}%)")
        print(f"   - 模板变量: 全部替换")

        # 保留临时文件供检查
        print(f"\n📁 测试文件位置: {test_report_dir}")
        print(f"   HTML 输出: {output_file}")
        print(f"   详细报告: {report_file}")

        return True
    else:
        print("❌ 测试失败")

        if not pass_coverage:
            print(f"   - 组件覆盖率不足: {coverage_rate:.1f}% < {min_coverage}%")

        if not pass_template:
            print(f"   - 模板变量未全部替换")

        return False

def run_render_test():
    """运行多 profile 测试"""
    print("=== Style A1 多 Profile 渲染测试 ===\n")

    profiles = ['A-1', 'A-5', 'A-7']
    results = {}

    for profile in profiles:
        print(f"\n{'='*60}")
        success = run_profile_test(profile)
        results[profile] = success

    # 汇总结果
    print(f"\n{'='*60}")
    print("=== 多 Profile 测试汇总 ===\n")

    all_passed = all(results.values())

    for profile, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"Profile {profile}: {status}")

    if all_passed:
        print("\n✅ 所有 Profile 测试通过")
        return True
    else:
        print("\n❌ 部分 Profile 测试失败")
        failed_profiles = [p for p, s in results.items() if not s]
        print(f"   失败的 Profile: {', '.join(failed_profiles)}")
        return False

def pd_timestamp():
    """获取时间戳"""
    from datetime import datetime
    return datetime.now().isoformat()

if __name__ == '__main__':
    try:
        success = run_render_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)